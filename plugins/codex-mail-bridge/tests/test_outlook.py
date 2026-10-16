"""Synthetic adapter tests; these do not claim another PC or Outlook edition passed."""
import copy
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
        self.env = patch.dict(os.environ, {"MAIL_BRIDGE_OUTLOOK_SETTINGS": str(self.path), "MAIL_BRIDGE_EXPORT_ROOT": str(Path(self.temp.name) / "exports")})
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
            Path(arguments["export_path"]).write_bytes(b'%PDF-sample\x00\xff')
            return {"account": ACCOUNT["address"], "attachment": meta, "exported": True}
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

    def test_metadata_topics_do_not_request_or_match_body(self):
        self.select()
        self.assertEqual(outlook.search(query="alex", field="metadata")["returned"], 2)
        request = self.calls[-1][1]
        self.assertFalse(request["include_body"])
        self.assertTrue(request["include_recipient_details"])
        self.assertTrue(request["include_attachment_names"])
        self.assertEqual(outlook.search(query="October", field="metadata")["returned"], 0)

    def test_duplicate_headers_remain_separate_and_missing_headers_use_local_keys(self):
        self.select()
        rows = copy.deepcopy(MESSAGES)
        for row in rows:
            row["message_id_header"] = "same@example.test"
        with patch(__name__ + ".MESSAGES", rows):
            value = outlook.search()
        self.assertEqual(value["returned"], 2)
        self.assertEqual(value["messages"][0]["dedup_key"], value["messages"][1]["dedup_key"])
        value = outlook.search()
        self.assertNotEqual(value["messages"][0]["dedup_key"], value["messages"][1]["dedup_key"])
        self.assertEqual(value["messages"][0]["dedup_basis"], "local_message_id")

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

    def test_metadata_default_snippet_opt_in_and_bounded_fields(self):
        self.select()
        value = outlook.search()
        self.assertFalse(self.calls[-1][1]["include_body"])
        self.assertNotIn("body", value["messages"][0])
        self.assertNotIn("snippet", value["messages"][0])
        outlook.search(query="Aurora", field="subject")
        self.assertFalse(self.calls[-1][1]["include_body"])
        value = outlook.search(query="October", include_snippet=True)
        self.assertTrue(self.calls[-1][1]["include_body"])
        self.assertIn("October 20", value["messages"][0]["snippet"])
        long = {**MESSAGES[0], "subject": "S" * 20000, "recipients": "R" * 20000,
                "attachment_names": ["F" * 1000] * 200}
        with patch.object(outlook, "backend", return_value={"account": ACCOUNT["address"], "messages": [long], "scanned_messages": 1, "scan_incomplete": False}):
            item = outlook.search()["messages"][0]
        self.assertLess(len(json.dumps(item)), 3000)
        self.assertTrue(item["attachment_names_truncated"])
        self.assertIn("subject", item["metadata_truncated_fields"])

    def test_status_folder_output_is_bounded_and_continuable(self):
        self.select()
        def native(*args, **kwargs):
            return {"configured": True, "account": ACCOUNT["address"], "latest_message_date": MESSAGES[1]["date"],
                    "folders": [{"id": str(n), "name": "F" * 5000, "folder_items": n} for n in range(3)]}
        with patch.object(outlook, "backend", side_effect=native):
            first = outlook.status(folder_limit=1)
            second = outlook.status(folder_limit=1, folder_offset=first["next_folder_offset"])
        self.assertEqual(first["folder_count"], 3)
        self.assertEqual(len(first["folders"][0]["name"]), 400)
        self.assertTrue(first["folders"][0]["name_truncated"])
        self.assertEqual(second["folders"][0]["id"], "1")
        self.assertEqual(first["latest_message_date"], second["latest_message_date"])

    def test_candidate_continuation_is_separate_from_result_pagination(self):
        self.select()
        windows = [
            {"account": ACCOUNT["address"], "messages": [copy.deepcopy(MESSAGES[1])], "scanned_messages": 1, "scan_incomplete": True, "next_scan_offset": 1},
            {"account": ACCOUNT["address"], "messages": [copy.deepcopy(MESSAGES[0])], "scanned_messages": 1, "scan_incomplete": False, "next_scan_offset": None},
        ]
        with patch.object(outlook, "backend", side_effect=windows) as backend:
            first = outlook.search_attachments(filename="agenda", scan_limit=1)
            self.assertFalse(first["has_more"])
            self.assertTrue(first["scan_incomplete"])
            second = outlook.search_attachments(filename="agenda", scan_limit=1, scan_offset=first["next_scan_offset"])
        self.assertEqual(backend.call_args.kwargs["scan_offset"], 1)
        self.assertFalse(backend.call_args.kwargs["include_body"])
        self.assertEqual(second["messages"][0]["id"], "A" * 32)
        self.assertIsNone(second["next_scan_offset"])

    def test_explicit_timestamp_bounds_reach_provider_as_utc(self):
        self.select()
        result = outlook.search_attachments(after="2026-10-12T00:00:00+09:00", before="2026-10-19T00:00:00+09:00")
        self.assertEqual(self.calls[-1][1]["after"], "2026-10-11T15:00:00+00:00")
        self.assertEqual(self.calls[-1][1]["before"], "2026-10-18T15:00:00+00:00")
        self.assertEqual(result["date_range"]["bounds"], "inclusive_start_exclusive_end")
        outlook.search(after="2026-10-01T00:00:00+09:00")
        self.assertEqual(self.calls[-1][1]["after"], "2026-09-30T15:00:00+00:00")

    def test_complete_candidate_scan_still_discloses_incomplete_matching(self):
        self.select()
        truncated = {**copy.deepcopy(MESSAGES[0]), "body": "prefix", "body_truncated": True,
                     "recipients_truncated": True, "attachments_truncated": True}
        def native(*args, **kwargs):
            return {"account": ACCOUNT["address"], "messages": [copy.deepcopy(truncated)], "scanned_messages": 1, "scan_incomplete": False}
        with patch.object(outlook, "backend", side_effect=native):
            value = outlook.search(query="unseen-tail", field="body")
            self.assertEqual(value["returned"], 0)
            self.assertFalse(value["scan_incomplete"])
            self.assertTrue(value["search_incomplete"])
            self.assertEqual(value["body_matching_truncated_messages"], 1)
            value = outlook.search_attachments(filename="unseen-name")
            self.assertEqual(value["returned"], 0)
            self.assertTrue(value["match_evaluation_incomplete"])
            self.assertEqual(value["metadata_matching_truncated_messages"], 1)
            self.assertFalse(outlook.search(query="Aurora", field="subject")["search_incomplete"])

    def test_body_search_depth_is_caller_controlled_without_returning_bodies(self):
        self.select()
        full = "x" * 7000 + " needle"
        def native(operation, **kwargs):
            limit = kwargs["max_characters"]
            return {"account": ACCOUNT["address"], "messages": [{**copy.deepcopy(MESSAGES[0]), "body": full[:limit], "body_truncated": len(full) > limit}],
                    "scanned_messages": 1, "scan_incomplete": False}
        with patch.object(outlook, "backend", side_effect=native) as backend:
            shallow = outlook.search(query="needle", field="body")
            deeper = outlook.search(query="needle", field="body", body_search_limit=10000)
        self.assertEqual(shallow["returned"], 0)
        self.assertTrue(shallow["search_incomplete"])
        self.assertEqual(deeper["returned"], 1)
        self.assertFalse(deeper["search_incomplete"])
        self.assertNotIn("body", deeper["messages"][0])
        self.assertEqual(backend.call_args.kwargs["max_characters"], 10000)

    def test_thread_aggregate_budget_and_later_body_section_request(self):
        self.select()
        messages = [{**copy.deepcopy(m), "body": "x" * 6000, "body_offset": 0,
                     "body_offset_unit": "utf16_code_units", "body_characters": 6000} for m in MESSAGES]
        messages[1].update(body="\U0001f680" * 6000, body_characters=12000)
        with patch.object(outlook, "backend", return_value={"account": ACCOUNT["address"], "messages": messages, "scanned_messages": 2, "scan_incomplete": False}):
            value = outlook.thread("conversation-demo", max_total_characters=6500)
        self.assertEqual(sum(len(m["body"]) for m in value["messages"]), 6500)
        self.assertTrue(value["body_budget_exhausted"])
        item = value["messages"][1]
        self.assertEqual(item["next_body_offset"], 1000)
        outlook.read(item["id"], body_offset=item["next_body_offset"], max_characters=2000)
        self.assertEqual(self.calls[-1][1]["body_offset"], 1000)
        self.assertEqual(self.calls[-1][1]["max_characters"], 2000)

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
        self.assertEqual(value.metadata["message_id"], "A" * 32)
        self.assertEqual(value.metadata["attachment_id"], listing["attachments"][0]["id"])
        self.assertEqual(value.metadata["client"], "outlook")
        self.assertEqual(self.calls[-1][1]["fingerprint"], ACCOUNT["fingerprint"])

    def test_attachment_scope_invalid_input_and_changed_selection(self):
        self.select()
        for mid, token in [("bad-id", "a_" + "c" * 64), ("A" * 32, "agenda.pdf")]:
            with self.assertRaises(BridgeError): outlook.get_attachment(mid, token)
        with patch.object(outlook, "selection", side_effect=[{"account_id": "one", "fingerprint": "one"}, {"account_id": "two", "fingerprint": "two"}]), patch.object(outlook, "backend", return_value={}):
            with self.assertRaisesRegex(BridgeError, "changed"): outlook.list_attachments("A" * 32)

    def test_subject_search_avoids_recipient_and_attachment_enumeration(self):
        self.select()
        outlook.search(query="Aurora", field="subject")
        self.assertFalse(self.calls[-1][1]["include_recipient_details"])
        self.assertFalse(self.calls[-1][1]["include_attachment_names"])
        outlook.search(recipient="alex")
        self.assertTrue(self.calls[-1][1]["include_recipient_details"])
        self.assertFalse(self.calls[-1][1]["include_attachment_names"])
        outlook.search_attachments(filename="agenda")
        self.assertTrue(self.calls[-1][1]["include_attachment_names"])

    def test_failed_provider_export_removes_partial_copy(self):
        import attachments
        self.select()
        def fail(operation, **arguments):
            Path(arguments["export_path"]).write_bytes(b"partial")
            raise BridgeError("Synthetic provider failure")
        with patch.object(outlook, "backend", side_effect=fail):
            with self.assertRaises(BridgeError):
                outlook.get_attachment("A" * 32, "a_" + "c" * 64)
        self.assertEqual(attachments.managed_exports(), [])

    def test_provider_file_limit_is_checked_after_save(self):
        import attachments
        self.select()
        with self.assertRaises(BridgeError):
            outlook.get_attachment("A" * 32, "a_" + "c" * 64, max_bytes=4)
        self.assertEqual(self.calls[-1][1]["max_bytes"], 4)
        self.assertEqual(attachments.managed_exports(), [])


class RuntimeTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows PowerShell syntax check")
    def test_powershell_sources_parse_without_executing_scripts(self):
        executable = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        paths = [Path(outlook.__file__).with_suffix(".ps1"), Path(__file__).with_name("test_outlook_scope.ps1")]
        command = "$failed=$false; foreach($p in ($env:MAIL_BRIDGE_PARSE_PATHS | ConvertFrom-Json)) { $tokens=$null; $errors=$null; [void][Management.Automation.Language.Parser]::ParseFile($p,[ref]$tokens,[ref]$errors); if($errors.Count) {$failed=$true} }; if($failed) {exit 1}"
        result = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-Command", command],
                                capture_output=True, text=True, timeout=15,
                                env={**outlook.powershell_environment(), "MAIL_BRIDGE_PARSE_PATHS": json.dumps([str(p) for p in paths])})
        self.assertEqual(result.returncode, 0, "PowerShell source syntax check failed")

    @unittest.skipUnless(sys.platform == "win32", "Windows PowerShell scope test")
    def test_powershell_scope_checks_with_synthetic_objects(self):
        executable = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        policy = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-Command", "Get-ExecutionPolicy"],
                                capture_output=True, text=True, timeout=15, env=outlook.powershell_environment())
        if policy.returncode == 0 and policy.stdout.strip() in {"Restricted", "AllSigned"}:
            self.skipTest("PowerShell policy prevents unsigned synthetic test scripts; no policy change or bypass attempted")
        script = Path(__file__).with_name("test_outlook_scope.ps1")
        result = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-STA", "-File", str(script)], capture_output=True, text=True, timeout=15,
                                env=outlook.powershell_environment())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Outlook scope tests passed", result.stdout)

    def test_non_windows_is_reported_without_fallback(self):
        with patch.object(outlook.sys, "platform", "linux"):
            with self.assertRaisesRegex(BridgeError, "Windows"):
                outlook.backend("accounts")

    def test_windows_powershell_module_defaults_preserve_policy(self):
        with patch.dict(os.environ, {"PSModulePath": "incompatible-module-location", "PSExecutionPolicyPreference": "Restricted"}):
            environment = {key.upper(): value for key, value in outlook.powershell_environment().items()}
        self.assertNotIn("PSMODULEPATH", environment)
        self.assertEqual(environment["PSEXECUTIONPOLICYPREFERENCE"], "Restricted")

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
