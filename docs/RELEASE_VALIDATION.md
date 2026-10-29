# Thunderbird Mail Bridge 0.11.0 release validation

Validation date: October 29, 2026. Both manifests and the runtime use 0.11.0.
Only synthetic `.test` accounts and generated originals are used for this change.
No production mailbox is accessed, selected, exported or published during testing.

## Checks

| Check | Result |
| --- | --- |
| Thunderbird runtime and setup diagnostics | 95 passed; no skips |
| Publication/package suite | 28 passed |
| Source installer suite | 11 passed |
| Generated host handoff | Three PDF/DOCX originals retained exact bytes/hashes across CLI exit; separate host reading, same-name revision comparison, strikethrough inspection and explicit release passed |
| Release archives | Plugin/source ZIP integrity, source-byte equality, relative documentation links and mirrored documentation passed |
| Isolated installation | Install/reinstall and upgrade from baseline 0.10.0 passed using temporary configuration; installed files and synthetic original export verified |
| Source scope | 82 distributable source files checked; no alternate-client implementation or references remain |
| Skill scenario | Starts with Thunderbird diagnostics, follows setup guidance, then checks status/profile/account discovery; eleven operations, explicit account authorization and no remote fallback |

The suites total 134 passing tests. Host analysis uses separate QA dependencies;
the runtime remains standard-library only. The isolated installation does not
modify the user's installed plugin or account selection.

The runtime contract requires exactly eleven Thunderbird operations with no mailbox
writes or client startup. Regression checks cover explicit account scope, read-only
SQLite, retained Thunderbird selection/identity keys, Unicode body continuation,
mbox/maildir original identity and private export lifecycle. Distribution checks
reject stale modules and mismatched installed runtime bytes.

## Limits

Synthetic checks do not establish a new live Thunderbird-version/OS/provider
certification, complete server synchronization, automatic skill routing in a newly
installed desktop chat or a hosted plugin update. No such live check is claimed
for this release. Document parsing in the QA script is a host action, outside
the plugin runtime.

Use a clean source/plugin extraction when upgrading. Keep private Thunderbird
selections outside the package. The immutable `v0.11.0` tag identifies the final
main-branch release commit; existing version tags are preserved.
See [release notes](RELEASE_NOTES.md) and [installation](../INSTALL.md).

Setup regression cases cover executable discovery, no installation/profile,
unregistered accounts, unreadable preferences/registries/profile paths, missing
indexes and reusable caches without a detected executable. Diagnostics never
claim to verify live authentication or silently choose an account.
