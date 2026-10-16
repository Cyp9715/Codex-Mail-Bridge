# Mail Bridge verification evidence

Version 0.8.0 · synthetic public data only

The local skill uses 19 one-shot CLI operations with schemas loaded on demand.
See [LOCAL_REVIEW.md](LOCAL_REVIEW.md) for findings and verification limits.

- Plugin suite: 94 cases; 93 pass, one PowerShell runtime case skipped under the
  existing Restricted policy. PowerShell 5.1 source syntax checks pass.
- Release/publication suite: 22 pass.
- Regression coverage includes scoped searches, UTC/subsecond bounds, body revision
  paging, selected originals, larger-file opt-in, old maildir and boundary-spanning mbox
  windows, capacity preservation, partial-copy cleanup and process locking.
- Source-only host QA generates PDF/DOCX mail, exports originals through separate
  CLI processes, checks bytes/hashes, reads with host-side libraries and releases
  exports. Runtime has no PDF/Office parser.
- Native Outlook SaveAsFile/Exchange provider behavior, an installed AI-host
  session, another PC and live non-Windows Thunderbird remain unverified.
- No production mail was accessed in this audit or included in releases.

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
