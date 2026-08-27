param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [Parameter(Mandatory = $true)]
    [string]$Report,
    # Optional override: directory holding Gaea.Engine/Gaea/Gaea.Nodes/Newtonsoft.Json.
    # Needed when the install root carries a Zone.Identifier that PowerShell 5.1
    # refuses to LoadFrom under .NET remote-source policy (0x80131515).
    [string]$AssemblyDir = 'C:\Program Files\QuadSpinner\Gaea 2'
)

# Sea Above native Gaea->Unreal export prep.
# Graph-specific sibling of prepare_gaea_unreal_export_native.ps1, wired to the
# "Canyon River with Sea" example graph (validated reference of the
# liquid_cathedral setup). Key node ids in that graph:
#   671 Canyon -> 184 Erosion2 -> 199 HydroFix -> 243 Sea -> 549 Trees
#   243.Sea exposes Out (flooded height incl. waterline), Water (waterline mask),
#   and Depth. 184.Erosion2 exposes Flow. This is the false-ocean donor data.

$ErrorActionPreference = 'Stop'
$gaeaRoot = $AssemblyDir

$resolver = [System.ResolveEventHandler]{
    param($sender, $args)
    $assemblyName = ([System.Reflection.AssemblyName]$args.Name).Name
    $candidate = Join-Path $gaeaRoot ($assemblyName + '.dll')
    if (Test-Path -LiteralPath $candidate) {
        return [System.Reflection.Assembly]::LoadFrom($candidate)
    }
    return $null
}
[System.AppDomain]::CurrentDomain.add_AssemblyResolve($resolver)

foreach ($assemblyName in @('Gaea.Engine.dll', 'Gaea.dll', 'Gaea.Nodes.dll')) {
    [System.Reflection.Assembly]::LoadFrom((Join-Path $gaeaRoot $assemblyName)) | Out-Null
}

$allAssemblies = [System.AppDomain]::CurrentDomain.GetAssemblies()
$fileServiceType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.IO.FileService') } | Where-Object { $_ } | Select-Object -First 1
$assetType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.Fx.Asset') } | Where-Object { $_ } | Select-Object -First 1
$unrealType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Nodes.Unreal') } | Where-Object { $_ } | Select-Object -First 1
$exportType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Nodes.Export') } | Where-Object { $_ } | Select-Object -First 1
$float2Type = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.Fx.Float2') } | Where-Object { $_ } | Select-Object -First 1
$recordType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.Fx.ConnectionRecord') } | Where-Object { $_ } | Select-Object -First 1
$saveDefinitionType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.Fx.SaveDefinition') } | Where-Object { $_ } | Select-Object -First 1
$fileFormatsType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.IO.FileFormats') } | Where-Object { $_ } | Select-Object -First 1

$settings = $fileServiceType.GetField('JsonSettings', [System.Reflection.BindingFlags]'Static,NonPublic,Public').GetValue($null)
$sourceText = [System.IO.File]::ReadAllText($Source)
$root = [Newtonsoft.Json.Linq.JObject]::Parse($sourceText)
$assetJson = $root['Assets']['$values'][0].ToString([Newtonsoft.Json.Formatting]::None)
$asset = [Newtonsoft.Json.JsonConvert]::DeserializeObject($assetJson, $assetType, $settings)
$terrain = $asset.Terrain
$projectType = $allAssemblies | ForEach-Object { $_.GetType('QuadSpinner.Gaea.Engine.Fx.Project') } | Where-Object { $_ } | Select-Object -First 1

# Sanity: refuse to run against an unexpected graph.
foreach ($requiredId in @(671, 184, 199, 243)) {
    if (-not $terrain.Nodes.ContainsKey($requiredId)) {
        throw "Source graph is missing expected Canyon-River-with-Sea node id $requiredId"
    }
}

$nodeIds = @($terrain.Nodes.Keys | ForEach-Object { [int]$_ })
$nodeId = [int](($nodeIds | Measure-Object -Maximum).Maximum + 1)
if ($terrain.Nodes.ContainsKey($nodeId)) {
    throw "Refusing to overwrite existing Gaea node id $nodeId"
}

