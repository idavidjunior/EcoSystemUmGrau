param(
    [Parameter(Position = 0)]
    [string]$Command = "help",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs = @()
)

# Test calling python directly with the args
$pyArgs = @("scripts/observability_reliability.py", "trace") + $RemainingArgs
Write-Host "Calling python with args: $pyArgs"
python @pyArgs