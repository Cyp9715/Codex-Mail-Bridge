# Mail Bridge · Cyp Soft

Read Thunderbird and classic Outlook mail in Codex. Office 2019 is supported;
Microsoft 365 is not required. The bridge searches and reads one explicitly
selected account per client without sending, saving drafts, deleting, moving,
or marking mail as read. Reply text can be written in chat.

Client data comes from registered Thunderbird profiles or the running Outlook
profile API. No fixed user/mail path is assumed. Retrieved data goes to the AI host.
Free MIT source; no publisher backend, analytics, or payments.

Version 0.4.0 can find attachment candidates by subject/date/sender/filename metadata,
list one message and hand off only requested originals. Supported images return typed
image content; other files use temporary local paths for Codex file tools. No document
parsers or attachment execution. See [attachment support and limits](ATTACHMENT_SUPPORT.md).

[Source and installation](https://github.com/Cyp9715/Codex-Mail-Bridge) · [Support](support.md) · [Privacy](privacy.md) · [Terms](terms.md)
