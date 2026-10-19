Mail Bridge v0.10.0 adds CLI-only Outlook diagnostics and startup while preserving existing mail workflows.

### Changes

- Use local Windows PowerShell/COM for Outlook mail lookup, startup and recovery. Explicitly prohibit Computer Use, screenshots, accessibility APIs, and mouse or keyboard automation in the skill.
- Add `outlook_diagnostics` to inspect installation/process state, existing-profile presence and the Windows PowerShell version without activating COM or accessing accounts/mail.
- Add `outlook_start` to launch installed classic Outlook with an existing configured profile. Leave an already running instance alone and disclose which command starts the client. A process starting does not prove COM/profile readiness.
- Return specific recovery actions for a stopped client, missing installation/profile, COM busy, access denial and timeouts. The user handles login/profile/security prompts; no security policies are weakened.

### Compatibility

The package name remains **codex-mail-bridge**. Thunderbird adapters, existing account choices, private settings and read-only mailbox access are preserved. The previous 19 operations remain, with two runtime commands bringing the total to 21. Existing search/read/status operations do not implicitly start Outlook. No remote MCP server or document parser has been added.

### Validation

- **141 tests passed with no skips:** 107 plugin cases, 26 release/publication cases and eight optional installer cases. Windows PowerShell 5.1 syntax, synthetic scope and lifecycle checks passed under the existing policy.
- Both archives passed integrity, source-byte and local documentation-link checks. Isolated installation, reinstallation, upgrade from v0.9.3 and synthetic original-file retrieval/hash/release checks passed.
- Live CLI status, compact metadata search, body reading and conversation queries passed with the selected Thunderbird and classic Outlook accounts. The sampled Outlook unread flag was unchanged. No Computer Use was used for these checks.
- Automatic routing in a newly updated desktop conversation and other providers/PCs remain unverified. Live original attachments were not re-exported for this release; generated-original regression and earlier live results cover the retained transfer code.

### Downloads

- `codex-mail-bridge-0.10.0-plugin.zip`: the complete plugin for desktop package import or an existing-plugin update.
- `codex-mail-bridge-0.10.0-source.zip`: repository source, tests and optional development helpers.
- `SHA256SUMS`: SHA-256 checksums for both ZIPs.

Update the existing plugin entry, then reload the plugin and start a new local conversation. An active chat may retain its earlier skill instructions. See [installation](../INSTALL.md) and [validation](RELEASE_VALIDATION.md).
