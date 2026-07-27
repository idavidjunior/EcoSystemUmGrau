param(
  [switch]$RunLab
)

$ErrorActionPreference = "Stop"

python ./scripts/build_core_and_targets.py
./scripts/validate-ecosystem.ps1
./scripts/validate-doc-links.ps1

if ($RunLab) {
  python ./scripts/evaluate_reliability_lab.py
}

Write-Host "Build pipeline completed." -ForegroundColor Green
