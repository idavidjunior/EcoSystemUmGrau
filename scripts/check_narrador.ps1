Get-CimInstance Win32_Process -Filter "name='python.exe' or name='pythonw.exe'" |
  Where-Object { $_.CommandLine -match 'narrador' } |
  ForEach-Object { "PID=$($_.ProcessId) CMD=$($_.CommandLine)" }