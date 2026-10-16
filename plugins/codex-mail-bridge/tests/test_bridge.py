import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "server"))
sys.path.insert(0, str(PLUGIN / "tests"))
import accounts
import bridge as bridge
from create_demo import create_demo


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("THUNDERBIRD_TEST_TMP"))
        self.env = create_demo(self.temp.name)
        self.patcher = patch.dict(os.environ, self.env)
        self.patcher.start()
        self.profile = accounts.profiles()[0]

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def select(self, account_id="account1"):
        return accounts.select_account(self.profile["id"], account_id, confirm=True)

    def test_no_implicit_selection(self):
        self.assertFalse(bridge.status()["configured"])
        self.assertTrue(bridge.call_tool("thunderbird_search", {})["isError"])
        self.assertFalse(accounts.settings_path().exists())

    def test_registered_absolute_profile_in_nonstandard_location(self):
        home = Path(self.env["THUNDERBIRD_HOME"])
        (home / "profiles.ini").write_text("[Profile0]\nName=Portable Profile\nIsRelative=0\nPath=" + str(self.profile["path"]) + "\n", encoding="utf-8")
        discovered = accounts.profiles()
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0]["path"], self.profile["path"])

    def test_windows_appdata_profile_discovery(self):
        home = Path(self.env["THUNDERBIRD_HOME"])
        with patch.dict(os.environ), patch.object(accounts.sys, "platform", "win32"):
            os.environ.pop("THUNDERBIRD_HOME", None)
            os.environ["APPDATA"] = str(home.parent)
            self.assertEqual(accounts.profiles()[0]["path"], self.profile["path"])

    def test_macos_and_linux_registered_locations(self):
        base = Path(self.temp.name) / "another user home"
        for platform, relative in (("darwin", "Library/Thunderbird"), ("linux", ".thunderbird"),
                                   ("linux", "snap/thunderbird/common/.thunderbird"),
                                   ("linux", ".var/app/org.mozilla.Thunderbird/.thunderbird")):
            registry = base / relative / "profiles.ini"
            registry.parent.mkdir(parents=True, exist_ok=True)
            registry.write_text("[Profile0]\nName=Alternate\nIsRelative=0\nPath=" + str(self.profile["path"]) + "\n", encoding="utf-8")
            try:
                with patch.dict(os.environ), patch.object(accounts.sys, "platform", platform), patch.object(accounts.Path, "home", return_value=base):
                    os.environ.pop("THUNDERBIRD_HOME", None)
                    self.assertEqual(accounts.profiles()[0]["path"], self.profile["path"])
            finally:
                registry.unlink()

    def test_discovery_and_explicit_selection(self):
        self.assertEqual(len(bridge.discover_profiles()["profiles"]), 1)
        self.assertEqual(len(bridge.discover_accounts(self.profile["id"])["accounts"]), 3)
        with self.assertRaises(accounts.BridgeError):
            accounts.select_account(self.profile["id"], "account1")
        self.select()
        self.assertEqual(bridge.status()["account"], "demo@example.test")
        self.assertEqual(bridge.status()["indexed_messages"], 3)

    def test_search_all_queries_are_scoped(self):
        self.select()
        self.assertEqual({m["id"] for m in bridge.search()["messages"]}, {101, 102, 103})
        for mid in (201, 202, 203, 301):
            with self.assertRaises(accounts.BridgeError):
                bridge.read(mid)
        with self.assertRaises(accounts.BridgeError):
            bridge.search(folder_id=3)

    def test_shared_thread_does_not_leak(self):
        self.select()
        self.assertEqual([m["id"] for m in bridge.thread(10)["messages"]], [101, 102])

    def test_positive_review_cases_at_tool_level(self):
        self.select()
        state = bridge.status()
        self.assertEqual(state["latest_message_date"], "2026-10-15T12:00:00+00:00")
        result = bridge.search(query="Project Aurora", sender="alex@example.test", after="2026-10-01", before="2026-10-17")
        self.assertEqual([m["id"] for m in result["messages"]], [101])
        self.assertIn("October 20", bridge.read(101)["message"]["body"])
        self.assertEqual([m["id"] for m in bridge.thread(10)["messages"]], [101, 102])
        self.assertEqual(bridge.search(limit=1)["messages"][0]["id"], 103)
        self.assertEqual(bridge.search(limit=1, offset=1)["messages"][0]["id"], 102)

    def test_keyword_unicode_and_literal_injection(self):
        self.select()
        self.assertEqual(bridge.search(query="회의 참석")["returned"], 1)
        self.assertEqual(bridge.search(query="' OR 1=1 --")["returned"], 0)
        self.assertEqual(bridge.search(query="agenda.pdf")["returned"], 1)

    def test_port_and_username_boundaries(self):
        account = accounts.account_by_id(self.profile, "account1")
        for uri in ("imap://demo@imap.example.test.evil.test/INBOX", "imap://other@imap.example.test/INBOX",
                    "imap://demo:secret@imap.example.test/INBOX", "imap://demo@imap.example.test:999/INBOX",
                    "mailbox://demo@imap.example.test/INBOX"):
            self.assertFalse(accounts.allowed_uri(uri, account))

    def test_pop3_and_account_switch(self):
        self.select("account3")
        self.assertEqual(bridge.search()["messages"][0]["id"], 301)
        with self.assertRaises(accounts.BridgeError):
            bridge.read(101)

    def test_changed_identity_fails_closed(self):
        self.select()
        prefs = self.profile["path"] / "prefs.js"
        prefs.write_text(prefs.read_text().replace("demo@example.test", "replacement@example.test"))
        self.assertTrue(bridge.call_tool("thunderbird_search", {})["isError"])

    def test_database_cannot_write(self):
        self.select()
        with accounts.database() as (db, *_):
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("DELETE FROM messages")

    def test_private_selection_has_no_address_or_path(self):
        self.select()
        saved = accounts.settings_path().read_text()
        self.assertNotIn("@", saved)
        self.assertNotIn(str(self.profile["path"]), saved)
        self.assertEqual(set(json.loads(saved)), {"version", "profile_id", "account_id", "fingerprint"})

    def previous_selection(self):
        self.select()
        saved = accounts.settings_path().read_bytes()
        storage = Path(self.temp.name) / "application-settings"
        previous = storage / "CypSoft/ThunderbirdMailBridge/settings.json"
        previous.parent.mkdir(parents=True)
        previous.write_bytes(saved)
        return storage, previous

    def test_previous_selection_survives_rename(self):
        storage, previous = self.previous_selection()
        saved = previous.read_bytes()
        with patch.dict(os.environ), patch.object(accounts.sys, "platform", "win32"):
            os.environ.pop("THUNDERBIRD_BRIDGE_SETTINGS", None)
            os.environ["LOCALAPPDATA"] = str(storage)
            current = storage / "CypSoft/MailBridge/thunderbird.json"
            self.assertEqual(accounts.settings_path(), current)
            self.assertEqual(bridge.status()["account"], "demo@example.test")
            self.assertEqual({m["id"] for m in bridge.search()["messages"]}, {101, 102, 103})
            self.assertFalse(current.exists())  # Read-only tools do not move settings.
            self.select("account2")
            self.assertTrue(current.is_file())
            self.assertEqual(bridge.status()["account"], "other@example.test")
            self.assertEqual(previous.read_bytes(), saved)

    def test_invalid_current_selection_does_not_use_previous(self):
        storage, _ = self.previous_selection()
        with patch.dict(os.environ), patch.object(accounts.sys, "platform", "win32"):
            os.environ.pop("THUNDERBIRD_BRIDGE_SETTINGS", None)
            os.environ["LOCALAPPDATA"] = str(storage)
            current = accounts.settings_path()
            current.parent.mkdir(parents=True)
            current.write_text("{}", encoding="utf-8")
            self.assertTrue(bridge.call_tool("thunderbird_search", {})["isError"])

    def test_explicit_settings_override_never_uses_previous(self):
        storage, _ = self.previous_selection()
        with patch.dict(os.environ), patch.object(accounts.sys, "platform", "win32"):
            os.environ["LOCALAPPDATA"] = str(storage)
            isolated = Path(self.temp.name) / "isolated/settings.json"
            os.environ["THUNDERBIRD_BRIDGE_SETTINGS"] = str(isolated)
            self.assertFalse(bridge.status()["configured"])
            self.assertTrue(bridge.call_tool("thunderbird_search", {})["isError"])
            self.assertFalse(isolated.exists())

    def test_invalid_inputs(self):
        self.select()
        for name, args in [("thunderbird_search", {"limit": True}), ("thunderbird_search", {"field": "bad"}),
                           ("thunderbird_read", {}), ("thunderbird_read", {"message_id": "101"}),
                           ("thunderbird_select_account", {"profile_id": self.profile["id"], "account_id": "account1", "confirm": "true"}),
                           ("thunderbird_search", {"query": "x" * 401}), ("thunderbird_search", {"sql": "SELECT 1"})]:
            self.assertTrue(bridge.call_tool(name, args)["isError"])
        with self.assertRaises(accounts.BridgeError):
            bridge.search(after="2026-02-31")

    def test_no_mail_write_or_attachment_tools(self):
        names = {t["name"] for t in bridge.TOOLS}
        self.assertEqual(len(names), 13)
        for tool in bridge.TOOLS:
            a = tool["annotations"]
            self.assertIs(a["destructiveHint"], False)
            self.assertEqual(a["openWorldHint"], tool["name"].startswith("outlook_"))
            self.assertEqual(a["readOnlyHint"], tool["name"] not in {"thunderbird_select_account", "outlook_select_account"})
        for name in ("thunderbird_send", "thunderbird_delete", "thunderbird_attachment"):
            self.assertTrue(bridge.call_tool(name, {})["isError"])

    def test_launcher_stdio_and_utf8(self):
        self.select()
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "thunderbird_search", "arguments": {"query": "회의"}}},
        ]
        result = subprocess.run(["node", str(PLUGIN / "server/launch.cjs")],
            input="\n".join(json.dumps(r) for r in requests) + "\n", capture_output=True, text=True,
            encoding="utf-8", timeout=20, env=dict(os.environ))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([r["id"] for r in replies], [1, 2, 3])
        self.assertEqual(replies[0]["result"]["serverInfo"], {"name": "mail-bridge", "version": "0.3.0"})
        self.assertEqual(len(replies[1]["result"]["tools"]), 13)
        hits = json.loads(replies[2]["result"]["content"][0]["text"])
        self.assertEqual(hits["messages"][0]["id"], 101)


if __name__ == "__main__":
    unittest.main()
