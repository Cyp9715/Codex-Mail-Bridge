"""Synthetic conversation/summary evidence, never production mailbox data."""
from contextlib import closing, contextmanager
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "server"))
sys.path.insert(0, str(PLUGIN / "tests"))
import accounts
import bridge
from create_demo import create_demo
from mail_output import message_identity


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, create_demo(self.temp.name))
        self.env.start()
        self.profile = accounts.profiles()[0]
        accounts.select_account(self.profile["id"], "account1", confirm=True)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_topic_metadata_matches_parties_without_reading_body_or_url_hits(self):
        with accounts.database() as (db, folders, profile, account):
            db.set_authorizer(lambda action, table, column, *_:
                sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and column == "c0body" else sqlite3.SQLITE_OK)
            @contextmanager
            def active():
                yield db, folders, profile, account
            with patch.object(bridge, "database", active):
                self.assertEqual([m["id"] for m in bridge.search(query="alex", field="metadata")["messages"]], [102, 101])
                self.assertEqual(bridge.search(query="October", field="metadata")["returned"], 0)
        self.assertEqual(bridge.search(query="October", field="body")["returned"], 1)

    def test_same_header_label_copies_are_preserved_with_duplicate_candidate_keys(self):
        with closing(sqlite3.connect(self.profile["path"] / "global-messages-db.sqlite")) as db:
            db.execute("UPDATE messages SET headerMessageID='same@example.test' WHERE id IN (101,103)")
            db.commit()
        messages = {m["id"]: m for m in bridge.search()["messages"]}
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[101]["dedup_key"], messages[103]["dedup_key"])
        self.assertEqual(messages[101]["dedup_basis"], "internet_message_id")
        self.assertNotEqual(bridge.read(101)["message"]["body_sha256"], bridge.read(103)["message"]["body_sha256"])
        self.assertEqual(messages[101]["date_basis"], "indexed_message_date")

    def test_configured_unicode_sent_role_does_not_invalidate_account_or_guess_names(self):
        uri = "imap://demo@imap.example.test/Letters%20%E5%8F%91%E9%80%81"
        prefs = self.profile["path"] / "prefs.js"
        with prefs.open("a", encoding="utf-8") as target:
            target.write('user_pref("mail.identity.id1.fcc_folder", ' + json.dumps(uri) + ');\n')
        with closing(sqlite3.connect(self.profile["path"] / "global-messages-db.sqlite")) as db:
            db.execute("UPDATE folderLocations SET folderURI=?,name='Custom cabinet' WHERE id=2", (uri,))
            db.commit()
        roles = {f["id"]: f["role"] for f in bridge.status()["folders"]}
        self.assertEqual(roles, {1: "inbox", 2: "sent"})
        self.assertEqual(bridge.read(102)["message"]["folder_role"], "sent")

    def test_foreign_and_ambiguous_folder_preferences_cannot_extend_scope(self):
        prefs = self.profile["path"] / "prefs.js"
        with prefs.open("a", encoding="utf-8") as target:
            target.write('user_pref("mail.identity.id1.fcc_folder", "imap://other@imap.example.test/INBOX");\n')
        self.assertEqual({m["id"] for m in bridge.search()["messages"]}, {101, 102, 103})
        self.assertEqual(bridge.read(102)["message"]["folder_role"], "other")
        with prefs.open("a", encoding="utf-8") as target:
            target.write('user_pref("mail.identity.id1.fcc_folder", "imap://demo@imap.example.test/INBOX");\n')
        self.assertEqual(bridge.read(101)["message"]["folder_role"], "other")
        with prefs.open("a", encoding="utf-8") as target:
            for pref in ("fcc_folder", "draft_folder"):
                target.write('user_pref("mail.identity.id1.' + pref + '", "imap://demo@imap.example.test/Sent");\n')
        self.assertEqual(bridge.read(102)["message"]["folder_role"], "other")

    def test_long_headers_keep_full_identity_before_metadata_clipping(self):
        headers = ["x" * 450 + suffix + "@example.test" for suffix in ("one", "two")]
        with closing(sqlite3.connect(self.profile["path"] / "global-messages-db.sqlite")) as db:
            for mid, header in zip((101, 103), headers):
                db.execute("UPDATE messages SET headerMessageID=? WHERE id=?", (header, mid))
            db.commit()
        messages = {m["id"]: m for m in bridge.search()["messages"]}
        self.assertEqual(messages[101]["message_id_header"], messages[103]["message_id_header"])
        self.assertNotEqual(messages[101]["dedup_key"], messages[103]["dedup_key"])
        self.assertIn("message_id_header", messages[101]["metadata_truncated_fields"])

    def test_missing_invalid_or_truncated_headers_do_not_merge_distinct_messages(self):
        for header in ("", "not a valid header", "<bad\n@example.test>", "<<same@example.test>>"):
            a = message_identity({"id": "one", "message_id_header": header}, "outlook", "scope")
            b = message_identity({"id": "two", "message_id_header": header}, "outlook", "scope")
            self.assertEqual(a["dedup_basis"], "local_message_id")
            self.assertNotEqual(a["dedup_key"], b["dedup_key"])
        a = message_identity({"id": "one", "message_id_header": "same@example.test", "message_id_header_truncated": True}, "outlook", "scope")
        self.assertEqual(a["dedup_basis"], "local_message_id")
        self.assertNotEqual(message_identity({"id": "one"}, "outlook", "scope")["dedup_key"],
                            message_identity({"id": "one"}, "outlook", "other")["dedup_key"])


if __name__ == "__main__":
    unittest.main()
