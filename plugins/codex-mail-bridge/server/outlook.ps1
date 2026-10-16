# Read-only Outlook Object Model adapter. No mailbox mutation or UI automation.
# Attach to a running classic Outlook instance; never guess a PST/OST path.
param([switch]$LibraryOnly)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::InputEncoding = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)

function Get-RegisteredOutlookApplication {
    return [Runtime.InteropServices.Marshal]::GetActiveObject('Outlook.Application')
}

function Get-RunningOutlookApplication {
    try { return Get-RegisteredOutlookApplication }
    catch {
        $failure = $_.Exception
        while ($failure.InnerException) { $failure = $failure.InnerException }
        # Only recover a missing ROT entry, never security/other COM failures.
        if ($failure -isnot [Runtime.InteropServices.COMException] -or $failure.HResult -ne -2147221021) { throw }
    }
    $sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
    $running = @(Get-Process -Name OUTLOOK -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $sessionId })
    if ($running.Count -eq 0) { throw 'outlook_not_running' }
    if ($running.Count -ne 1) { throw 'outlook_instance_ambiguous' }
    # Outlook's COM activation reuses its existing single instance. Require an
    # already-running process in this session; never log on or choose a profile.
    return New-Object -ComObject Outlook.Application
}

function Get-Digest([string]$Text) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Get-AccountRows($Session) {
    $rows = @()
    for ($n = 1; $n -le $Session.Accounts.Count; $n++) {
        $account = $Session.Accounts.Item($n)
        $store = $account.DeliveryStore
        if ($null -eq $store) { continue }
        $identity = @([string]$Session.CurrentProfileName, [string]$account.DisplayName,
                      [string]$account.SmtpAddress, [string]$account.AccountType, [string]$store.StoreID) -join "`n"
        $fingerprint = Get-Digest $identity
        $rows += [pscustomobject]@{ id = 'o_' + $fingerprint.Substring(0, 24); fingerprint = $fingerprint
            name = [string]$account.DisplayName; address = [string]$account.SmtpAddress
            type = [int]$account.AccountType; store = $store }
    }
    return $rows
}

function Get-ScopedAccount($Rows, [string]$AccountId, [string]$Fingerprint) {
    $matches = @($Rows | Where-Object { $_.id -ceq $AccountId })
    if ($matches.Count -ne 1 -or $matches[0].fingerprint -cne $Fingerprint) { throw 'selection_changed' }
    $chosen = $matches[0]
    $sameStore = @($Rows | Where-Object { $_.store.StoreID -ceq $chosen.store.StoreID })
    if ($sameStore.Count -ne 1) { throw 'shared_delivery_store' }
    if ($chosen.type -notin @(0, 1, 2)) { throw 'unsupported_account_type' }
    return $chosen
}

function Get-ScopedFolders($Store) {
    $excluded = New-Object 'System.Collections.Generic.HashSet[string]'
    # Deleted items must be identifiable; never fall back to reading all stores.
    [void]$excluded.Add([string]$Store.GetDefaultFolder(3).EntryID)
    foreach ($kind in @(4, 16)) {
        try { [void]$excluded.Add([string]$Store.GetDefaultFolder($kind).EntryID) } catch { }
    }
    try { foreach ($folder in $Store.GetSearchFolders()) { [void]$excluded.Add([string]$folder.EntryID) } } catch { }
    $pending = New-Object Collections.Queue
    $pending.Enqueue(@($Store.GetRootFolder(), 0))
    $visited = New-Object 'System.Collections.Generic.HashSet[string]'
    $result = @()
    while ($pending.Count -gt 0) {
        $pair = $pending.Dequeue(); $folder = $pair[0]; $depth = [int]$pair[1]
        $id = [string]$folder.EntryID
        if ($excluded.Contains($id) -or -not $visited.Add($id)) { continue }
        if ($folder.StoreID -cne $Store.StoreID) { throw 'folder_outside_scope' }
        if ($depth -gt 30 -or $visited.Count -gt 500) { throw 'folder_limit' }
        if ([int]$folder.DefaultItemType -eq 0) { $result += $folder }
        for ($n = 1; $n -le $folder.Folders.Count; $n++) { $pending.Enqueue(@($folder.Folders.Item($n), $depth + 1)) }
    }
    return $result
}

