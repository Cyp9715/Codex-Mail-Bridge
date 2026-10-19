$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../server/outlook.ps1" -LibraryOnly
function Assert-Blocked([scriptblock]$Action, [string]$Expected) {
    try { & $Action; throw 'Expected a scope rejection' }
    catch { if ($_.Exception.Message -ne $Expected) { throw } }
}
$store = [pscustomobject]@{ StoreID = 'store-a' }
$otherStore = [pscustomobject]@{ StoreID = 'store-b' }
$one = [pscustomobject]@{ id = 'o_demo'; fingerprint = 'chosen-identity'; type = 1; store = $store }
$two = [pscustomobject]@{ id = 'o_other'; fingerprint = 'other-identity'; type = 1; store = $otherStore }
$chosen = Get-ScopedAccount @($one, $two) 'o_demo' 'chosen-identity'
if ($chosen.id -ne 'o_demo') { throw 'Wrong account selected' }
Assert-Blocked { Get-ScopedAccount @($one, $two) 'o_demo' 'changed-identity' } 'selection_changed'
$shared = [pscustomobject]@{ id = 'o_shared'; fingerprint = 'shared-identity'; type = 2; store = $store }
Assert-Blocked { Get-ScopedAccount @($one, $shared) 'o_demo' 'chosen-identity' } 'shared_delivery_store'
$folderIds = New-Object 'System.Collections.Generic.HashSet[string]'
[void]$folderIds.Add('inbox-a')
$session = New-Object psobject
$session | Add-Member ScriptMethod GetItemFromID { param($MessageId, $StoreId) return $script:sample }
$script:sample = [pscustomobject]@{ Parent = [pscustomobject]@{ StoreID = 'store-b'; EntryID = 'inbox-a' }; Class = 43 }
Assert-Blocked { Get-ScopedItem $session $store $folderIds ('A' * 32) } 'message_outside_scope'
$script:sample.Parent.StoreID = 'store-a'; $script:sample.Parent.EntryID = 'deleted-a'
Assert-Blocked { Get-ScopedItem $session $store $folderIds ('A' * 32) } 'message_outside_scope'
$script:sample.Parent.EntryID = 'inbox-a'; $script:sample.Class = 26
Assert-Blocked { Get-ScopedItem $session $store $folderIds ('A' * 32) } 'message_outside_scope'
$script:sample.Class = 43
[void](Get-ScopedItem $session $store $folderIds ('A' * 32))
Assert-Blocked { Get-ScopedItem $session $store $folderIds 'not-an-entry-id' } 'invalid_message_id'

