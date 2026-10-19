# Mail Bridge 0.10.0 release validation

Validated October 19, 2026. No production mail, identities, message/store IDs,
filenames, contents or local paths are published. Private comparisons stay in
ignored work files. Both manifests and the local runtime report 0.10.0.

## Change and compatibility

Outlook mail access already used Windows PowerShell/COM. Its skill and errors
did not provide an explicit CLI startup/recovery path or forbid screen automation
fallback. This release adds installation/process diagnostics and an idempotent
start command, exposes `starts_client` in command descriptions, and makes CLI-only
mail handling and user-managed login/profile/security prompts explicit.

The existing 19 mail/setup operations remain; two runtime operations make 21.
Search/read/status never start Outlook implicitly. Thunderbird adapters, explicit
account choices, private settings paths and read-only mailbox behavior are retained.

## Checks

| Check | Result |
| --- | --- |
| Plugin suite | 107 passed; no skips |
| Release/publication suite | 26 passed |
| Source-only installer suite | 8 passed |
| Windows PowerShell 5.1 | Source parsing, synthetic scope and lifecycle cases passed under existing policy |
| Synthetic lifecycle | Mail-free diagnostics, explicit startup, idempotence, missing installation/profile and ambiguous-instance rejection passed |
| Live Outlook classic / Office 2019 | CLI detected a stopped configured client, started it, then confirmed the running process |
| Live selected Outlook account | Status, compact metadata search, body read and conversation query passed through the launcher |
| Outlook read state | Sampled mail retained its before/after unread flag |
| Live selected Thunderbird account | Status, compact metadata search, body read and conversation query passed through the launcher |
| Host-only generated originals | Three PDF/DOCX originals retained bytes/hashes across CLI exit, were analyzed by host libraries and explicitly released |
| Distribution | Plugin/source archives passed integrity, source-byte and documentation-link checks |
| Isolated installation | Installation, reinstallation, upgrade from 0.9.3 and synthetic original-file handoff passed |

No Computer Use, screenshot, accessibility, browser, mouse or keyboard automation
was used for these mail checks. No account was switched or selected afresh. No
mail send/save/delete/move/mark-read, forced sync or policy change was requested.
Account-specific evidence is excluded from all source and archives.

The installed 0.9.3 archive is managed separately from this repository's release.
Update the existing entry with the 0.10.0 plugin ZIP; a currently active chat may
retain its earlier skill instructions. Account-service update/automatic routing
in a new chat and other providers/PCs are separate, unverified host checks.
Live original attachments were not re-exported for this runtime change; generated
original-file regression and earlier release evidence cover retained transfer code.
Successful sampled queries do not certify complete server sync or mailbox coverage.

## Distribution

Use `codex-mail-bridge-0.10.0-plugin.zip` for a desktop plugin update, and the
source ZIP for development. Both archives contain the release notes. `SHA256SUMS`
records the published archive hashes. See [installation](../INSTALL.md),
[release notes](RELEASE_NOTES.md), and [Outlook compatibility](OUTLOOK_COMPATIBILITY.md).
Prior validation reports remain in the corresponding immutable version tags.
