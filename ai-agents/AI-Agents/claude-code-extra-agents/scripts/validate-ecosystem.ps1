param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Test-FrontMatterFile {
  param([string]$Path)

  $content = Get-Content $Path -Raw
  $result = [ordered]@{
    Path = $Path
    Ok = $true
    Issues = @()
  }

  if (-not $content.StartsWith("---")) {
    $result.Ok = $false
    $result.Issues += "Missing front matter start (---)"
    return [pscustomobject]$result
  }

  $required = @("name:", "description:", "allowed-tools:", "version:")
  foreach ($r in $required) {
    if ($content -notmatch [regex]::Escape($r)) {
      $result.Ok = $false
      $result.Issues += "Missing field: $r"
    }
  }

  return [pscustomobject]$result
}

$targets = @()
$targets += Get-ChildItem -Path (Join-Path $Root "agents") -Filter *.md -File -ErrorAction SilentlyContinue
$targets += Get-ChildItem -Path (Join-Path $Root "skills") -Recurse -Filter skill.md -File -ErrorAction SilentlyContinue

if ($targets.Count -eq 0) {
  Write-Host "No target files found."
  exit 1
}

$results = $targets | ForEach-Object { Test-FrontMatterFile -Path $_.FullName }
$failures = $results | Where-Object { -not $_.Ok }

Write-Host "Checked $($results.Count) files."
if ($failures.Count -eq 0) {
  Write-Host "OK: all files have required front matter fields."
  exit 0
}

Write-Host "FAIL: $($failures.Count) files with issues."
foreach ($f in $failures) {
  Write-Host "`n- $($f.Path)"
  foreach ($i in $f.Issues) {
    Write-Host "  - $i"
  }
}

exit 2
