Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
[Windows.Forms.Screen]$scr = [Windows.Forms.Screen]::PrimaryScreen
$bounds = $scr.Bounds
$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size)
$g.Dispose()
$outp = "C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\shot_now.png"
$bmp.Save($outp, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output ("screenshot salvo: " + $outp + " " + $bounds.Width + "x" + $bounds.Height)