$hits = @()
Get-Process | ForEach-Object {
  $p = $_
  try {
    if ($p.Modules -ne $null) {
      foreach ($m in $p.Modules) {
        if ($m.FileName -like '*BongoCat*') { $hits += ($p.ProcessName + ' PID=' + $p.Id) }
      }
    }
  } catch {}
}
$hits | Select-Object -Unique
if (-not $hits) { 'NO_LOCKER' }
