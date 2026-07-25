Add-Type -Assembly System.Windows.Forms, System.Drawing
Add-Type @"
using System;using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool ReleaseCapture();
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
    public const uint WM_NCLBUTTONDOWN = 0x00A1;
    public const int HTCAPTION = 2;
    public static void DragForm(IntPtr h) { ReleaseCapture(); SendMessage(h, WM_NCLBUTTONDOWN, (IntPtr)HTCAPTION, IntPtr.Zero); }
}
"@

$jsonPath = "$env:USERPROFILE\Desktop\widget_status.json"
$updaterPath = "$env:USERPROFILE\Desktop\widget_updater.py"
$launcherPath = "$env:USERPROFILE\Desktop\launch_widget.vbs"
$startupDir = [Environment]::GetFolderPath("Startup")
$startupLnk = Join-Path $startupDir "MonitorPane.lnk"

$form = New-Object System.Windows.Forms.Form
$form.Text = "Monitor Pane"
$form.BackColor = [System.Drawing.Color]::FromArgb(12,12,18)
$form.Size = New-Object System.Drawing.Size(640, 370)
$form.MinimumSize = New-Object System.Drawing.Size(400, 220)
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.ShowInTaskbar = $false
$form.TopMost = $false
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.Add_Load({
    $screenW = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Width
    $form.Location = New-Object System.Drawing.Point(($screenW - $form.Width - 20), 10)
})
$form.Add_MouseDown({ param($s,$e) if ($e.Button -eq "Left") { [Win32]::DragForm($form.Handle) } })
$form.Add_Resize({
    $closeBtn.Location = New-Object System.Drawing.Point(($form.ClientSize.Width - 30), 2)
    $resize.Location = New-Object System.Drawing.Point(($form.ClientSize.Width - 16), ($form.ClientSize.Height - 16))
})

$web = New-Object System.Windows.Forms.WebBrowser
$web.Size = $form.ClientSize
$web.Location = New-Object System.Drawing.Point(0,0)
$web.ScrollBarsEnabled = $false
$web.AllowWebBrowserDrop = $false
$web.IsWebBrowserContextMenuEnabled = $false
$web.WebBrowserShortcutsEnabled = $false
$web.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$form.Controls.Add($web)

$closeBtn = New-Object System.Windows.Forms.Button
$closeBtn.Text = "x"
$closeBtn.Font = New-Object System.Drawing.Font("Consolas", 14)
$closeBtn.ForeColor = [System.Drawing.Color]::FromArgb(80,80,104)
$closeBtn.BackColor = [System.Drawing.Color]::FromArgb(12,12,18)
$closeBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$closeBtn.FlatAppearance.BorderSize = 0
$closeBtn.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Right
$closeBtn.Location = New-Object System.Drawing.Point(($form.ClientSize.Width - 30), 2)
$closeBtn.Size = New-Object System.Drawing.Size(28, 28)
$closeBtn.Add_Click({ $form.Close() })
$form.Controls.Add($closeBtn)
$closeBtn.BringToFront()