function New-CandidateFilter([string]$After = '', [string]$Before = '', [bool]$AttachmentsOnly = $false) {
    $clauses = @('"http://schemas.microsoft.com/mapi/proptag/0x001A001F" LIKE ''IPM.Note%''')
    if ($AttachmentsOnly) { $clauses += '"http://schemas.microsoft.com/mapi/proptag/0x0E1B000B" = 1' }
    foreach ($pair in @(@($After, '>='), @($Before, '<'))) {
        if (-not $pair[0]) { continue }
        $utc = [DateTimeOffset]::Parse($pair[0], [Globalization.CultureInfo]::InvariantCulture).UtcDateTime
        # The provider's locale date literal has minute precision. Broaden the
        # table filter, then apply exact bounds before counting candidates.
        $floor = $utc.AddTicks(-($utc.Ticks % [TimeSpan]::TicksPerMinute))
        $utc = if ($pair[1] -eq '<' -and $floor -ne $utc) { $floor.AddMinutes(1) } else { $floor }
        # DASL namespace comparisons are UTC, formatted with the user's culture.
        $literal = $utc.ToString('g', [Globalization.CultureInfo]::CurrentCulture).Replace("'", "''")
        $clauses += '"http://schemas.microsoft.com/mapi/proptag/0x0E060040" ' + $pair[1] + " '" + $literal + "'"
    }
    return '@SQL=' + ($clauses -join ' AND ')
}

function Get-Candidates($Folders, [int]$Limit, [string]$FolderId, [string]$After = '', [string]$Before = '', [bool]$AttachmentsOnly = $false) {
    $candidates = @{}
    $filter = New-CandidateFilter $After $Before $AttachmentsOnly
    $startUtc = if ($After) { [DateTimeOffset]::Parse($After, [Globalization.CultureInfo]::InvariantCulture).UtcDateTime } else { $null }
    $endUtc = if ($Before) { [DateTimeOffset]::Parse($Before, [Globalization.CultureInfo]::InvariantCulture).UtcDateTime } else { $null }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    foreach ($folder in $Folders) {
        if ($FolderId -and $folder.EntryID -cne $FolderId) { continue }
        $table = $folder.GetTable($filter, 0)
        [void]$table.Columns.Add('ReceivedTime')
        $table.Sort('ReceivedTime', $true)
        $count = 0
        while (-not $table.EndOfTable -and $count -lt $Limit) {
            if ($watch.Elapsed.TotalSeconds -gt 20) { throw 'candidate_scan_timeout' }
            $row = $table.GetNextRow()
            $id = [string]$row.Item('EntryID')
            $utc = [DateTime]::SpecifyKind([DateTime]$row.LocalTimeToUTC('ReceivedTime'), [DateTimeKind]::Utc)
            if (-not (Test-TimeBounds $utc $startUtc $endUtc)) { continue }
            $count++
            $candidates[$id] = [pscustomobject]@{ id = $id; date = $utc.ToString('o'); folder_id = [string]$folder.EntryID }
        }
        if ($candidates.Count -gt 2 * $Limit) {
            $newest = @($candidates.Values | Sort-Object @{Expression='date'; Descending=$true}, id | Select-Object -First $Limit)
            $candidates = @{}
            foreach ($row in $newest) { $candidates[$row.id] = $row }
        }
    }
    return @($candidates.Values | Sort-Object @{Expression='date'; Descending=$true}, id)
}

function Test-TimeBounds([DateTime]$Value, $After, $Before) {
    return (($null -eq $After -or $Value -ge $After) -and ($null -eq $Before -or $Value -lt $Before))
}

function Get-ScopedItem($Session, $Store, $FolderIds, [string]$MessageId) {
    if ($MessageId -notmatch '^[0-9A-Fa-f]{16,4096}$') { throw 'invalid_message_id' }
    $item = $Session.GetItemFromID($MessageId, [string]$Store.StoreID)
    # Check parent/store before accessing subject, sender, recipients, or body.
    $parent = $item.Parent
    if ($parent.StoreID -cne $Store.StoreID -or -not $FolderIds.Contains([string]$parent.EntryID) -or [int]$item.Class -ne 43) {
        throw 'message_outside_scope'
    }
    return $item
}

