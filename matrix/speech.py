"""Local speech file input and output for the MATRIX task runner."""

import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from tempfile import TemporaryDirectory

POWERSHELL_SPEAK = """
[void][Reflection.Assembly]::LoadWithPartialName('System.Speech')
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
    if ($env:MATRIX_SPEECH_WAV) {
        $format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(
            16000,
            [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
            [System.Speech.AudioFormat.AudioChannel]::Mono)
        $speaker.SetOutputToWaveFile($env:MATRIX_SPEECH_WAV, $format)
    }
    $speaker.Speak([Console]::In.ReadToEnd())
} finally { $speaker.Dispose() }
"""


def audio_command(command, *, text=None, timeout=90, environment=None):
    try:
        result = subprocess.run(
            command, input=text, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=environment,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Local speech engine timed out.") from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[-1_000:]
        raise RuntimeError(f"Local speech engine exited {result.returncode}: {detail}")


def speech_assets():
    directory = Path(os.environ.get("MATRIX_SPEECH_HOME", Path.home() / ".jacked/speech")).expanduser()
    binary = directory / ("whisper-cli.exe" if sys.platform == "win32" else "whisper-cli")
    executable = shutil.which(str(binary)) or shutil.which("whisper-cli")
    model = Path(os.environ.get("MATRIX_WHISPER_WEIGHTS", directory / "ggml-base.en.bin")).expanduser()
    if not executable or not model.is_file():
        raise ValueError(
            "Local speech input needs whisper-cli and local weights. "
            "Set MATRIX_SPEECH_HOME or MATRIX_WHISPER_WEIGHTS."
        )
    return executable, model.resolve()


def transcribe(audio):
    audio = Path(audio).expanduser().resolve(strict=True)
    try:
        with wave.open(str(audio), "rb") as source:
            if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 16_000):
                raise ValueError("Supply a mono 16 kHz, 16-bit PCM WAV file.")
            if not 0 < source.getnframes() <= 16_000 * 300:
                raise ValueError("Supply a WAV file between zero and five minutes.")
    except (EOFError, wave.Error) as error:
        raise ValueError("Supply a valid PCM WAV file.") from error

    program, weights = speech_assets()
    with TemporaryDirectory(prefix="matrix-transcript-") as directory:
        output = Path(directory) / "transcript"
        audio_command([
            program, "-m", str(weights), "-f", str(audio), "-nt", "-np", "-ng",
            "-otxt", "-of", str(output), "-t", str(min(os.cpu_count() or 1, 4)),
        ], timeout=120)
        transcript = output.with_suffix(".txt").read_text(encoding="utf-8").strip()
    transcript = re.sub(r"\[(?:BLANK_AUDIO|SILENCE|NO_SPEECH)\]", "", transcript, flags=re.I).strip()
    if not transcript:
        raise RuntimeError("The local speech engine found no speech.")
    return transcript


def speech_command(target):
    if sys.platform == "darwin":
        command = ["/usr/bin/say", "-v", "Samantha", "-f", "-"]
        if target:
            command += ["-o", str(target), "--file-format=WAVE", "--data-format=LEI16@16000"]
        return command, None
    if sys.platform == "win32":
        shell = shutil.which("powershell.exe")
        if shell:
            environment = dict(os.environ)
            environment.pop("MATRIX_SPEECH_WAV", None)
            if target:
                environment["MATRIX_SPEECH_WAV"] = str(target)
            return [shell, "-NoProfile", "-NonInteractive", "-Command", POWERSHELL_SPEAK], environment
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak:
        return [espeak, "--stdin", *(["-w", str(target)] if target else [])], None
    raise ValueError("Install eSpeak NG for local speech output on this machine.")


def speak(text, output=None):
    text = text.strip()
    if not 1 <= len(text) <= 12_000:
        raise ValueError("Provide 1–12,000 characters for speech output.")
    if output is None:
        command, environment = speech_command(None)
        audio_command(command, text=text, environment=environment)
        return

    output = Path(output).expanduser()
    if output.suffix.lower() != ".wav" or output.exists() or output.is_symlink():
        raise ValueError("Choose a new .wav file for speech output.")
    with TemporaryDirectory(prefix="matrix-speech-", dir=output.parent) as directory:
        target = Path(directory) / "speech.wav"
        command, environment = speech_command(target)
        audio_command(command, text=text, environment=environment)
        try:
            with wave.open(str(target), "rb") as generated:
                if generated.getnframes() == 0:
                    raise RuntimeError("The local speech engine returned an empty file.")
        except (EOFError, wave.Error) as error:
            raise RuntimeError("The local speech engine returned an invalid WAV file.") from error
        with target.open("rb") as source, output.open("xb") as destination:
            shutil.copyfileobj(source, destination)
