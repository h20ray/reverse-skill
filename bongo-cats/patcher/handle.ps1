$f = 'C:\Program Files (x86)\Steam\steamapps\common\BongoCat\BongoCat_Data\Managed\Assembly-CSharp.dll'
# try to open with no sharing to detect lock
try {
  $s = [System.IO.File]::Open($f, 'Open', 'ReadWrite', 'None')
  $s.Close()
  'UNLOCKED_OPEN_OK'
} catch { 'LOCKED: ' + $_.Exception.Message }
