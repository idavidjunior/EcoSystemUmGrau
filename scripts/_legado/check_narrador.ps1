Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'widget_edge|narrador_desktop|tts_service' } |
  ForEach-Object { "PID=$($_.ProcessId) NAME=$($_.Name) CMD=$($_.CommandLine)" }