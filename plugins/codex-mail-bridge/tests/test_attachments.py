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
import thunderbird_attachments as tb
from create_demo import create_demo
from attachment_demo import mime, png, setup


class ThunderbirdAttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-mail-')
        environment = create_demo(self.temp.name)
        environment['MAIL_BRIDGE_EXPORT_ROOT'] = str(Path(self.temp.name) / 'exports')
        self.env = patch.dict(os.environ, environment); self.env.start()
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
        self.assertFalse(bridge.call_operation('thunderbird_search_attachments', {'limit': 21})['ok'])
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
        result = bridge.call_operation('thunderbird_get_attachment', {'message_id': 101, 'attachment_id': entry['id']})
        self.assertTrue(result['ok'])
        meta = result['result']
        self.assertEqual(Path(meta['local_path']).read_bytes(), self.originals[0])
        self.assertEqual(meta['sha256'], hashlib.sha256(self.originals[0]).hexdigest())
        self.assertFalse(meta['document_parsed'])
        self.assertEqual(meta['client'], 'thunderbird')
        self.assertEqual(meta['message_id'], 101)
        self.assertEqual(meta['attachment_id'], entry['id'])
        self.assertEqual(meta['format_hint'], 'document')
        self.assertLess(len(json.dumps(result)), 2200)
        self.assertFalse({'blob', 'data', 'resource_uri', 'content'} & set(meta))

    def test_image_is_an_original_file_for_explicit_host_viewing(self):
        entry = self.listing()[1]
        value = tb.get_attachment(101, entry['id'])
        self.assertEqual(value.metadata['content_type'], 'image/png')
        self.assertEqual(Path(value.metadata['local_path']).read_bytes(), self.originals[1])
        self.assertFalse(hasattr(value, 'content'))

    def test_tnef_is_hinted_without_expansion_and_only_original_bytes_are_exported(self):
        from email.message import EmailMessage, Message
        from email import policy
        original = b'\x78\x9f\x3e\x22' + b'Synthetic opaque transport container'
        message = EmailMessage(policy=policy.SMTP)
        message['Message-ID'] = '<demo-101@example.test>'
        message.set_content('Synthetic container example')
        message.add_attachment(original, maintype='application', subtype='ms-tnef', filename='winmail.dat')
        self.folder.write_bytes(b'From - date\n' + message.as_bytes())
        payload = Message.get_payload
        def no_decode(part, i=None, decode=False):
            if decode: raise AssertionError('Container listing decoded bytes')
            return payload(part, i=i, decode=False)
        with patch.object(Message, 'get_payload', no_decode):
            entry = self.listing()[0]
        self.assertEqual(entry['format_hint'], 'tnef')
        self.assertFalse(entry['container_members_listed'])
        value = tb.get_attachment(101, entry['id']).metadata
        self.assertEqual(Path(value['local_path']).read_bytes(), original)
        self.assertEqual(value['content_type'], 'application/ms-tnef')
        self.assertEqual(value['host_action'], 'inspect_container_with_host_tools')
        self.assertFalse(value['document_parsed'])

    def test_same_filename_originals_keep_distinct_hashes_and_provenance(self):
        entries = self.listing()
        first = tb.get_attachment(101, entries[0]['id']).metadata
        second = tb.get_attachment(101, entries[2]['id']).metadata
        self.assertEqual(first['name'], second['name'])
        self.assertNotEqual(first['sha256'], second['sha256'])
        self.assertNotEqual(first['attachment_id'], second['attachment_id'])
        self.assertEqual(first['message_id'], second['message_id'])

    def test_scope_deleted_other_account_and_forged_ids(self):
        entry = self.listing()[0]
        for message_id in (201, 202, 203, 301):
            with self.assertRaises(accounts.BridgeError): tb.list_attachments(message_id)
        for token in ('agenda.pdf', '../attachment', 'a_' + '0' * 64):
            with self.assertRaises(accounts.BridgeError): tb.get_attachment(101, token)
        accounts.select_account(self.profile['id'], 'account2', confirm=True)
        with self.assertRaises(accounts.BridgeError): tb.get_attachment(101, entry['id'])

    def test_account_change_cannot_authorize_another_get_or_recall_host_copy(self):
        entry = self.listing()[0]
        value = tb.get_attachment(101, entry['id'])
        path = Path(value.metadata['local_path'])
        accounts.select_account(self.profile['id'], 'account2', confirm=True)
        with self.assertRaises(accounts.BridgeError):
            tb.get_attachment(101, entry['id'])
        self.assertTrue(path.exists())
        self.assertTrue(attachments.release_export(value.metadata['export_id'])['released'])
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
        with self.assertRaisesRegex(accounts.BridgeError, 'byte limit'): tb.get_attachment(101, entry['id'])
        larger = tb.get_attachment(101, entry['id'], max_bytes=attachments.MAX_BYTES + 1)
        self.assertEqual(larger.metadata['bytes'], attachments.MAX_BYTES + 1)
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

    def test_old_mbox_windows_continue_and_keep_crossing_message_complete(self):
        old = b'From - date\nMessage-ID: <old@example.test>\n\n' + b'x' * 70000 + b'\n'
        latest = b'From - date\nMessage-ID: <latest@example.test>\n\nrecent\n'
        self.folder.write_bytes(old + latest)
        with self.assertRaises(accounts.BridgeError) as caught:
            tb.mbox_message(self.folder, 'old@example.test', None, cache_scan_bytes=65536)
        self.assertEqual(caught.exception.code, 'cache_search_incomplete')
        offset = caught.exception.details['next_cache_scan_offset']
        raw = tb.mbox_message(self.folder, 'old@example.test', None, cache_scan_bytes=65536, cache_scan_offset=offset)
        self.assertEqual(raw, old.split(b'\n', 1)[1])
        self.assertEqual(tb.mbox_message(self.folder, 'old@example.test', 0), raw)

    def test_cache_limits_are_available_only_on_thunderbird_attachment_operations(self):
        schema = next(op for op in bridge.OPERATIONS if op['name'] == 'thunderbird_get_attachment')['inputSchema']
        self.assertIn('cache_scan_offset', schema['properties'])
        self.assertIn('max_bytes', schema['properties'])
        result = bridge.call_operation('thunderbird_get_attachment', {'message_id': 101, 'attachment_id': 'a_' + '0'*64, 'cache_scan_bytes': True})
        self.assertEqual(result['error']['code'], 'invalid_arguments')

    def test_maildir_cache_continues_without_reading_skipped_file_contents(self):
        folder = Path(self.temp.name)/'maildir'
        (folder/'cur').mkdir(parents=True)
        (folder/'cur'/'first').write_bytes(b'Message-ID: <first@example.test>\n\nfirst')
        (folder/'cur'/'second').write_bytes(b'Message-ID: <second@example.test>\n\nsecond')
        # The cache enumerator owns ordering; the test supplies a stable one.
        original = Path.iterdir
        def ordered(path):
            return iter(sorted(original(path)))
        with patch.object(Path, 'iterdir', ordered):
            with self.assertRaises(accounts.BridgeError) as error:
                tb.maildir_message(folder,'second@example.test',maildir_scan_limit=1)
            offset=error.exception.details['next_maildir_scan_offset']
            self.assertEqual(offset,1)
            original_open=Path.open
            def reject_skipped(path,*args,**kwargs):
                if path.name == 'first':
                    raise AssertionError('Skipped cache content was opened')
                return original_open(path,*args,**kwargs)
            with patch.object(Path,'open',reject_skipped):
                raw=tb.maildir_message(folder,'second@example.test',maildir_scan_limit=1,maildir_scan_offset=offset)
        self.assertEqual(raw,b'Message-ID: <second@example.test>\n\nsecond')

    def test_cli_search_list_get_survives_exit_and_explicit_release(self):
        launcher = Path(__file__).resolve().parents[1] / 'scripts/mail_bridge.cjs'
        def request(operation, arguments=None, release=False):
            command = ['node', str(launcher), '--release', operation] if release else ['node', str(launcher), '--call', operation, '--arguments-stdin']
            process = subprocess.run(command, input=json.dumps(arguments or {}), capture_output=True,
                                     text=True, encoding='utf-8', timeout=20,
                                     env={**os.environ, 'MAIL_BRIDGE_PYTHON': sys.executable})
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, '')
            result = json.loads(process.stdout)
            self.assertTrue(result['ok'])
            return result['result']
        search = request('thunderbird_search_attachments', {'query': 'Aurora', 'filename': 'agenda'})
        self.assertEqual(search['returned'], 1)
        listing = request('thunderbird_list_attachments', {'message_id': 101})
        aid = listing['attachments'][0]['id']
        meta = request('thunderbird_get_attachment', {'message_id': 101, 'attachment_id': aid})
        path = Path(meta['local_path'])
        self.assertEqual(path.read_bytes(), self.originals[0])
        self.assertEqual(meta['sha256'], hashlib.sha256(self.originals[0]).hexdigest())
        self.assertTrue(request(meta['export_id'], release=True)['released'])
        self.assertFalse(path.exists())

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'exports'
        self.env = patch.dict(os.environ, {'MAIL_BRIDGE_EXPORT_ROOT': str(self.root)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_expiry_limit_and_untrusted_names_never_choose_path(self):
        result = attachments.transfer(b'original', {'name': '../../outside.exe'})
        path = Path(result.metadata['local_path'])
        self.assertEqual(path.name, 'attachment.bin')
        with patch.object(attachments.time, 'time', return_value=10**12):
            self.assertEqual(attachments.expire_exports()['removed'], 1)
        self.assertFalse(path.exists())
        paths = []
        with patch.object(attachments, 'EXPORT_LIMIT', 2):
            for _ in range(2):
                paths.append(Path(attachments.transfer(b'x', {'name': 'x.dat'}).metadata['local_path']))
            with self.assertRaises(accounts.BridgeError) as error:
                attachments.transfer(b'x', {'name': 'x.dat'})
            self.assertEqual(error.exception.code, 'export_limit')
            self.assertTrue(all(path.exists() for path in paths))
            self.assertEqual(len(attachments.managed_exports()), 2)

    def test_fake_image_is_delivered_as_an_opaque_file(self):
        result = attachments.transfer(b'not an image', {'name': 'bad.png'})
        self.assertEqual(result.metadata['content_type'], 'application/octet-stream')
        self.assertFalse(hasattr(result, 'content'))

    def test_cleanup_preserves_unrelated_files_and_rejects_forged_release(self):
        value = attachments.transfer(b'synthetic', {'name': 'sample.pdf'})
        foreign = self.root / 'unrelated.txt'
        foreign.write_text('unrelated', encoding='utf-8')
        for token in ('../outside', str(foreign), 'attachment.pdf'):
            with self.assertRaises(accounts.BridgeError):
                attachments.release_export(token)
        attachments.release_export(value.metadata['export_id'])
        self.assertTrue(foreign.exists())

    def test_cleanup_does_not_follow_directory_links(self):
        value = attachments.transfer(b'synthetic', {'name': 'sample.pdf'})
        path = Path(value.metadata['local_path'])
        with patch.object(attachments, 'is_link', side_effect=lambda p: p == path.parent):
            self.assertFalse(attachments.release_export(value.metadata['export_id'])['released'])
        self.assertTrue(path.exists())

    def test_retention_is_recognized_by_another_process(self):
        value = attachments.transfer(b'synthetic', {'name': 'sample.pdf'})
        program = "import attachments,json; print(json.dumps(attachments.expire_exports()))"
        process = subprocess.run([sys.executable, '-c', program], capture_output=True, text=True,
                                 env={**os.environ, 'PYTHONPATH': str(Path(attachments.__file__).parent)}, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['remaining'], 1)
        self.assertTrue(Path(value.metadata['local_path']).exists())

    def test_concurrent_process_cannot_clean_or_allocate_during_export(self):
        self.root.mkdir()
        program = "import attachments\nfrom accounts import BridgeError\ntry: attachments.expire_exports()\nexcept BridgeError as error: print(error.code)"
        with attachments.export_lock(self.root):
            process = subprocess.run([sys.executable, '-c', program], capture_output=True, text=True,
                env={**os.environ, 'PYTHONPATH': str(Path(attachments.__file__).parent)}, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.strip(), 'export_busy')
        self.assertEqual(attachments.expire_exports()['remaining'], 0)


if __name__ == '__main__': unittest.main()
