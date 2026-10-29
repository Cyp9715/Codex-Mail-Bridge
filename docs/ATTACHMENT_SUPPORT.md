# Thunderbird original attachment handoff

Version 0.11.0 supports original files from safely mapped Thunderbird local MIME
caches. Three attachment operations are part of the eleven-operation CLI. The bridge
does not parse PDF/DOCX/XLSX or archive contents, perform OCR, execute files or call
an upload API. Host tools interpret selected originals separately.

## Search before transfer

1. `thunderbird_search_attachments` narrows mail by subject, sender, recipient,
   folder, explicit date/time bounds and indexed filename. Words are AND literal
   substrings. Default 10 results, maximum 20. No body, MIME cache or attachment
   payload is read. Indexed filenames can omit inline images and unindexed files.
2. `thunderbird_list_attachments(message_id)` lists one candidate message's MIME
   metadata. Default 20 entries, maximum 50 per page, within a 200-attachment bound.
   Duplicate filenames have distinct opaque IDs; inline images include content IDs.
   Listing reads the scoped MIME structure without decoding attachment payloads.
3. `thunderbird_get_attachment(message_id, attachment_id)` decodes and exports one
   requested original, default 10 MiB; explicit `max_bytes` can allow 100 MiB.
   Broad authorized reviews may continue search pages and consume relevant files
   sequentially in manageable batches. Never implicitly export a whole mailbox.

An empty indexed filename search does not prove absence from the cache or server.
For a known message, list its attachments directly.

## Thunderbird cache identity

The index contains no attachment bytes. The adapter resolves the selected server's
`directory-rel` (`[ProfD]`) or absolute `directory` and `storeContractID`. It never
assumes a fixed `Mail`/`ImapMail` directory or developer profile. Overlapping roots
and unsafe/escaping paths are refused. Normal nested `.sbd` folders and Unicode
custom paths work; hashed/special layouts that cannot be safely mapped do not.

Only a scoped, nondeleted indexed message is eligible. Its RFC Message-ID must
match the cached MIME. An offset-like `messageKey` is verified; otherwise a 64 MiB
mbox window or at most 2,000 maildir entries is scanned by default, within five
seconds and a 160 MiB MIME message cap. Callers may widen `cache_scan_bytes` up to
256 MiB, continue `cache_scan_offset`, or raise `maildir_scan_limit` up to 100,000
and continue `maildir_scan_offset`. Structured incomplete errors expose the next
window; filesystem changes can shift maildir windows. Reuse successful options
for get. Messages crossing mbox window boundaries remain complete.

Only matching header identities lead to full MIME reads. Missing/ambiguous IDs,
unavailable caches and changed account/message/attachment identities fail closed.
Malformed encodings, ambiguous escaped mbox payloads, excessive nesting/parts,
over 200 attachments and encrypted/protected MIME are refused. Nested message
attachments and TNEF expansion are unsupported. No network fetch or decryption is
attempted. No companion extension is required or claimed implemented.

## What reaches the host

Get returns a generated private path, original name, bytes, SHA-256, content type
and export ID. Receipts preserve `client:thunderbird`, message ID, attachment ID
and format hints. No base64, pixels or extracted document text is emitted.
The host's authorized file tools read selected originals; its image tool can view
requested inline images. A returned path alone is not proof of analysis or upload.

TNEF originals are transferred without expansion. Hints disclose
`container_members_listed:false`. An available authorized host decoder can inspect
selected members as data; the bridge installs or executes no decoder. Filename
search cannot see members hidden inside a container.

## Export lifecycle

Exports survive command exit under `exports/` in the private settings directory;
`MAIL_BRIDGE_EXPORT_ROOT` can override it locally. At most 16 files remain, default
10 MiB each and at most 100 MiB by explicit request. Later exports or `--cleanup`
remove managed files older than ten minutes. A full store returns `export_limit`
without evicting unexpired files. An OS lock serializes export/cleanup.

Consume batches sequentially and `--release EXPORT_ID` for each finished file.
Cleanup removes only generated files and empty directories, never recursively or
through links. Locked files and no later cleanup can leave copies. There is no
background cleaner. Account changes cannot recall exports or host/chat copies.
For longer authorized analysis, retain a verified private host copy and receipt,
then release the managed export. See [workflows](AGENT_WORKFLOWS.md).

Synthetic checks cover metadata-only search, payload-free listing, duplicate names,
byte/hash equality, custom mbox/maildir paths, identity/protection boundaries,
cross-process retention, host reading and explicit release. No real mailbox data
is required. See [release validation](RELEASE_VALIDATION.md).
