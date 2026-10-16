# MuMu Player ADB & MuMuManager 指南 / Guide

> 专用于 Windows 环境下 MuMu 模拟器（MuMu Player 12 / MuMu Player Pro）的 ADB 连接、Logcat 调试与 MuMuManager 自动化调用。

---

## 1. 核心二进制路径 (Fixed Paths)

在 MuMu 12 / Pro 安装环境下，不要使用系统全局或其他 SDK 的 `adb`，必须优先使用 MuMu 自身携带的工具链以避免 adb server 版本冲突或 offline 问题：

| 工具 | 绝对路径 | 用途 |
|------|---------|------|
| **MuMuManager CLI** | `C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe` | 推荐！直接透传 ADB 指令至指定多开实例，无需手动管理 port/connect |
| **MuMu ADB (v12.0)** | `C:\Program Files\Netease\MuMuPlayer\nx_device\12.0\shell\adb.exe` | MuMu 12.0 (Android 12 镜像) 专用 adb 可执行文件 |
| **MuMu ADB (v15.0)** | `C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\adb.exe` | MuMu 15.0 (Android 15 镜像) adb — **新版实例多为 Android 15，优先确认** |

### adb 版本与实例 Android 版本的对应关系（重要）

`MuMuManager info -v <index>` 返回的 `android_version` 决定该用哪个 adb：

- `android_version: 15.0` → 用 `nx_device\15.0\shell\adb.exe`（当前主流新装实例，如 "Game Lib" 实例）
- `android_version: 12.0` → 用 `nx_device\12.0\shell\adb.exe`
- 不确定或路径不存在时，回退 `nx_main\adb.exe`（任何实例都能连，仅功能略少）

不要假设目录里只有 12.0；12.0 路径在 Android 15 镜像上**不存在**。

### Git Bash / MSYS 路径转换坑

在 Git Bash 里直接调 adb.exe 时，`/storage/...` 会被 MSYS 转换成 `C:/Program Files/Git/storage/...` 导致 pull 失败；加 `MSYS_NO_PATHCONV=1` 后，本地目标路径又必须写成 Windows 形式（`C:\...`）：

```bash
export MSYS_NO_PATHCONV=1
"/c/Program Files/Netease/MuMuPlayer/nx_device/15.0/shell/adb.exe" \
  -s 127.0.0.1:16480 pull /storage/emulated/0/Android/data/<pkg>/files/... 'C:\local\dest'
```

---

## 2. 推荐调用方式：MuMuManager CLI

使用 `MuMuManager.exe adb -v <instance_index> -c "<cmd>"` 是最稳健的方式，它通过内部 IPC 直接与目标模拟器通信，不会受 TCP connect offline 影响。

### 查看模拟器实例状态
```powershell
# 查看所有/指定实例信息 (例如实例 0 或 实例 1)
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" info -v 0
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" info -v 1
```

### 执行 ADB 命令
```powershell
# 1. 运行 logcat (转储最近 100 行)
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "logcat -d -t 100"

# 2. 运行 logcat 过滤特定 Tag / Package / Error
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "logcat -d *:E"

# 3. 执行 Shell 命令 (例如 root shell)
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "shell getprop ro.build.version.release"
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "shell id"

# 4. 安装 APK
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "install -r C:\path\to\app.apk"

# 5. 推送/拉取文件
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "push C:\local\file /data/local/tmp/"
& "C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuManager.exe" adb -v 1 -c "pull /data/local/tmp/file C:\local\"
```

---

## 3. TCP 端口映射连接 (Direct TCP Connect)

如果需要配合 Frida 或第三方 IDE/工具（需要 standard adb socket）：

### 端口规则 (MuMu Player 12)
- **Instance 0**: `127.0.0.1:16384`
- **Instance 1**: `127.0.0.1:16416`
- **Instance N**: `16384 + (N * 32)`
- *(旧版 MuMu 6 / MuMu X 默认端口: `127.0.0.1:7555`)*

### 使用 MuMu ADB 连接
```powershell
$mumuAdb = "C:\Program Files\Netease\MuMuPlayer\nx_device\12.0\shell\adb.exe"

# 连接实例 1 (端口 16416)
& $mumuAdb kill-server
& $mumuAdb connect 127.0.0.1:16416
& $mumuAdb devices

# 执行 logcat
& $mumuAdb -s 127.0.0.1:16416 logcat -d -v time
```

---

## 4. 故障排查 (Troubleshooting)

1. **Device Offline**:
   - 优先改用 `MuMuManager.exe adb -v <index> -c "<cmd>"`。
   - 或杀掉后台其他版本的 adb.exe 进程（避免版本不匹配导致 server 踢掉连接）：
     ```powershell
     Stop-Process -Name "adb" -Force -ErrorAction SilentlyContinue
     ```
2. **Root 权限**:
   - MuMu 模拟器已默认开启 root，通过 `adb shell su` 或 MuMuManager 传入命令即具备 root 环境。
