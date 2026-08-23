param(
    [Parameter(Position = 0)]
    [string]$Command = "help",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs = @()
)

function Test-Args {
    param([string[]]$Args)
    Write-Host "Args type: $($Args.GetType())"
    Write-Host "Args count: $($Args.Count)"
    Write-Host "Args: $Args"
}

Test-Args @RemainingArgs