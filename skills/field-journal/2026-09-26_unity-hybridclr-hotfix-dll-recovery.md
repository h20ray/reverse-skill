# 2026-09-26 Unity HybridCLR 热更 DLL 定位与 AES 解密恢复

## 场景分类
APK逆向 / Unity 资源分析 / HybridCLR 热更程序集恢复 / 自实现加密(密钥派生)还原 / .NET 程序集脱壳

## 目标概述
移动端 Unity 游戏(IL2CPP + HybridCLR 热更架构)的**真实游戏逻辑**长期被记为"未取得"——
热更 DLL 不在 `libil2cpp.so` 里。本次证明:**它一直在随包下发的 AssetBundle 里**,并把它
从加密状态恢复成 142 万行可读 C#。同时把上一阶段遗留的"客户端自带 TLS 栈"定位到具体组件,
并澄清了"Mumu Houdini 地址空间分裂"的真实含义。

> 本条是 `2026-09-25_unity-localization-grid-and-bundle-path-grouping.md`(同目标静态阶段)的
> **续作**:上一条把"热更 DLL 未取得 / 请求响应体未取得"列为诚实边界,本条目打破了其中
> **Blocker 1**,把 Blocker 2 从"未知"缩小到"已命名组件"。

## Scope 摘要(脱敏)
- auth_basis: own_device(自有模拟器实例、自装游戏)
- network_profile: lab_only(本阶段全程静态,未触网、未 hook 进程)
- asset_types: [apk-splits, unity-assetbundles, hybridclr-hotfix-assembly, il2cpp-metadata-v31, astc-atlas-pages]

## 角色
- lead_role: lead
- specialists: [cae, cre]

## 完整执行链路

1. **先确定"哪个实例"**,而非直接开工:
   `MuMuManager.exe info -v all` 列出 5 个实例;`MuMuManager.exe adb -v 3 -c root` 取 root。
   实例 3 的 adb 端口是 **16480**,而我最初连的是 **7555**(另一个实例,没装这个游戏)。
   → **多实例模拟器上,先确认 adb 端口归属再动手**,否则会在"没有目标的设备"上分析半天。

2. **环境定性(这决定了后续所有动态手段是否可行)**:
   - `ro.product.cpu.abi = x86_64`,`abilist = x86_64, arm64-v8a, x86`
   - 但 `primaryCpuAbi = arm64-v8a`
   - `/system/lib64/libhoudini.so`(9.7 MB)、`/system/bin/houdini64`、`/system/lib64/houdini/arm64/`
   → 上一阶段所谓"**Houdini 地址空间分裂使 Frida 够不到 ARM 空间**"至此有了确切含义:
     它就是 **Intel Houdini,ARM 二进制翻译层**;ARM64 代码在 x86_64 guest 上**被翻译执行**,
     不存在一个可常规 attach 的原生 ARM 进程。**不是壳、不是反调试、不是 attach 模式问题。**

3. **样本重取 + 定影**:`pm path` 得到 3 个 split,全部 pull + `sha256sum`。
   版本 `versionName=1.9.3`、`versionCode=64`、Unity `2022.3.62f2`。

4. **在资源包里按体积找热更载荷**(关键动作,上一阶段漏在这里):
   `unzip -l split_UnityDataAssetPack.apk | sort -rn | head` → 最大文件是
   `assets/FullRes/dll_assets_all_<32hex>.bundle`(21.3 MB,`UnityFS`)。
   UnityPy 展开 → 9 个 `TextAsset`,其中一个直接叫 **`HotFix.dll`(18,953,744 字节)**。
   **热更程序集是随包下发的,不是运行时下载的**——不需要启动游戏就能拿到。

5. **逐个体检,而不是假设"全加密"**:
   9 个里 **8 个是明文托管 PE**(`MZ` + CLR v4.0.30319,熵 5.66–5.94),
   **只有 `HotFix.dll` 加密**(熵 7.9992,无 `MZ`,19 MB 全程均匀)。
   → **保护是不对称的:只加密主逻辑程序集,依赖程序集留明文。**

