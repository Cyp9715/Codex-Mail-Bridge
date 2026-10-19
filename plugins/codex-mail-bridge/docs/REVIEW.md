# Mail Bridge verification evidence

Version 0.10.0 · synthetic public evidence only

The skill uses 21 one-shot CLI operations. Outlook diagnosis/startup and mail
access require no Computer Use. New lifecycle tests cover mail-free diagnostics,
idempotent startup, existing-profile requirements, ambiguous instances and
specific recovery actions. Existing account/store/folder scope tests remain.

- Plugin suite: 107 passed; no skips, including PowerShell 5.1 syntax and synthetic runtime checks.
- Release/publication suite: 26 passed. Source-only installer suite: 8 passed.
- Live selected Thunderbird and classic Outlook status/search/read/thread passed.
  The sampled Outlook unread flag was unchanged. Mail evidence remains private.
- Three generated PDF/DOCX originals passed hash, host analysis and release checks.
- Plugin/source ZIP integrity, source bytes, links and isolated install/reinstall/
  upgrade from 0.9.3 passed. Existing account settings are outside the package.

See [release validation](RELEASE_VALIDATION.md) for scope and unverified host routing,
and [local review](LOCAL_REVIEW.md) for design. Live attachment transfer was not
repeated for this runtime-only change; retained transfer behavior has synthetic
regression and previous live-release evidence.

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
