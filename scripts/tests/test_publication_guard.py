"""Synthetic tests: publication checks must never echo rejected private input."""
import base64
import contextlib
import io
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import publication_guard as guard


class PublicationGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Synthetic Author")
        self.run_git("config", "user.email", "author@example.test")

    def run_git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True,
                       env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})

    def stage(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.run_git("add", "--", name)

    def test_synthetic_source_passes(self):
        self.stage("README.md", "Contact demo@example.test. No mail included.")
        self.assertTrue(guard.inspect(self.root, staged=True)["ok"])

    def test_real_address_shape_blocks_staged_blob_without_echo(self):
        address = "someone@" + "example.invalid"
        self.stage("README.md", address)
        result = guard.inspect(self.root, staged=True)
        self.assertFalse(result["ok"])
        self.assertNotIn(address, json.dumps(result))
        self.assertEqual(result["findings"][0]["rule"], "non-test-email")

    def test_deleted_historical_content_still_blocks(self):
        self.stage("notes.md", "private-project-marker")
        self.run_git("commit", "-qm", "Synthetic initial change")
        (self.root / "notes.md").unlink()
        self.run_git("add", "-u")
        self.run_git("commit", "-qm", "Remove synthetic note")
        result = guard.inspect(self.root, history=True, denylist=["private-project-marker"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["commits_checked"], 2)
        self.assertNotIn("private-project-marker", json.dumps(result))

    def test_commit_message_and_author_are_checked(self):
        self.stage("README.md", "Synthetic project")
        self.run_git("commit", "-qm", "Internal project marker")
        for marker in ("Internal project marker", "Synthetic Author"):
            self.assertFalse(guard.inspect(self.root, history=True, denylist=[marker])["ok"])

    def test_pending_commit_message_blocks(self):
        message = self.root / "pending-message"
        message.write_text("Internal project marker", encoding="utf-8")
        self.assertFalse(guard.inspect(self.root, staged=True, message_file=message,
                                       denylist=["Internal project marker"])["ok"])

    def test_file_paths_and_private_formats_block(self):
        for name in ("private/notes.md", "work/test.md", "outputs/result.md", "mail.eml", "mail.msg",
                     "mail.pst", "mail.ost", "mail.sqlite", "mail.sqlite-wal", "mail.msf", "prefs.js", ".env.production"):
            self.assertTrue(guard.path_findings(name), name)
        self.stage("secret-filename.md", "Synthetic")
        result = guard.inspect(self.root, staged=True, denylist=["secret-filename"])
        self.assertFalse(result["ok"])
        self.assertNotIn("secret-filename", json.dumps(result))

    def test_private_token_encodings(self):
        secret = "private-project-marker"
        variants = [secret.encode(), secret.upper().encode(), secret.encode("utf-16-le"),
                    secret.encode("utf-16-be"), base64.b64encode(secret.encode()),
                    "".join("\\u%04x" % ord(c) for c in secret).encode(),
                    "".join("%%%02x" % ord(c) for c in secret).encode()]
        for value in variants:
            self.assertIn("private-denylist-match", guard.content_findings(value, [secret]))

    def test_personal_paths_and_credentials(self):
        for value in ("C:" + "\\Users\\" + "synthetic\\mail", "/" + "home/" + "synthetic/mail",
                      "-----BEGIN " + "PRIVATE KEY-----", "ghp_" + "X" * 36):
            self.assertTrue(guard.content_findings(value.encode()))

    def test_png_pixels_do_not_produce_random_text_matches_but_metadata_is_checked(self):
        address = ("someone@" + "example.invalid").encode()
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        signature = b"\x89PNG\r\n\x1a\n"
        tail = chunk(b"IEND", b"")
        pixels = chunk(b"IDAT", address)
        self.assertNotIn("non-test-email", guard.content_findings(signature + pixels + tail))
        for metadata in (chunk(b"tEXt", b"Comment\0" + address),
                         chunk(b"zTXt", b"Comment\0\0" + zlib.compress(address)),
                         chunk(b"iTXt", b"Comment\0\0\0\0\0" + address)):
            self.assertIn("non-test-email", guard.content_findings(signature + metadata + pixels + tail))
        with self.assertRaises(guard.GuardError):
            guard.content_findings(signature + b"invalid")

    def test_reviewed_asset_exception_is_hash_bound_and_never_bypasses_private_tokens(self):
        address = ("someone@" + "example.invalid").encode()
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        data = b"\x89PNG\r\n\x1a\n" + chunk(b"tEXt", b"Contact\0" + address) + chunk(b"IEND", b"")
        oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        approved = {oid: {hashlib.sha256(address).hexdigest()}}
        with patch.object(guard, "PUBLIC_ASSET_EMAIL_HASHES", approved):
            self.assertNotIn("non-test-email", guard.content_findings(data))
            self.assertIn("private-denylist-match", guard.content_findings(data, [address.decode()]))
            self.assertIn("non-test-email", guard.content_findings(data + b"changed"))

    def test_private_denylist_never_falls_back_after_configuration_error(self):
        with self.assertRaises(guard.GuardError):
            guard.load_denylist(self.root, "private/missing.json")
        path = self.root / "private/publication-denylist.json"
        path.parent.mkdir()
        for text in ("{}", "[null]", '[""]', "not-json"):
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.load_denylist(self.root)
        path.write_text('["private-project-marker"]', encoding="utf-8")
        self.assertEqual(guard.load_denylist(self.root), ["private-project-marker"])

    def test_oversized_blob_and_symlink_fail_closed(self):
        self.stage("large.txt", "x" * (guard.MAX_BLOB + 1))
        self.assertFalse(guard.inspect(self.root, staged=True)["ok"])
        self.run_git("reset", "-q")
        oid = subprocess.check_output(["git", "-C", str(self.root), "hash-object", "-w", "--stdin"], input=b"target.md").decode().strip()
        self.run_git("update-index", "--add", "--cacheinfo", "120000," + oid + ",link.md")
        self.assertFalse(guard.inspect(self.root, staged=True)["ok"])

    def test_cli_exit_status_and_sanitized_error(self):
        self.stage("README.md", "Synthetic")
        output = io.StringIO()
        with patch.object(sys, "argv", ["publication_guard", "--repo", str(self.root), "--staged"]), contextlib.redirect_stdout(output):
            self.assertEqual(guard.main(), 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])
        output = io.StringIO()
        with patch.object(sys, "argv", ["publication_guard", "--repo", str(self.root), "--deny-file", "missing.json"]), contextlib.redirect_stdout(output):
            self.assertEqual(guard.main(), 1)
        self.assertNotIn(str(self.root), output.getvalue())

    def test_node_launcher_honors_explicit_python_and_fails_closed(self):
        launcher = Path(__file__).resolve().parents[1] / "run_publication_guard.cjs"
        self.stage("README.md", "Synthetic")
        env = {**os.environ, "MAIL_BRIDGE_PYTHON": sys.executable}
        result = subprocess.run(["node", str(launcher), "--repo", str(self.root), "--staged"],
                                env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        env["MAIL_BRIDGE_PYTHON"] = str(self.root / "missing-python")
        result = subprocess.run(["node", str(launcher), "--repo", str(self.root), "--staged"],
                                env=env, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(str(self.root), result.stderr)


if __name__ == "__main__":
    unittest.main()
