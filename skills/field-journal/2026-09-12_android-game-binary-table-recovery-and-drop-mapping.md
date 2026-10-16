# 2026-09-12 Android Game Binary Table Recovery & Protocol Drop Mapping

## 场景分类
APK逆向 / 协议逆向 / 移动游戏数据恢复 / ADB Root 提取

## 目标概述
解决移动端游戏（Summoners War / Com2uS 协议栈）在抓包与自动化逆向过程中，从服务器返回的 Master ID（如 `25804`）缺少对应名称、导致 drop 报告回退为通用占位符（`"Light Monster #25804"`）的问题。通过 ADB Root 提取客户端本地二进制数据表（`text_eng.dat`），完整解析 248 个内部二进制表，重建 2,520 个官方怪兽与掉落道具映射，并修正协议 drop 解析与显示。

## Scope 摘要（脱敏）
- auth_basis: offline-sample / local-emulator-research
- network_profile: isolated-local
- asset_types: [apk, binary-table, json-protocol-logs]

## 角色
- lead_role: cre
- specialists: [mobile-reverse, protocol-reverse]

## 完整执行链路

1. **抓包与日志审查发现缺失映射**：
   - 审查 200 个游戏协议交互日志（`BattleHeroDungeonResult`, `changed_item_list`），发现 `item_master_type: 12` 携带 `item_master_id: 25804`。
   - 原 dictionary 仅收录 1,780 条目，缺少 743 个新单元与未觉醒形态，导致算法 fallback 为 `"Light Monster #25804"`。

2. **定位本地二进制客户端主数据**：
   - 通过 ADB 连接 Emulator (`127.0.0.1:16416`)，在 App 沙盒 `/data/data/com.com2us.../text_eng.dat` 发现 2.9 MB 的客户端只读主索引文件。

3. **二进制多表结构反向解析**：
   - `text_eng.dat` 头部由 248 个 Table 指针偏移数组构成。
   - Table #2 为官方怪兽表（2,520 records），采用 `[4-byte ID] + [1-byte length] + [UTF-8 string]` 结构。
   - Table #27 为服务端错误代码与提示表（758 records），对应 `ret_code`（如 8000 系）。

4. **数据同步与协议解析器重构**：
   - 将解析出的 2,520 个完整怪兽名称导出至 `monster_id_to_name.json`。
   - 确认 `25804` 为 `Light Rune Blacksmith`（觉醒名 `Madeleine` / `25814`）。
   - 在掉落物解析逻辑中将 `item_type: 12`（召唤书碎片）对接 `format_hoh_monster_name`，输出规范的 `"[Element] [Family] ([Awakened]) Summoning Pieces x[Qty]"`。

## Evidence 链摘要（脱敏）
| E-id | severity | status | source_type | 可复用命令模式 | 关联 Finding |
|------|----------|--------|-------------|----------------|--------------|
| E-001 | info | validated | command | `adb pull /data/data/com.com2us.../text_eng.dat` | F-001 |
| E-002 | info | validated | script | `python parse_table2.py text_eng.dat` | F-002 |
| E-003 | low | validated | command | `cargo test --workspace` | F-003 |

## Finding / Path 摘要
- top_finding: 游戏客户端本地二进制资源表包含完整 2,520 条怪兽与道具定义，可无损补齐协议逆向中的 ID 语义缺失。
- path_type: callflow
- path_one_liner: ADB pull text_eng.dat -> 二进制表提取 -> 2,520 ID 字典恢复 -> 掉落物协议格式化。

## 踩坑记录

| 问题 | 原因 | 解决方案 | 耗时 |
|------|------|---------|------|
| 掉落物显示 `"Light Monster #25804"` | 静态字典仅 1,780 项，缺少 743 个未觉醒/新 4-5★ 单元 | 从 `text_eng.dat` Table #2 提取全量 2,520 单元并按 `family_id` 关联未觉醒与觉醒名 | 15m |
| Homunculus 命名断言失败 | 官方字符串为 `"Homunculus(Attack)"`，原测试硬编码旧合成名 | 对齐官方 `text_eng.dat` 真实字符串，更新单测断言 | 5m |

## 工具链发现
- **ADB Root Pull**：直接从 Android 沙盒提取 `.dat` 资源文件，相比解包 APK 更及时（包含热更数据）。
- **Python Binary Slicing**：快速读取 Multi-Table 二进制头与 Length-prefixed 记录，比静态反编译 IDA 分析更快还原完整字典。