$unreal = [System.Activator]::CreateInstance($unrealType)
$unreal.Id = $nodeId
$unreal.Name = 'Unreal_SeaAbove'
$unreal.ExportState = [System.Enum]::Parse($unreal.ExportState.GetType(), 'WillExport')
$unreal.TargetSize = [System.Enum]::Parse($unreal.TargetSize.GetType(), 'x2017')
$unreal.Format = [System.Enum]::Parse($unreal.Format.GetType(), 'PNG')
$unreal.UnrealFriendlyNaming = $true
$unreal.Map1 = [System.Enum]::Parse($unreal.Map1.GetType(), 'Height')
$unreal.Map2 = [System.Enum]::Parse($unreal.Map2.GetType(), 'Mask')
$unreal.Map3 = [System.Enum]::Parse($unreal.Map3.GetType(), 'Mask')
$position = [System.Activator]::CreateInstance($float2Type)
$position.X = 32000.0
$position.Y = 27000.0
$unreal.Position = $position

$addPort = $unrealType.GetMethod('AddNewPort', [System.Reflection.BindingFlags]'Instance,NonPublic')
foreach ($unused in 1..3) {
    $null = $addPort.Invoke($unreal, @())
}
foreach ($port in $unreal.Ports) {
    $port.Parent = $unreal
    $port.IsExporting = $true
}

function Set-GaeaConnectionRecord {
    param(
        [int]$From,
        [string]$FromPort,
        [string]$ToPort
    )
    $target = $unreal.Ports | Where-Object { $_.Name -eq $ToPort } | Select-Object -First 1
    if ($null -eq $target) {
        throw "Unreal export input '$ToPort' was not created"
    }
    $recordConstructor = $recordType.GetConstructor([type[]]@([int], [int], [string], [string]))
    $record = $recordConstructor.Invoke([object[]]@($From, $nodeId, $FromPort, $ToPort))
    $target.Record = $record
}

# In = flooded height (includes sea/waterline), Input1 = river flow,
# Input2 = waterline mask (the false-ocean donor), Input3 = sea depth.
Set-GaeaConnectionRecord -From 243 -FromPort 'Out'   -ToPort 'In'
Set-GaeaConnectionRecord -From 184 -FromPort 'Flow'  -ToPort 'Input1'
Set-GaeaConnectionRecord -From 243 -FromPort 'Water' -ToPort 'Input2'
Set-GaeaConnectionRecord -From 243 -FromPort 'Depth' -ToPort 'Input3'


function New-GaeaMapExportNode {
    param(
        [int]$Id,
        [string]$Name,
        [int]$From,
        [string]$FromPort,
        [double]$X,
        [double]$Y
    )
    $exportNode = [System.Activator]::CreateInstance($exportType)
    $exportNode.Id = $Id
    $exportNode.Name = $Name
    $exportNode.ExportState = [System.Enum]::Parse($exportNode.ExportState.GetType(), 'WillExport')
    $exportNode.Format = [System.Enum]::Parse($exportNode.Format.GetType(), 'PNG16')
    $exportNode.Location = [System.Enum]::Parse($exportNode.Location.GetType(), 'BuildFolder')
    $exportPosition = [System.Activator]::CreateInstance($float2Type)
    $exportPosition.X = $X
    $exportPosition.Y = $Y
    $exportNode.Position = $exportPosition
    $exportInput = $exportNode.Ports | Where-Object { $_.Name -eq 'In' } | Select-Object -First 1
    if ($null -eq $exportInput) {
        throw "Export node '$Name' is missing its In port"
    }
    $exportInput.Record = $recordConstructor.Invoke([object[]]@($From, $Id, $FromPort, 'In'))
    $exportSaveDefinitionsListType = [System.Collections.Generic.List``1].MakeGenericType($saveDefinitionType)
    $exportSaveDefinitions = [System.Activator]::CreateInstance($exportSaveDefinitionsListType)
    $exportSaveDefinitionConstructor = $saveDefinitionType.GetConstructor([type[]]@([int], [string], $fileFormatsType, [bool]))
    $exportSaveFormat = [System.Enum]::Parse($fileFormatsType, 'PNG16')
    $exportSaveDefinition = $exportSaveDefinitionConstructor.Invoke([object[]]@($Id, $Name, $exportSaveFormat, $true))
    $exportSaveDefinitions.Add($exportSaveDefinition)
    $exportNode.SaveDefinitions = $exportSaveDefinitions
    return $exportNode
}

# Deterministic, independently verifiable map artifacts (mirrors the Aurora lane).
$newNodes = @()
$newNodes += New-GaeaMapExportNode -Id ($nodeId + 1) -Name 'SeaAbove_Height'    -From 243 -FromPort 'Out'   -X 31500.0 -Y 27250.0
$newNodes += New-GaeaMapExportNode -Id ($nodeId + 2) -Name 'SeaAbove_Waterline' -From 243 -FromPort 'Water' -X 32000.0 -Y 27500.0
$newNodes += New-GaeaMapExportNode -Id ($nodeId + 3) -Name 'SeaAbove_Flow'      -From 184 -FromPort 'Flow'  -X 32500.0 -Y 27250.0
$newNodes += New-GaeaMapExportNode -Id ($nodeId + 4) -Name 'SeaAbove_Depth'     -From 243 -FromPort 'Depth' -X 33000.0 -Y 27500.0

