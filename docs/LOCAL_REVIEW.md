# Mail Bridge 0.10.0 local architecture review

Reviewed 2026-10-19. Version 0.10.0 adds explicit Outlook CLI diagnostics and
startup, structured recovery actions and instructions that prohibit Computer Use
for mail tasks. Thunderbird adapters, account selection and mailbox read-only
behavior are retained. See [release notes](RELEASE_NOTES.md).

## Execution choice

Keep the skill plus 21 one-shot CLI operations. It runs only on request, needs no
server lifetime, socket, OAuth, API key or new dependency, and exposes one schema
on demand. This suits a local host with command/file tools. MCP could offer native
tool discovery in a different host, but would add lifecycle and integration work
without improving original-file delivery here. The earlier 0.8 architecture shortened the primary skill. Version 0.9 adds
three task references that load only for the requested workflow; byte counts are
not token measurements. Schemas remain lazy and no document dependencies are added.

The bridge discovers scoped mail, filters metadata/text, pages bodies and
separates MIME transfer encoding. GPT decides dates, relevance and interpretation.
PDF, Office, archive, OCR and image-content parsers are absent from the runtime.
A file export is not proof of host analysis or a cloud upload.

## Findings and changes

| Finding | Change and practical effect |
| --- | --- |
| Outlook recovery said to check the client without a CLI path | Dedicated diagnostics and explicit idempotent startup; failures identify the next action. |
| The skill did not prohibit screen automation fallback | CLI-only instructions cover startup, mail lookup and troubleshooting; prompts are handled by the user. |
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

The 0.9.0 validation run: 104 plugin cases pass and 22 release/publication cases pass, with
no skips under the existing RemoteSigned policy. PowerShell syntax and synthetic
scope/COM-connection cases pass. Automated fixtures use synthetic .test mail only.
The earlier 0.8.0 audit skipped its runtime case under Restricted policy; policies
were not changed for either run.

Regression coverage includes original byte/hash equality, explicit larger files,
old mbox/maildir windows and boundary-spanning records, metadata-only SQL searches,
partial provider cleanup, post-save byte limits, preservation at export capacity,
cross-process locking, date/body pagination and schema/signature consistency.

Separate PDF/DOCX host handoff QA and extracted-package CLI verification are
performed for the release. They do not establish a live Outlook provider or an
installed AI-host session. Subsequent archive CLI checks passed native Thunderbird
and classic Outlook SaveAsFile/export, search/body/thread and sampled unread-state
checks. No account-specific data is published. Exchange-specific SMTP resolution,
installed-host routing, another PC and live non-Windows Thunderbird remain
unverified. See [release validation](RELEASE_VALIDATION.md).

## Primary API references

- [Attachment.SaveAsFile](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.saveasfile)
- [Efficient table enumeration](https://learn.microsoft.com/en-us/office/client-developer/outlook/pia/how-to-filter-and-efficiently-enumerate-items-in-a-folder)
- [PidTagHasAttachments](https://learn.microsoft.com/en-us/office/client-developer/outlook/mapi/pidtaghasattachments-canonical-property)
- [AddressEntry.GetExchangeUser](https://learn.microsoft.com/en-us/office/vba/api/outlook.addressentry.getexchangeuser)

Version 0.8.1 fixes missing Outlook ROT registration by reconnecting only to one
already-running process in the current Windows session. Closed/foreign/ambiguous
instances and unrelated/security COM errors are refused. No profile or policy
changes are made. The original v0.8.0 tag is preserved.

## Version 0.9 agent analysis review

Generic topic searches previously had to use subject-only or body-inclusive any
matching. The metadata field now covers subject, parties and indexed filenames
without reading bodies. It does not silently change existing query semantics.

Every returned copy remains visible. Scoped Internet Message-ID candidate keys
help the agent identify label copies, while invalid/missing IDs remain local.
Body hashes resolve material differences; no content or subject heuristic merges
mail. Configured/provider folder roles and date-basis labels replace assumptions
about translated folder names or receipt timestamps. Mixed/unknown roles remain
explicit, and role preferences cannot expand account scope or invalidate a
previously selected identity.

Original-file receipts preserve mail/attachment IDs and host-action hints. TNEF
is identified but never expanded by the bridge. Optional host decoding remains
separate, as do document parsing, strike/track-change review, OCR and image viewing.
The task references cover quoted histories, calendar boundaries, evidence-based
counts, provenance, identical filenames, signed-final uncertainty and private
retention during longer comparisons. Source-only host QA now covers two same-name
DOCX versions and ordinary strikethrough as well as PDF reading.
