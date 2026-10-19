# Plugin architecture review for 0.7.1

> Historical notes through 0.7.1. See [LOCAL_REVIEW.md](LOCAL_REVIEW.md) for
> the current local 0.10.0 architecture and verification. Public submission
> is not part of this local release.

The current plugin is a desktop skill plus a one-shot local CLI. It needs no MCP
server or remote backend because its source is the already signed-in desktop mail
client. GPT invokes the packaged CLI with JSON data arguments, reads compact
metadata/text, and opens selected original files with authorized host tools.

The 19 operation contracts retain explicit account scope, arbitrary date/time
bounds, literal filters, status/result/candidate pagination, body budgets/revision
checks and actionable errors. `--describe` loads one schema only when needed;
results are returned once instead of mirrored structured/text MCP content.

Attachment exports survive CLI exit, are bounded by size/count/lazy TTL, and are
released by opaque ID after host access. Image viewing is a separate explicit host
action; no base64, resource protocol, document parsing or execution remains.
No global background process, listener, lifecycle hook or mail credentials are added.

The manifests honestly mark local execution as required and contain no MCP/app
configuration. The package format is documented for desktop skills-only plugins and removes
the command-MCP component that caused the reported finding. This does not establish
that new skills-only submissions are currently accepted. A current intake closure
applies regardless of the local implementation; confirm eligibility before review.
Directory eligibility, scan results and review approval are external states and
cannot be guaranteed by source changes. Public metadata describes the real data
flow: local signed-in Thunderbird/classic Outlook mail becomes reference material
for GPT, under the AI host's processing and permission controls.

CLI/synthetic tests and separate host PDF/DOCX reads establish local code behavior.
Live Outlook attachments, installed-host routing and another-PC compatibility
remain unverified. Removing MCP sacrifices automatic dedicated mail-tool discovery;
the installed skill instead uses the host's existing command/file tools.

## Historical 0.6.0 contract review

The following section describes the previous MCP implementation. Its transport
and resource details are historical, not claims about the 0.7.0 runtime.


## Assessment

The bridge's responsibility is to expose reliable, composable mail/file primitives.
GPT chooses the search criteria and interprets natural language. A plugin does not
need separate commands for particular languages or phrases such as a relative week.
The core architecture is appropriate: explicit account selection, local filtering,
bounded metadata, targeted body reads, attachment listings and selected originals.

This review covered discovery and selection, scope enforcement, dates and literal
filters, result/candidate pagination, text and image budgets, body consistency,
attachment identity/bytes/resources, error recovery, MCP transport, launcher,
manifests, skills, documentation, tests and publication controls. It found real
contract defects beyond the original focus on natural-language date conveniences.

## Findings and changes

| Finding | Consequence | 0.6.0 behavior |
| --- | --- | --- |
| Date inputs only accepted whole days; relative presets duplicated caller reasoning | GPT could not request a precise arbitrary interval | after/before accept explicit RFC 3339 timestamps with offsets or UTC dates; relative presets and timezone-database dependency removed |
| Provider table date literals have minute precision | A precise exclusive end could lose mail before filtering | Broaden the provider filter, then apply exact UTC bounds before candidate limits; SQLite microseconds use integer arithmetic |
| SQLite lower() and Outlook casefold() had different Unicode matching | Equivalent literal searches could disagree across clients | Thunderbird uses deterministic Unicode casefolding for subject/body/sender/recipient/filename predicates |
| A completed candidate scan could still search truncated fields | Empty results could hide missed body/recipient/filename matches | search_incomplete includes candidate coverage and matching-field truncation, counted before filtering returned matches |
| Outlook body matching was fixed to one prefix size | GPT could not widen a deeper local keyword search | body_search_limit is caller-controlled, 6000 by default and up to 60000 |
| Paginated body reads had no revision check | Sections from changed content could be combined | Full-body SHA-256 is returned; optional expected_body_sha256 rejects mixed revisions |
| Defaults were mainly prose; results/errors mainly text | Programmatic callers had to infer settings and recovery | Schema defaults reflect implementation; structured metadata plus compatible JSON text; errors include code/retryable/next_action |
| Unexpected dispatch failures lost request IDs; empty invalid params became defaults | MCP clients could lose request correlation or receive misleading errors | Preserve valid request IDs, validate envelopes/params and sanitize failures; reject non-JSON numeric constants |
| Returned result offsets could exceed their input-schema ceiling | Deep pagination could produce an unusable next offset | Matched-result offsets support the same integer continuation range as body reads; bounded Outlook candidate offsets still disclose partition requirements |
| Status returned every folder on each check | A mailbox with many folders could consume excessive context before searching | folder_limit/folder_offset paginate bounded folder summaries while preserving account totals and latest date |

These changes retain original attachment handoff without adding document parsers.
Search work performed locally is not automatically sent to GPT. Returned metadata,
requested body sections and explicitly requested images contribute host context.
Character bounds are not token counts, and host handling of mirrored structured/text
results needs host-specific measurement; no token-savings percentage is claimed.

## Tool families reviewed

