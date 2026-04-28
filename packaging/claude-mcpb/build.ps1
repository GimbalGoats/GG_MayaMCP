[CmdletBinding()]
param(
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$packageDir = Split-Path -Parent $PSCommandPath
$repoRoot = Resolve-Path (Join-Path $packageDir "..\..")

if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "dist\mcpb"
}

$resolvedOutputParent = Split-Path -Parent $OutputDir
if ($resolvedOutputParent -and -not (Test-Path $resolvedOutputParent)) {
    New-Item -ItemType Directory -Path $resolvedOutputParent | Out-Null
}

$outputRoot = if (Test-Path $OutputDir) {
    Resolve-Path $OutputDir
} else {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Resolve-Path $OutputDir
}

$stageDir = Join-Path $outputRoot "maya-mcp"
$resolvedRepoRoot = [System.IO.Path]::GetFullPath($repoRoot)
$resolvedStageDir = [System.IO.Path]::GetFullPath($stageDir)

if (-not $resolvedStageDir.StartsWith($resolvedRepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to stage outside the repository: $resolvedStageDir"
}

if (Test-Path $stageDir) {
    Remove-Item -LiteralPath $stageDir -Recurse -Force
}

New-Item -ItemType Directory -Path $stageDir | Out-Null

Copy-Item -LiteralPath (Join-Path $packageDir "manifest.json") -Destination $stageDir
Copy-Item -LiteralPath (Join-Path $packageDir ".mcpbignore") -Destination $stageDir
Copy-Item -LiteralPath (Join-Path $packageDir "README.md") -Destination (Join-Path $stageDir "README.md")
Copy-Item -LiteralPath (Join-Path $repoRoot "LICENSE") -Destination $stageDir
Copy-Item -LiteralPath (Join-Path $repoRoot "pyproject.toml") -Destination $stageDir
Copy-Item -LiteralPath (Join-Path $repoRoot "CHANGELOG.md") -Destination $stageDir
Copy-Item -LiteralPath (Join-Path $repoRoot "src") -Destination $stageDir -Recurse
Copy-Item -LiteralPath (Join-Path $repoRoot "docs") -Destination $stageDir -Recurse

$mcpbCommand = Get-Command mcpb -ErrorAction SilentlyContinue
if (-not $mcpbCommand) {
    $localMcpb = Join-Path $env:USERPROFILE ".tools\mcpb\node_modules\.bin\mcpb.cmd"
    if (Test-Path $localMcpb) {
        $mcpbCommand = Get-Command $localMcpb
    }
}

if (-not $mcpbCommand) {
    throw "mcpb CLI not found. Install it with: npm install --prefix `$env:USERPROFILE\.tools\mcpb @anthropic-ai/mcpb"
}

Push-Location $stageDir
try {
    & $mcpbCommand.Source pack
} finally {
    Pop-Location
}

Write-Host "MCPB staging directory: $stageDir"
