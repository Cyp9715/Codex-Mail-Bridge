# Thunderbird Mail Bridge 0.11.0

Release · October 29, 2026

The new `thunderbird_diagnostics` operation checks installation evidence,
registered profiles/accounts and index presence without mail access. Missing,
unreadable or unconfirmed setup gets a concrete next action. Existing local
caches stay usable when an executable is not detected; account configuration
does not imply successful server authentication.

The project is dedicated to Thunderbird: eleven local operations cover profile/account
discovery, explicit selection, index status, mail search/read/conversations and
original attachment search/list/get. Attachment definitions bind directly to the
Thunderbird MIME cache adapter. No operation starts a mail client.

Existing Thunderbird account settings, duplicate-candidate keys, mailbox read-only
boundaries and original-file receipts remain compatible. Body continuation uses
Unicode characters, including supplementary characters. Discovery still supports
registered standard and custom profiles; no fixed mail paths are introduced.

Both manifests, runtime version, listing, English/Korean readmes, skill, task guides,
privacy, support and compatibility documentation describe the same Thunderbird
scope. Package identity `codex-mail-bridge` and default prompt order are retained.

Packaging and the optional source installer verify the six-module runtime inventory;
the installer verifies all installed runtime bytes. Upgrade from a clean plugin
directory so removed source files cannot survive an overlay extraction. Existing
private selection files outside the plugin need no deletion.

Tests and release archives use synthetic data. See [validation](RELEASE_VALIDATION.md)
for actual checks and limits. The release includes plugin/source ZIPs and their SHA-256 checksums. The immutable
version tag identifies the final main-branch release commit. Installing or
updating an account-hosted plugin is a separate user action.
