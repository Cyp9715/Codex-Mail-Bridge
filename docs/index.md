# Mail Bridge · Cyp Soft

Let GPT find and reference mail from Thunderbird or classic Outlook already
signed in on this computer, including Office 2019.
Sign in and sync needed mail in the desktop client first; keep classic Outlook running.
The desktop skill invokes one-shot local CLI operations, without an MCP server
or Cyp Soft remote service. A local conversation with command/file permissions
and Python 3.10+ is required. The bridge provides explicit date/time filters,
metadata/result pages, body sections, conversation budgets and selected original
files. GPT interprets natural-language requests and chooses those arguments.

Original files use generated private local export paths that survive command exit.
Images are viewed separately through the host's authorized image tool. The CLI
emits no base64, pixels or document text. No PDF/Office parsers or file execution.
Actual host file access/analysis requires host permissions and format support.
Mailboxes remain read-only; account selection and exports write only local settings/copies.

Broad work can continue candidate/result pages and partition dates/folders. Coverage,
truncation, revision hashes and actionable errors support targeted follow-up.
Registered client paths are used; no fixed mailbox path is assumed. Retrieved
data and host-opened files can reach OpenAI; local execution does not mean offline
AI processing. Free MIT source; no publisher backend, tracking or payments.

[Source and installation](https://github.com/Cyp9715/Codex-Mail-Bridge) · [Support](support.md) · [Privacy](privacy.md) · [Terms](terms.md)

[Full plugin contract review](DESIGN_REVIEW.md) · [Original-file support and limits](ATTACHMENT_SUPPORT.md)

[Local CLI contract](CLI.md) · [Desktop skills-only submission](SUBMISSION.md)