# Synthetic attachment properties: metadata listing must never access file bytes.
$script:byteReads = 0
$property = New-Object psobject
$property | Add-Member ScriptMethod GetProperty {
    param($Tag)
    if ($Tag.EndsWith('0x37010102')) { $script:byteReads++; return ,([byte[]]@(0, 1, 254, 255)) }
    if ($Tag.EndsWith('0x370E001F')) { return 'application/octet-stream' }
    if ($Tag.EndsWith('0x3712001F')) { return '' }
    if ($Tag.EndsWith('0x7FFE000B')) { return $false }
    throw 'Missing synthetic property'
}
$script:attachment = [pscustomobject]@{ FileName = 'example.bin'; Size = 4; Type = 1; PropertyAccessor = $property }
$script:attachment | Add-Member ScriptMethod SaveAsFile {
    param($Path)
    $script:byteReads++
    [IO.File]::WriteAllBytes($Path, [byte[]]@(0, 1, 254, 255))
}
$collection = New-Object psobject -Property @{ Count = 2 }
$collection | Add-Member ScriptMethod Item { param($Index) return $script:attachment }
$item = [pscustomobject]@{ EntryID = 'A' * 32; Permission = 0; MessageClass = 'IPM.Note'; LastModificationTime = [datetime]'2026-10-15T12:00:00'; Attachments = $collection }
$listing = Get-ItemAttachments $item 'selected-fingerprint'
if ($script:byteReads -ne 0 -or $listing.returned -ne 2) { throw 'Metadata listing accessed original files' }
if ($listing.attachments[0].id -eq $listing.attachments[1].id) { throw 'Duplicate filename IDs collided' }
$exportRoot = Join-Path ([IO.Path]::GetTempPath()) ('mail-bridge-synthetic-' + [guid]::NewGuid().ToString('N'))
$exportDirectory = Join-Path $exportRoot ('e_' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($exportDirectory)
$exportPath = Join-Path $exportDirectory 'attachment.bin'
try {
    $original = Get-ItemAttachments $item 'selected-fingerprint' $listing.attachments[1].id $exportPath
    if (-not $original.exported -or [Convert]::ToBase64String([IO.File]::ReadAllBytes($exportPath)) -ne 'AAH+/w==' -or $script:byteReads -ne 1) { throw 'Original bytes changed or multiple attachments read' }
    Assert-Blocked { Get-ItemAttachments $item 'selected-fingerprint' $listing.attachments[1].id $exportPath } 'invalid_export_path'
} finally {
    [IO.File]::Delete($exportPath)
    [IO.Directory]::Delete($exportDirectory)
    [IO.Directory]::Delete($exportRoot)
}
Assert-Blocked { Get-ItemAttachments $item 'different-fingerprint' $listing.attachments[0].id } 'attachment_changed'
$item.Permission = 1
Assert-Blocked { Get-ItemAttachments $item 'selected-fingerprint' } 'protected_message'
$item.Permission = 0; $item.MessageClass = 'IPM.Note.SMIME'
Assert-Blocked { Get-ItemAttachments $item 'selected-fingerprint' } 'protected_message'
$item.MessageClass = 'IPM.Note'; $script:attachment.Type = 5
$listing = Get-ItemAttachments $item 'selected-fingerprint'
Assert-Blocked { Get-ItemAttachments $item 'selected-fingerprint' $listing.attachments[0].id } 'unsupported_attachment'
$script:attachment.Type = 1; $script:attachment.Size = 10485761
$listing = Get-ItemAttachments $item 'selected-fingerprint'
Assert-Blocked { Get-ItemAttachments $item 'selected-fingerprint' $listing.attachments[0].id } 'unsupported_attachment'
$script:attachment.Size = 4
$listing = Get-ItemAttachments $item 'selected-fingerprint'
$item.LastModificationTime = $item.LastModificationTime.AddSeconds(1)
Assert-Blocked { Get-ItemAttachments $item 'selected-fingerprint' $listing.attachments[0].id } 'attachment_changed'

# Restrict the requested date range before applying the newest-candidate limit.
$filter = New-CandidateFilter '2026-10-01T00:00:00+00:00' '2026-11-01T00:00:00+00:00'
if ($filter -notmatch '0x0E060040.*>=' -or $filter -notmatch '0x0E060040.*<') { throw 'Missing UTC table date bounds' }
$attachmentsFilter = New-CandidateFilter '' '' $true
if ($attachmentsFilter -notmatch '0x0E1B000B.*= 1' -or $filter -match '0x0E1B000B') { throw 'Attachment metadata filter did not precede candidate limits' }
$precise = New-CandidateFilter '2026-10-01T10:30:15+00:00' '2026-10-01T10:30:45+00:00'
$broadEnd = ([datetime]'2026-10-01T10:31:00').ToString('g', [Globalization.CultureInfo]::CurrentCulture).Replace("'", "''")
if (-not $precise.Contains($broadEnd)) { throw 'Provider date filter rounded exclusive end inward' }
$startUtc = [DateTimeOffset]::Parse('2026-10-01T10:30:15.000001Z').UtcDateTime
$endUtc = $startUtc.AddTicks(10)
if (-not (Test-TimeBounds $startUtc $startUtc $endUtc) -or (Test-TimeBounds $endUtc $startUtc $endUtc)) { throw 'Exact inclusive/exclusive date bounds failed' }

# Body paging reaches later text and never breaks a Unicode surrogate pair.
$body = ('A' * 100) + [char]::ConvertFromUtf32(0x1F680) + ('B' * 100)
$offset = 0; $reconstructed = ''
do {
    $page = Get-BodySection $body 101 $offset
    if ($page.body_sha256 -cne (Get-Digest $body)) { throw 'Body revision changed across sections' }
    $reconstructed += $page.body
    $offset = $page.next_body_offset
} while ($page.has_more_body)
if ($reconstructed -cne $body) { throw 'Body pagination lost or duplicated text' }
$later = Get-BodySection $body 100 102
if ($later.body -cne ('B' * 100) -or $later.has_more_body) { throw 'Later body section unavailable' }
if ((Get-BodySection $body 100 10000).body -ne '') { throw 'Offset beyond body must be empty' }

# Candidate continuation advances even when a window has no matching results.
$candidates = @('newest', 'middle', 'oldest')
$first = @(Get-ScanWindow $candidates 0 1)
$progress = Get-ScanProgress $candidates.Count 0 $first.Count
if ($first[0] -ne 'newest' -or $progress.next_scan_offset -ne 1 -or -not $progress.scan_incomplete) { throw 'First candidate window continuation missing' }
$last = @(Get-ScanWindow $candidates $progress.next_scan_offset 2)
$finished = Get-ScanProgress $candidates.Count 1 $last.Count
if (($last -join ',') -ne 'middle,oldest' -or $finished.scan_incomplete -or $null -ne $finished.next_scan_offset) { throw 'Older candidate window did not complete' }
$partial = Get-ScanProgress 10 2 3
if ($partial.next_scan_offset -ne 5) { throw 'Timed scan continuation skipped unexamined candidates' }

# Compact subject/newest queries must not enumerate collections or read the body.
$forbidden = New-Object psobject -Property @{ Count = 1 }
$forbidden | Add-Member ScriptMethod Item { throw 'Unrequested metadata collection access' }
$compact = [pscustomobject]@{ EntryID = 'A' * 32; ConversationID = 'demo'; ReceivedTime = [datetime]'2026-10-15T12:00:00'
    Subject = 'Synthetic'; SenderName = 'Alex'; SenderEmailAddress = 'alex@example.test'; SenderEmailType = 'SMTP'
    To = 'Demo'; CC = ''; Parent = [pscustomobject]@{ EntryID = 'inbox-a'; Name = 'Inbox' }
    Recipients = $forbidden; Attachments = $forbidden }
$compact | Add-Member ScriptProperty Body { throw 'Unrequested body access' }
$summary = Get-Message $compact $false 6000 0 $false $false
if ($summary.recipient_addresses_included -or $summary.attachment_names_included -or -not $summary.has_attachments) { throw 'Compact metadata disclosure is incorrect' }

# Unicode/ANSI Internet Message-ID fallback supports label-copy candidates without
# reading a body or enumerating recipients/attachments for compact searches.
$mailProperty = New-Object psobject
$mailProperty | Add-Member ScriptMethod GetProperty {
    param($Tag)
    if ($Tag.EndsWith('0x1035001E')) { return '<same@example.test>' }
    throw 'Synthetic Unicode property unavailable'
}
$compact | Add-Member NoteProperty PropertyAccessor $mailProperty
$roles = @{ 'inbox-a' = 'inbox' }
$summary = Get-Message $compact $false 6000 0 $false $false $roles
if ($summary.message_id_header -cne '<same@example.test>' -or $summary.folder_role -ne 'inbox' -or $summary.date_basis -ne 'received_time') { throw 'Message evidence metadata unavailable' }
if ($summary.message_id_header_truncated) { throw 'Short header was marked truncated' }
$oversizeProperty = New-Object psobject
$oversizeProperty | Add-Member ScriptMethod GetProperty { param($Tag) return ('x' * 5000) }
$compact.PropertyAccessor = $oversizeProperty
$summary = Get-Message $compact $false 6000 0 $false $false
if (-not $summary.message_id_header_truncated -or $summary.message_id_header.Length -ne 4096) { throw 'Provider header output is unbounded' }

# Provider folder IDs, not translated display names, define roles. A foreign or
# unknown default folder never adds an account folder to the eligible set.
$roleStore = New-Object psobject -Property @{ StoreID = 'store-a' }
$roleStore | Add-Member ScriptMethod GetDefaultFolder {
    param($Kind)
    if ($Kind -eq 5) { return [pscustomobject]@{ EntryID = 'foreign-sent'; StoreID = 'store-b'; Name = 'Sent' } }
    if ($Kind -eq 6) { return [pscustomobject]@{ EntryID = 'inbox-a'; StoreID = 'store-a'; Name = 'Translated folder' } }
    throw 'Synthetic folder absent'
}
$roles = Get-FolderRoles $roleStore $folderIds
if ($roles.Count -ne 1 -or $roles['inbox-a'] -ne 'inbox') { throw 'Folder roles guessed names or escaped scope' }

$exchangeProperty = New-Object psobject
$exchangeProperty | Add-Member ScriptMethod GetProperty { param($Tag) return 'alex@example.test' }
$exchange = [pscustomobject]@{ Type = 'EX'; Address = '/o=synthetic/ou=example'; PropertyAccessor = $exchangeProperty }
if ((Get-SmtpAddress $exchange 'fallback') -cne 'alex@example.test') { throw 'Exchange SMTP resolution failed' }

# A visible Outlook instance may not yet have registered its ROT object. Only
# that COM failure may reconnect, and only to one process in this session.
$script:registeredFailure = $true
$script:activationCalls = 0
$script:currentSessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
$script:processes = @([pscustomobject]@{ SessionId = $script:currentSessionId })
function Get-RegisteredOutlookApplication {
    if ($script:registeredFailure) { throw [Runtime.InteropServices.COMException]::new('Synthetic missing ROT entry', -2147221021) }
    return 'registered-synthetic-instance'
}
function Get-Process { param($Name, $ErrorAction) return $script:processes }
function New-Object { param($ComObject) $script:activationCalls++; return 'connected-synthetic-instance' }
try {
    if ((Get-RunningOutlookApplication) -cne 'connected-synthetic-instance' -or $script:activationCalls -ne 1) { throw 'Missing ROT entry did not reconnect' }
    $script:registeredFailure = $false
    if ((Get-RunningOutlookApplication) -cne 'registered-synthetic-instance' -or $script:activationCalls -ne 1) { throw 'Registered instance caused unnecessary activation' }
    $script:registeredFailure = $true; $script:processes = @()
    Assert-Blocked { Get-RunningOutlookApplication } 'outlook_not_running'
    $script:processes = @([pscustomobject]@{ SessionId = $script:currentSessionId + 1 })
    Assert-Blocked { Get-RunningOutlookApplication } 'outlook_not_running'
    $script:processes = @([pscustomobject]@{ SessionId = $script:currentSessionId }, [pscustomobject]@{ SessionId = $script:currentSessionId })
    Assert-Blocked { Get-RunningOutlookApplication } 'outlook_instance_ambiguous'
    if ($script:activationCalls -ne 1) { throw 'Closed, foreign or ambiguous instance was activated' }
    function Get-RegisteredOutlookApplication { throw [Runtime.InteropServices.COMException]::new('Synthetic denied COM access', -2147024891) }
    Assert-Blocked { Get-RunningOutlookApplication } 'Synthetic denied COM access'
} finally {
    Remove-Item Function:Get-Process
    Remove-Item Function:New-Object
}

# Lifecycle requests must never activate COM, read accounts or inspect windows.
$script:runtimeProcesses = @()
$script:runtimeInstalled = $true
$script:runtimeProfile = $true
$script:startCalls = 0
function Get-RegisteredOutlookApplication { throw 'Lifecycle touched COM' }
function Get-ClassicOutlookExecutable { if ($script:runtimeInstalled) { return 'synthetic-outlook.exe' }; return '' }
function Test-OutlookProfileConfigured { return $script:runtimeProfile }
function Get-SessionOutlookProcesses { return $script:runtimeProcesses }
function Get-Process { param($Name, $ErrorAction) return @() }
function Start-Process {
    param($FilePath, $WindowStyle, [switch]$PassThru)
    if ($FilePath -cne 'synthetic-outlook.exe' -or $WindowStyle -cne 'Hidden') { throw 'Unsafe startup arguments' }
    $script:startCalls++
    $script:runtimeProcesses = @([pscustomobject]@{ Id = 1 })
}
try {
    $state = Invoke-OutlookRequest @{ operation = 'diagnostics' }
    if ($state.classic_outlook_running -or $state.computer_use_required -or $state.next_action -ne 'start_outlook' -or $script:startCalls) { throw 'Diagnostics started or read Outlook' }
    $started = Invoke-OutlookRequest @{ operation = 'start' }
    if (-not $started.started -or $script:startCalls -ne 1) { throw 'CLI did not start Outlook' }
    $again = Start-ClassicOutlook
    if ($again.started -or -not $again.already_running -or $script:startCalls -ne 1) { throw 'Startup is not idempotent' }
    $script:runtimeProcesses = @([pscustomobject]@{ Id = 1 }, [pscustomobject]@{ Id = 2 })
    Assert-Blocked { Start-ClassicOutlook } 'outlook_instance_ambiguous'
    $script:runtimeProcesses = @(); $script:runtimeInstalled = $false
    Assert-Blocked { Start-ClassicOutlook } 'classic_outlook_not_installed'
    $state = Get-OutlookRuntimeState
    if ($state.next_action -ne 'install_classic_outlook') { throw 'Missing classic Outlook reported ready' }
    $script:runtimeInstalled = $true; $script:runtimeProfile = $false
    Assert-Blocked { Start-ClassicOutlook } 'outlook_profile_required'
    $state = Get-OutlookRuntimeState
    if ($state.next_action -ne 'user_setup_outlook_profile' -or $script:startCalls -ne 1) { throw 'Unconfigured profile started' }
} finally {
    Remove-Item Function:Get-Process
    Remove-Item Function:Start-Process
}
Write-Output 'Outlook scope tests passed'
