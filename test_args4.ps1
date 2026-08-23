$pyArgs = @('scripts/observability_reliability.py', 'trace', '--action', 'start', '--mission-id', 'test-123')
Write-Host "Args: $pyArgs"
python @pyArgs