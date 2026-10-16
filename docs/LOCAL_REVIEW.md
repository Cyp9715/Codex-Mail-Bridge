# Mail Bridge 0.8.0 local architecture review

Reviewed 2026-10-17. Local distribution and useful mail access are the release
criteria; public-directory submission is not part of this release.

## Execution choice

Keep the skill plus 19 one-shot CLI operations. It runs only on request, needs no
server lifetime, socket, OAuth, API key or new dependency, and exposes one schema
on demand. This suits a local host with command/file tools. MCP could offer native
tool discovery in a different host, but would add lifecycle and integration work
without improving original-file delivery here. The skill was reduced from 7,080
to 5,408 UTF-8 bytes (24%); byte savings are not exact token counts.

The bridge discovers scoped mail, filters metadata/text, pages bodies and
separates MIME transfer encoding. GPT decides dates, relevance and interpretation.
PDF, Office, archive, OCR and image-content parsers are absent from the runtime.
A file export is not proof of host analysis or a cloud upload.

## Findings and changes

| Finding | Change and practical effect |
| --- | --- |
| Outlook subject/newest scans enumerated up to 200 recipients and filenames on every candidate | Compact searches avoid those collection loops; flags distinguish omitted details from absence. Relevant filters still inspect needed collections. |
| Attachment scans spent candidate windows on messages without files | PR_HASATTACH filters the Outlook metadata table before date-limited candidate windows. No payload is read for search. |
| Exchange addresses could be internal EX identifiers | SMTP properties and Exchange user/distribution-list addresses are attempted, with the provider value retained if resolution is unavailable. |
| Outlook converted originals to base64 JSON and back | Scoped by-value SaveAsFile writes one generated private destination. Python validates the file and hashes it; JSON contains metadata only. |
| Fixed recent Thunderbird cache window prevented older originals | Caller-controlled mbox windows expose structured continuation; maildir windows also continue. Only matching identities load complete MIME, including records spanning a window edge. |
| A 10 MiB transfer ceiling constrained local delivery | Keep 10 MiB as default; permit explicit max_bytes up to 100 MiB for a needed file. Host tools retain separate limits. |
| Full export storage silently evicted unexpired originals | Return export_limit and preserve unfinished files. Expiry remains lazy. |
| Concurrent short processes could race cleanup | Use a cross-process OS lock; competing operations return retryable export_busy. |
| Listings emphasized public submission | Local setup and compatibility now lead. Public-review metadata was removed. |

## Safety and coverage

Preserved explicit account choice, identity fingerprints, store/folder/item
checks, read-only SQLite snapshots, UTC inclusive/exclusive bounds, literal
filters, body revision hashes, bounded replies and scan continuation. No mailbox
writes, attachment execution, remote image fetch, forced sync or policy change
was introduced. Mail and files stay untrusted evidence.

Export directories/basenames are independent of attachment names. Python verifies
actual size/type and SHA-256. Outlook rejects existing or nongenerated destinations
and reparse-point parents. Failures attempt to remove partial copies; locked files
can remain. Expiry is lazy, not guaranteed deletion at exactly ten minutes.
Default private application-data paths are used; local overrides remain user
configuration.

Thunderbird needs its global index and a supported, registered MIME cache layout.
The adapter does not implement IMAP, an independent index, Mork parsing or a
Thunderbird companion. Hashed/special layouts, absent offline copies and protected
or embedded-message attachments remain limited. A companion would be the next
project if these unsupported layouts become common.

Outlook uses the running Windows profile and Windows PowerShell 5.1. Existing
execution policy can prevent startup. Shared delivery stores, additional archive
stores and New/Mac/web Outlook remain unsupported. No PST/OST parser or policy
bypass was added.

## Verification

Plugin suite: 94 cases, 93 pass and one synthetic PowerShell runtime case skipped
under Restricted policy. PowerShell 5.1 AST syntax validation passes; this is not
proof of execution. Release/publication suite: 22 pass. Synthetic .test mail only.

Regression coverage includes original byte/hash equality, explicit larger files,
old mbox/maildir windows and boundary-spanning records, metadata-only SQL searches,
partial provider cleanup, post-save byte limits, preservation at export capacity,
cross-process locking, date/body pagination and schema/signature consistency.

Separate PDF/DOCX host handoff QA and extracted-package CLI verification are
performed for the release. They do not establish a live Outlook provider or an
installed AI-host session. Native Outlook SaveAsFile/provider behavior, live
Exchange SMTP resolution, installed-host routing, another PC and live non-Windows
Thunderbird remain unverified. No production mail was accessed in this audit.

## Primary API references

- [Attachment.SaveAsFile](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.saveasfile)
- [Efficient table enumeration](https://learn.microsoft.com/en-us/office/client-developer/outlook/pia/how-to-filter-and-efficiently-enumerate-items-in-a-folder)
- [PidTagHasAttachments](https://learn.microsoft.com/en-us/office/client-developer/outlook/mapi/pidtaghasattachments-canonical-property)
- [AddressEntry.GetExchangeUser](https://learn.microsoft.com/en-us/office/vba/api/outlook.addressentry.getexchangeuser)
