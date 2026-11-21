#!/usr/bin/env bash
cd "$(dirname "$0")/dumptool"
dotnet bin/Debug/net8.0/d.dll "C:/Program Files (x86)/Steam/steamapps/common/BongoCat/BongoCat_Data/Managed/Assembly-CSharp.dll" > /c/GitHub/reverse-skill/bongo-cats/authenticated 2>&1
echo "rc=$?"