function Get-BodySection([string]$Body, [int]$Limit, [int]$Offset = 0) {
    $start = $Offset
    if ($start -gt 0 -and $start -lt $Body.Length -and [char]::IsLowSurrogate($Body[$start]) -and [char]::IsHighSurrogate($Body[$start - 1])) { $start-- }
    $end = [Math]::Min($Body.Length, [long]$start + $Limit)
    if ($end -gt $start -and $end -lt $Body.Length -and [char]::IsHighSurrogate($Body[$end - 1]) -and [char]::IsLowSurrogate($Body[$end])) { $end-- }
    $text = if ($start -lt $Body.Length) { $Body.Substring($start, $end - $start) } else { '' }
    $more = $end -lt $Body.Length
    return @{ body = $text; body_characters = $Body.Length; body_offset = $start
        body_sha256 = (Get-Digest $Body)
        body_offset_unit = 'utf16_code_units'; body_truncated = ($start -gt 0 -or $more)
        has_more_body = $more; next_body_offset = $(if ($more) { $end } else { $null }) }
}

function Get-ScanProgress([int]$Count, [int]$Offset, [int]$Examined) {
    $more = $Count -gt ([long]$Offset + $Examined)
    $next = if ($more -and $Examined -gt 0 -and ([long]$Offset + $Examined) -le 100000) { $Offset + $Examined } else { $null }
    return @{ scan_incomplete = $more; next_scan_offset = $next }
}

function Get-ScanWindow($Candidates, [int]$Offset, [int]$Limit) {
    return @($Candidates | Select-Object -Skip $Offset -First $Limit)
}

function Get-SmtpAddress($Entry, [string]$Fallback) {
    if ($null -eq $Entry) { return $Fallback }
    if ([string]$Entry.Type -ne 'EX') { return [string]$Entry.Address }
    try {
        $smtp = [string]$Entry.PropertyAccessor.GetProperty('http://schemas.microsoft.com/mapi/proptag/0x39FE001E')
        if ($smtp) { return $smtp }
    } catch { }
    try { $smtp = [string]$Entry.GetExchangeUser().PrimarySmtpAddress; if ($smtp) { return $smtp } } catch { }
    try { $smtp = [string]$Entry.GetExchangeDistributionList().PrimarySmtpAddress; if ($smtp) { return $smtp } } catch { }
    return $Fallback
}

function Get-Message($Item, [bool]$IncludeBody, [int]$BodyLimit, [int]$BodyOffset = 0,
                     [bool]$IncludeRecipientDetails = $true, [bool]$IncludeAttachmentNames = $true) {
    $recipients = @()
    if ($IncludeRecipientDetails) {
        for ($n = 1; $n -le [Math]::Min(200, $Item.Recipients.Count); $n++) {
            $recipient = $Item.Recipients.Item($n)
            $address = Get-SmtpAddress $recipient.AddressEntry ([string]$recipient.Address)
            $recipients += ([string]$recipient.Name + ' <' + $address + '>')
        }
    } else {
        $recipients = @([string]$Item.To, [string]$Item.CC) | Where-Object { $_ }
    }
    $attachments = @()
    if ($IncludeAttachmentNames) {
        for ($n = 1; $n -le [Math]::Min(200, $Item.Attachments.Count); $n++) { $attachments += [string]$Item.Attachments.Item($n).FileName }
    }
    $senderAddress = [string]$Item.SenderEmailAddress
    if ([string]$Item.SenderEmailType -eq 'EX') { $senderAddress = Get-SmtpAddress $Item.Sender $senderAddress }
    $message = [ordered]@{ id = [string]$Item.EntryID; conversation_id = [string]$Item.ConversationID
        date = $Item.ReceivedTime.ToUniversalTime().ToString('o'); subject = [string]$Item.Subject
        sender = ([string]$Item.SenderName + ' <' + $senderAddress + '>')
        recipients = $recipients -join '; '; folder_id = [string]$Item.Parent.EntryID
        folder_name = [string]$Item.Parent.Name; attachment_names = $attachments
        recipient_addresses_included = $IncludeRecipientDetails; attachment_names_included = $IncludeAttachmentNames
        has_attachments = ($Item.Attachments.Count -gt 0)
        recipients_truncated = ($IncludeRecipientDetails -and $Item.Recipients.Count -gt 200)
        attachments_truncated = ($IncludeAttachmentNames -and $Item.Attachments.Count -gt 200) }
    if ($IncludeBody) {
        $section = Get-BodySection ([string]$Item.Body) $BodyLimit $BodyOffset
        foreach ($key in $section.Keys) { $message[$key] = $section[$key] }
    }
    return [pscustomobject]$message
}

function Assert-AttachmentMessage($Item) {
    if ([int]$Item.Permission -ne 0 -or [string]$Item.MessageClass -match '(?i)SMIME|RPMSG|Secure|Encrypted') {
        throw 'protected_message'
    }
}

