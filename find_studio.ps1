
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
foreach ($w in $windows) {
    try {
        $name = $w.Current.Name
        $procId = $w.Current.ProcessId
        if ($name) {
            Write-Host "PID=$procId | '$name'"
        }
    } catch {}
}
