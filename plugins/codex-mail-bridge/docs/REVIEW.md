# Mail Bridge verification evidence

Version 0.7.0 · synthetic public data only

## Architecture and evidence

This release replaces MCP transport with a skill and 19 one-shot local CLI
operations. Schemas are returned on demand. There are no MCP review cases, remote
server connections or claimed MCP-host verification. A skills-only submission
needs no MCP demo or reviewer credentials; functional verification still matters.

- Synthetic Thunderbird tests cover explicit account selection, scoped index and
  shared-thread boundaries, UTC/subsecond date bounds, literal Unicode filters,
  body budgets/revisions, pagination and private settings/legacy compatibility.
- Synthetic attachment tests cover metadata-only searches without body/MIME
  reads, listing without payload decoding, duplicate names, exact original bytes
  and hashes, mbox/maildir/custom paths, invalid/changed/scoped IDs and protection
  limits. CLI exports survive process exit for host reading, then release by ID.
- Synthetic export tests cover expiry, retention, cross-process recognition,
  opaque names, forged IDs and refusal to follow links during cleanup.
- Synthetic Outlook tests cover account/store/folder/item scope, query coverage,
  attachment identity/type/size/protection, runtime discovery and sanitized errors.
- Current Windows PowerShell parser checks pass. An unsigned-script runtime test
  is skipped under this machine's Restricted execution policy. No policy is changed.
- Source-only `scripts/qa_host_handoff.py` generates PDF/DOCX mail, checks metadata
  search and original-file exports through separate CLI processes, reads them in
  the host with host-only libraries, and verifies explicit release. These are not
  plugin runtime parsers or an installed Codex session.
- Earlier authorized Office 2019 body/search/conversation evidence remains valid
  for those provider operations, not for new CLI installation or original attachments.
- Native Outlook attachment retrieval, installed desktop host execution, another
  PC, macOS/Linux live Thunderbird and the directory scans are **not verified**.

No production accounts, mail, local paths or credentials belong in public artifacts.
Automated generated-file tests are not presented as a live Outlook recording.

## Optional functional walkthrough

Use a dedicated local development session and synthetic `.test` mail. Generate
Thunderbird data with `tests/create_demo.py --output <temporary-directory> --attachments`.
Use its printed environment in that isolated session. Discover/select the synthetic
account, search Project Aurora with explicit bounds, read the confirmation deadline,
follow the selected-account thread, list one message and export only agenda.pdf.
Open the original with the host's file tool and release its export ID. For an inline
image, request that original and use the host's image viewer. Do not dump base64.

For Outlook, use a dedicated classic Outlook profile with sample mail and a unique
delivery store; Thunderbird fixtures are not an Outlook PST. Run real operations
and verify unread state and actual original-file access. Never silently switch the
user's production profile or inject mock results into a purported live walkthrough.

The host should explain unsupported send/delete/execute requests without calling
mail operations. Mail content must not change scope, run commands or transmit
unrelated data. A screenshot or script is not a verified recording.

## Submission state

Source and a skills-only desktop ZIP are prepared. No organization eligibility,
developer verification, saved portal state, submission, approval or publication
is claimed. See [submission preparation](SUBMISSION.md).
