Start-Service WinHttpAutoProxySvc -ErrorAction SilentlyContinue
Start-Sleep 1
Start-Service iphlpsvc -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Service Tailscale -ErrorAction SilentlyContinue
Start-Sleep 2
& "C:\Program Files\Tailscale\tailscale.exe" up