6. **不猜密钥,去读代码(本节是本次最大的教训)**:
   - 第一步我走错了:`#US` 堆顶部有四个 16 位 hex 串(`8cf90d6d...`、`0c49c3ed...`、
     `cd1a90321a5dbf4c`、`bc4652c76f95b847`),形态**极像** key/IV。按 275 种
     key/IV/mode 组合试解 —— **全负**。它们是无关常量。
   - 正确做法:**明文的兄弟程序集就是解密器**。`ilspycmd Framework.dll -o out` 反编译,
     直接读到 `AesTools`:

     ```csharp
     static AesTools() {
         AES_SecretKey = GenerateKey("hgjj1100#$#!!C>?<>{{::@g", 32);
         AES_IvKey     = GenerateKey("@#^*B>!", 16);
     }
     private static byte[] GenerateKey(string s, int n) {
         byte[] a = Encoding.UTF8.GetBytes(s);
         Array.Resize(ref a, n);      // 零填充,无 KDF/盐/迭代
         return a;
     }
     // RijndaelManaged: KeySize=256, BlockSize=128, Mode=CBC, Padding=PKCS7
     ```
   - 密钥 = UTF8(口令) + 零填充,**没有任何密钥派生**,直接可复现。
   - **顺带拿到调用点与入口**:`byte[] bytes = AesTools.AesDecrypt(val.bytes);` 紧邻
     `CreateInstance("HotFix.Main")`,并暴露源路径 `Assets/_Resources/Dll/HotFix.dll.bytes`。

7. **解密 + 独立校验**:
   Python 复现 → 首字节 `4d5a9000`(`MZ`)、PE 签名 `PE\0\0`。
   再**独立**解析解密后文件的 CLR 目录:RVA `0x2008`,找到 `BSJB` 签名(offset 8,198,596)。
   → 两条相互独立的观察支撑"这是真托管程序集",而非 AOT supplement blob。

8. **反编译取证**:`ilspycmd HotFix.decrypted.dll` → **41.9 MB / 1,426,319 行 C#**。
   `#Strings` 类型普查:战斗相关 **6,331**、玩家/背包 **4,930**、章节/关卡 **1,098**、
   状态机 **49**。关键命名空间:
   - `HotFix.Logic.BattleMain` → `BattleMainWaveManager`、`enum GameOverType { Win, Failure }`
   - `ServerGameEvent` → `MindNodeBase` / `MindNodeBattle` / `MindNodeBox` / `MindNodeCommonEx`
     + `enum EventFunction`(**肉鸽事件/选择是一棵服务端驱动的节点树**)
   - `Proto.*`(上百个)、`NetWork`、`Socket.Guild`、`Grpc.Health.V1`

## Evidence 链摘要(脱敏)

| E-id | severity | status | source_type | 可复用命令模式 | 关联 Finding |
|------|----------|--------|-------------|----------------|--------------|
| E-002 | info | validated | command | `unzip -l <assetpack>.apk \| sort -rn \| head` → UnityPy load `dll_*.bundle` | F-001 |
| E-003 | info | validated | command | 逐文件 `MZ`+CLR 体检 + 分块熵(10 块) | F-002 |
| E-005 | info | validated | command | `ilspycmd <plaintext-sibling>.dll` → 读 crypto 类 | F-002 |
| E-006 | info | validated | command | `python decrypt.py`;再独立验 CLR 目录 + `BSJB` | F-003 |
| E-007 | info | validated | command | `grep -n "^namespace " <decompiled>.cs`;类型普查 | F-003, F-005 |

> 完整证据(7 条 `E-001..E-007`)与 1 条 Path 落盘在用户项目
> `work/capybara-go/evidence/`、`work/capybara-go/report/01-*.md`,
> `python skills/case-review/scripts/review_case.py work/capybara-go --verify-hashes --strict`
> → **PASS(0 error / 0 warning)**。

## Finding / Path 摘要
- top_finding: F-001 热更逻辑一直随包下发(`dll_assets_all_*` → `HotFix.dll`),此前"未取得"的判断不成立
- path_type: callflow
- path_one_liner: `split_UnityDataAssetPack.apk` → 按体积锁定 `dll_*` bundle → UnityPy 取 `TextAsset`
  → 9 个里只有 `HotFix.dll` 加密 → 反编译明文兄弟 `Framework.dll` 读 `AesTools`
  → `GenerateKey` = UTF8+零填充(无 KDF) → AES-256-CBC/PKCS7 解密 → CLR+BSJB 独立校验 → 142 万行 C#

## 踩坑记录

