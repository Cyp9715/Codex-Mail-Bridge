# Mail Bridge 0.9.3 release validation

Validated October 18, 2026. This release makes the standard plugin ZIP the primary
artifact. Both manifests and the CLI runtime report 0.9.3. Both author/developer
fields credit Cyp, and About makes that credit explicit. Mail retrieval, package
identity and private selection-settings paths are unchanged.

## Installation finding

The user confirmed that the desktop **New Plugin** creation failure occurred when
an existing plugin had the same name. This is an existing-entry conflict in the
reported account workflow, not evidence that the Cyp credit is forbidden. Use the
existing plugin's update action rather than creating another same-name plugin.
The new installation guide describes first installation, updates, and precautions
when a host requires explicit replacement.

The 0.9.0 and 0.9.1 release ZIPs had the same 43 paths and archive structure, and
their mail implementation differed only in the version constant. The 0.9.3 plugin
ZIP adds its installation guide. No separate local-installer ZIP is produced.
The optional marketplace helpers remain in developer source only.

The desktop client renders the developer label provided by its plugin service.
A creating account's display label can therefore differ from source attribution.
Changing account identity or promising an existing record will refresh is outside
this package. The deleted reported entry could not be inspected server-side.

## Checks for 0.9.3

- Plugin suite: 104 cases, 103 passed and one PowerShell runtime case skipped
  under the existing script policy. No policy was changed or bypassed.
- Release/publication suite: all 26 passed, including author/developer consistency.
- Optional source-only installer suite: all eight passed.
- Both archives passed integrity and source-byte checks. The plugin archive has
  44 files, its manifests and skill at the plugin root, and no marketplace wrapper
  or separate installer. Relative documentation links resolve inside the package.
- Isolated source-marketplace installation, reinstallation and an upgrade from
  0.9.1 passed. Version/file checks and synthetic original-file retrieval, byte
  hashes and explicit export release passed. The active user install was untouched.

Account-service creation/update and automatic skill routing in a new desktop
conversation are separate host checks. No new hosted upload or live mailbox test
is claimed for this packaging release.

## Prior 0.9.2 validation record

The 0.9.2 optional local-marketplace workflow passed 103 of 104 plugin cases (one
PowerShell case skipped under the existing policy), 24 release tests and eight
installer tests. Isolated local installation, reinstallation, upgrade, source
byte checks and synthetic original-file handoff passed. Those tests verified a
different installation path and did not fix the account-service creation error.

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

Use **codex-mail-bridge-0.9.3-plugin.zip** in the desktop app. The source archive is
for development and must not be uploaded as one plugin. Verify release archives
with **SHA256SUMS**. See [installation and updates](../INSTALL.md).

Local plugin use does not require OpenAI public-directory approval.
