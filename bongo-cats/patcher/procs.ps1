Get-Process | Where-Object { $_.ProcessName -match 'steam|Bongo|Unity|mono|Crash' } |
  Select-Object ProcessName,Id | Format-Table -AutoSize
