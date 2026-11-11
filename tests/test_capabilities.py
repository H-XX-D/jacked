import json
import sys
import tempfile
import unittest
from pathlib import Path
from threading import Event, Timer
from unittest.mock import patch

from matrix.capabilities import task_capabilities
from matrix.integrations import project_skills
from matrix.process import run_program
from matrix.tasks import TaskStore
from matrix.tools import execute
from matrix.workspace import Workspace


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        work = self.root / "work"
        work.mkdir()
        self.workspace = Workspace(work, self.root / "backups")
        self.store = TaskStore(self.root / "state")
        self.addCleanup(self.store.close)
        entry = work.stat()
        self.config = {"workspace": str(self.workspace.root), "workspace_identity": [entry.st_dev, entry.st_ino],
                       "model": {"provider": "ollama"}, "local_memory_requested": True}

    def test_skill_discovery_loading_and_module_contracts(self):
        path = self.workspace.root / ".agents/skills/example/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\nname: example\ndescription: Run a project check\n---\nRun checks.\n")
        self.assertEqual(project_skills(self.workspace.root), [
            {"name": "example", "description": "Run a project check"},
        ])
        tools = task_capabilities(self.workspace, self.store, self.config)
        result = execute(self.workspace, "load_project_skill", {"name": "example"}, tools)
        self.assertIn("Run checks.", result["context"])
        report = execute(self.workspace, "get_module_status", {}, tools)
        self.assertEqual(len(report["repositories"]), 14)
        self.assertNotIn("run_local_program", tools)
        with self.assertRaises(ValueError):
            execute(self.workspace, "load_project_skill", {"name": "../outside"}, tools)

    def test_task_evidence_and_exports_are_workspace_scoped(self):
        task_id = self.store.create("inspect", self.config)
        attempt = self.store.start(task_id)
        receipt = self.store.begin_tool(task_id, attempt, "read_file", {"path": "readme.txt"})
        self.store.finish_tool(receipt, "verified", {"sha256": "abc"})
        self.store.finish(task_id, "completed", answer="Inspected the file.")
        tools = task_capabilities(self.workspace, self.store, self.config)
        for format_name in ("json", "graph", "capsule", "tablet"):
            artifact = execute(self.workspace, "export_task_artifact", {
                "task_id": task_id, "format_name": format_name,
            }, tools)
            self.assertTrue(Path(artifact["path"]).is_file())
            self.assertEqual(len(artifact["sha256"]), 64)
        other = self.store.create("other", {**self.config, "workspace_identity": [1, 2]})
        with self.assertRaisesRegex(ValueError, "outside"):
            execute(self.workspace, "inspect_task_evidence", {"task_id": other}, tools)

    def test_enabled_assessors_share_the_task_tool_registry(self):
        (self.workspace.root / "signals.json").write_text("{}")
        config = {**self.config, "nexus_url": "http://127.0.0.1:1", "psyche_calibration": "calibration.json",
                  "cramps_checkout": str(self.root)}
        tools = task_capabilities(self.workspace, self.store, config)
        self.assertTrue(tools["assess_claim"].advisory)
        self.assertTrue(tools["assess_inference_signals"].advisory)
        self.assertNotIn("check_study_package", tools)
        self.workspace.allow_write = True
        tools = task_capabilities(self.workspace, self.store, config)
        with patch("matrix.capabilities.cramps_check", return_value={"report": {"blockers": ["missing"]}}):
            self.assertFalse(execute(self.workspace, "check_study_package", {"path": "."}, tools)["ok"])
        with self.assertRaises(ValueError):
            execute(self.workspace, "check_study_package", {"path": ".."}, tools)

    def test_program_authorization_output_failure_timeout_and_cancellation(self):
        arguments = json.dumps([sys.executable, "-c", "print('skill check passed')"])
        with self.assertRaisesRegex(ValueError, "disabled"):
            run_program(self.workspace, arguments)
        self.workspace.allow_execute = True
        tools = task_capabilities(self.workspace, self.store, self.config)
        result = execute(self.workspace, "run_local_program", {"argv_json": arguments}, tools)
        self.assertTrue(result["ok"])
        self.assertIn("skill check passed", result["output"])
        failed = run_program(self.workspace, json.dumps([sys.executable, "-c", "raise SystemExit(7)"]))
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["exit_code"], 7)
        noisy = run_program(self.workspace, json.dumps([sys.executable, "-c", "print('x' * 50000)"]))
        self.assertTrue(noisy["truncated"])
        self.assertEqual(len(noisy["output"]), 24_000)
        sleepy = json.dumps([sys.executable, "-c", "import time; time.sleep(60)"])
        timed = run_program(self.workspace, sleepy, 1)
        self.assertFalse(timed["ok"])
        self.assertEqual(timed["error"], "timed out")
        cancelled = Event()
        timer = Timer(0.2, cancelled.set)
        timer.start()
        try:
            with self.assertRaises(InterruptedError):
                run_program(self.workspace, sleepy, cancelled=cancelled)
        finally:
            timer.cancel()
