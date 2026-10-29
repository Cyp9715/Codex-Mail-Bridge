# Support

Thunderbird Mail Bridge · Cyp

Use [GitHub Issues](https://github.com/Cyp9715/Codex-Mail-Bridge/issues) for setup
problems, bugs and feature requests. Include plugin/Thunderbird/Python versions,
operating system and a synthetic reproduction. Check local command/file access,
registered profiles, the explicit account choice, global indexing and available
local cache. A missing cache or unsupported layout cannot be repaired by a remote
fetch or automatic account switch. See [compatibility](THUNDERBIRD_COMPATIBILITY.md).

For `index_unavailable`, inspect Thunderbird indexing/permissions. For
`query_incomplete`, narrow filters or retry when the index is ready. For
`cache_search_incomplete`, follow the returned cache scan continuation. For
`body_changed`, restart the body read. For `export_limit`, release finished files;
for `export_busy`, wait for the other local export/cleanup command to end.

Issues are public. Never post real messages, addresses, server names, profile paths,
databases, settings, passwords or production identifiers. Use `.test` identities
and generated originals. A non-sensitive issue may request a private contact
method for security details; no dedicated private disclosure channel or response
time is guaranteed.

[Privacy](privacy.md) · [Terms](terms.md)

Start with `thunderbird_diagnostics` for installation/account guidance; see [setup and troubleshooting](SETUP.md).
