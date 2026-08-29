Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName WindowsBase

# Define the window
$window = New-Object System.Windows.Window
$window.WindowStyle = 'None'
$window.AllowsTransparency = $true
$window.Background = [System.Windows.Media.Brushes]::Transparent
$window.Topmost = $true
$window.ShowInTaskbar = $false
$window.Width = 200
$window.Height = 100
$window.Left = ([System.Windows.SystemParameters]::PrimaryScreenWidth - $window.Width) - 10
$window.Top = 10

# Create a grid for layout
$grid = New-Object System.Windows.Controls.Grid
$window.Content = $grid

# Add row definitions
$grid.RowDefinitions.Add((New-Object System.Windows.RowDefinition)) # Title
$grid.RowDefinitions.Add((New-Object System.Windows.RowDefinition)) # RAM text
$grid.RowDefinitions.Add((New-Object System.Windows.RowDefinition)) # Progress bar

# Title label
$titleLabel = New-Object System.Windows.Controls.Label
$titleLabel.Content = "MEMÓRIA RAM"
$titleLabel.FontSize = 14
$titleLabel.FontWeight = "Bold"
$titleLabel.Foreground = [System.Windows.Media.Brushes]::White
$titleLabel.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Left
$titleLabel.Margin = "10,10,0,0"
Grid.SetRow($titleLabel, 0)
$grid.Children.Add($titleLabel)

# RAM usage label
$ramLabel = New-Object System.Windows.Controls.Label
$ramLabel.Name = "RamLabel"
$ramLabel.FontSize = 16
$ramLabel.Foreground = [System.Windows.Media.Brushes]::White
$ramLabel.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Left
$ramLabel.Margin = "10,5,0,0"
Grid.SetRow($ramLabel, 1)
$grid.Children.Add($ramLabel)

# Progress bar
$progressBar = New-Object System.Windows.Controls.ProgressBar
$progressBar.Name = "ProgressBar"
$progressBar.Width = 180
$progressBar.Height = 10
$progressBar.Margin = "10,5,0,0"
$progressBar.HorizontalAlignment = [System.Windows.HorizontalAlignment]::Left
$progressBar.Background = [System.Windows.Media.Brushes]::Gray
$progressBar.Foreground = [System.Windows.Media.Brushes]::DodgerBlue
Grid.SetRow($progressBar, 2)
$grid.Children.Add($progressBar)

# Function to update RAM usage
function Update-RamInfo {
    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem
        $totalVisibleMB = $os.TotalVisibleMemorySize / 1024
        $freePhysicalMB = $os.FreePhysicalMemorySize / 1024
        $usedMB = $totalVisibleMB - $freePhysicalMB
        $percent = ($usedMB / $totalVisibleMB) * 100
        $totalGB = $totalVisibleMB / 1024
        $usedGB = $usedMB / 1024

        $ramLabel.Content = "{0:F1}% ({1:F1} GB / {2:F1} GB)" -f $percent, $usedGB, $totalGB
        $progressBar.Value = [int]$percent
    } catch {
        $ramLabel.Content = "Erro"
        $progressBar.Value = 0
    }
}

# Set up a timer to update every second
$timer = New-Object System.Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromSeconds(1)
$timer.Add_Tick({ Update-RamInfo })
$timer.Start()

# Initial update
Update-RamInfo

# Show the window
$window.ShowDialog() | Out-Null