function Get-AttachmentProperty($Attachment, [string]$Tag, $Fallback) {
    try { return $Attachment.PropertyAccessor.GetProperty('http://schemas.microsoft.com/mapi/proptag/' + $Tag) }
    catch { return $Fallback }
}

function Get-AttachmentMetadata($Item, $Attachment, [int]$Index, [string]$Fingerprint) {
    $name = [string]$Attachment.FileName
    if ($name.Length -gt 512) { $name = $name.Substring(0, 512) }
    $size = [long]$Attachment.Size
    $kind = [int]$Attachment.Type
    $cid = [string](Get-AttachmentProperty $Attachment '0x3712001F' '')
    if ($cid.Length -gt 512) { $cid = $cid.Substring(0, 512) }
    $mime = [string](Get-AttachmentProperty $Attachment '0x370E001F' '')
    $modified = $Item.LastModificationTime.ToUniversalTime().Ticks
    $identity = @($Fingerprint, [string]$Item.EntryID, $Index, $name, $size, $kind, $cid, $modified) -join "`n"
    return @{ id = 'a_' + (Get-Digest $identity); name = $name; bytes = $size; content_type = $mime
        inline = ($cid -ne '' -or [bool](Get-AttachmentProperty $Attachment '0x7FFE000B' $false))
        content_id = $cid; transferable = ($kind -eq 1 -and $size -ge 0 -and $size -le 104857600)
        requires_larger_limit = ($size -gt 10485760) }
}

