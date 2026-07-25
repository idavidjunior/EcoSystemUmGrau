CreateObject("WScript.Shell").Run "pythonw.exe ""C:\Users\Playtec-bancada\Desktop\widget_updater.py""", 0, False
CreateObject("WScript.Shell").Run "pythonw.exe ""C:\Users\Playtec-bancada\Desktop\watchdog.py""", 0, False
WScript.Sleep 2000
CreateObject("WScript.Shell").Run "powershell.exe -STA -NoProfile -File ""C:\Users\Playtec-bancada\Desktop\MonitorPane.ps1""", 0, False
