$WSH = New-Object -ComObject WScript.Shell
$LNK = 'C:\Users\David Jr\Desktop\Narrador.lnk'
if (Test-Path $LNK) { Remove-Item $LNK }
$shortcut = $WSH.CreateShortcut($LNK)
$shortcut.TargetPath = 'cmd.exe'
$shortcut.Arguments = '/c "C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\iniciar_narrador.bat"'
$shortcut.WorkingDirectory = 'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau'
$shortcut.Description = 'Narrador do EcoSystemUmGrau - TTS continuo'
$shortcut.Save()
Write-Host 'Atalho criado com sucesso' -ForegroundColor Green