$WSH = New-Object -ComObject WScript.Shell
$LNK = 'C:\Users\David Jr\Desktop\Narrador.lnk'
if (Test-Path $LNK) { Remove-Item $LNK }
$shortcut = $WSH.CreateShortcut($LNK)
$shortcut.TargetPath = 'C:\Users\David Jr\AppData\Local\Programs\Python\Python312\pythonw.exe'
$shortcut.Arguments = '"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\narrador_desktop.py"'
$shortcut.WorkingDirectory = 'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau'
$shortcut.Description = 'Narrador do EcoSystemUmGrau - TTS continuo'
$shortcut.Save()
Write-Host 'Atalho criado com sucesso' -ForegroundColor Green