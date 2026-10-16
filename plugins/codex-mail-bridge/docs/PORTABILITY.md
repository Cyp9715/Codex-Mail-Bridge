# Portability and verification boundaries

Mail Bridge discovers user configuration; no developer mailbox path is shipped.

| Area | Design | Evidence |
| --- | --- | --- |
| Thunderbird registry | Standard per-OS locations plus THUNDERBIRD_HOME | Windows live; Windows/macOS/Linux/Snap/Flatpak synthetic registry tests |
| Thunderbird profile | profiles.ini relative or absolute paths | Synthetic nonstandard/absolute registration test |
| Outlook storage | Account.DeliveryStore in the running classic profile | Office Standard 2019 x64 live; no PST/OST parsing |
| Outlook account boundary | Identity fingerprint, unique delivery store, scoped folder/item checks | Synthetic COM scope tests and one real IMAP account |
| Settings | User application-data folders; independent environment overrides | Temporary paths with spaces/non-ASCII characters; legacy selection tests |
| Python/Node | Existing runtime discovery, explicit override, PATH fallback | Current Windows setup; no dependency downloads |
| PowerShell | SystemRoot-derived Windows PowerShell 5.1, -File, no execution-policy override | Alternate SystemRoot mocked test; current Windows live |

Actual Outlook read/search/conversation and unchanged unread state were checked
on one Windows Office 2019 x64 installation. This is not evidence for every
third-party PC, x86 Office, another Office edition, Exchange configuration,
corporate security policy, macOS, or Linux. Automated mocks are labeled as such.
Blocked COM access, a closed/changed profile, shared stores, unsupported clients,
and invalid settings produce errors rather than guessing another mailbox/path.

No real accounts, addresses, folder paths, store/message IDs, or mail bodies are
included in the distributable. Public screenshots/recordings must use isolated
synthetic data. Report compatibility issues with redacted diagnostics only.

Version 0.9.0 retains metadata-first original-file access through a skill and local
CLI, with no MCP transport. Generated-file/CLI and synthetic COM tests cover the
adapters. Extracted ZIP CLI checks additionally passed with live Thunderbird
and classic Outlook original-file exports; installed-host routing and other
providers/PCs remain unverified. See [release validation](RELEASE_VALIDATION.md).
See [attachment support](ATTACHMENT_SUPPORT.md) and [CLI contract](CLI.md).

See [the current local review](LOCAL_REVIEW.md) for SMTP resolution, direct
original-file export, cache continuation and verification limits.
