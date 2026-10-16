---
name: delphi-binary-audit
description: |
  Delphi x64 应用程序逆向工程、破解完整性审计、多层许可证检测与后台看门狗绕过。
  适用场景：Delphi 64-bit 逆向、UPX 魔改头脱壳、RTTI / DFM 事件还原、BASS 音频流注入审计、
  多级后台 Watchdog Timer (TTimer) 逆向、守护进程 (Guard / Supervisor) 派生阻断、二进制无网络化 (Airgap Patching)。
  触发关键词：Delphi 逆向, delphi reverse, crack audit, 破解审计, 音频水印, periodic beep, timer watchdog,
  tmrDemo, StartGuard, radiocaster, radioboss, bass audio reverse.
---

# Delphi x64 逆向分析与 Crack 完整性审计 (Delphi Binary Audit)

## ACTION REQUIRED

1. `NOW`: 确认目标是否为 Delphi (Win32/Win64) 编译的二进制文件（特征：`DVCLAL`, RTTI 字符串, `System.Classes`, VMT 表）。
2. `NOW`: 检查文件是否加壳（如 UPX 被擦除 section 名称和 Header Magic 的魔改壳）。
3. `NEXT`: 提取 DFM 资源与 RTTI 字段表，还原 UI Form 组件、Timer 列表与 Published Event Handlers。
4. `ACT`: 按照多层防御链（UI flag -> Background Timer -> Periodic Evaluator -> Audio DSP -> Guard Process -> Outbound Telemetry）系统性分析并实施内存/二进制 Patch。

---

## 核心分析方法论

Delphi 编译的二进制程序在商业软件中经常采用**多层防御与延迟惩罚 (Delayed Penalty / Honey-Crack)** 机制：

```text
┌────────────────────────────────────────────────────────────┐
│                  Delphi Multi-Tier Defense                 │
├────────────────────────────────────────────────────────────┤
│ Tier 1: Startup UI Flag (TRegistration Object Constructor) │
│         └──> 破解者常误以为改 1 字节即完成                │
│ Tier 2: Background Watchdog Timer (TTimer / Form Event)    │
│         └──> 周期性触发 (如每 10 秒 / 每分钟)             │
│ Tier 3: Deep Algorithmic Evaluator (Key Re-validation)     │
│         └──> 异步二次验签，未通过则激活限制               │
│ Tier 4: Audio Stream / DSP Interruption                    │
│         └──> BASS_StreamCreate / DSP 回调注入高频音/静音   │
│ Tier 5: Background Supervisor / Guard Process              │
│         └──> CreateProcessW 隐式派生 watchdog 进程         │
│ Tier 6: Outbound Telemetry & Update Checkers               │
│         └──> WinHttp / Sockets 周期上报激活状态            │
└────────────────────────────────────────────────────────────┘
```

---

## 逆向步骤与工作流

### 1. 魔改壳脱壳 (Custom UPX / Obfuscated Headers)
当 UPX 头部特征（如 `UPX!`、Section Name）被清零导致 `upx -d` 报错时：
* 动态附加或在 OEP 断点处 Dump 内存镜像。
* 内存修正 PE Header 的 `SizeOfImage`、`AddressOfEntryPoint` 与 `SectionHeaders`。

### 2. Delphi RTTI & DFM 事件还原
* **DFM 资源定位**: 搜索 `TPF0` 标志或窗体对象定义字符串（如 `object Form4: TForm4`）。
* **组件与事件映射**:
  * 提取 `TTimer` 组件的 `Interval` 与 `OnTimer` 属性名。
  * 在 Published Methods 表查找函数名对应的真实 VA 指针：
    ```python
    # WORD size; QWORD methodVA; PascalString methodName
    ```

### 3. 多级防御链定位
* **启动标志 (Startup State)**: 定位 `TRegistration` 构造函数，修改全局/实例注册状态。
* **周期性看门狗 (tmrDemo / Watchdog)**: 定位 OnTimer 处理函数，将其首指令打为 `RET` (`0xC3`)。
* **深层算法验证核心**: 定位包含多轮异或/哈希验证的子函数，打为 `RET`。
* **音频注入 / 水印中和**: 定位 `BASS_StreamCreate` / `BASS_ChannelSetDSP` 注册的发生器，打入 `XOR EAX, EAX; RET` (`31 C0 C3`)。
* **守护进程阻断**: 定位窗体创建时的 `CreateProcessW` 调用（如 `StartGuard`），将派生函数首指令打为 `RET`。
* **二进制级纯净离线 (Airgap Patching)**: 直接将二进制中的更新/上报 URL（如 `https://.../checkupdate.php`）替换为 `http://127.0.0.1/null`，无需依赖外部 hosts 或防火墙配置。

---

## 常用脚本模板

### 自动化多层 Patch 脚本 (Python Capstone / Struct)

```python
import hashlib

def patch_delphi_binary(input_exe, output_exe, patches):
    with open(input_exe, "rb") as f:
        raw = bytearray(f.read())
    
    for p in patches:
        offset = p["offset"]
        expected = p.get("expected")
        new_bytes = p["bytes"]
        if expected:
            assert raw[offset : offset + len(expected)] == expected, f"Mismatch at {hex(offset)}"
        raw[offset : offset + len(new_bytes)] = new_bytes
        print(f"[PATCH] {p['desc']} @ {hex(offset)}")
        
    with open(output_exe, "wb") as f:
        f.write(raw)
    print(f"Output SHA256: {hashlib.sha256(raw).hexdigest()}")
```
