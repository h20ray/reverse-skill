using System;
using System.IO;
using System.Collections.Generic;
using Mono.Cecil;
using Mono.Cecil.Cil;

class Patch
{
    static int FACTOR;
    static void Main(string[] args)
    {
        string path = args[0];
        FACTOR = int.Parse(args.Length > 1 ? args[1] : "10000");
        var dir = Path.GetDirectoryName(path);
        var log = dir + "/patch_status.txt";
        string tmp = path + ".patched";
        try
        {
            var rp = new ReaderParameters {
                ReadingMode = ReadingMode.Immediate,
                InMemory = true,
                AssemblyResolver = new LocalResolver(dir)
            };
            var asm = AssemblyDefinition.ReadAssembly(path, rp);
            var t = Find(asm, "BongoCat.OSSpecific.GlobalKeyHook");
            var m = FindM(t, "Process");
            var body = m.Body;
            var proc = body.GetILProcessor();
            int patched = 0;
            var insn = body.Instructions[0];
            while (insn != null)
            {
                if (insn.OpCode == OpCodes.Add)
                {
                    var prev = insn.Previous;
                    if (prev != null && prev.OpCode == OpCodes.Callvirt &&
                        prev.Operand is MethodReference mr && mr.Name == "ProcessInput")
                    {
                        var nxt = insn.Next;
                        if (nxt != null && nxt.OpCode == OpCodes.Stfld &&
                            ((FieldReference)nxt.Operand).Name == "_keysDown")
                        {
                            proc.InsertBefore(insn, Instruction.Create(OpCodes.Ldc_I4, FACTOR));
                            proc.InsertBefore(insn, Instruction.Create(OpCodes.Mul));
                            patched++;
                        }
                    }
                }
                insn = insn.Next;
            }
            if (patched == 0) { File.WriteAllText(log, "NO_PATTERN"); return; }
            asm.Write(tmp);
            asm.Dispose();
            string bak = path + ".bak";
            if (File.Exists(bak)) File.Delete(bak);
            File.Copy(path, bak, true);
            File.Copy(tmp, path, true);
            File.Delete(tmp);
            File.WriteAllText(log, "OK patched=" + patched + " factor=" + FACTOR);
        }
        catch (Exception e) { File.WriteAllText(log, "ERR: " + e.Message); }
    }
    static TypeDefinition Find(AssemblyDefinition a, string name)
    { foreach (var t in a.MainModule.Types) if (t.FullName == name) return t;
      foreach (var t in a.MainModule.Types) foreach (var n in t.NestedTypes) if (n.FullName == name) return n;
      throw new Exception("type not found"); }
    static MethodDefinition FindM(TypeDefinition t, string name)
    { foreach (var mm in t.Methods) if (mm.Name == name) return mm;
      throw new Exception("method not found"); }
}

class LocalResolver : DefaultAssemblyResolver
{
    string dir;
    public LocalResolver(string dir) { this.dir = dir;
        var search = new string[] { dir, dir + "/../" };
        foreach (var s in search) if (Directory.Exists(s)) AddSearchDirectory(s);
    }
    public override AssemblyDefinition Resolve(AssemblyNameReference name)
    {
        try { return base.Resolve(name); }
        catch
        {
            var path = Path.Combine(dir, name.Name + ".dll");
            if (File.Exists(path)) return AssemblyDefinition.ReadAssembly(path);
            // UnityEngine.CoreModule etc often share UnityEngine.dll facade — try named file only
            throw;
        }
    }
}
