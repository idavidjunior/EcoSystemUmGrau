param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

$mdFiles = Get-ChildItem -Path $Root -Recurse -File -Include *.md
if ($mdFiles.Count -eq 0) {
  Write-Host "No markdown files found."
  exit 0
}

$pattern = '\[[^\]]+\]\(([^)]+)\)'
$errors = @()

foreach ($file in $mdFiles) {
  $content = Get-Content $file.FullName -Raw
  $matches = [regex]::Matches($content, $pattern)

  foreach ($m in $matches) {
    $target = $m.Groups[1].Value.Trim()

    if ([string]::IsNullOrWhiteSpace($target)) { continue }
    if ($target.StartsWith("http://") -or $target.StartsWith("https://") -or $target.StartsWith("mailto:")) { continue }
    if ($target.StartsWith("#")) { continue }

    $clean = $target.Split('#')[0].Split('?')[0]
    if ([string]::IsNullOrWhiteSpace($clean)) { continue }

    $resolved = Join-Path $file.DirectoryName $clean
    if (-not (Test-Path $resolved)) {
      $errors += [pscustomobject]@{
        File = $file.FullName
        Link = $target
      }
    }
  }
}

Write-Host "Checked $($mdFiles.Count) markdown files."
if ($errors.Count -eq 0) {
  Write-Host "OK: no broken local markdown links found."
  exit 0
}

Write-Host "FAIL: $($errors.Count) broken local markdown links found."
foreach ($e in $errors) {
  Write-Host "- $($e.File) -> $($e.Link)"
}
exit 2
