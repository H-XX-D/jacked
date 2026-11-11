import json
import os
import subprocess
import sys
import tempfile
import threading
from unittest.mock import patch
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from matrix.integrations import nexus_claim
from matrix.model import LocalModel
from matrix.tasks import TaskStore
from matrix.workspace import Workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.files = self.root / "work"
        self.files.mkdir()
        self.backups = self.root / "backups"

    def test_read_only_and_protected_paths(self):
        workspace = Workspace(self.files, self.backups)
        external = self.root / "outside.txt"
        external.write_text("private")
        protected = ["../outside.txt", "hardlinked.txt", "api_keys.json", ".env", "CON.txt", "visible.txt:stream"]
        try:
            (self.files / "linked.txt").symlink_to(external)
        except OSError as error:
            if sys.platform != "win32" or error.winerror != 1314:
                raise
        else:
            protected.append("linked.txt")
        os.link(external, self.files / "hardlinked.txt")
        (self.files / "api_keys.json").write_text("{}")
        (self.files / "visible.txt").write_text("expected")
        self.assertEqual(workspace.list_files()["files"], ["visible.txt"])
        for path in protected:
            with self.subTest(path=path), self.assertRaises(ValueError):
                workspace.read_file(path)
        with self.assertRaises(ValueError):
            workspace.write_file("new.txt", "denied", "missing")
        self.assertFalse((self.files / "new.txt").exists())

    def test_write_readback_stale_hash_and_backup(self):
        workspace = Workspace(self.files, self.backups, True)
        created = workspace.write_file("code.py", "result = 1\n", "missing")
        self.assertEqual(workspace.check_python("code.py")["sha256"], created["sha256"])
        with self.assertRaises(ValueError):
            workspace.write_file("code.py", "result = 2\n", "missing")
        with self.assertRaises(ValueError):
            workspace.write_file("code.py", "result = 2\n", "invalid hash")
        with self.assertRaises(SyntaxError):
            workspace.write_file("code.py", "result =\n", created["sha256"])
        changed = workspace.write_file("code.py", "result = 2\n", created["sha256"])
        self.assertEqual(Path(changed["backup"]).read_text(), "result = 1\n")
        self.assertEqual(workspace.read_file("code.py")["text"], "result = 2\n")
        self.assertEqual(workspace.read_file("code.py")["sha256"], changed["sha256"])

    def test_run_lock_releases_and_interruption_is_visible(self):
        state = self.root / "state"
        first = TaskStore(state)
        self.addCleanup(first.close)
        second = TaskStore(state)
        self.addCleanup(second.close)
        with first.exclusive_run():
            task = first.create("modify", {})
            attempt = first.start(task)
            first.begin_tool(task, attempt, "write_file", {"path": "pending.txt"})
            with self.assertRaisesRegex(RuntimeError, "Another MATRIX"):
                with second.exclusive_run():
                    self.fail("A concurrent writer acquired the run lock.")
        with second.exclusive_run():
            self.assertEqual(second.get(task)["status"], "running")
            self.assertEqual(second.receipts(task)[0]["status"], "started")


class WireTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.workspace = self.root / "work"
        self.workspace.mkdir()
        (self.workspace / "fact.txt").write_text("Local build identifier: ZEPHYR-1734.")
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == "/api/tags":
                    self.reply({"models": [{"name": "test-model"}]})
                else:
                    self.send_response(302)
                    self.send_header("Location", "http://example.com/")
                    self.end_headers()

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append((self.path, payload))
                if self.path == "/api/verify":
                    outer.nexus_header = self.headers.get("X-API-Key")
                    self.reply({"label": "NOT_ENOUGH_INFO", "confidence": 0.8})
                    return
                if not payload.get("tools"):
                    self.reply({"choices": [{"message": {"content": "Local text response."}}]})
                    return
                native = self.path == "/api/chat"
                if payload["messages"][-1]["role"] == "tool":
                    result = json.loads(payload["messages"][-1]["content"])
                    message = {"content": result.get("text") or result.get("context") or result.get("error") or "write verified"}
                else:
                    prompt = payload["messages"][1]["content"].lower()
                    if "run_local_program" in prompt:
                        name, arguments = "run_local_program", {
                            "argv_json": json.dumps([sys.executable, "-c", "print('local skill executed')"]),
                        }
                    elif "read_project_skill" in prompt:
                        name, arguments = "read_project_skill", {}
                    elif "write" in prompt:
                        name = "write_file"
                        arguments = {"path": "new.txt", "text": "written", "expected_sha256": "missing"}
                    else:
                        name, arguments = "read_file", {"path": "fact.txt"}
                    function = {"name": name, "arguments": arguments if native else json.dumps(arguments)}
                    call = {"function": function} if native else {"id": "call_1", "type": "function", "function": function}
                    message = {"content": "", "tool_calls": [call]}
                self.reply({"message": message} if native else {"choices": [{"message": message}]})

            def reply(self, body):
                data = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "matrix", "--state-dir", str(self.root / "state"), *args],
            check=True, capture_output=True, text=True, timeout=30,
        )

    def run_cli(self, provider, goal, *flags):
        result = self.cli(
            "run", goal, "--provider", provider, "--url", self.url, "--model", "test-model",
            "--workspace", str(self.workspace), *flags,
        )
        return json.loads(self.cli("show", result.stderr.strip().split()[-1]).stdout)

    def test_ollama_wire_read_and_doctor(self):
        models = self.cli("doctor", "--provider", "ollama", "--url", self.url)
        self.assertEqual(json.loads(models.stdout)["models"], ["test-model"])
        task = self.run_cli("ollama", "Read the workspace file")
        self.assertIn("ZEPHYR-1734", task["answer"])
        self.assertEqual(task["receipts"][0]["status"], "verified")
        self.assertEqual(self.requests[-1][1]["messages"][-1]["tool_name"], "read_file")

    def test_openai_wire_write_and_permission_enforcement(self):
        blocked = self.cli_status(
            "run", "write a new file", "--provider", "openai", "--url", self.url,
            "--model", "test-model", "--workspace", str(self.workspace), "--json",
        )
        self.assertEqual(blocked.returncode, 2)
        denied = json.loads(blocked.stdout)
        self.assertEqual(denied["status"], "needs_review")
        self.assertEqual(denied["receipts"][0]["status"], "failed")
        self.assertNotIn("write_file", [item["function"]["name"] for item in self.requests[0][1]["tools"]])
        self.assertFalse((self.workspace / "new.txt").exists())
        result = self.run_cli("openai", "write a new file", "--write")
        self.assertEqual(result["receipts"][0]["result"]["verification"], "SHA-256 readback")
        self.assertEqual(self.requests[-1][1]["messages"][-1]["tool_call_id"], "call_1")
        self.assertEqual((self.workspace / "new.txt").read_text(), "written")

    def test_enabled_program_runs_through_the_normal_task_loop(self):
        task = self.run_cli("openai", "Use run_local_program", "--execute")
        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["receipts"][0]["tool"], "run_local_program")
        self.assertEqual(task["receipts"][0]["result"]["exit_code"], 0)
        self.assertIn("local skill executed", task["receipts"][0]["result"]["output"])

    def test_resume_does_not_replay_pending_write(self):
        state = self.root / "state"
        store = TaskStore(state)
        entry = self.workspace.stat()
        try:
            task = store.create("write a new file", {
                "workspace": str(self.workspace),
                "workspace_identity": [entry.st_dev, entry.st_ino],
                "write_requested": True,
                "model": {"provider": "openai", "url": self.url, "model": "test-model"},
            })
            attempt = store.start(task)
            store.begin_tool(task, attempt, "write_file", {"path": "new.txt"})
        finally:
            store.close()
        resumed = self.cli_status("resume", task)
        self.assertEqual(resumed.returncode, 2)
        report = json.loads(self.cli("show", task).stdout)
        self.assertEqual(report["attempt"], 2)
        self.assertEqual([row["status"] for row in report["receipts"]], ["started", "failed"])
        self.assertFalse((self.workspace / "new.txt").exists())

    def test_predeclared_acceptance_and_json_export(self):
        goal = ["run", "Read the workspace file", "--provider", "openai", "--url", self.url,
                "--model", "test-model", "--workspace", str(self.workspace), "--json"]
        failed = self.cli_status(*goal, "--require-python", "absent.py")
        self.assertEqual(failed.returncode, 2)
        report = json.loads(failed.stdout)
        self.assertEqual(report["schema"], "jacked.task.v1")
        self.assertEqual(report["status"], "needs_review")
        self.assertEqual(report["receipts"][-1]["status"], "failed")
        exported = self.cli("export", report["id"])
        self.assertEqual(json.loads(exported.stdout), report)

    def cli_status(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "matrix", "--state-dir", str(self.root / "state"), *args],
            capture_output=True, text=True, timeout=30,
        )

    def test_attached_skill_is_callable_and_recorded(self):
        directory = self.workspace / ".agents" / "skills" / "sample"
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Test\n---\nVerify the exact output.\n", encoding="utf-8",
        )
        task = self.run_cli("openai", "Call read_project_skill", "--skill", "sample", "--max-tokens", "1000")
        self.assertEqual(task["receipts"][0]["tool"], "read_project_skill")
        self.assertEqual(task["receipts"][0]["status"], "verified")
        self.assertIn("Verify the exact output.", task["answer"])
        self.assertEqual(self.requests[0][1]["max_tokens"], 1000)

    def test_workflow_records_advice_separately_from_observations(self):
        task = self.run_cli("openai", "Read the workspace file", "--workflow")
        self.assertEqual([row["status"] for row in task["receipts"]], ["advisory", "verified", "advisory"])
        graph = json.loads(self.cli("export", task["id"], "--format", "graph").stdout)
        self.assertEqual([edge["relation"] for edge in graph["edges"]], ["advises", "supports", "advises"])
        self.assertNotIn("tools", self.requests[0][1])
        self.assertNotIn("tools", self.requests[-1][1])

    def test_memory_is_workspace_scoped_and_opt_in(self):
        self.run_cli("openai", "Read the workspace file")
        self.run_cli("openai", "Read the workspace file again", "--memory")
        self.assertIn("Recent completed workspace tasks", self.requests[-2][1]["messages"][1]["content"])
        self.assertTrue(self.requests[-2][1]["messages"][1]["content"].endswith("Read the workspace file again"))
        self.run_cli("openai", "Read the workspace file without history")
        self.assertNotIn("Recent completed workspace tasks", self.requests[-2][1]["messages"][1]["content"])

    def test_zeta09_text_only(self):
        result = self.run_cli("zeta09", "Answer in text")
        self.assertEqual(result["answer"], "Local text response.")
        self.assertEqual(result["receipts"], [])
        self.assertNotIn("tools", self.requests[0][1])
        self.assertIn("You are MATRIX", self.requests[0][1]["system"])

    def test_nexus_assessment_is_labeled_and_uses_loopback(self):
        with patch.dict(os.environ, {"NEXUS_API_KEY": "dummy-key"}):
            report = nexus_claim(self.url, "Example claim", {"observation": "unclear"})
        self.assertEqual(self.nexus_header, "dummy-key")
        self.assertEqual(report["assessment"], "NOT_ENOUGH_INFO")
        self.assertEqual(report["verification"], "model_assessment")
        self.assertEqual(self.requests[0][0], "/api/verify")
        self.assertEqual(self.requests[0][1]["evidence"], {"observation": "unclear"})

    def test_loopback_only_and_redirect_is_rejected(self):
        with self.assertRaises(ValueError):
            LocalModel("openai", "http://example.com", "test-model")
        with self.assertRaisesRegex(RuntimeError, "HTTP 302"):
            LocalModel("openai", self.url, "test-model").models()


if __name__ == "__main__":
    unittest.main()
