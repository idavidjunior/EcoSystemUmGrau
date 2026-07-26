# Uninstall watcher
& "C:\Users\Playtec-bancada\.local\share\opencode\worktree\EcoSystemUmGrau\install-watcher.ps1" -Uninstall
Remove-Item "C:\Users\Playtec-bancada\.vault-watch-launcher.ps1" -Force -ErrorAction SilentlyContinue
Write-Host "Watcher removido completamente." -ForegroundColor Green
Start-Sleep 2
