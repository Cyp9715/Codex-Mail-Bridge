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
$collection = New-Object psobject -Property @{ Count = 2 }
$collection | Add-Member ScriptMethod Item { param($Index) return $script:attachment }
$item = [pscustomobject]@{ EntryID = 'A' * 32; Permission = 0; MessageClass = 'IPM.Note'; LastModificationTime = [datetime]'2026-10-15T12:00:00'; Attachments = $collection }
$listing = Get-ItemAttachments $item 'selected-fingerprint'
if ($script:byteReads -ne 0 -or $listing.returned -ne 2) { throw 'Metadata listing accessed original files' }
if ($listing.attachments[0].id -eq $listing.attachments[1].id) { throw 'Duplicate filename IDs collided' }
$original = Get-ItemAttachments $item 'selected-fingerprint' $listing.attachments[1].id
if ($original.data_base64 -ne 'AAH+/w==' -or $script:byteReads -ne 1) { throw 'Original bytes changed or multiple attachments read' }
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

# Body paging reaches later text and never breaks a Unicode surrogate pair.
$body = ('A' * 100) + [char]::ConvertFromUtf32(0x1F680) + ('B' * 100)
$offset = 0; $reconstructed = ''
do {
    $page = Get-BodySection $body 101 $offset
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
Write-Output 'Outlook scope tests passed'
