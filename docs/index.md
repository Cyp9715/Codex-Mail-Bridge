# Thunderbird Mail Bridge

Research mail, summarize conversations/date ranges and compare relevant original
attachments from one explicitly selected Thunderbird account. A local skill invokes
eleven one-shot CLI operations against existing index/cache data. Python 3.10+ and
local command/file access are required. There is no server or remote mail fetch.

Sign in and sync needed mail in Thunderbird and let global indexing finish.
Existing local data can be read with its window closed. Retrieved data and
host-opened originals can reach the invoking AI service; local does not mean offline.

- [Install and update](../INSTALL.md)
- [CLI contract](CLI.md)
- [Thunderbird compatibility](THUNDERBIRD_COMPATIBILITY.md)
- [Research workflows](AGENT_WORKFLOWS.md)
- [Original attachments](ATTACHMENT_SUPPORT.md)
- [Release validation](RELEASE_VALIDATION.md)
- [Privacy](privacy.md), [terms](terms.md) and [support](support.md)

Start with `thunderbird_diagnostics` for installation/account guidance; see [setup and troubleshooting](SETUP.md).
