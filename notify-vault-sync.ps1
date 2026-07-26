<#
.SYNOPSIS
    Exibe popup de notificacao do vault sync + som caracteristico.
    Chamado pelo watch-vault.ps1 como processo separado (nao bloqueante).
#>
param(
    [string[]]$ChangedFiles,
    [string]$Status = "ok",
    [string]$ErrorMessage = "",
    [string]$VaultPath = "$env:USERPROFILE\Desktop\Codigos",
    [string]$RepoRoot = ""
)

function Show-SyncNotification {
    param(
        [string[]]$ChangedFiles,
        [string]$Status,
        [string]$ErrorMessage,
        [string]$VaultPath,
        [string]$RepoRoot
    )

    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Vault Sync - Obsidian para GitHub"
    $form.Size = New-Object System.Drawing.Size(520, 380)
    $form.StartPosition = "CenterScreen"
    $form.TopMost = $true
    $form.ControlBox = $true
    $form.ShowInTaskbar = $true

    $form.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 245)

    $title = New-Object System.Windows.Forms.Label
    $title.Text = if ($Status -eq "ok") { "VAULT SINCRONIZADO COM GITHUB" } else { "ERRO NA SINCRONIZACAO" }
    $title.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
    $title.ForeColor = if ($Status -eq "ok") { [System.Drawing.Color]::DarkGreen } else { [System.Drawing.Color]::DarkRed }
    $title.Size = New-Object System.Drawing.Size(480, 30)
    $title.Location = New-Object System.Drawing.Point(20, 15)
    $form.Controls.Add($title)

    $ts = New-Object System.Windows.Forms.Label
    $ts.Text = (Get-Date -Format "dd/MM/yyyy HH:mm:ss")
    $ts.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $ts.ForeColor = [System.Drawing.Color]::Gray
    $ts.Size = New-Object System.Drawing.Size(480, 20)
    $ts.Location = New-Object System.Drawing.Point(20, 48)
    $form.Controls.Add($ts)

    $srcLabel = New-Object System.Windows.Forms.Label
    $srcLabel.Text = "DE: $VaultPath"
    $srcLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8)
    $srcLabel.ForeColor = [System.Drawing.Color]::DimGray
    $srcLabel.Size = New-Object System.Drawing.Size(480, 18)
    $srcLabel.Location = New-Object System.Drawing.Point(20, 72)
    $form.Controls.Add($srcLabel)

    $dstLabel = New-Object System.Windows.Forms.Label
    $dstLabel.Text = "PARA: $RepoRoot\vault\ -> GitHub (opencode/mighty-meadow)"
    $dstLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8)
    $dstLabel.ForeColor = [System.Drawing.Color]::DimGray
    $dstLabel.Size = New-Object System.Drawing.Size(480, 18)
    $dstLabel.Location = New-Object System.Drawing.Point(20, 92)
    $form.Controls.Add($dstLabel)

    if ($Status -eq "error") {
        $errBox = New-Object System.Windows.Forms.TextBox
        $errBox.Text = $ErrorMessage
        $errBox.Multiline = $true
        $errBox.ReadOnly = $true
        $errBox.ScrollBars = "Vertical"
        $errBox.Size = New-Object System.Drawing.Size(480, 150)
        $errBox.Location = New-Object System.Drawing.Point(20, 120)
        $errBox.BackColor = [System.Drawing.Color]::FromArgb(255, 240, 240)
        $form.Controls.Add($errBox)
    } else {
        $listLabel = New-Object System.Windows.Forms.Label
        $listLabel.Text = "ARQUIVOS ATUALIZADOS ($($ChangedFiles.Count)):"
        $listLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
        $listLabel.Size = New-Object System.Drawing.Size(480, 20)
        $listLabel.Location = New-Object System.Drawing.Point(20, 120)
        $form.Controls.Add($listLabel)

        $listBox = New-Object System.Windows.Forms.ListBox
        $listBox.Size = New-Object System.Drawing.Size(480, 150)
        $listBox.Location = New-Object System.Drawing.Point(20, 145)
        $listBox.Font = New-Object System.Drawing.Font("Consolas", 8)
        $listBox.ScrollAlwaysVisible = $true

        $displayFiles = $ChangedFiles | Select-Object -First 50
        if ($ChangedFiles.Count -gt 50) {
            $displayFiles += "... e mais $($ChangedFiles.Count - 50) arquivos"
        }
        $displayFiles | ForEach-Object { [void]$listBox.Items.Add($_) }
        $form.Controls.Add($listBox)
    }

    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = "FECHAR"
    $btn.Size = New-Object System.Drawing.Size(100, 30)
    $btn.Location = New-Object System.Drawing.Point(400, $form.Height - 65)
    $btn.BackColor = [System.Drawing.Color]::FromArgb(50, 50, 55)
    $btn.ForeColor = [System.Drawing.Color]::White
    $btn.FlatStyle = "Flat"
    $btn.Add_Click({ $form.Close() })
    $form.Controls.Add($btn)

    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 30000
    $timer.Add_Tick({ $form.Close() })
    $timer.Start()

    $form.ShowDialog() | Out-Null
}

function Play-SyncSound {
    param([string]$Type = "success")

    if ($Type -eq "success") {
        [System.Console]::Beep(660, 150)
        Start-Sleep -Milliseconds 80
        [System.Console]::Beep(880, 150)
        Start-Sleep -Milliseconds 80
        [System.Console]::Beep(1100, 250)
    } else {
        [System.Console]::Beep(400, 200)
        Start-Sleep -Milliseconds 100
        [System.Console]::Beep(300, 300)
    }
}

Show-SyncNotification -ChangedFiles $ChangedFiles -Status $Status -ErrorMessage $ErrorMessage -VaultPath $VaultPath -RepoRoot $RepoRoot
Play-SyncSound -Type $Status
