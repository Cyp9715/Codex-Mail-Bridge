# Thunderbird local CLI contract

Version 0.11.0 provides ten operations, each in one local process. Python 3.10+
and host command/file permissions are required. There is no MCP transport,
background process, client startup or network mail fetch.

## Commands and JSON

From the plugin directory:

```powershell
node ./scripts/mail_bridge.cjs --version
node ./scripts/mail_bridge.cjs --list
node ./scripts/mail_bridge.cjs --describe thunderbird_search
node ./scripts/mail_bridge.cjs --call thunderbird_status
node ./scripts/mail_bridge.cjs --call thunderbird_search --arguments-file ./private-query.json
node ./scripts/mail_bridge.cjs --release EXPORT_ID
node ./scripts/mail_bridge.cjs --cleanup
```

Alternatively use a verified Python with `./server/bridge.py` and the same options.
Resolve installed paths rather than assuming the repository working directory.
`--list` returns ten names; `--describe` returns one schema and local side effects.
Neither reads mail. Every operation has `mailbox_write:false` and `starts_client:false`.

Without an input option, `--call` uses `{}` without waiting on stdin. A private
UTF-8/BOM argument file or explicit `--arguments-stdin` accepts one JSON object up
to 65,536 characters. Unknown/missing keys, wrong types, duplicate keys and non-JSON
constants are rejected. Mail text must never become executable command text.

Example query data:

```json
{"query":"Project Aurora","field":"subject","after":"2026-10-01T00:00:00+09:00","before":"2026-11-01T00:00:00+09:00","limit":10}
```

Success exits 0 with `{"ok":true,"result":{...}}`. Operation/input/storage errors
exit 1 with `{"ok":false,"error":{"error":"...","code":"...","retryable":false}}`.
Errors may include `next_action` and bounded `details`; they contain no tracebacks,
credentials or binary payloads. CLI syntax errors use argument-parser help.

## Operations

| Purpose | Names |
| --- | --- |
| Setup | `thunderbird_profiles`, `thunderbird_accounts`, `thunderbird_select_account` |
| Coverage | `thunderbird_status` |
| Mail | `thunderbird_search`, `thunderbird_read`, `thunderbird_thread` |
| Originals | `thunderbird_search_attachments`, `thunderbird_list_attachments`, `thunderbird_get_attachment` |

Use `--describe` for exact IDs, required arguments, defaults and bounds.
Selection needs the user's explicit profile/account choice and `confirm:true`;
only the private selection file is written. Other mailbox queries read only the
selected account. Attachment get writes a selected original to private storage.

## Search, evidence and continuation

Search defaults to 10 results, maximum 50. `field` is `subject`, `metadata`, `body`
or `any`. Metadata means subject/parties/indexed filenames; it reads no body unless
`include_snippet:true`. Query words are AND literal substrings with Unicode case
folding. `sender`, `recipient` and a scoped numeric `folder_id` refine results.
Dates use inclusive `after` and exclusive `before`: RFC 3339 with Z/offset, or a
UTC date. Follow `next_offset`; the coverage is the selected local index, not the
server mailbox. An empty result does not establish server absence.

Search/read/thread messages carry `dedup_key`, `dedup_basis`, `folder_role` and
`date_basis:indexed_message_date`. Duplicate keys preserve earlier Thunderbird
values and are scoped to an account. Valid full Message-IDs identify duplicate
candidates; invalid/truncated headers use local IDs. Every mailbox copy remains
visible. Compare hashes before collapsing materially different copies.

Folder roles use configured identity folder URIs and the inbox URI. Localized
names are never role heuristics. `other` means unknown/mixed; a folder role is
not proof of an individual message's direction. Status supports folder pagination
while reporting whole-account counts. Index modification time is not proof of sync.

Read defaults to 16,000 characters, maximum 60,000. `body_offset` counts Unicode
characters; use `next_body_offset` and prior `body_sha256` as `expected_body_sha256`
for consistent continuation. A changed body returns `body_changed`. Threads are
oldest first, default 20 messages with 6,000 characters each and a 24,000-character
total budget. Omitted sections remain available through read. Follow thread pages.

## Attachments and private file lifecycle

Attachment search is subject/filename/date/party metadata only, default 10 results,
maximum 20. List/get is scoped to one indexed message in its local MIME cache.
List defaults to 20 entries, maximum 50 per page, at most 200 attachments. Listing
does not decode attachment payloads. Duplicate filenames have distinct opaque IDs.

List/get accepts `cache_scan_bytes` (64 MiB default, 256 MiB maximum),
`cache_scan_offset` (bytes backward from mbox EOF), `maildir_scan_limit` (2,000
default, 100,000 maximum) and `maildir_scan_offset`. A bounded miss can return
`cache_search_incomplete` with `error.details.next_cache_scan_offset` or
`next_maildir_scan_offset`. Reuse successful options for get. Cache changes can
shift scan windows. The scan time budget is five seconds; full MIME is capped at
160 MiB. Unsupported, changed or ambiguous cache identities fail closed.

Get defaults to 10 MiB; explicit `max_bytes` can allow up to 100 MiB. It returns
`local_path`, `export_id`, name, bytes, SHA-256, content type and original-file
provenance (`client:thunderbird`, message/attachment IDs and format hints).
No base64, pixels, document text or cloud-upload receipt is emitted. Host tools
read/view the original separately. See [attachment support](ATTACHMENT_SUPPORT.md).

Exports default to `exports/` under the private Thunderbird settings directory;
`MAIL_BRIDGE_EXPORT_ROOT` is a local environment override, never a mail argument.
Paths are generated independently of untrusted filenames. Root/child links are
refused or skipped. At most 16 files remain; later get/cleanup expires files older
than 600 seconds without evicting unexpired files. Calls use an OS lock; contention
returns retryable `export_busy`. `--release EXPORT_ID` deletes one generated file
and its empty directory, never recursively. Locked files can remain. No background
cleanup runs, and host/chat copies cannot be recalled.
