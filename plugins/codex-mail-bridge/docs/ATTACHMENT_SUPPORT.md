# Original attachment handoff

Version 0.5.0 retains the original-file handoff introduced in 0.4.0. It supports
Thunderbird local MIME caches and classic Outlook by-value attachments. There are
six attachment tools, for 19 tools in total.
The bridge does not parse PDF, Word, Excel, archives or other document contents,
perform OCR, execute files, or upload files to an OpenAI Files API.

## Search before transfer

For either client use the following sequence, restricted to its explicitly
selected account:

1. `thunderbird_search_attachments` or `outlook_search_attachments` narrows mail
   by **subject**, sender, recipient, folder, calendar dates/periods and/or filename. Subject
   query words and filename words are literal substring matches, not file-content
   searches. Default 10 results, maximum 20, with bounded filename summaries.
   Neither search reads message bodies, MIME caches or attachment payloads.
2. `*_list_attachments(message_id)` lists metadata for **one** candidate message.
   Default 20 entries, maximum 50 per page, within a 200-attachment safety bound.
   Duplicate filenames get distinct opaque IDs; inline images include content IDs.
3. `*_get_attachment(message_id, attachment_id)` transfers **one** needed original,
   at most 10 MiB. Never enumerate and transfer all mailbox attachments implicitly.
   User-requested broad review may search many pages and transfer relevant originals
   in manageable batches.

Refine dates/subject/sender before widening a large search. Outlook applies date
filters to its metadata table before choosing its newest candidate window, then
scans at most 1,000 candidates by default, maximum 5,000. Inspect `scan_incomplete`;
paginate matches within that window, then follow next_scan_offset with offset 0
and unchanged filters, or partition by date/folder. Weeks start Monday in the
user's time_zone; period:this_week and explicit after/before are mutually exclusive.
Thunderbird searches
indexed filenames, which can omit inline images, stale entries or unindexed mail.
An empty result does not establish absence from the complete mailbox.

## What reaches Codex

The get tool writes the exact original bytes into a random private temporary
directory chosen by the OS, using a generated basename rather than a mail-provided
path. The result includes its absolute `local_path`, original display name, byte
count, SHA-256 and an opaque MCP resource link. Codex can use its existing local
file tools on this path; native document handling depends on the host. A resource
link alone is not a cloud upload receipt or proof that GPT analyzed a document.

PNG, JPEG, GIF and WebP signatures produce typed MCP image content only when
`include_image:true` is requested for visual analysis. The default false delivers
the exact original file without image-token use.
Raw file bytes are **not** dumped into ordinary JSON/base64 text or embedded blob
content in the get response. A host that supports binary MCP resources can explicitly
call `resources/read`; that returns the original blob and rechecks scope/identity.
`resources/list` is empty so automatic discovery cannot expose past filenames.

Exports/resources expire after 10 minutes, checked on subsequent transfer/resource
requests, and normal process exit attempts cleanup. At most 16 exports are retained.
A crash, locked file or lack of later requests can leave files in the OS temporary
directory. Remove only the returned files and their generated empty directories
when no longer needed. No recursive cleanup of user-supplied paths is implemented.
Already handed-off files, host copies and chat history cannot be recalled by switching
accounts. Treat originals and their paths as confidential runtime data.

The mailbox remains read-only. Get tools declare `readOnlyHint:false` and
`idempotentHint:false` because they create temporary local copies, not because they
modify mail. Selection tools write private bridge settings; other mail tools do
not write mailbox files. No document-parser dependencies are added.

## Client adapters and limits

### Thunderbird

The local global index contains no attachment bytes. The adapter resolves the
selected server's registered `directory-rel` (`[ProfD]`) or absolute `directory`
preferences and `storeContractID`. It never assumes a `Mail`/`ImapMail` directory
or one developer's profile. Overlapping account roots and unsafe/escaping folder
paths are refused. Normal nested `.sbd` folders and Unicode/custom paths are supported;
hashed/special folder layouts that cannot be safely mapped are unsupported.

Only a scoped, nondeleted indexed message is eligible. Its RFC Message-ID must
match cached MIME. An offset-like `messageKey` is verified; otherwise a bounded
recent 64 MiB mbox scan or at most 2,000 maildir files is used, with a five-second
scan budget and a 32 MiB message cap. Older messages outside those fallback bounds
can be unavailable even when their index entries exist. Missing/ambiguous identities,
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
Only by-value files up to 10 MiB are transferred via
[PidTagAttachDataBinary](https://learn.microsoft.com/en-us/office/client-developer/outlook/mapi/pidtagattachdatabinary-canonical-property)
and [Attachment.PropertyAccessor](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.propertyaccessor).
No `SaveAsFile`, message save, UI opening or read-state assignment is used.

Listings include at most 200 attachments and disclose truncation. Linked/cloud,
OLE, embedded-message and protected/IRM/S/MIME items are unsupported. Providers may
not expose the original bytes and can use their normal network connection. The
bridge never weakens Outlook or organizational security settings.

## Verification

Synthetic tests cover metadata-only searches, no body-column access, no MIME/file
reads during search, listing without decoding payloads, duplicate names, original
byte/hash equality, typed images and opt-out, mbox/maildir, absolute/Unicode/nested
paths, invalid/changed/out-of-scope IDs, encrypted/malformed/oversized inputs,
expiry/cleanup and stdio `search → list → get → resources/read`. Synthetic PowerShell
objects verify that listing reads no bytes and get accesses only one file, plus
scope, protection, type, size and modification checks.

These are generated-file/unit/stdio tests. Attachment get has not yet been verified
against a live Outlook provider or installed Codex MCP session, nor on another PC.
Previous live Office 2019 body/search evidence does not establish attachment support
in every provider. Public review recordings must use isolated synthetic mail.

See [MCP tool content](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
and [publication controls](DEVELOPMENT_SECURITY.md). Local file access, typed image
delivery, host document analysis and public-directory approval are distinct outcomes.
