# Mail Bridge verification evidence

Version 0.9.1 · synthetic public data only

The attribution patch ran 104 plugin cases: 103 passed and one PowerShell runtime
case was skipped under the existing script policy. All 22 release/publication
cases passed. The extracted release passed synthetic CLI and original-file
handoff checks. No live mailbox checks were repeated for this metadata patch.

The local skill uses 19 one-shot CLI operations with schemas loaded on demand.
See [LOCAL_REVIEW.md](LOCAL_REVIEW.md) for findings and verification limits.

- The 0.9.0 plugin suite: 104 pass; no skips. PowerShell 5.1 source syntax, synthetic
  scope and missing-ROT-connection checks pass under the existing policy.
- Release/publication suite: 22 pass.
- Regression coverage includes scoped searches, UTC/subsecond bounds, body revision
  paging, selected originals, larger-file opt-in, old maildir and boundary-spanning mbox
  windows, capacity preservation, partial-copy cleanup and process locking.
- Source-only host QA generates PDF/DOCX mail, exports originals through separate
  CLI processes, checks bytes/hashes, reads with host-side libraries and releases
  exports. Runtime has no PDF/Office parser.
- The 0.9.0 extracted ZIP CLI status/search/read/thread and original-file export passed
  with live Thunderbird and classic Outlook, including sampled unread-state checks.
  Account-specific evidence stays private; no mail/identities/files enter releases.
- Installed-host routing, Exchange-specific SMTP resolution, other providers/PCs
  and live non-Windows Thunderbird remain unverified. See
  [release validation](RELEASE_VALIDATION.md).

New synthetic coverage includes body-free metadata topics, duplicate-candidate
keys/fallbacks, localized/custom/mixed folder roles, attachment provenance,
same-name different originals and TNEF hints without expansion. Host QA verifies
ordinary DOCX strikethrough separately from plugin transport.

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