$nodesAddMethod = $terrain.Nodes.GetType().GetMethod('Add')
foreach ($newNode in @($unreal) + $newNodes) {
    $null = $nodesAddMethod.Invoke($terrain.Nodes, @([object]$newNode.Id, $newNode))
}

# Serialize through Project to keep backing fields coherent (see Aurora notes:
# raw Asset rewrites interleave serializers and corrupt the file).
$project = [System.Activator]::CreateInstance($projectType)
$project.Id = [string]$root['Id']
$project.Branch = [int]$root['Branch']
if ($null -ne $root['Iteration']) {
    $project.Iteration = [int]$root['Iteration']
}
$metadata = [System.Collections.Generic.Dictionary[string,string]]::new()
if ($null -ne $root['Metadata']) {
    foreach ($property in $root['Metadata'].Properties()) {
        if ($property.Name -ne '$id') {
            $metadata[$property.Name] = [string]$property.Value
        }
    }
}
$project.Metadata = $metadata
$assetsField = $projectType.GetField('Assets', [System.Reflection.BindingFlags]'Instance,Public,NonPublic')
$assetsListType = [System.Collections.Generic.List``1].MakeGenericType($assetType)
$assets = [System.Activator]::CreateInstance($assetsListType)
$assets.Add($asset)
$assetsField.SetValue($project, $assets)
$currentAssetBackingField = $projectType.GetField('<CurrentAsset>k__BackingField', [System.Reflection.BindingFlags]'Instance,NonPublic')
$currentAssetBackingField.SetValue($project, $asset)
$currentAssetIndexBackingField = $projectType.GetField('<_currentAsset>k__BackingField', [System.Reflection.BindingFlags]'Instance,NonPublic')
$currentAssetIndexBackingField.SetValue($project, 0)
$outputText = [Newtonsoft.Json.JsonConvert]::SerializeObject($project, $settings)
$destinationDirectory = Split-Path -Parent $Destination
New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($Destination, $outputText, $utf8NoBom)

$hash = [System.Security.Cryptography.SHA256]::Create()
$sourceHash = ([System.BitConverter]::ToString($hash.ComputeHash([System.IO.File]::ReadAllBytes($Source)))).Replace('-', '').ToLowerInvariant()
$destinationHash = ([System.BitConverter]::ToString($hash.ComputeHash([System.IO.File]::ReadAllBytes($Destination)))).Replace('-', '').ToLowerInvariant()
$result = [ordered]@{
    schema = 'melodia.gaea_unreal_export_native_copy.v1'
    variant = 'sea_above_2026_08_26'
    gaea_version = '2.2.3.2'
    source_graph = (Resolve-Path -LiteralPath $Source).Path
    source_sha256 = $sourceHash
    destination_graph = (Resolve-Path -LiteralPath $Destination).Path
    destination_sha256 = $destinationHash
    added_node_id = $nodeId
    added_node = 'Unreal_SeaAbove'
    target_size = 'x2017'
    format = 'PNG'
    save_definition = [ordered]@{ filename = 'Unreal_SeaAbove'; format = 'PNG16'; enabled = $true }
    map_export_nodes = @(
        [ordered]@{ id = ($nodeId + 1); filename = 'SeaAbove_Height';    source = 'Sea.Out (243)' },
        [ordered]@{ id = ($nodeId + 2); filename = 'SeaAbove_Waterline'; source = 'Sea.Water (243)' },
        [ordered]@{ id = ($nodeId + 3); filename = 'SeaAbove_Flow';      source = 'Erosion2.Flow (184)' },
        [ordered]@{ id = ($nodeId + 4); filename = 'SeaAbove_Depth';     source = 'Sea.Depth (243)' }
    )
    channels = [ordered]@{
        height   = 'Sea.Out (flooded terrain incl. waterline)'
        mask_1   = 'Erosion2.Flow (river flow)'
        mask_2   = 'Sea.Water (waterline/false-ocean mask)'
        mask_3   = 'Sea.Depth (sea depth)'
    }
    validation_repairs = [ordered]@{
        weathering_node = $null
        note = 'none required; Canyon River with Sea graph has no dangling optional ports observed'
    }
    classic_landscape_used = $false
}
$reportDirectory = Split-Path -Parent $Report
New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Report -Encoding utf8
$result | ConvertTo-Json -Depth 8
