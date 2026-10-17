# Mail Bridge 0.9.2 release validation

Validated October 18, 2026. This release adds a local installation ZIP and a
Codex CLI installer. Both manifests and the CLI runtime report 0.9.2. Developer
attribution remains Cyp; existing marketplace identity and account settings paths
are preserved. Mail retrieval behavior is unchanged.

## Installation regression and evidence

The reported desktop New Plugin dialog returned a generic archive-upload error.
The published 0.9.0 and 0.9.1 plugin ZIPs have the same 43 file paths, compression
methods and entry permission metadata. The skill and retrieval implementation are
unchanged apart from the version constant. The 0.9.1 package installs successfully
through the local Codex marketplace workflow. No server response identifying the
reported upload failure was available, so this release does not attribute it to a
specific package defect, duplicate name, account restriction, or service outage.

The new local ZIP contains the marketplace, complete plugin, Windows helper and
Node installer. It avoids the account-upload dialog. Preflight is read-only;
installation uses supported marketplace/add commands and verifies installed files.
Tests cover missing files, unsupported CLI, wrong source/version, stale installed
content and executable selection. Packaging also rejects runtime-version drift
and an invalid marketplace target. The original plugin-only ZIP remains available.

## Checks completed for 0.9.2

- Plugin suite: 104 executed, 103 passed, one PowerShell runtime case skipped under
  the existing script policy. No policy was changed or bypassed.
- Release/publication suite: all 24 passed.
- Installer suite: all 8 passed.
- Release archives: exact source bytes, manifests, local links and hashes passed.
- Integration: installation, reinstallation and an in-place upgrade from 0.9.1
  passed from the extracted local ZIP in isolated Codex settings. Cached files,
  Windows helper preflight, paths containing spaces, and synthetic original-file
  retrieval/hash/release checks passed. The test did not change the active install.
- Codex rejects a second source folder for an existing marketplace name. Updates
  must use the same registered folder; the helper preserves a conflicting source
  and reports the CLI diagnostic. No existing marketplace is silently removed.

Live mailbox checks were not repeated for this installation patch. Automatic
skill routing in a new desktop conversation and account ZIP upload remain
unverified. Earlier live runtime evidence is retained separately below.

## Prior 0.9.0 validation record

Validated October 17, 2026. This report contains technical outcomes only. No
mailbox identities, subjects, bodies, filenames, message/store IDs, user paths or
attachment contents are included. Account-specific evidence stays outside releases.

## Agent workflow improvements

Version 0.9.0 adds body-free metadata topic searches, scoped duplicate-candidate
keys, configured/provider folder roles, timestamp-basis labels and original-file
provenance/handoff hints. Three lazy skill references describe broad conversation
research, local-calendar summaries and original-file comparisons. TNEF expansion,
document parsing and OCR remain outside the bridge. All 19 existing operations,
explicit selections and mailbox read-only behavior are retained.

## Retained runtime correction

A running classic Outlook window can exist before `GetActiveObject` can resolve
its COM registration. Version 0.8.1 recovers only the missing-ROT-entry error by
connecting through Outlook's documented single-instance COM activation, after
confirming exactly one Outlook process exists in the caller's Windows session.
Closed, foreign-session or ambiguous instances are refused. Security and other COM
errors are not retried this way. No logon, profile selection or policy changes are
performed; existing account/store/folder/item checks still run before mail access.
The existing `v0.8.0` tag is preserved.

See Microsoft's [Outlook automation guidance](https://learn.microsoft.com/en-us/office/vba/outlook/concepts/getting-started/automating-outlook-from-other-office-applications).

## Checks completed for 0.9.0

| Check | Result |
| --- | --- |
| Plugin unit/runtime suite | 104 passed; no skips in this run |
| Release/publication suite | 22 passed |
| Extracted plugin ZIP | Every file matched the inspected Git tree; CLI version/schema discovery worked |
| Live Thunderbird CLI | Status, compact metadata search, body continuation/revision hash, conversation budget, attachment metadata search/list/get passed |
| Live classic Outlook for Windows / Office 2019 CLI | The same operations and native attachment SaveAsFile export passed |
| Requested original files | Host-side byte counts and SHA-256 matched; repeated export hashes agreed; copies survived CLI exit |
| Export release | Every validation export was explicitly released |
| Outlook read-state check | Sampled body and attachment messages retained their before/after unread state |
| Separate generated PDF/DOCX handoff | Host-only libraries read PDF and same-name DOCX revisions, including strike edits; receipts and hashes matched; the bridge added no document parser |
| Boundaries | Existing account choices retained; no send/save/delete/move/mark-read, forced sync, remote image fetch or security-policy changes requested |

The local CLI ran from extracted release content through Codex command/file tools. New metadata searches, duplicate keys, folder roles and file provenance were checked locally for both clients. Automatic routing is a separate host-installation check.
After archive validation, the existing local plugin was updated through the
supported Codex plugin CLI and its installed runtime version was checked. Existing
account selections remain outside the plugin cache. Reload/start a new conversation
to load the updated skill; source edits do not refresh an active conversation.
Automatic routing in a newly installed 0.9.0 plugin conversation, other providers,
Exchange-specific SMTP resolution, other PCs and live non-Windows Thunderbird
remain unverified. Successful sampled requests do not certify complete mailbox
coverage, all attachments, or every client/store layout. No public demo recording
or OpenAI directory approval is claimed.

## Download and install

For desktop use, download **codex-mail-bridge-0.9.2-local.zip**, extract it into a
folder you will keep, and run **install-local.cmd** on Windows or
`node scripts/install-local.cjs` from that folder. The **source.zip** includes the
same installer plus developer source. Restart the app and use a new local chat.

The **plugin.zip** is a single plugin for compatible import workflows; it does
not contain a marketplace. Local/source ZIPs are not account-upload packages.
Use the release SHA256SUMS to verify downloads. Git installation is also available:

```powershell
codex plugin marketplace add Cyp9715/Codex-Mail-Bridge --ref v0.9.2
codex plugin add codex-mail-bridge@cyp-soft-local
```

Local installation does not require OpenAI public-directory submission.
