$dumpFile = "C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\screenshots\ui_dump3.xml"
$formattedFile = "C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\screenshots\ui_dump3_formatted.xml"

# Read raw content
$raw = Get-Content $dumpFile -Raw

# Format XML
$formatted = $raw -replace '><', ">`n<"
$formatted | Set-Content $formattedFile -Encoding utf8

# Find elements with text
$lines = Get-Content $formattedFile
foreach ($line in $lines) {
    if ($line -match 'text="([^"]+)"') {
        $text = $matches[1]
        if ($text.Length -gt 2 -and $text -notmatch '^\s*$') {
            Write-Host $text.Substring(0, [Math]::Min(80, $text.Length))
        }
    }
}
