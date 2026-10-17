# Original attachment handoff

Version 0.9.3 retains the original-file handoff introduced in 0.4.0. It supports
Thunderbird local MIME caches and classic Outlook by-value attachments. There are
six attachment operations, for 19 local CLI operations in total; no MCP server is used.
The bridge does not parse PDF, Word, Excel, archives or other document contents,
perform OCR, execute files, or upload files to an OpenAI Files API.

## Search before transfer

For either client use the following sequence, restricted to its explicitly
selected account:

1. `thunderbird_search_attachments` or `outlook_search_attachments` narrows mail
   by **subject**, sender, recipient, folder, explicit date/time bounds and/or filename. Subject
   query words and filename words are literal substring matches, not file-content
   searches. Default 10 results, maximum 20, with bounded filename summaries.
   Neither search reads message bodies, MIME caches or attachment payloads.
2. `*_list_attachments(message_id)` lists metadata for **one** candidate message.
   Default 20 entries, maximum 50 per page, within a 200-attachment safety bound.
   Duplicate filenames get distinct opaque IDs; inline images include content IDs.
3. `*_get_attachment(message_id, attachment_id)` transfers **one** needed original,
   default 10 MiB; `max_bytes` may explicitly allow up to 100 MiB. Never enumerate and transfer all mailbox attachments implicitly.
   User-requested broad review may search many pages and transfer relevant originals
   in manageable batches.

Refine dates/subject/sender before widening a large search. Outlook applies date
filters to its metadata table before choosing its newest candidate window, then
scans at most 1,000 candidates by default, maximum 5,000. Inspect `search_incomplete` and `scan_incomplete`;
paginate matches within that window, then follow next_scan_offset with offset 0
and unchanged filters, or partition by date/folder. The caller supplies inclusive
after/exclusive before RFC 3339 bounds or UTC dates; no natural-language presets
are needed. Matching-field truncation is disclosed even for empty results.
Thunderbird searches
indexed filenames, which can omit inline images, stale entries or unindexed mail.
An empty result does not establish absence from the complete mailbox.

## What reaches GPT and the host

Get writes the exact original bytes to a generated private local export path,
returning name, byte count, SHA-256, content type and export ID. No MCP resources,
base64 text, typed image pixels or document text are emitted by the CLI.
The host's authorized file tools read selected originals; its image tool can view
requested inline images. A local path is not proof of analysis or cloud upload.

Exports survive process exit. They default to `exports/` under the private settings
directory, with an optional local `MAIL_BRIDGE_EXPORT_ROOT` override. At most 16
files are retained, default 10 MiB each and up to 100 MiB on explicit request. Later exports or `--cleanup` remove managed
files older than 10 minutes; a full store returns `export_limit` without evicting an unexpired file.
OS locking serializes export and cleanup across processes.
Run sequentially, consume each batch, then `--release <export_id>` for each finished
file. The CLI never recursively deletes arbitrary paths, and refuses/skips linked
export roots or children. Locked files or no later cleanup can leave copies.

Version comparisons should retain the receipt's client, message ID, attachment ID,
original name, bytes and SHA-256 alongside the search metadata. Names and delivery
dates alone do not identify revisions. A verified host copy under a private task
directory can support longer analysis; it is outside bridge export cleanup.

TNEF listings/receipts include a format hint and `container_members_listed:false`.
The bridge transfers winmail.dat as an original without expanding it. An available
authorized host decoder may inspect selected inner files; no decoder is installed
or executed by the bridge. Metadata filename search cannot see container members.
See [agent workflows](AGENT_WORKFLOWS.md) for comparisons and edit-mark handling.

The mailbox remains read-only. Selection changes only private bridge settings;
get creates selected original copies. Switching accounts cannot recall previously
exported files or host/chat copies. No document-parser dependencies are added.

## Client adapters and limits

### Thunderbird

The local global index contains no attachment bytes. The adapter resolves the
selected server's registered `directory-rel` (`[ProfD]`) or absolute `directory`
preferences and `storeContractID`. It never assumes a `Mail`/`ImapMail` directory
or one developer's profile. Overlapping account roots and unsafe/escaping folder
paths are refused. Normal nested `.sbd` folders and Unicode/custom paths are supported;
hashed/special folder layouts that cannot be safely mapped are unsupported.

Only a scoped, nondeleted indexed message is eligible. Its RFC Message-ID must
match cached MIME. An offset-like `messageKey` is verified; otherwise a 64 MiB mbox window or at most 2,000 maildir files is used by default,
with a five-second scan budget and a 160 MiB message cap. Callers can follow older
`cache_scan_offset` windows, widen `cache_scan_bytes` up to 256 MiB, or raise
`maildir_scan_limit` up to 100,000 and continue `maildir_scan_offset` windows.
Maildir misses disclose `next_maildir_scan_offset`; filesystem changes can shift
entry windows. Missing mbox results disclose the next window
in structured error details. Full MIME is read only for matching header identities;
messages crossing window boundaries remain complete. Missing/ambiguous identities,
unavailable cache and changed account/message/attachment IDs fail closed.

MIME handling only separates/decode-transports attachments. Listing reads one
message's MIME structure but decodes **no** attachment payloads; only the requested
part is decoded on get. No document contents are interpreted. Malformed encodings,
ambiguous escaped mbox payloads, excessive MIME nesting/parts, over 200 attachments
and encrypted/protected MIME are refused. Nested message attachments and TNEF
expansion are unsupported. No network fetch or decryption is attempted. A future
Thunderbird companion could broaden cache/layout coverage; none is required or
claimed implemented in this release.

### Classic Outlook / Office 2019

The existing COM adapter checks the selected account fingerprint, unique delivery
store, eligible folder and item's parent before attachment access. Metadata IDs bind
the account, message, index, filename, size, type, content ID and modification time.
Only by-value files within the requested `max_bytes` limit (default 10 MiB,
maximum 100 MiB) are copied using the documented
[Attachment.SaveAsFile](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.saveasfile)
method. The destination is a bridge-generated private file, never an input path
or attachment filename. Python checks the file type, actual byte limit, SHA-256
and account selection, then returns only metadata. No base64 attachment bytes are
transported over JSON. A failed provider or identity check attempts to remove its partial
copy; locked files can remain for later cleanup. No message save, UI opening or read-state assignment is used.

Listings include at most 200 attachments and disclose truncation. Linked/cloud,
OLE, embedded-message and protected/IRM/S/MIME items are unsupported. Providers may
not expose the original bytes and can use their normal network connection. The
bridge never weakens Outlook or organizational security settings.

## Verification

Synthetic tests cover metadata-only search, listing without payload decoding,
duplicate names, byte/hash equality, mbox/maildir/custom paths, input/scope/change
and protection limits, plus CLI search/list/get, survival after process exit,
host-side file reading and explicit release. No binary bytes or image pixels are
returned as JSON. Expiry, retention, cross-process storage and nonrecursive cleanup
have synthetic coverage. PowerShell scope tests use synthetic COM objects.

Extracted ZIP CLI attachment get passed with live Thunderbird and classic Outlook
for Windows; original-byte hashes and explicit cleanup were checked. A new installed
desktop plugin conversation, other providers and another PC remain unverified.
See [release validation](RELEASE_VALIDATION.md). See [CLI contract](CLI.md),
[verification evidence](../plugins/codex-mail-bridge/docs/REVIEW.md) and [publication controls](DEVELOPMENT_SECURITY.md).
