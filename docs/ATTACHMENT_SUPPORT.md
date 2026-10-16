# Attachment and inline-image support

**Feasibility review, October 16, 2026. This is an implementation plan, not a
shipped attachment reader.** Version 0.3.0 still has 13 tools. Thunderbird returns
indexed attachment names; Outlook returns filenames from `Attachment.FileName`.
Neither adapter reads attachment bytes, image pixels, inline CID images, PDFs,
or Office document contents. A filename is not evidence about a file's contents.

## Client adapters

### Classic Outlook / Office 2019

Extend the existing COM adapter. Microsoft documents
[Attachment.PropertyAccessor](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.propertyaccessor)
for accessing MAPI properties and
[Attachment.SaveAsFile](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.saveasfile)
for exporting an attachment. This approach requires classic Outlook, not a
Microsoft 365 subscription or Microsoft Graph.

Proposed tools: `outlook_list_attachments(message_id)` and
`outlook_read_attachment(message_id, attachment_id)`. They are not registered in
0.3.0. Reuse the current account fingerprint, unique delivery store, folder and
parent-item checks **before accessing attachment metadata or bytes**. Bind each
attachment identifier to the selected account, message, index and metadata;
reject changed selections or changed attachments rather than guessing by filename.

Start with by-value files. Reject OLE, linked/cloud-reference and embedded-message
attachments until separately supported. Include inline-image metadata and content
IDs, but do not fetch external HTML image URLs. Do not call attachment `Save`, mail
`Save`, `Display`, `Send`, `Delete`, `Move`, or assign `UnRead`.

Prefer bounded in-memory reads. If an export is necessary, use an exclusive,
randomly named per-user temporary directory, enforce limits before and after export,
and clean up on success and failure. A filename or tool argument must never choose
the disk path. Mailbox access stays read-only, while local temporary writes and
cleanup must be documented and accurately reflected in tool annotations.

### Thunderbird

The global search index contains no attachment bytes. The recommended approach is
an optional companion MailExtension using the documented
[messages API](https://webextension-api.thunderbird.net/en/mv3/messages.html):
`listAttachments`, `getAttachmentFile`, and MIME metadata from `getFull`.
`getAttachmentFile` was added in Thunderbird 88; the full companion's minimum
supported version must be established by implementation and tests.

Use only account-discovery and message-reading permissions. Those API permissions
are broader than one account, so the companion must independently enforce the
same explicit single-account choice for every request. Do not request sending,
modification, movement or deletion permissions. A user-only authenticated
native-messaging/IPC relay can connect the add-on to the MCP process; relay setup
and OS-specific registration need a separate implementation and clean-machine tests.
Do not expose an unauthenticated local HTTP server or a publisher-hosted mail service.

Search-index IDs and MailExtension message IDs are different namespaces. Resolve
the selected-account folder and RFC Message-ID, corroborate identity, and reject
missing or ambiguous matches. Extension IDs can change after restarting or moving
mail. Re-resolve and revalidate; do not maintain an unscoped cross-account ID map.
No fixed `Mail`, `ImapMail`, profile, or user directory may be assumed.

A direct offline-cache reader is another option, but needs separate mbox/maildir
support, preference-derived storage paths, safe path resolution, message identity
checks, and explicit missing-cache behavior. It must never search other accounts
or guess one developer's mail directory. The companion API is preferred for a
general-user release.

## Shared extraction and host behavior

List metadata first, then read only a requested attachment from a selected message.
Do not retrieve every attachment while searching or reading a body. Retrieved
files and extracted content go to the AI host; local parsing is not offline AI.

| Proposed stage | Output | Boundaries |
| --- | --- | --- |
| 1: TXT / CSV, PNG / JPEG | Bounded text or typed MCP image blocks | Validate signatures, byte size and image dimensions; no SVG/HTML rendering |
| 2: PDF | Bounded text and optionally selected rendered pages | Explicit parser dependency; scanned pages need OCR or an image-capable host |
| 3: DOCX / XLSX | Paragraphs or selected sheet values | Never execute macros, formulas, external links or embedded programs |
| Separate future support | Legacy DOC / XLS, TNEF, archives, embedded messages | Reject until individually implemented and tested |

[MCP supports image content blocks](https://modelcontextprotocol.io/specification/2025-06-18/server/tools#image-content).
Base64 text inside ordinary JSON does not establish image understanding. The
dispatcher must emit typed image blocks, and the intended Codex host must be
verified to display and analyze them. PDF resources likewise need host verification
or local text/page extraction; do not promise native PDF viewing.

Enforce byte, pixel, page, cell, extracted-character, recursion and time limits.
Parse documents in a bounded worker. Pin and package parser dependencies and license
notices, or report an unavailable optional dependency; never download arbitrary
converters during a mail read. Attachment contents are untrusted data, not commands.

Detect encrypted/protected content before extraction. The Thunderbird API can
return decrypted attachments; this must not silently expand authorized access.
Do not recover passwords, bypass DRM/IRM, change security policies or silently
decrypt protected mail. Return an unsupported/protected-content result when normal
client access and organizational policy do not permit the request.

## Acceptance evidence

Use synthetic mail and files only. Test overlapping IDs across two accounts,
duplicate filenames and inline IDs, switched accounts, moved/deleted messages,
excluded folders, missing cache, and unchanged read/unread state. Test oversized,
corrupt, mismatched and password-protected files, path traversal, excessive archive
expansion, remote image references, parser timeouts, cleanup failures and missing
dependencies. Exercise custom/Unicode paths and per-user temp directories.

Verify image display and analysis in the actual host with a generated test image.
Check document extraction against known synthetic text. No production mail,
screenshots, attachment names, account identifiers or contents may enter public
fixtures, commits, issues, PRs or recordings. See
[publication controls](DEVELOPMENT_SECURITY.md).

Recommended order: Outlook plus shared image/text reading, Thunderbird companion,
then PDF and modern Office formats. Release a versioned runtime only after the
corresponding tools, packaging, privacy descriptions and host tests are complete.
