"""Synthetic adapter tests; these do not claim another PC or Outlook edition passed."""
import copy
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import outlook
from accounts import BridgeError

ACCOUNT = {"id": "o_" + "a" * 24, "fingerprint": "b" * 64, "address": "demo@example.test",
           "name": "Review Demo", "type": 1, "supported": True}
MESSAGES = [
    {"id": "A" * 32, "conversation_id": "conversation-demo", "date": "2026-10-10T09:00:00+00:00",
     "subject": "Project Aurora 회의", "body": "Please confirm by October 20.", "sender": "alex@example.test",
     "recipients": "demo@example.test", "attachment_names": ["agenda.pdf"]},
    {"id": "B" * 32, "conversation_id": "conversation-demo", "date": "2026-10-11T10:00:00+00:00",
     "subject": "Re: Project Aurora", "body": "I will confirm.", "sender": "demo@example.test",
     "recipients": "alex@example.test", "attachment_names": []},
]


class OutlookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "different user 위치/settings/outlook.json"
        self.env = patch.dict(os.environ, {"MAIL_BRIDGE_OUTLOOK_SETTINGS": str(self.path)})
        self.env.start()
        self.calls = []
        self.mock = patch.object(outlook, "backend", side_effect=self.backend)
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.env.stop()
        self.temp.cleanup()

    def backend(self, operation, **arguments):
        self.calls.append((operation, arguments))
        if operation == "accounts":
            return {"accounts": [dict(ACCOUNT)], "outlook_version": "16.0-demo"}
        self.assertEqual(arguments["account_id"], ACCOUNT["id"])
        self.assertEqual(arguments["fingerprint"], ACCOUNT["fingerprint"])
        if operation == "validate":
            return {"validated": True}
        if operation == "scan":
            return {"account": ACCOUNT["address"], "messages": copy.deepcopy(MESSAGES), "scanned_messages": 2, "scan_incomplete": True}
        if operation == "read":
            return {"account": ACCOUNT["address"], "message": copy.deepcopy(MESSAGES[0])}
        if operation in {"attachments", "attachment"}:
            meta = {"id": "a_" + "c" * 64, "name": "agenda.pdf", "content_type": "application/pdf", "bytes": 12, "transferable": True}
            if operation == "attachments":
                return {"account": ACCOUNT["address"], "attachments": [meta], "returned": 1}
            return {"account": ACCOUNT["address"], "attachment": meta, "data_base64": base64.b64encode(b'%PDF-sample\x00\xff').decode()}
        return {"configured": True, "account": ACCOUNT["address"]}

    def select(self):
        outlook.select_account(ACCOUNT["id"], confirm=True)

    def test_discovery_and_no_implicit_selection(self):
        self.assertNotIn("fingerprint", outlook.accounts()["accounts"][0])
        self.calls.clear()
        self.assertFalse(outlook.status()["configured"])
        with self.assertRaises(BridgeError):
            outlook.search()
        self.assertEqual(self.calls, [])

    def test_explicit_selection_and_portable_private_path(self):
        with self.assertRaises(BridgeError):
            outlook.select_account(ACCOUNT["id"])
        self.select()
        self.assertTrue(self.path.is_file())
        text = self.path.read_text()
        self.assertNotIn("@", text)
        self.assertNotIn(str(self.path), text)
        self.assertEqual(set(json.loads(text)), {"version", "account_id", "fingerprint"})
        self.assertTrue(outlook.status()["configured"])

    def test_shared_store_and_unknown_account_cannot_be_selected(self):
        with patch.object(outlook, "backend", return_value={"accounts": [{**ACCOUNT, "supported": False}]}):
            with self.assertRaises(BridgeError):
                self.select()
        with self.assertRaises(BridgeError):
            outlook.select_account("o_" + "c" * 24, confirm=True)
        self.assertFalse(self.path.exists())

    def test_invalid_settings_fail_before_outlook_access(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text('{"version":1,"account_id":5,"fingerprint":null}')
        with self.assertRaises(BridgeError):
            outlook.search()
        self.assertEqual(self.calls, [])

    def test_literal_search_unicode_and_filters(self):
        self.select()
        self.assertEqual(outlook.search(query="Aurora 회의", field="subject")["returned"], 1)
        self.assertEqual(outlook.search(query="' OR 1=1 --")["returned"], 0)
        self.assertEqual(outlook.search(query="agenda.pdf", sender="alex", recipient="demo")["returned"], 1)
        self.assertEqual(outlook.search(query="October", field="body")["returned"], 1)

    def test_partial_results_and_pagination_remain_explicit(self):
        self.select()
        first = outlook.search(limit=1)
        second = outlook.search(limit=1, offset=1)
        self.assertEqual(first["messages"][0]["id"], "B" * 32)
        self.assertEqual(second["messages"][0]["id"], "A" * 32)
        self.assertTrue(first["scan_incomplete"])
        self.assertTrue(second["scan_incomplete"])
        self.assertEqual(first["next_offset"], 1)
        self.assertFalse(second["has_more"])

    def test_conversation_scope_and_order(self):
        self.select()
        value = outlook.thread("conversation-demo")
        self.assertEqual([m["id"] for m in value["messages"]], ["A" * 32, "B" * 32])
        self.assertEqual(self.calls[-1][1]["conversation_id"], "conversation-demo")
        self.assertTrue(value["scan_incomplete"])
        self.assertEqual(outlook.thread("other-conversation")["returned"], 0)

    def test_read_id_validation_and_selected_context(self):
        self.select()
        with self.assertRaises(BridgeError):
            outlook.read("'; Start-Process calc; '")
        self.assertEqual(outlook.read("A" * 32)["message"]["id"], "A" * 32)
        self.assertEqual(self.calls[-1][1]["account_id"], ACCOUNT["id"])

    def test_utc_boundaries_and_invalid_dates(self):
        self.select()
        outlook.search(after="2026-10-01", before="2026-10-17")
        self.assertEqual(self.calls[-1][1]["after"], "2026-10-01T00:00:00+00:00")
        self.assertEqual(self.calls[-1][1]["before"], "2026-10-17T00:00:00+00:00")
        for arguments in ({"after": "2026-02-31"}, {"after": "2026-10-17", "before": "2026-10-01"}):
            with self.assertRaises(BridgeError):
                outlook.search(**arguments)

    def test_attachment_metadata_search_never_requests_body_or_file(self):
        self.select()
        value = outlook.search_attachments(query="Aurora", filename="agenda.pdf", sender="alex", after="2026-10-01", before="2026-11-01")
        self.assertEqual(value["returned"], 1)
        self.assertNotIn("body", value["messages"][0]); self.assertNotIn("snippet", value["messages"][0])
        self.assertFalse(self.calls[-1][1]["include_body"])
        self.assertEqual(self.calls[-1][0], "scan")
        self.assertEqual(outlook.search_attachments(query="October 20")["returned"], 0)

    def test_original_attachment_bytes_and_selected_context(self):
        import attachments
        self.addCleanup(attachments.cleanup)
        self.select()
        listing = outlook.list_attachments("A" * 32)
        value = outlook.get_attachment("A" * 32, listing["attachments"][0]["id"])
        self.assertEqual(Path(value.metadata["local_path"]).read_bytes(), b'%PDF-sample\x00\xff')
        self.assertEqual(self.calls[-1][1]["fingerprint"], ACCOUNT["fingerprint"])

    def test_attachment_scope_invalid_input_and_changed_selection(self):
        self.select()
        for mid, token in [("bad-id", "a_" + "c" * 64), ("A" * 32, "agenda.pdf")]:
            with self.assertRaises(BridgeError): outlook.get_attachment(mid, token)
        with patch.object(outlook, "selection", side_effect=[{"account_id": "one", "fingerprint": "one"}, {"account_id": "two", "fingerprint": "two"}]), patch.object(outlook, "backend", return_value={}):
            with self.assertRaisesRegex(BridgeError, "changed"): outlook.list_attachments("A" * 32)
        with patch.object(outlook, "attachment_request", return_value={"data_base64": "%%%invalid"}):
            with self.assertRaises(BridgeError): outlook.source_attachment("A" * 32, "a_" + "c" * 64)


class RuntimeTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows PowerShell scope test")
    def test_powershell_scope_checks_with_synthetic_objects(self):
        executable = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        script = Path(__file__).with_name("test_outlook_scope.ps1")
        result = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-STA", "-File", str(script)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Outlook scope tests passed", result.stdout)

    def test_non_windows_is_reported_without_fallback(self):
        with patch.object(outlook.sys, "platform", "linux"):
            with self.assertRaisesRegex(BridgeError, "Windows"):
                outlook.backend("accounts")

    def test_runtime_path_uses_system_root_and_json_without_shell(self):
        result = subprocess.CompletedProcess([], 0, json.dumps({"ok": True, "result": {"accounts": []}}), "")
        with patch.object(outlook.sys, "platform", "win32"), patch.dict(os.environ, {"SystemRoot": "D:/Windows location"}), patch.object(outlook.subprocess, "run", return_value=result) as run:
            outlook.backend("accounts")
            args, kwargs = run.call_args
            self.assertIn("D:", args[0][0])
            self.assertEqual(json.loads(kwargs["input"]), {"operation": "accounts"})
            self.assertIs(kwargs["shell"], False)
            self.assertNotIn("-ExecutionPolicy", args[0])

    def test_security_timeout_and_backend_errors_are_sanitized(self):
        with patch.object(outlook.sys, "platform", "win32"), patch.object(outlook.subprocess, "run", side_effect=subprocess.TimeoutExpired("private path", 45)):
            with self.assertRaisesRegex(BridgeError, "security/access prompt") as error:
                outlook.backend("accounts")
            self.assertNotIn("private path", str(error.exception))
        result = subprocess.CompletedProcess([], 0, '{"ok":false,"error":"shared_delivery_store"}', "private message")
        with patch.object(outlook.sys, "platform", "win32"), patch.object(outlook.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(BridgeError, "share a delivery store"):
                outlook.backend("accounts")


if __name__ == "__main__":
    unittest.main()