| 问题 | 原因 | 解决方案 | 耗时 |
|------|------|---------|------|
| 在"没有目标的实例"上分析 | 多实例模拟器,我连的 7555 与装游戏的 16480 是**不同实例** | `MuMuManager info -v all` 核对 `adb_port`/`name`;`MuMuManager adb -v <n> -c root` | 0.4h |
| 把 4 个 hex 串当 AES key/IV,275 种组合全负 | 形态巧合即下结论,**没读代码** | 反编译明文兄弟程序集,一次读到 `AesTools` 全貌 | 0.8h |
| 一度判定热更为"流密码/XOR 流" | 均匀熵 7.999 被当作流密码特征 | **熵只能排除"可见块结构",不能识别算法**;AES-CBC 同样均匀。实际是 AES-256-CBC | 0.3h |
| 怀疑 50 MB 自定义 `il2cpp` 段是被搬走并加密的代码 | 只看体积和"非标准段名" | 与已知代码段比对熵:`il2cpp`=6.5705 vs `libunity.so .text`=6.5786 → **是正常编译产物**,撤回该判断 | 0.3h |
| 按"metadata 可能加密"预案准备 | 沿用**另一个** Unity 项目的记忆 | 实测本目标 `global-metadata.dat` 是**明文 v31**(magic `0xFAB11BAF`) | 0.1h |
| `ilspycmd` 反编译 19 MB 程序集超时 | 19 MB IL 需要约 3.5 GB 内存 | 转后台执行,不要前台等 | 0.2h |
| 本地 Python 脚本 `import re` 失败 | 我把脚本命名为 `types.py`,**遮蔽了标准库 `types`** | 改名为 `dotnet_types.py` | 0.2h |
| Git Bash 拉取路径被改写 / `adb` 建不了目录 | `/sdcard/...` 被 MSYS 转成 Windows 路径;开 `MSYS_NO_PATHCONV=1` 后**本地目标**又被透传 | 远端路径用 `MSYS_NO_PATHCONV=1`,**本地目标必须写 `C:\...` 形式** | 0.3h |

## 工具链发现

- **HybridCLR 类的热更程序集优先去资源包里找,不要先假设它运行时下载**。判据是体积:
  资源包中最大的 `*_assets_all_<32hex>.bundle` 很可能就是 `dll` 家族。`TextAsset` 的
  `m_Name` 直接给出真实程序集名(`HotFix.dll`),不需要猜。
- **UnityPy 导出 `TextAsset` 字节要用 `m_Script.encode('utf-8','surrogateescape')`**;
  用 latin-1 会损坏字节(上一条 journal 已记,本次再次验证)。
- **"只有主程序集加密、依赖程序集明文"是常见的不对称保护**。因此**先做逐文件体检**
  (`MZ` + CLR + 分块熵),不要看到第一个加密文件就断言"全加密",更不要直接上密码学。
  一旦确认存在明文兄弟程序集,**它就是解密器**:反编译它比任何爆破都便宜。
- **`ilspycmd` 是无 GUI 环境下最顺手的 .NET 反编译 CLI**(`~/.dotnet/tools/ilspycmd.exe`),
  `-o` 输出目录即可。大程序集耗内存,需后台跑。
- **熵的正确用法**:只能回答"像不像编译产物/有没有可见块结构",**不能**回答"用了什么算法"。
  本次先误判为流密码,实为 AES-CBC。
- **识别私有 TLS 的最高效信号是"`files/` 下的 SDK 命名目录"**,不是 `.so` 字符串扫描。
  本次 `libil2cpp.so` / `libunity.so` 扫 BoringSSL 标记**一无所获**(弱证据),
  而 `files/com.Tivadar.Best.HTTP.v3/` 一眼定性(Best HTTP/3,自带 TLS + 证书固定)。
- **非标准大段名(如 50 MB 的 `il2cpp` 段)不等于加壳**;与已知代码段比熵即可快速排除。

## 关键代码/命令

```bash
# 1) 多实例模拟器:先确认端口归属,再取 root
MuMuManager.exe info -v all
MuMuManager.exe adb -v 3 -c root          # -> restarting adbd as root
adb connect 127.0.0.1:16480
adb -s 127.0.0.1:16480 shell pm path <pkg>

# 2) 在资源包里按体积找 dll 家族
unzip -l split_UnityDataAssetPack.apk | sort -rn | head

# 3) 逐文件体检:是 PE 还是被加密
#    (MZ + CLR header) + (分块熵，10 块均匀≈加密)
python dllcheck.py ; python peinfo.py

# 4) 明文的兄弟程序集 = 解密器
~/.dotnet/tools/ilspycmd.exe Framework.dll.bin -o decompiled
grep -n -A 30 "class AesTools" decompiled/Framework.dll.decompiled.cs

# 5) 独立校验:CLR 目录 + BSJB
python -c "…parse PE CLR dir 14, assert nonzero; find b'BSJB'…"
```

