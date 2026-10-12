[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'ScheduleI-ChineseLauncher'),
    [string]$FontPath = '',
    [int]$FontNumber = 0,
    [string]$ZipPath = '',
    [switch]$NoZip
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'This builder supports Windows x64 only.'
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outputPath) {
    throw 'Output directory already exists. Keep the installed launcher and choose another -OutputDirectory.'
}
if (-not $FontPath) {
    $fontDirectory = [Environment]::GetFolderPath('Fonts')
    foreach ($fontName in @('msyh.ttc', 'simhei.ttf')) {
        $candidate = Join-Path $fontDirectory $fontName
        if (Test-Path -LiteralPath $candidate) { $FontPath = $candidate; break }
    }
}
if (-not $FontPath -or -not (Test-Path -LiteralPath $FontPath -PathType Leaf)) {
    throw 'No Chinese font found. Supply -FontPath with a local TTF, OTF, or TTC font.'
}
if ($NoZip -and $ZipPath) { throw '-NoZip and -ZipPath cannot be used together.' }
if (-not $NoZip) {
    if (-not $ZipPath) { $ZipPath = $outputPath.TrimEnd('\') + '.zip' }
    $ZipPath = [IO.Path]::GetFullPath($ZipPath)
    if (Test-Path -LiteralPath $ZipPath) { throw 'ZIP output already exists. Choose another -ZipPath.' }
}
$cachePath = Join-Path ([IO.Path]::GetTempPath()) 'ScheduleI-ChineseLauncher-downloads'
New-Item -ItemType Directory -Path $cachePath -Force | Out-Null
$pythonZip = Join-Path $cachePath 'python-3.13.5-embed-amd64.zip'
$pythonUrl = 'https://www.python.org/ftp/python/3.13.5/python-3.13.5-embed-amd64.zip'
$pythonHash = '7d2650fd9d1b9d002d4a315d5f354247fd6a44f30517c7ef577b08f57a0fb6d9'
if (-not (Test-Path -LiteralPath $pythonZip)) {
    Write-Host 'Downloading the private Python runtime...'
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip
}
if ((Get-FileHash -LiteralPath $pythonZip -Algorithm SHA256).Hash -ine $pythonHash) {
    throw 'Python download checksum failed. No launcher was installed.'
}
$runtimePath = Join-Path $outputPath 'runtime'
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
Expand-Archive -LiteralPath $pythonZip -DestinationPath $runtimePath
$searchPaths = "python313.zip`n.`n..`nLib/site-packages`nimport site`n"
[IO.File]::WriteAllText((Join-Path $runtimePath 'python313._pth'), $searchPaths, [Text.Encoding]::ASCII)
$bundleArgs = @((Join-Path $PSScriptRoot 'build_bundle.py'), '--source', $PSScriptRoot,
    '--output', $outputPath, '--font', [IO.Path]::GetFullPath($FontPath), '--font-number', [string]$FontNumber,
    '--cache', $cachePath)
if (-not $NoZip) { $bundleArgs += @('--zip', $ZipPath) }
& (Join-Path $runtimePath 'python.exe') @bundleArgs
if ($LASTEXITCODE -ne 0) {
    throw 'Build failed. The game and Steam settings were not changed. See the error above.'
}
Write-Host ('Launcher ready: ' + $outputPath)
if (-not $NoZip) { Write-Host ('Transfer ZIP: ' + $ZipPath) }
Write-Host 'Next: double-click the generated CMD file, then copy its line into Steam Launch Options.'