function Assert-ExportPath([string]$Path) {
    if (-not [IO.Path]::IsPathRooted($Path) -or [IO.Path]::GetFileName($Path) -cne 'attachment.bin') { throw 'invalid_export_path' }
    $directory = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Path))
    if ([IO.Path]::GetFileName($directory) -cnotmatch '^e_[0-9a-f]{32}$' -or [IO.File]::Exists($Path)) { throw 'invalid_export_path' }
    foreach ($candidate in @($directory, [IO.Path]::GetDirectoryName($directory))) {
        if (-not [IO.Directory]::Exists($candidate) -or (([IO.File]::GetAttributes($candidate) -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'invalid_export_path' }
    }
}

function Get-ItemAttachments($Item, [string]$Fingerprint, [string]$RequestedId = '', [string]$ExportPath = '', [long]$MaxBytes = 10485760) {
    Assert-AttachmentMessage $Item
    if ($RequestedId -and $RequestedId -cnotmatch '^a_[0-9a-f]{64}$') { throw 'invalid_attachment_id' }
    $found = @()
    for ($n = 1; $n -le [Math]::Min(200, $Item.Attachments.Count); $n++) {
        $attachment = $Item.Attachments.Item($n)
        $metadata = Get-AttachmentMetadata $Item $attachment $n $Fingerprint
        if (-not $RequestedId) { $found += $metadata; continue }
        if ($metadata.id -cne $RequestedId) { continue }
        if ($MaxBytes -lt 1 -or $MaxBytes -gt 104857600 -or -not $metadata.transferable -or $metadata.bytes -gt $MaxBytes) { throw 'unsupported_attachment' }
        # Save only the requested original to the bridge-generated private path.
        # No base64 transport, document parser, item.Save, UI opening or execution.
        Assert-ExportPath $ExportPath
        $attachment.SaveAsFile($ExportPath)
        if (-not [IO.File]::Exists($ExportPath) -or (Get-Item -LiteralPath $ExportPath).Length -gt $MaxBytes) { throw 'attachment_data_unavailable' }
        $after = Get-AttachmentMetadata $Item $attachment $n $Fingerprint
        if ($after.id -cne $metadata.id) { throw 'attachment_changed' }
        return @{ attachment = $metadata; exported = $true }
    }
    if ($RequestedId) { throw 'attachment_changed' }
    return @{ attachments = $found; returned = $found.Count; attachments_truncated = ($Item.Attachments.Count -gt 200) }
}

function Invoke-OutlookRequest($Request) {
    if ($Request.operation -notin @('accounts', 'validate', 'status', 'scan', 'read', 'attachments', 'attachment')) { throw 'unknown_operation' }
    $application = Get-RunningOutlookApplication
    $session = $application.Session
    $rows = @(Get-AccountRows $session)
    if ($Request.operation -eq 'accounts') {
        return @{ accounts = @($rows | ForEach-Object {
            $id = $_.store.StoreID
            @{ id = $_.id; fingerprint = $_.fingerprint; name = $_.name; address = $_.address; type = $_.type
               supported = ($_.type -in @(0, 1, 2) -and @($rows | Where-Object { $_.store.StoreID -ceq $id }).Count -eq 1) }
        }); outlook_version = [string]$application.Version }
    }
    $chosen = Get-ScopedAccount $rows $Request.account_id $Request.fingerprint
    if ($Request.operation -eq 'validate') { return @{ account = $chosen.address; validated = $true } }
    $folders = @(Get-ScopedFolders $chosen.store)
    $folderIds = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($folder in $folders) { [void]$folderIds.Add([string]$folder.EntryID) }
    if ($Request.operation -eq 'status') {
        $newest = @(Get-Candidates $folders 1 '') | Select-Object -First 1
        return @{ configured = $true; account = $chosen.address; outlook_version = [string]$application.Version
            offline = [bool]$session.Offline; latest_message_date = $newest.date
            folders = @($folders | ForEach-Object { @{ id = [string]$_.EntryID; name = [string]$_.Name; folder_items = [int]$_.Items.Count } }) }
    }
    if ($Request.operation -eq 'read') {
        $item = Get-ScopedItem $session $chosen.store $folderIds $Request.message_id
        $message = Get-Message $item $true ([int]$Request.max_characters) ([int]$Request.body_offset)
        if ($Request.expected_body_sha256 -and $message.body_sha256 -cne $Request.expected_body_sha256) { throw 'body_changed' }
        return @{ account = $chosen.address; message = $message }
    }
    if ($Request.operation -in @('attachments', 'attachment')) {
        $item = Get-ScopedItem $session $chosen.store $folderIds $Request.message_id
        $requested = if ($Request.operation -eq 'attachment') { [string]$Request.attachment_id } else { '' }
        if ($Request.operation -eq 'attachment' -and -not $requested) { throw 'invalid_attachment_id' }
        $maximum = if ($Request.operation -eq 'attachment') { [long]$Request.max_bytes } else { 10485760 }
        $result = Get-ItemAttachments $item $chosen.fingerprint $requested ([string]$Request.export_path) $maximum
        $result.account = $chosen.address
        return $result
    }
    $limit = [int]$Request.scan_limit
    if ($limit -lt 1 -or $limit -gt 5000) { throw 'scan_limit' }
    $offset = [int]$Request.scan_offset
    if ($offset -lt 0 -or $offset -gt 100000) { throw 'scan_limit' }
    $folderId = [string]$Request.folder_id
    if ($folderId -and -not $folderIds.Contains($folderId)) { throw 'folder_outside_scope' }
    $candidates = @(Get-Candidates $folders ($offset + $limit + 1) $folderId $Request.after $Request.before ([bool]$Request.attachments_only))
    $messages = @(); $watch = [Diagnostics.Stopwatch]::StartNew(); $examined = 0
    foreach ($candidate in (Get-ScanWindow $candidates $offset $limit)) {
        if ($watch.Elapsed.TotalSeconds -gt 25) { break }
        $examined++
        $item = Get-ScopedItem $session $chosen.store $folderIds $candidate.id
        if ($Request.conversation_id -and [string]$item.ConversationID -cne $Request.conversation_id) { continue }
        $messages += Get-Message $item ([bool]$Request.include_body) ([int]$Request.max_characters) 0 ([bool]$Request.include_recipient_details) ([bool]$Request.include_attachment_names)
    }
    $progress = Get-ScanProgress $candidates.Count $offset $examined
    return @{ account = $chosen.address; messages = $messages; scanned_messages = $examined
        scan_incomplete = $progress.scan_incomplete; next_scan_offset = $progress.next_scan_offset }
}

if (-not $LibraryOnly) {
    try {
        $request = [Console]::In.ReadToEnd() | ConvertFrom-Json
        $result = Invoke-OutlookRequest $request
        @{ ok = $true; result = $result } | ConvertTo-Json -Depth 12 -Compress
    } catch {
        $known = @('outlook_not_running', 'outlook_instance_ambiguous', 'selection_changed', 'shared_delivery_store', 'unsupported_account_type', 'folder_outside_scope', 'folder_limit', 'invalid_message_id', 'message_outside_scope', 'unknown_operation', 'scan_limit', 'candidate_scan_timeout', 'protected_message', 'invalid_attachment_id', 'invalid_export_path', 'unsupported_attachment', 'attachment_data_unavailable', 'attachment_changed', 'body_changed')
        $code = if ($_.Exception.Message -in $known) { $_.Exception.Message } else { 'outlook_access_failed' }
        @{ ok = $false; error = $code } | ConvertTo-Json -Compress
    }
}
