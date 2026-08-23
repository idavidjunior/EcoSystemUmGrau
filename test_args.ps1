$args = '--action start --mission-id test-123'
$arr = $args.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
Write-Host "Array: $arr"
Write-Host "Type: $($arr.GetType())"
Write-Host "Length: $($arr.Length)"
for ($i = 0; $i -lt $arr.Length; $i++) {
    Write-Host "[$i] = $($arr[$i])"
}