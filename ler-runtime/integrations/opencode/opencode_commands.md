# OpenCode Commands for Loop Engineering Agent

## Start Agent with Goal
```powershell
python loop.py "Create an Android Bible app with PDF and Word import"
```

## Check Status
```powershell
python loop.py --status
```

## Resume from Checkpoint
```powershell
python loop.py --resume
```

## Reset State
```powershell
python loop.py --reset
```

## OpenCode Bridge API

### Delegate a Goal
```python
from integrations.opencode.opencode_bridge import OpenCodeBridge
bridge = OpenCodeBridge("/path/to/LoopEngineeringAgent")
result = bridge.delegate_goal("Your goal here")
```

### Get Status
```python
status = bridge.get_status()
print(status["progress"])
```

### Execute Command
```python
result = bridge.execute_command("dir")
```

### Generate Report
```python
report = bridge.generate_report()
```