$resize = New-Object System.Windows.Forms.Panel
$resize.Cursor = [System.Windows.Forms.Cursors]::SizeNWSE
$resize.Anchor = [System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Right
$resize.BackColor = [System.Drawing.Color]::FromArgb(40,40,60)
$resize.Size = New-Object System.Drawing.Size(16, 16)
$resize.Location = New-Object System.Drawing.Point(($form.ClientSize.Width - 16), ($form.ClientSize.Height - 16))
$resize.Add_MouseDown({
    [Win32]::ReleaseCapture()
    [Win32]::SendMessage($form.Handle, 0x0112, [IntPtr]0xF008, [IntPtr]0)
})
$form.Controls.Add($resize)
$resize.BringToFront()

function BridgeState {
    $startup = Test-Path $startupLnk
    $mon = $false
    if (Test-Path $jsonPath) {
        $age = [int]((Get-Date) - (Get-Item $jsonPath).LastWriteTime).TotalSeconds
        $mon = $age -le 20
    }
    return @{startup=$startup;monitoring=$mon}
}

function BuildHtml {
    $d = $null
    if (Test-Path $jsonPath) { try { $d = Get-Content $jsonPath -Raw | ConvertFrom-Json } catch {} }
    $st = BridgeState

    if (-not $d) {
        return "<html><body style='background:#0c0c12;color:#606080;font:16px Consolas;padding:10px'>aguardando...</body></html>"
    }

    $pro = $d.providers.providers; $po = $d.ports; $svc = $d.services; $srv = $d.servers
    $total = $pro.Count + 2 + 3; $ok = 0
    foreach ($p in $pro) { if ($p.status -match "ATIVO|FALLBACK|ONLINE") { $ok++ } }
    if ($po."50136" -eq "LISTENING") { $ok++ }
    if ($po."50137" -eq "LISTENING") { $ok++ }
    if ($svc.rustdesk -eq "RUNNING") { $ok++ }
    if ($svc.adb -eq "CONNECTED") { $ok++ }
    if ($svc.mcp -eq "RUNNING") { $ok++ }
    $pct = if ($total -gt 0) { [math]::Round($ok / $total * 100) } else { 0 }
    $hc = if ($pct -ge 85) { "#4ac85a" } elseif ($pct -ge 60) { "#c8b830" } else { "#f04838" }

    $stxt = if ($st.startup) { "Iniciar c/ Windows: ON" } else { "Iniciar c/ Windows: OFF" }
    $mtxt = if ($st.monitoring) { "Monitoramento: ATIVO" } else { "Monitoramento: PARADO" }

    $h = @"
<html><head><meta http-equiv='X-UA-Compatible' content='IE=edge'>
<style>
*{margin:0;padding:0}
html,body{width:100%;height:100%}
body{background:#0c0c12;color:#c8c8d8;font:16px Consolas;padding:8px 14px;cursor:default;overflow:hidden;display:flex;flex-direction:column;box-sizing:border-box}
#hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
#tt{font-size:14px;color:#7070a0;font-weight:bold}
#saude{font-size:26px;font-weight:bold;margin-bottom:6px;flex-shrink:0}
.sep{color:#505078;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin:5px 0 2px 0;flex-shrink:0}
.row{display:flex;flex-wrap:wrap;gap:3px 6px;line-height:1.9;flex-shrink:0}
.b{display:inline-block;padding:0 7px;border-radius:3px;white-space:nowrap;font-size:16px;flex-shrink:0}
.g{background:#183018;color:#4ac85a}
.gg{background:#183018;color:#4ac85a;font-weight:bold}
.rr{background:#301818;color:#f04838}
.z{background:#181824;color:#606080}
#ts{color:#404060;font-size:12px;margin-top:3px;flex-shrink:0}
#leg{color:#505068;font-size:11px;border-top:1px solid #1a1a24;padding:3px 0;margin-top:2px;flex-shrink:0}
#bar{border-top:1px solid #1a1a24;padding:4px 0;margin-top:auto;display:flex;gap:5px;flex-wrap:wrap;flex-shrink:0}
.btn{display:inline-block;padding:2px 10px;border-radius:3px;font:12px Consolas;cursor:pointer;text-decoration:none}
.on{background:#1a3a1a;color:#6ad87a}
.off{background:#3a1a1a;color:#f06050}
@media(max-height:280px){#leg{display:none}}
@media(max-height:240px){.sep{font-size:10px;margin:3px 0 1px 0}.row{line-height:1.6}}
</style></head><body>
<div id='hd'><span id='tt'>Monitor Pane</span></div>
<div id='saude' style='color:$hc'>SAUDE $pct%</div>
<div class='sep'>Provedores</div><div class='row'>
"@
    foreach ($p in $pro) {
        $on = $p.status -match "ATIVO|FALLBACK|ONLINE"
        $cl = if ($on) { "g" } else { "z" }
        $n = $p.name -replace ".*/"
        $h += "<span class='b $cl'>$n</span>"
    }
    if ($d.providers.active_provider) {
        $an = $d.providers.active_provider -replace ".*/"
        $h += "<span class='b gg'>&rarr; $an</span>"
    }

    $h += "</div><div class='sep'>Servidores MCP</div><div class='row'>"
    foreach ($s in $srv) {
        $on = ($s.port -eq 50136 -and $po."50136" -eq "LISTENING") -or ($s.port -eq 50137 -and $po."50137" -eq "LISTENING")
        $cl = if ($on) { "g" } else { "rr" }
        $h += "<span class='b $cl'>$($s.name) :$($s.port)</span>"
    }

    $h += "</div><div class='sep'>Servicos</div><div class='row'>"
    $items = @( @("RustDesk", $svc.rustdesk, "RUNNING"), @("ADB", $svc.adb, "CONNECTED"), @("MCP", $svc.mcp, "RUNNING") )
    foreach ($item in $items) {
        $on = ($item[1] -eq $item[2]); $dot = if ($on) { "&#9679;" } else { "&#9678;" }
        $cl = if ($on) { "g" } else { "rr" }
        $h += "<span class='b $cl'>$($item[0]) $dot</span>"
    }

    $sb = if ($st.startup) { "on" } else { "off" }
    $mb = if ($st.monitoring) { "on" } else { "off" }

    # Recovery section
    $rc = $d.recovery
    $rhtml = ""
    if ($rc) {
        $rcStatus = $rc.status
        $rcMsg = $rc.message
        $rcFree = $rc.consecutive_failures
        $rcTotal = $rc.total_recoveries
        $rcColor = "#4ac85a"
        $rcIcon = "&#9679;"
        if ($rcStatus -eq "critical") { $rcColor = "#f04838"; $rcIcon = "&#9888;" }
        elseif ($rcStatus -eq "failed") { $rcColor = "#c8b830"; $rcIcon = "&#9678;" }
        elseif ($rcStatus -eq "recovered") { $rcColor = "#6ad87a"; $rcIcon = "&#10003;" }
        $rhtml = "<div class='sep' style='margin-top:2px'>Recuperacao</div><div class='row'><span class='b' style='background:#181824;color:$rcColor'>$rcIcon watchdog $(if ($rcTotal -gt 0){$rcTotal}else{'ativo'})</span>"
        if ($rcFree -gt 0) { $rhtml += "<span class='b rr'>$rcFree falhas consec.</span>" }
        if ($rcMsg -and $rcMsg -ne "Watchdog iniciado" -and $rcMsg -ne "MCP saudavel") {
            $shortMsg = $rcMsg
            if ($shortMsg.Length -gt 35) { $shortMsg = $shortMsg.Substring(0,35) + "..." }
            $rhtml += "<span class='b' style='background:#181824;color:#8080b0;font-size:14px'>$shortMsg</span>"
        }
        $rhtml += "</div>"
    }

    $h += @"
</div>
$rhtml
<div id='ts'>atualizado $(Get-Date -Format HH:mm:ss)</div>
<div id='leg'><span style='color:#4ac85a'>&#9679;</span> $ok/$total itens online &nbsp; verde &#8805;85% &nbsp; amarelo &#8805;60% &nbsp; vermelho &lt;60%</div>
<div id='bar'>
<a class='btn $sb' href='widget://toggle-startup'>$stxt</a>
<a class='btn $mb' href='widget://toggle-monitor'>$mtxt</a>
</div>
</body></html>
"@
    return $h
}

$web.Add_Navigating({
    param($s, $e)
    $url = $e.Url.ToString()
    if ($url -match "widget://toggle-startup") {
        $e.Cancel = $true
        $lnk = $startupLnk
        if (Test-Path $lnk) {
            Remove-Item $lnk -Force
        } else {
            $wshell = New-Object -ComObject WScript.Shell
            $s = $wshell.CreateShortcut($lnk)
            $s.TargetPath = "wscript.exe"
            $s.Arguments = "`"$launcherPath`""
            $s.WindowStyle = 7
            $s.Save()
        }
        $web.DocumentText = BuildHtml
        return
    }
    if ($url -match "widget://toggle-monitor") {
        $e.Cancel = $true
        $procs = @(Get-Process -Name pythonw -ErrorAction SilentlyContinue)
        if ($procs.Count -gt 0) {
            $procs | Stop-Process -Force
            Start-Sleep -Milliseconds 500
        } else {
            Start-Process pythonw -ArgumentList "`"$updaterPath`"" -WindowStyle Hidden
        }
        $web.DocumentText = BuildHtml
        return
    }
})

$web.DocumentText = BuildHtml

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 3000
$timer.Add_Tick({ $web.DocumentText = BuildHtml })
$timer.Start()

[System.Windows.Forms.Application]::Run($form)
