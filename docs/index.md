# Mail Bridge · Cyp Soft

Read Thunderbird and classic Outlook mail in Codex. Office 2019 is supported;
Microsoft 365 is not required. The bridge searches and reads one explicitly
selected account per client without sending, saving drafts, deleting, moving,
or marking mail as read. Reply text can be written in chat.

Client data comes from registered Thunderbird profiles or the running Outlook
profile API. Sign in and sync in the mail client first; keep classic Outlook running. No fixed user/mail path is assumed. Retrieved data goes to the AI host.
Free MIT source; no publisher backend, analytics, or payments.

Version 0.5.0 can find attachment candidates by subject/date/sender/filename metadata,
list one message and hand off only requested originals. Supported images return typed
image content when include_image:true is requested; other files use temporary local paths for Codex file tools. No document
parsers or attachment execution. See [attachment support and limits](ATTACHMENT_SUPPORT.md).

[Source and installation](https://github.com/Cyp9715/Codex-Mail-Bridge) · [Support](support.md) · [Privacy](privacy.md) · [Terms](terms.md)

Search by local calendar dates or this/last week/month. Metadata is the default;
request snippets, body sections and larger thread budgets when useful. Broad
reviews can continue older candidates and partition dates/folders.
See [design review](DESIGN_REVIEW.md).