| Family | Inputs and outputs | Scope and side effects |
| --- | --- | --- |
| Thunderbird profiles / client accounts | Discover opaque IDs and account metadata without message payloads | Discovery metadata goes to the host; no implicit selection |
| client_select_account | Explicit account choice and confirm; private opaque settings | One selected account per client; settings write only |
| client_status | Selected client, paginated local folders, account totals and freshness limitations | No forced sync; no claim of complete server state |
| client_search | Query/field/sender/recipient/folder/time bounds, output/result/candidate/depth controls | Selected account only; bounded metadata and optional snippet |
| client_read | Message ID, body offset/limit, optional expected hash | Selected message, reported offset units and continuation; no mailbox write |
| client_thread | Conversation ID, page and per-message/aggregate budgets | Selected account only; omitted bodies retain IDs for targeted read |
| client_search_attachments | Subject/filename/sender/recipient/folder/time filters | Metadata only, no MIME caches, body or document payloads |
| client_list_attachments | One message ID and metadata pagination | Scoped cache/COM metadata; no payload decoding for a filename search |
| client_get_attachment | One message/attachment ID and image opt-in | Exact original temporary file; byte/hash checks, no parser/execution |
| MCP resources | Opaque URI from get; empty automatic catalog | Deferred reads recheck source scope/identity; original binary resource only |

There are 19 tools. Thunderbird uses registered profile/server paths and a read-only
SQLite connection. Outlook uses the running classic COM profile and a unique
delivery store, checking item parent/store before content access. Shared Outlook
stores, excluded folders and out-of-scope IDs fail closed. Plugin identity, audience
and read-only mailbox behavior remain unchanged. Selection/get annotations disclose
their local writes; no arbitrary local-path, SQL or command-execution tool is exposed.

The manifests, compatibility overlay and MCP server report the same version.
Default prompts remain within the portable limit. The listing and skill explicitly
require a signed-in/synced client; classic Outlook must remain running. The launcher
uses existing Node/Python and downloads nothing. Windows PowerShell uses its own
module defaults while preserving execution-policy variables.

## Original files and host boundary

Get writes original bytes to an OS-temporary file and returns its absolute path,
size, SHA-256 and resource link. Supported image pixels are included only when
requested. Ordinary text responses never contain document bytes/base64 blobs.
This is a local file handoff, not a native cloud attachment or upload receipt.
Actual host file permissions, document support and model analysis remain separate
requirements. A successful export alone does not prove GPT opened a PDF/Office file.

No PDF/Office/archive parsers, OCR, attachment execution, implicit bulk transfer,
remote tracking-image fetches or security-policy changes were added. Generic host
file tools can handle files outside the mailbox when the user's task and host
permissions authorize it; the mail plugin need not duplicate general filesystem tools.

## Remaining limits and proposals

1. Verify actual original-file access and analysis in an installed Codex connection
   using generated PDF/Office/image files and an isolated Outlook profile. Check
   exact bytes, host permissions and unchanged read state. Consider a native file
   attachment integration only after verifying a supported host API.
2. Numeric Outlook candidate windows rebuild a bounded view and can shift as mail
   changes. Deduplicate IDs and partition dates/folders for broad work. A stable
   cursor or short-lived account-bound candidate snapshot would improve large stores;
   provider-side metadata filters could reduce COM round trips.
3. Thunderbird's index/cache can be stale or incomplete; safe MIME lookup is bounded
   to a recent mbox window/maildir count and message size. An optional companion
   using documented Thunderbird APIs could broaden uncached/special-layout access.
4. Per-file delivery is limited to 10 MiB, with 16 exports and lazy 10-minute expiry.
   Crashes/locks can leave copies. Explicit export release and stronger interrupted
   session cleanup are potential lifecycle improvements. Delivered host/chat copies
   cannot be recalled by switching accounts.
5. Outlook matching can still be incomplete at the maximum prefix/metadata limits.
   The plugin now reports this even for empty results. Broad tasks can enumerate
   metadata and read relevant bodies/files in sections; small defaults do not cap
   an entire investigation. Complete local evaluation never proves server freshness.

## Verification boundary

Synthetic tests cover all tool-schema signatures/defaults, explicit and subsecond
time bounds, actual scoped SQLite predicates, Unicode literal matching, body
reconstruction/revision checks, aggregate budgets, separate candidate/result paging,
truncated nonmatching candidates, configurable body matching, structured/legacy MCP
results, sanitized correlated errors, attachment byte/hash equality, image opt-in,
scope/protection limits, stdio handoff and package/publication checks.

The current environment's Restricted PowerShell policy prevents the unsigned
synthetic runtime script from running; that test is explicitly skipped. Both
PowerShell sources receive parser-only syntax checks. Native provider date filtering,
body hashes and attachment access still need live/synthetic runtime verification in
an allowed environment. No policy was changed or bypassed. Existing live body/search
evidence covers one Office 2019 setup, not all new behavior or installed hosts.
No production mail is used in source/tests or public review materials.

Additional standalone QA generated valid PDF and DOCX originals, retrieved them
through the stdio search/list/get workflow, verified exact bytes/hashes, then read
their text using separate host-side PDF/Word libraries. Normal-exit cleanup passed.
Those libraries are not plugin runtime dependencies. This verifies downstream local
file access, not an installed MCP plugin session or live Outlook provider.
Reproduce with `python scripts/qa_host_handoff.py` from the source repository when
the host has optional `pypdf` and `python-docx` libraries. The QA script is included
in the source ZIP, not the plugin runtime package, and uses only synthetic data.

References: [MCP tool results](https://modelcontextprotocol.io/specification/2025-06-18/server/tools),
[Outlook table date filters](https://learn.microsoft.com/en-us/office/vba/outlook/how-to/search-and-filter/filtering-items-using-a-date-time-comparison),
and [Outlook attachment property access](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.propertyaccessor).
