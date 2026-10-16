# Design review for 0.5.0

## Assessment

The core architecture fits a local desktop mail plugin: discover accounts, persist
one explicit account per client, search metadata, list one message's attachments,
and transfer selected originals. Thunderbird's index is separate from MIME-cache
access; classic Outlook uses the running profile's scoped COM delivery store.
The bridge need not contain PDF/Office parsers to deliver original files.

Local work and model context are different costs. Filtering many cached messages
locally does not send those messages to GPT. Only returned metadata, requested body
sections, file links/paths and explicitly requested image pixels reach the host.
Document delivery is also distinct from analysis: a local path/resource link is
not a native cloud attachment or proof that a model opened the document. Host file
tools and permissions determine what happens next. This release does not invent a
cloud upload receipt or encode document bytes into ordinary text responses.

## Findings addressed

| Previous behavior | Consequence | 0.5.0 change |
| --- | --- | --- |
| Search could read bodies for a newest/subject listing and return very long metadata | Unnecessary work and unpredictable context size | Metadata-only output by default, optional 280-character snippet, bounded fields with truncation flags; subject/empty metadata searches do not read bodies |
| Read returned only a body prefix, up to 60,000 characters | Important later text was unreachable through the read tool | Body offset and explicit next offset allow complete, incremental reading |
| Default conversation output allowed 20 times 6,000 body characters | One call could return 120,000 body characters; maximum settings allowed 480,000 | Aggregate body budget defaults to 24,000, up to 120,000; every omitted section remains reachable by message ID |
| Outlook result offset stayed inside a fixed newest-candidate window | Repeated pagination could never reach older candidates | Separate candidate scan offset and next offset, plus date/folder partition guidance |
| Calendar dates were UTC only and relative periods were absent | Local midnight and 'this week' could be interpreted incorrectly | Time-zone-aware inclusive start/exclusive end, this/last week/month and normalized UTC range in results |
| Image get automatically included pixels | Saving an original image could also spend image tokens | Original file remains the default; pixels require include_image:true |
| Listing did not explicitly require an existing signed-in client account | Installation could be mistaken for mail authentication | Prerequisite stated in English/Korean listing, README and skill; classic Outlook must remain running |
| Four default prompts exceeded the portable format's limit of three | Package compatibility problem | Three existing prompts retained, with release-time validation and overlay consistency checks |

Character budgets are practical bounds, not token estimates. Tool schemas,
instructions and metadata have their own context cost. Images depend on the host's
vision accounting. This review makes no percentage-token-savings claim.

## Calendar and broad-reading behavior

'Since October 2026' maps to after:2026-10-01 without an end date. 'This week'
maps to period:this_week and the user's time_zone. Weeks start Monday; this/last
month use calendar boundaries. Korean dates can use +09:00 without dependencies.
IANA zones require local timezone data, which may need optional tzdata on Windows.
Unavailable zones fail clearly rather than silently using the machine's zone.

Small defaults do not cap a user-authorized investigation. A task may paginate
results, inspect older candidate windows, partition by dates/folders, read later
body sections, increase conversation budgets, and analyze many selected files in
batches. Explicit account isolation, per-file byte limits and original-byte checks
remain in effect. There is no arbitrary-path tool or implicit access to every
mail account. General local-file analysis belongs to the host's existing file tools.

Outlook candidate offsets are bounded to 100,000 and each request retains time
limits. They rebuild a bounded local candidate view; they are not a server snapshot.
Mail changes can shift windows, so broad reviews must deduplicate message IDs and
disclose partial coverage. Date/folder partitions remain necessary for large stores
or slow providers. Thunderbird cache lookup is likewise bounded and may not find
old or specially laid-out MIME even when the index has a match.

## Further improvements

1. Verify the full installed-host path using generated PDF/Office/image originals
   and an isolated classic Outlook profile: byte equality, host file permissions,
   actual model analysis and unchanged unread state. A native host attachment
   integration could improve document handoff when a supported API is verified.
2. Replace numeric candidate offsets with a stable date/ID cursor or short-lived,
   account-bound local candidate snapshot for very large Outlook mailboxes.
   Consider provider-side metadata prefilters while preserving literal matching,
   Unicode handling, account boundaries and honest partial-result reporting.
3. Consider an optional Thunderbird companion using its documented APIs for
   special/hashed cache layouts and uncached originals. Keep normal sync/authentication
   in the mail client and never fetch remote tracking images implicitly.
4. Consider explicit release of exported temporary files and stronger cleanup after
   interrupted sessions. Current expiry is lazy and crashes/locks can leave copies;
   files already delivered to a host cannot be recalled by switching accounts.

## Evidence and limits

Synthetic tests exercise calendar rollover/local midnight, actual scoped SQLite
date filtering, metadata without body-column reads, long-body reconstruction,
aggregate budgets, separate scan continuation, image opt-in, original byte/hash
equality, scope/protection checks, stdio transport and release validation.
PowerShell tests use synthetic objects/functions and do not open a real mailbox.
On the current validation machine, the effective Restricted execution policy
prevents the unsigned PowerShell runtime test from running. That test is explicitly
skipped; both PowerShell files receive a parser-only syntax check. No execution
policy is changed or bypassed. Windows PowerShell starts with its own module-path
defaults to avoid incompatible PowerShell 7 modules inherited through Python;
execution-policy environment variables remain intact.
Existing live body/search evidence covers one Office 2019 setup. It does not prove
the new attachment, pagination or host-analysis behavior against a live provider
or every installed Codex environment. No production mailbox data is needed for review.

Reference: [MCP tool content and resource links](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
and [Outlook attachment property access](https://learn.microsoft.com/en-us/office/vba/api/outlook.attachment.propertyaccessor).
