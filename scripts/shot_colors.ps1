Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Bitmap]::FromFile("C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\screen_full.png")
$w = $img.Width; $h = $img.Height
$colors = @{}
$step = 7  # sample para ir mais rapido
for ($y=0; $y -lt $h; $y+=$step) {
  for ($x=0; $x -lt $w; $x+=$step) {
    $px = $img.GetPixel($x, $y)
    $c = "{0:x2}{1:x2}{2:x2}" -f $px.R, $px.G, $px.B
    $colors[$c] = ($colors[$c] ?? 0) + 1
  }
}
# top colors
$top = $colors.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 12
Write-Output ("pixels(sampled step=$step): w=$w h=$h total_amostrado=" + ($colors.Values | Measure-Object -Sum).Sum)
Write-Output "Top cores:"
foreach ($e in $top) {
  Write-Output ("  $({0:x6} -f [int]0x$($e.Name))  -> $($e.Value)  (#$($e.Name))")
}