```python
# GenerateKey 的等价复现(关键:零填充,无 KDF)
def generate_key(s, n):
    return s.encode("utf-8") + b"\0" * (n - len(s.encode("utf-8")))
key = generate_key("hgjj1100#$#!!C>?<>{{::@g", 32)   # AES-256
iv  = generate_key("@#^*B>!", 16)
# AES.new(key, AES.MODE_CBC, iv).decrypt(ct)  ->  b"MZ..."
```

## 对本包的改进建议

1. **建议在 `apk-reverse` 增加一节「Unity 热更程序集(HybridCLR/ILRuntime)定位」**:
   资源包按体积排序 → `dll` 家族 bundle → `TextAsset.m_Name` 即程序集名;并写明
   "热更载荷常随包下发,先找包内再假设下载"。这是本类目标第一优先动作。
2. **建议新增 pitfalls:「熵只能排除可见块结构,不能识别算法」**。本次被判为流密码,实为
   AES-CBC,差点走偏到错误的攻击方向。判据应写成"均匀熵 ⇒ 非简单定长块结构",
   而**不是** ⇒ 流密码。
3. **建议新增 pitfalls:「非标准大段名 ≠ 加壳;先与已知代码段比熵」**。本例 50 MB 的
   `il2cpp` 段一度被读作"被搬走并加密的代码",比对 `libunity.so .text` 熵后即排除。
4. **建议新增 pitfalls:「哈希/常量形态巧合不可作为密钥判据」**。四个 16-hex 串形态极像
   key/IV,275 种组合全负。**先去反编译明文的同族程序集读代码**,不要从形态猜。
5. **建议把"逐文件体检(PE/CLR/分块熵)"写进 `apk-reverse` 的产物验证层级**:
   与上一条 journal 建议的"HTTP 200 < JSON 可解析 < 组件可挂载 < 渲染正确"并列,
   增加"文件是否为有效托管 PE"这一层。**保护常是不对称的,别用第一个样本定性全体。**
6. **建议在环境识别清单中加入「模拟器实例/端口归属」与「guest ABI vs `primaryCpuAbi`」**:
   前者避免在无目标实例上白干,后者一眼判定"ARM 代码是否被翻译执行"
   (Houdini/ndk_translation),直接决定动态阶段是否可行、是否必须换真机。
7. **建议把「识别私有 TLS:看 `files/` 下 SDK 目录名,而非 `.so` 字符串扫描」写成可复用模式**。
   本次 `.so` 字符串扫描一无所获且具误导性,目录名一眼定性。
8. **建议 journal 模板增加「Retraction / 本人中途判断的撤回」小节**。本次有 4 条中途判断
   被实测推翻(流密码、il2cpp 段加密、hex 串为密钥、metadata 加密预案)。
   上一条 journal 已建议过 Finding 级 `retracts:`;此处建议**在 journal 模板层面**固定一节,
   因为"同一会话内自我推翻"比"跨会话推翻"更常见、也更容易被静默抹掉。

## 可复用的模式/脚本片段

**模式 A:Unity 热更程序集定位(以体积为线索)**
1. `pm path <pkg>` 取全部 split;
2. 资源包内 `unzip -l | sort -rn | head`,最大者常为 `dll_assets_all_<32hex>` bundle;
3. UnityPy load → `TextAsset` 的 `m_Name` 即程序集名;
4. 逐文件体检分流:`MZ`+CLR → 直接反编译;**无 MZ + 均匀熵 → 走模式 B**。

**模式 B:从"明文的同族程序集"还原自实现加密(不爆破)**
1. 确认存在明文兄弟程序集(同 bundle 内);
2. `ilspycmd` 反编译它,`grep -i "aes|decrypt|encrypt|key|iv|hotfix|loadassembly"`;
3. 读密钥派生函数 —— **自实现方案常是"UTF8 + 零填充"或简单拼接,没有 KDF**;
4. 复现并解密,用**独立**手段验收(`MZ`/`PE\0\0`/CLR 目录/`BSJB`),
   而不是只看"解出来不像乱码"。

**模式 C:宿主环境定性(决定动态阶段可行性)**
1. `getprop ro.product.cpu.abi` vs `primaryCpuAbi`;
2. 若 guest 是 x86_64 而 app 是 arm64-v8a → 存在翻译层,查 `libhoudini.so` /
   `ndk_translation` / `libnativebridge.so`;
3. 翻译执行下,**常规 Frida attach 到"ARM 空间"不成立** —— 结论是换真机,
   而不是继续调 attach 参数。

