import json
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from matrix.cabinet import capsule, capsule_context, tablet
from matrix.integrations import project_context
from matrix.psyche import assess
from matrix.runtime import ModelSpec, launch_command, select_weights
from matrix.speech import speech_command, transcribe


class LocalElementsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_local_gguf_command_works_without_hub_model_id(self):
        weights = self.root / "local.gguf"
        weights.write_bytes(b"GGUF")
        provider, path = select_weights("auto", weights, self.root)
        self.assertEqual(provider, "llamacpp")
        with patch("matrix.runtime.shutil.which", return_value="llama-server"):
            command, model = launch_command(ModelSpec(provider, weights=str(path)), 1234)
        self.assertIn(str(path), command)
        self.assertIn("127.0.0.1", command)
        self.assertEqual(model, "matrix-local")
        with self.assertRaises(ValueError):
            ModelSpec(provider, url="http://localhost:1234", weights=str(path))

    def test_offline_project_skill_is_independent_of_esk(self):
        skill = self.root / ".agents" / "skills" / "sample" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: sample\ndescription: Test\n---\nUse workspace tools.\n", encoding="utf-8")
        with patch("matrix.integrations.shutil.which", return_value=None):
            self.assertIn("Use workspace tools.", project_context(self.root.resolve(), "goal", False, "sample"))

    def test_cabinet_formats_and_context_import(self):
        packet = {
            "id": "123a", "updated_at": "2026-11-10T10:00:00+00:00", "status": "completed",
            "goal": "Inspect document", "receipts": [{"request": {"path": "doc.txt"}}],
        }
        raw = capsule(packet, "Test")
        path = self.root / "task.auractx"
        path.write_bytes(raw)
        self.assertEqual(raw[:10], b"AURACTX1" + struct.pack(">H", 1))
        self.assertIn("doc.txt", capsule_context(path))
        self.assertEqual(tablet(packet)[:10], b"AURATAB1" + struct.pack(">H", 1))
        path.write_bytes(raw[:-1])
        with self.assertRaises(ValueError):
            capsule_context(path)

    def test_psyche_accepts_supplied_signal_export_only(self):
        path = self.root / "signals.json"
        calibration = self.root / "calibration.json"
        path.write_text('{"generation_id":"test"}', encoding="utf-8")
        calibration.write_text(
            '{"format_version":"2.0","profile":{},"gbm":{"feature_indices":[0]}}', encoding="utf-8"
        )
        seen = []

        class FakeDetector:
            def ingest_signals_json(self, raw):
                seen.append(json.loads(raw)["generation_id"])

            def classify(self, *, raise_on_degenerate):
                if not raise_on_degenerate:
                    raise AssertionError("Psyche must reject degenerate input.")
                return SimpleNamespace(to_dict=lambda: {
                    "verdict": "factual", "degenerate": False, "n_gen_tokens": 2, "confidence": 0.8,
                })

        def detector_for(arch, calibration_path):
            self.assertEqual(arch, "dolphin")
            calibration_data = json.loads(calibration_path.read_text(encoding="utf-8"))
            self.assertEqual(calibration_data["weights"]["gbm"], calibration_data["gbm"])
            return FakeDetector()

        sdk = SimpleNamespace(create_detector=detector_for)
        with patch.dict(sys.modules, {"psyche": sdk}):
            result = assess(path, "dolphin", calibration)
        self.assertEqual(seen, ["test"])
        self.assertEqual(result["verification"], "model_signal_assessment")

    def test_windows_and_linux_speech_commands(self):
        target = self.root / "output.wav"
        with patch("matrix.speech.sys.platform", "win32"), patch("matrix.speech.shutil.which", return_value="powershell.exe"):
            command, env = speech_command(target)
        self.assertEqual(command[0], "powershell.exe")
        self.assertIn("System.Speech", command[-1])
        self.assertEqual(env["MATRIX_SPEECH_WAV"], str(target))
        with patch("matrix.speech.sys.platform", "linux"), patch("matrix.speech.shutil.which", return_value="espeak-ng"):
            command, env = speech_command(target)
        self.assertEqual(command, ["espeak-ng", "--stdin", "-w", str(target)])
        self.assertIsNone(env)

    def test_whisper_silence_markers_do_not_become_prompts(self):
        audio = self.root / "silence.wav"
        with wave.open(str(audio), "wb") as output:
            output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            output.writeframes(b"\0" * 3200)

        def whisper(arguments, **kwargs):
            Path(arguments[arguments.index("-of") + 1]).with_suffix(".txt").write_text("[BLANK_AUDIO]")

        with patch("matrix.speech.speech_assets", return_value=("whisper-cli", self.root / "model.bin")), \
                patch("matrix.speech.audio_command", side_effect=whisper):
            with self.assertRaisesRegex(RuntimeError, "no speech"):
                transcribe(audio)
