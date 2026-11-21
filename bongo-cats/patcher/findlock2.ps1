$targets = @('BongoCat','Bongo','steam','UnityCrash','CrashReport')
Get-Process -ErrorAction SilentlyContinue | ForEach-Object {
  $p=$_
  if ($targets -contains $p.ProcessName) { "$($p.ProcessName) PID=$($p.Id) " }
} | Sort-Object -Unique
'---'
try {
  $bh = Get-Process | ForEach-Object { $_.ProcessName }
  "bongocat_running=" + [bool](Get-Process -Name 'BongoCat' -ErrorAction SilentlyContinue)
} catch { 'check_failed' }
