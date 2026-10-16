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
Write-Output 'Outlook scope tests passed'
