param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [Parameter(Mandatory = $true)]
    [string]$Report
)

$ErrorActionPreference = 'Stop'
$gaeaRoot = 'C:\Program Files\QuadSpinner\Gaea 2'

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

$nodeIds = @($terrain.Nodes.Keys | ForEach-Object { [int]$_ })
$nodeId = [int](($nodeIds | Measure-Object -Maximum).Maximum + 1)
if ($terrain.Nodes.ContainsKey($nodeId)) {
    throw "Refusing to overwrite existing Gaea node id $nodeId"
}

$unreal = [System.Activator]::CreateInstance($unrealType)
$unreal.Id = $nodeId
$unreal.Name = 'Unreal_AuroraGlacier'
$unreal.ExportState = [System.Enum]::Parse($unreal.ExportState.GetType(), 'WillExport')
$unreal.TargetSize = [System.Enum]::Parse($unreal.TargetSize.GetType(), 'x2017')
$unreal.Format = [System.Enum]::Parse($unreal.Format.GetType(), 'PNG')
$unreal.UnrealFriendlyNaming = $true
$unreal.Map1 = [System.Enum]::Parse($unreal.Map1.GetType(), 'Height')
$unreal.Map2 = [System.Enum]::Parse($unreal.Map2.GetType(), 'Mask')
$unreal.Map3 = [System.Enum]::Parse($unreal.Map3.GetType(), 'Mask')
$unreal.Map4 = [System.Enum]::Parse($unreal.Map4.GetType(), 'Mask')
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

Set-GaeaConnectionRecord -From 989 -FromPort 'Out' -ToPort 'In'
Set-GaeaConnectionRecord -From 459 -FromPort 'Flow' -ToPort 'Input1'
Set-GaeaConnectionRecord -From 948 -FromPort 'SnowMap' -ToPort 'Input2'
Set-GaeaConnectionRecord -From 355 -FromPort 'Out' -ToPort 'Input3'

# The stock Glacier example has a second Weathering node (758) whose optional
# height-dependent port is empty. Swarm refuses the whole build when an export
# is present, so repair only this generated copy with the graph's existing
# radial-height source (339.Out).
$weathering = $terrain.Nodes[758]
$weatheringHeight = $weathering.Ports | Where-Object { $_.Name -eq 'Height' } | Select-Object -First 1
if ($null -eq $weatheringHeight) {
    throw 'Weathering node 758 is missing its Height port'
}
$recordConstructor = $recordType.GetConstructor([type[]]@([int], [int], [string], [string]))
$weatheringRecord = $recordConstructor.Invoke([object[]]@(339, 758, 'Out', 'Height'))
$weatheringHeight.Record = $weatheringRecord

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

# The UE node is retained as the platform definition target. These standard
# Gaea exports provide deterministic, independently verifiable map artifacts
# for the MeshTerrain adapter and are intentionally confined to this copy.
$mapExportNodes = @(
    (New-GaeaMapExportNode -Id 1000 -Name 'AuroraGlacier_Height' -From 989 -FromPort 'Out' -X 34000 -Y 25500),
    (New-GaeaMapExportNode -Id 1001 -Name 'AuroraGlacier_Flow' -From 459 -FromPort 'Flow' -X 34000 -Y 26500),
    (New-GaeaMapExportNode -Id 1002 -Name 'AuroraGlacier_Snow' -From 948 -FromPort 'SnowMap' -X 34000 -Y 27500),
    (New-GaeaMapExportNode -Id 1003 -Name 'AuroraGlacier_Curvature' -From 355 -FromPort 'Out' -X 34000 -Y 28500)
)
foreach ($mapExportNode in $mapExportNodes) {
    $terrain.Nodes.Add($mapExportNode.Id, $mapExportNode)
}

# Gaea persists Mark for Export as a SaveDefinition. ExportState itself is a
# runtime-only property and is intentionally ignored by the native serializer.
$saveDefinitionsListType = [System.Collections.Generic.List``1].MakeGenericType($saveDefinitionType)
$saveDefinitions = [System.Activator]::CreateInstance($saveDefinitionsListType)
$saveDefinitionConstructor = $saveDefinitionType.GetConstructor([type[]]@([int], [string], $fileFormatsType, [bool]))
$saveFormat = [System.Enum]::Parse($fileFormatsType, 'PNG16')
$saveDefinition = $saveDefinitionConstructor.Invoke([object[]]@($nodeId, 'Unreal_AuroraGlacier', $saveFormat, $true))
$saveDefinitions.Add($saveDefinition)
$unreal.SaveDefinitions = $saveDefinitions

$terrain.Nodes.Add($nodeId, $unreal)

# A .terrain file is a serialized Project wrapper, not just an Asset.  Serialize
# the complete native wrapper so Json.NET creates one consistent $id/$ref graph.
# Replacing the inner Asset in a previously parsed JObject leaves reference IDs
# from two serializer graphs interleaved and Gaea reports the file as corrupt.
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
    gaea_version = '2.2.3.2'
    source_graph = (Resolve-Path -LiteralPath $Source).Path
    source_sha256 = $sourceHash
    destination_graph = (Resolve-Path -LiteralPath $Destination).Path
    destination_sha256 = $destinationHash
    added_node_id = $nodeId
    added_node = 'Unreal_AuroraGlacier'
    target_size = 'x2017'
    format = 'PNG'
    save_definition = [ordered]@{
        filename = 'Unreal_AuroraGlacier'
        format = 'PNG16'
        enabled = $true
    }
    map_export_nodes = @(
        [ordered]@{ id = 1000; filename = 'AuroraGlacier_Height'; source = 'Glacier.Out' },
        [ordered]@{ id = 1001; filename = 'AuroraGlacier_Flow'; source = 'Erosion2.Flow' },
        [ordered]@{ id = 1002; filename = 'AuroraGlacier_Snow'; source = 'Snow.SnowMap' },
        [ordered]@{ id = 1003; filename = 'AuroraGlacier_Curvature'; source = 'Curvature.Out' }
    )
    channels = [ordered]@{
        height = 'Glacier.Out'
        mask_1 = 'Erosion2.Flow'
        mask_2 = 'Snow.SnowMap'
        mask_3 = 'Curvature.Out'
    }
    validation_repairs = [ordered]@{
        weathering_node = 758
        height_source = 'RadialGradient.Out (339)'
        repaired_port = 'Height'
    }
    classic_landscape_used = $false
}
$reportDirectory = Split-Path -Parent $Report
New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Report -Encoding utf8
$result | ConvertTo-Json -Depth 8