**模式 D:多实例模拟器的目标确认**
`MuMuManager.exe info -v all` → 按 `name` 找实例 → 读该实例 `adb_port` → 连对应端口。
不要凭默认端口假设目标。

## 边界(诚实标注)

- **Blocker 1 已破**:热更程序集已解密并反编译为原始 C#。
- **Blocker 2 未破,但已命名**:`Best HTTP/3` 自带 TLS 栈与证书固定,系统 CA/proxy 看不到明文。
  **本次未截获任何请求/响应体**——按契约,"连接日志"不算抓包,也**没有**拿它充数。
- **重要范围修正**:原计划假定第 5 项(网络/API)必须靠抓包。实际恢复出的程序集自带
  `*Request` / `*Response` / `*Dto` 类型**且带显式字段编号**(如 `ChapterBattlePassDtoFieldNumber`),
  **协议结构可纯静态还原**;抓包因此只对"取值"和"判定服务端权威"必要,而不再是对"枚举接口"必要。
- **未解决**:第 3 项的"确定性/服务端权威 vs 纯表现"问题**仍开放**。恢复出的代码同时存在
  客户端战斗阶段(`PlayRevivePhase1/2`)与服务端 DTO(`ChapterBattle*Request/Response`),
  两种模型都说得通;`CBuffBase` 的行为由服务端下发的 `CBuffData.m_parameters` 参数化、
  表现为客户端 prefab/特效,这是**可见的客户/服务端接缝**,但不足以定论。
  定论需要读 authority 判定处的 handler,尚未做。

## 进化动作
- [ ] 更新了路由矩阵
- [ ] 更新了 tool-index
- [ ] 更新了 bootstrap-manifest
- [ ] 更新了子 skill 文档
- [x] 新增了 pitfalls 记录(见"对本包的改进建议"2/3/4/7,待操作者确认后落入对应 skill)
- [x] 修正了本条自身的判断(4 条中途判断被实测推翻,已如实记录而非静默抹掉)
- [ ] 无需更新

> 说明:pitfalls 建议与契约改进以文本形式给出,**未直接改 `skills/` 下文档或
> `skills/ops/*.md` 契约**,等操作者确认后再落。

## 环境信息
- OS: Windows 11 Enterprise 10.0.26200(Shell: Git Bash)
- 工具版本: Python 3.14.3(pycryptodome 3.23.0)、UnityPy、ilspycmd 11.0.0.9375、
  adb 1.0.41 (37.0.1)、Node/前端工具本阶段未用
- 目标平台/版本: MuMu Player 12 实例(Android 15,guest `x86_64` + Intel Houdini 翻译层)、
  游戏 Unity 2022.3.62f2、IL2CPP metadata **v31**(明文)、HybridCLR 热更

## 脱敏要求

已执行:
- 未写入真实域名/IP;目标主机以"自有模拟器实例"描述,进程以 `{target_app}` 语义表述。
- 未含 token/cookie/密码/JWT/api key。
  ⚠️ **例外说明**:AES 口令与 IV 口令是**客户端内置的静态常量**(用于解密随包下发的
  程序集),不属用户凭证,且是复现本方法的关键。本条目以**方法 + 常量**形式保留,
  以便同类目标复现;如认为不宜外传,可将两处常量替换为 `{builtin_aes_passphrase}`。
- 游戏内部命名空间/类型名(`HotFix.Logic.BattleMain`、`ServerGameEvent` 等)为反编译标识,
  保留以维持可复现性;不含用户数据。
- 未粘贴完整二进制 dump,仅贴字段结构、关键代码与自检命令。

## 索引同步
- [x] `_index.md` 按场景分类新增一行(APK / Android 逆向)
- [x] 高频成功模式:新增「HybridCLR 热更程序集恢复与自实现加密还原」与「宿主环境定性」
- [x] 实体倒排:新增「Unity 手游 HybridCLR 热更程序集 / 私有 TLS 栈」
- [x] 累计统计与"最近更新"日期(真实项目 22→23,总条目 39→40,最近更新 2026-09-25→2026-09-26)

---
<!-- [进化统计] 本包累计完成项目: N | 本次新增模式: 4(体积线索定位热更程序集 / 明文兄弟还原自实现加密 / 宿主翻译层定性 / 多实例目标确认) | 本次修复工具链问题: 8 -->
<!-- [社区贡献] 完成后询问用户是否 PR 到主仓库。流程见 CONTRIBUTE-BACK.md -->
