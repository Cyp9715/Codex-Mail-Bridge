"""Attachment transport tests use generated originals and synthetic accounts."""
import base64
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import accounts
import attachments
import bridge
import outlook
import thunderbird_attachments as tb
from create_demo import create_demo
from attachment_demo import mime, png, setup


class ThunderbirdAttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-mail-')
        self.env = patch.dict(os.environ, create_demo(self.temp.name)); self.env.start()
        self.profile = accounts.profiles()[0]
        accounts.select_account(self.profile['id'], 'account1', confirm=True)
        self.folder, self.raw, self.originals = setup(self.profile['path'])

    def tearDown(self):
        attachments.cleanup(); self.env.stop(); self.temp.cleanup()

    def listing(self):
        return tb.list_attachments(101)['attachments']

    def test_metadata_search_never_reads_mime_or_body(self):
        with patch.object(tb, 'selected_message', side_effect=AssertionError('Must not read cache')):
            result = bridge.search_attachments(query='Aurora', filename='agenda.pdf', sender='alex', after='2026-10-01', before='2026-11-01')
        self.assertEqual([m['id'] for m in result['messages']], [101])
        self.assertNotIn('body', result['messages'][0]); self.assertNotIn('snippet', result['messages'][0])
        self.assertEqual(bridge.search_attachments(query='October 20')['returned'], 0)
        self.assertEqual(bridge.search_attachments(filename="' OR 1=1 --")['returned'], 0)
        self.assertTrue(bridge.call_tool('thunderbird_search_attachments', {'limit': 21})['isError'])
        with accounts.database() as (db, folders, profile, account):
            statements = []; db.set_trace_callback(statements.append)
            from contextlib import contextmanager
            @contextmanager
            def active():
                yield db, folders, profile, account
            # Use an authorizer to enforce that metadata search never reads body.
            def authorize(action, table, column, *_):
                return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and column == 'c0body' else sqlite3.SQLITE_OK
            db.set_authorizer(authorize)
            with patch.object(bridge, 'database', active):
                self.assertEqual(bridge.search_attachments(filename='agenda')['returned'], 1)

    def test_listing_decodes_no_file_payloads(self):
        from email.message import Message
        original = Message.get_payload
        def reject_decode(obj, i=None, decode=False):
            if decode: raise AssertionError('Listing must not decode files')
            return original(obj, i=i, decode=False)
        with patch.object(Message, 'get_payload', reject_decode):
            entries = self.listing()
        self.assertEqual([e['name'] for e in entries], ['agenda.pdf', 'diagram.png', 'agenda.pdf'])
        self.assertTrue(entries[1]['inline']); self.assertNotEqual(entries[0]['id'], entries[2]['id'])
        first = tb.list_attachments(101, limit=1)
        self.assertTrue(first['has_more']); self.assertEqual(first['next_offset'], 1)
        self.assertEqual(tb.list_attachments(101, limit=1, offset=1)['attachments'][0]['id'], entries[1]['id'])

    def test_original_file_handoff_no_base64_text_or_document_parser(self):
        entry = self.listing()[0]
        result = bridge.call_tool('thunderbird_get_attachment', {'message_id': 101, 'attachment_id': entry['id']})
        self.assertFalse(result['isError'])
        meta = json.loads(result['content'][0]['text'])
        self.assertEqual(Path(meta['local_path']).read_bytes(), self.originals[0])
        self.assertEqual(meta['sha256'], hashlib.sha256(self.originals[0]).hexdigest())
        self.assertFalse(meta['document_parsed']); self.assertLess(len(result['content'][0]['text']), 2200)
        self.assertFalse(any(c['type'] in {'resource', 'image'} for c in result['content']))
        fetched = attachments.resource_read(meta['resource_uri'])
        self.assertEqual(base64.b64decode(fetched['contents'][0]['blob']), self.originals[0])
        self.assertEqual(attachments.resource_list(), {'resources': []})

    def test_only_requested_image_is_typed(self):
        entry = self.listing()[1]
        value = tb.get_attachment(101, entry['id'])
        pixels = next(c for c in value.content if c['type'] == 'image')
        self.assertEqual(base64.b64decode(pixels['data']), self.originals[1])
        value = tb.get_attachment(101, entry['id'], include_image=False)
        self.assertFalse(any(c['type'] == 'image' for c in value.content))

    def test_scope_deleted_other_account_and_forged_ids(self):
        entry = self.listing()[0]
        for message_id in (201, 202, 203, 301):
            with self.assertRaises(accounts.BridgeError): tb.list_attachments(message_id)
        for token in ('agenda.pdf', '../attachment', 'a_' + '0' * 64):
            with self.assertRaises(accounts.BridgeError): tb.get_attachment(101, token)
        accounts.select_account(self.profile['id'], 'account2', confirm=True)
        with self.assertRaises(accounts.BridgeError): tb.get_attachment(101, entry['id'])

    def test_deferred_read_rechecks_scope_and_removes_export(self):
        entry = self.listing()[0]; value = tb.get_attachment(101, entry['id'])
        path = Path(value.metadata['local_path'])
        accounts.select_account(self.profile['id'], 'account2', confirm=True)
        with self.assertRaises(accounts.BridgeError): attachments.resource_read(value.metadata['resource_uri'])
        self.assertFalse(path.exists())

    def test_changed_mime_and_duplicate_message_identity(self):
        entry = self.listing()[0]
        self.folder.write_bytes(self.folder.read_bytes().replace(b'Synthetic body.', b'Changed synthetic body.'))
        with self.assertRaises(accounts.BridgeError): tb.get_attachment(101, entry['id'])
        self.folder.write_bytes(self.folder.read_bytes() * 2)
        with self.assertRaisesRegex(accounts.BridgeError, 'Ambiguous'): self.listing()

    def test_missing_cache_and_mismatched_message_identity(self):
        self.folder.write_bytes(b'From - date\nMessage-ID: <different@example.test>\n\nNo match')
        with self.assertRaises(accounts.BridgeError): self.listing()
        self.folder.unlink()
        with self.assertRaises(OSError): self.listing()

    def test_overlapping_storage_is_refused(self):
        prefs = self.profile['path'] / 'prefs.js'
        with prefs.open('a', encoding='utf-8') as target:
            target.write('user_pref("mail.server.server2.directory-rel", "[ProfD]custom cache 공간");\n')
        with self.assertRaisesRegex(accounts.BridgeError, 'overlap'): self.listing()

    def test_folder_traversal_refused_before_file_access(self):
        for path in ('../INBOX', '%2e%2e/INBOX', '%2fINBOX', 'INBOX.msf', 'INBOX%5cother'):
            account = accounts.selection()[1]
            with self.assertRaises(accounts.BridgeError):
                tb.scoped_cache_path(self.profile, account, 'imap://demo@imap.example.test/' + path)

    def test_custom_absolute_maildir_and_nested_unicode_folder(self):
        self.folder.unlink(); self.folder.parent.rmdir()
        folder, raw, originals = setup(self.profile['path'], maildir=True, absolute=True)
        nested = folder.parent / 'Archive.sbd' / '분석'
        nested.parent.mkdir(); folder.rename(nested)
        with closing(sqlite3.connect(self.profile['path'] / 'global-messages-db.sqlite')) as db:
            db.execute("UPDATE folderLocations SET folderURI=? WHERE id=1", ('imap://demo@imap.example.test/Archive/%EB%B6%84%EC%84%9D',))
            db.commit()
        entries = self.listing()
        self.assertEqual(tb.source_attachment(101, entries[2]['id'])[0], originals[2])

    def test_oversize_and_malformed_base64_are_refused(self):
        raw, _ = mime([b'x' * (attachments.MAX_BYTES + 1), png(), b'duplicate'])
        self.folder.write_bytes(b'From - date\n' + raw)
        entry = self.listing()[0]
        with self.assertRaisesRegex(accounts.BridgeError, '10 MiB'): tb.get_attachment(101, entry['id'])
        self.folder.write_bytes(b'From - date\n' + self.raw.replace(base64.b64encode(self.originals[2]), b'%%%%INVALID'))
        entry = self.listing()[2]
        with self.assertRaises(accounts.BridgeError): tb.get_attachment(101, entry['id'])

    def test_encrypted_mime_is_refused_without_decryption(self):
        raw = b'Message-ID: <demo-101@example.test>\nContent-Type: multipart/encrypted; boundary=x\n\n--x\nContent-Type: application/pgp-encrypted\n\nVersion: 1\n--x--\n'
        self.folder.write_bytes(b'From - date\n' + raw)
        with self.assertRaisesRegex(accounts.BridgeError, 'Encrypted'): self.listing()

    def test_truncated_mime_never_returns_partial_originals(self):
        self.folder.write_bytes(b'From - date\n' + self.raw.rsplit(b'--', 2)[0])
        with self.assertRaisesRegex(accounts.BridgeError, 'incomplete|malformed'): self.listing()

    def test_message_key_is_verified_and_stale_key_falls_back(self):
        with closing(sqlite3.connect(self.profile['path'] / 'global-messages-db.sqlite')) as db:
            db.execute('ALTER TABLE messages ADD COLUMN messageKey INTEGER')
            db.execute('UPDATE messages SET messageKey=0 WHERE id=101')
            db.commit()
        self.assertEqual(len(self.listing()), 3)
        with closing(sqlite3.connect(self.profile['path'] / 'global-messages-db.sqlite')) as db:
            db.execute('UPDATE messages SET messageKey=17 WHERE id=101')
            db.commit()
        self.assertEqual(len(self.listing()), 3)

    def test_stdio_search_list_get_resource_and_exit_cleanup(self):
        launcher = Path(__file__).resolve().parents[1] / 'server/launch.cjs'
        process = subprocess.Popen(['node', str(launcher)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding='utf-8', env={**os.environ, 'MAIL_BRIDGE_PYTHON': sys.executable})
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        def request(n, method, params=None):
            process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': n, 'method': method, 'params': params or {}}) + '\n'); process.stdin.flush()
            return json.loads(process.stdout.readline())['result']
        initialized = request(1, 'initialize', {'protocolVersion': '2025-06-18'})
        self.assertIn('resources', initialized['capabilities'])
        search = request(2, 'tools/call', {'name': 'thunderbird_search_attachments', 'arguments': {'query': 'Aurora', 'filename': 'agenda'}})
        self.assertEqual(json.loads(search['content'][0]['text'])['returned'], 1)
        listing = request(3, 'tools/call', {'name': 'thunderbird_list_attachments', 'arguments': {'message_id': 101}})
        aid = json.loads(listing['content'][0]['text'])['attachments'][0]['id']
        result = request(4, 'tools/call', {'name': 'thunderbird_get_attachment', 'arguments': {'message_id': 101, 'attachment_id': aid}})
        meta = json.loads(result['content'][0]['text']); path = Path(meta['local_path'])
        self.assertEqual(path.read_bytes(), self.originals[0])
        resource = request(5, 'resources/read', {'uri': meta['resource_uri']})
        self.assertEqual(base64.b64decode(resource['contents'][0]['blob']), self.originals[0])
        process.stdin.close(); process.wait(timeout=15)
        self.assertEqual(process.returncode, 0); self.assertEqual(process.stderr.read(), '')
        process.stdout.close(); process.stderr.close()
        self.assertFalse(path.exists())


class TransportTests(unittest.TestCase):
    def tearDown(self): attachments.cleanup()

    def test_expiry_limit_and_untrusted_names_never_choose_path(self):
        data = b'original'
        result = attachments.transfer(data, {'name': '../../outside.exe'}, lambda: (data, {}))
        path = Path(result.metadata['local_path'])
        self.assertEqual(path.name, 'attachment.bin')
        with patch.object(attachments.time, 'monotonic', return_value=10**12):
            with self.assertRaises(accounts.BridgeError): attachments.resource_read(result.metadata['resource_uri'])
        self.assertFalse(path.exists())
        paths = []
        with patch.object(attachments, 'RESOURCE_LIMIT', 2):
            for _ in range(3): paths.append(Path(attachments.transfer(data, {'name': 'x.dat'}, lambda: (data, {})).metadata['local_path']))
            self.assertFalse(paths[0].exists()); self.assertEqual(len(attachments._resources), 2)

    def test_fake_image_is_never_emitted_and_changed_resource_refused(self):
        result = attachments.transfer(b'not an image', {'name': 'bad.png'}, lambda: (b'changed', {}))
        self.assertFalse(any(c['type'] == 'image' for c in result.content))
        with self.assertRaises(accounts.BridgeError): attachments.resource_read(result.metadata['resource_uri'])

    def test_protocol_resource_errors_are_sanitized(self):
        result = bridge.dispatch({'jsonrpc': '2.0', 'id': 1, 'method': 'resources/read', 'params': {'uri': 'file:///outside'}})
        self.assertEqual(result['error']['code'], -32002)
        self.assertNotIn('outside', result['error']['message'])
        self.assertEqual(bridge.dispatch({'id': 2, 'method': 'resources/list'})['result'], {'resources': []})


if __name__ == '__main__': unittest.main()
