# Local Thunderbird review

Version 0.11.0 uses a skill and one-shot local CLI. It has no MCP server, network
listener or application startup path. The operation catalog and attachment schema
registration are dedicated to Thunderbird's index/cache model.

| Area | Current behavior |
| --- | --- |
| Scope | Explicit profile/account selection; identity change and cross-account IDs fail closed |
| Retrieval | Read-only SQLite, metadata-first queries and scoped MIME cache identity |
| Research | Stable duplicate keys, configured folder roles, date basis and body hashes |
| Continuation | Result/folder pages, Unicode body offsets, thread budgets and bounded cache windows |
| Originals | Unchanged bytes, original-file provenance, private export lifecycle |
| Upgrade | Clean plugin tree; exact runtime inventory and installed bytes checked |
| Publication | Synthetic data, allowlisted packaging and staged-tree/history/message guard |

Reply drafts stay in chat. No mailbox mutation, forced synchronization, account
switching based on mail, attachment execution or tracking-image fetch is supported.
Missing indexes/caches are reported rather than replaced by remote access.

Originals are interpreted only through separately authorized host tools; a returned
path is not proof that the document was read. Local execution does not make AI
processing offline. See [privacy](privacy.md).

[Validation](RELEASE_VALIDATION.md) records actual candidate checks and remaining
platform/host limits. Earlier historical reports remain in existing immutable tags.
