#!/usr/bin/env bash
cd /c/GitHub/reverse-skill/bongo-cats/patcher/bin/Debug/net8.0
dotnet p.dll "/c/Program Files (x86)/Steam/steamapps/common/BongoCat/BongoCat_Data/Managed/Assembly-CSharp.dll" 10000 > /tmp/pres.txt 2>&1
echo "rc=$?"
