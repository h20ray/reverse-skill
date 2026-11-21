using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
class NestedDump {
  static void Main(string[] a){
    var f = Path.GetFullPath(a[0]); var dir = Path.GetDirectoryName(f);
    var rp = new ReaderParameters{ReadingMode=ReadingMode.Immediate,InMemory=true};
    rp.AssemblyResolver = new LResolver(dir);
    var asm = AssemblyDefinition.ReadAssembly(f, rp);
    string want = a[1];
    foreach (var t in asm.MainModule.Types){
      Dump(t, want);
      foreach (var n in t.NestedTypes) Dump(n, want);
    }
  }
  static void Dump(TypeDefinition t, string want){
    if(!t.FullName.Contains(want)) return;
    Console.WriteLine("## TYPE "+t.FullName);
    foreach (var m in t.Methods.Where(m=>m.HasBody)){
      Console.WriteLine("### METHOD "+m.Name);
      foreach (var il in m.Body.Instructions)
        Console.WriteLine("  "+il.Offset.ToString("X4")+" "+il.OpCode+" "+(il.Operand==null?"":il.Operand.ToString()));
    }
    foreach (var fld in t.Fields) Console.WriteLine("FIELD "+fld.FieldType.FullName+" "+fld.Name);
  }
}
class LResolver : DefaultAssemblyResolver {
  string dir; public LResolver(string d){dir=d; AddSearchDirectory(d);}
  public override AssemblyDefinition Resolve(AssemblyNameReference name){
    try{return base.Resolve(name);}catch{ var p=Path.Combine(dir,name.Name+".dll"); if(File.Exists(p)) return AssemblyDefinition.ReadAssembly(p); throw; }
  }
}
