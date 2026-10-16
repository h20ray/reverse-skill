# 2026-09-04 RadioCaster Delphi x64 Crack 审计与多层防护穿透

## 场景分类
二进制逆向分析 / Delphi x64 / Crack 完整性审计 / 音频流保护绕过

## 目标概述
审计 RadioCaster 3.7.4.0 (x64) 的第三方 Crack (`Crack UZ1`) 为何在生产广播环境下每隔数分钟仍会爆出刺耳的 Demo 蜂鸣音（Beep/Tone），并彻底定位其全部后台看门狗、周期性验签、音频注入点、守护进程派生与网络外联，产出 100% 离线、纯净、无守护进程的完整 Patch。

## Scope 摘要
- auth_basis: offline-sample / local binary audit
- network_profile: airgap / isolated
- asset_types: [PE64, Delphi VCL, BASS Audio Engine]

## 角色
- lead_role: lead
- specialists: [cre, cpe]

## 完整执行链路

1. **样本比对与脱壳**:
   - 从安装包解压出干净原版 `caster.exe` (SHA256: `6DEF086D...`, 21.2 MB)。
   - 对比 `Crack UZ1\caster.exe`：发现其为 UPX 魔改脱壳壳，全文件仅在 `0x140D02992` 修改了 1 个字节 (`01` -> `00`)。
2. **Honey-Crack (假死破解) 根因定位**:
   - 深入 Delphi Form4 (主界面) 的 DFM 与 RTTI 表，发现后台存在定时器 `tmrDemo` (`Interval = 10000ms`, `OnTimer = tmrDemoTimer`)。
   - `tmrDemoTimer` (VA `0x140DBCA60`) 周期性调用深度验签核心 `0x140DB8E90`，在未输入合法 License 时重新激活 Trial 惩罚。
3. **音频注入点定位**:
   - 跟踪 `BASS_StreamCreate` 与 DSP 管道，锁定音频注入核心 `0x140C94430`。
4. **后台守护进程阻断**:
   - 分析 `TForm4.FormCreate`，定位到 `StartGuard` (VA `0x140DB6A30`)，其在后台通过 `CreateProcessW` 隐式启动 `radiocaster_guard.exe`。
5. **网络外联与更新上报中和**:
   - 提取所有 WinHttp/Sockets 调用的 `djsoft.net` 端点 (`checkupdate3.php`, `bugreport`, `cloudsrv`)，在二进制内部直接替换为 `127.0.0.1/null`，免去修改 hosts 和防火墙的繁琐步骤。
6. **自动化多层 Patch 验证**:
   - 编写 Python 自动化脚本应用 7 项 Patch，并在沙箱中验证进程存活、0% guard 派生、音频流完全纯净。

## Finding / Path 摘要
- top_finding: Delphi 商业软件的 Delayed Audio Penalty (延迟音频惩罚) 与 Watchdog Timer 绕过了单纯的 Startup Flag 破解。
- path_type: solve
- path_one_liner: Startup Flag Patch + tmrDemoTimer RET + tmrUpdateChecker RET + StartGuard RET + Airgap URL Nullification.

## 关键代码/命令

```python
# 核心 Patch 点
patches = [
    {"name": "Startup Full License", "offset": 0xd01d92, "bytes": b"\x00"},
    {"name": "Kill tmrDemoTimer", "offset": 0xdbbe60, "bytes": b"\xc3"},
    {"name": "Kill Demo Eval Core", "offset": 0xdb8290, "bytes": b"\xc3"},
    {"name": "Kill Update Timer", "offset": 0xdbc160, "bytes": b"\xc3"},
    {"name": "Kill Audio Tone Gen", "offset": 0xc93830, "bytes": b"\x31\xc0\xc3"},
    {"name": "Kill StartGuard", "offset": 0xdb5e30, "bytes": b"\xc3"},
]
```
