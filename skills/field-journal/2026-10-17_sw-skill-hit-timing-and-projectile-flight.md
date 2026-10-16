# 2026-10-17 Summoners War 技能命中时间与投射物飞行:时间模型、曲线飞行与未解的多段命中

## 场景分类
游戏客户端资源逆向 / 主数据表(master data)语义还原 / Web 查看器时间轴

## 目标概述
让查看器里技能的投射物飞行与命中时间对上游戏:确定投射物从出手到命中的时间构成,补上曲线飞行,并核查"无 `atk info` 的技能命中次数从哪里来"这一遗留问题。

## Scope 摘要（脱敏）
- auth_basis: 用户本人的游戏客户端与本地模拟器(离线分析,无网络交互、无账号操作)
- network_profile: offline
- asset_types: [master-data-table, effect-peft, web-viewer]
- 说明:本条只记录数据侧结论与查看器实现;客户端代码层面的获取与分析方法不在此记录。

## 角色
- lead_role: lead
- specialists: [cre]

## 完整执行链路

1. **时间模型(数据侧可复现部分)**:命中时间 = 攻击动画开始 + 技能延迟 + `begin_delay`(仅飞行模式 2/4) + `projectile info.time`。
   - 飞行时间是固定毫秒数,与距离无关(距离只拉伸路径);9.3.6 中 `time` 恒为 800,`run_type` 从未出现 ⇒ 线性。
   - `effect play` 第 2 个值(0 起计为 f1)是飞行模式:0 计时、1 直线、2 曲线、3/5 光束、4 等待后直线。
   - **没有 `projectile info` 的投射物出手即命中**(0 ms),而不是旧假设的 500 ms。
   - 实际影响:Storm and Gale 命中 800 → 1100 ms,Trickster 800 → 1500 ms,其他行不变。
2. **`projectile info` 字段**:`{type, time, begin_delay, disappear_time, curve_value, run_type, disappear_len}`,每行恰好 1 条。318 / 5,262 技能行、193 / 7,065 皮肤技能行带有该列。`begin_delay` 只出现两种值(300 / 700),`disappear_len` 只出现在一个技能上。
3. **曲线飞行**:模式 2 是二次贝塞尔,控制点 = 起终点中点沿 `type` 指定方向偏移 `curve_value`(3 = 向上,4 = 水平侧向,2 = 两者混合)。
   - **先按数据分组再动手**:"模式 2 共 120 行"里有 69 行 `type 1` 且无 `curve_value` ⇒ 控制点就是中点,轨迹仍是直线。真正弯曲的只有 51 行:`type 3 / 8` ×13、`type 2 / 3` ×38。
   - 查看器实现:导出 `curve: {type, value}`,`travelAt()` 按贝塞尔求位置;`value` 按游戏单位换算。
   - 验收:Forest Keeper ATK_1(type 3,value 8)在 k = 0 / 0.5 / 1 处高度为 1 / 5 / ≈1 游戏单位,中点峰值 = 偏移量一半,符合二次贝塞尔。
   - `type 2` 的混合权重未确认,按 45° 近似并在代码中注明。
4. **遗留问题核查:无 `atk info` 的多段命中**(Light Fairy "Light Hurricane" 游戏内 3 段、间隔 200 ms):
   - 曾假设来自客户端里按技能 ID 特判的那部分逻辑。核对后 **Light Fairy(1154)不在特判技能列表中**,该假设不成立。
   - 结论:这类技能的命中次数来源仍未找到;查看器继续用 `delay param`(数据)或描述文本 "N times" + 200 ms(启发式,带 `repeat_source` 标记)。

## Evidence 链摘要（脱敏）
| E-id | severity | status | source_type | 可复用命令模式 | 关联 Finding |
|------|----------|--------|-------------|----------------|--------------|
| E-101 | info | validated | command | 按表头定位技能表,统计 `(effect play f1, type, curve_value, begin_delay)` 组合 | F-101 真正弯曲的只有 51 行 |
| E-102 | info | validated | command | 查看器 `swsaViewer.seek(t)` 逐点读取投射物位置 | F-102 贝塞尔峰值 = 偏移量一半 |
| E-103 | info | validated | file | 特判技能 ID 列表 vs Light Fairy 技能 ID | F-103 多段命中来源仍未知 |

## Finding / Path 摘要
- top_finding: 投射物命中 = 动画开始 + 延迟 + begin_delay + 固定飞行时间;无 `projectile info` 时出手即命中
- path_type: solve(时间模型) / open(多段命中来源)
- path_one_liner: 数据分组统计 → 时间模型 → 查看器贝塞尔飞行 → seek 数值验收

## 踩坑记录

| 问题 | 原因 | 解决方案 | 耗时 |
|------|------|---------|------|
| 以为"模式 2 = 120 行弯曲" | 模式与曲线参数是两回事,69 行无 `curve_value` | 先按 `(模式, type, curve_value)` 分组计数再定范围 | 短 |
| 无 `projectile info` 的投射物按 500 ms 飞行 | 旧代码的默认值是猜的 | 缺省 = 0 ms,出手即命中 | 短 |
| 笔记与代码对 `effect play` 字段编号不一致 | 一处 1 起计(f2),一处 0 起计(f1) | 文档统一写明"0 起计",并附示例值 | 短 |
| `localvalue.decompressed` 按 UTF-8 打开报错 | 文件里混有非 UTF-8 字节 | 按字节读,`decode('utf-8', 'replace')` 后按 `\t` 切列 | 短 |
| 把"可能来自特判逻辑"当成结论 | 没先核对目标技能是否在列表中 | 先查列表成员,再下结论;不成立则保留为 open | 短 |
| `export` 后其他族仍是旧数据 | 增量导出按 `.dat` 哈希跳过,特效逻辑变化不会触发 | 只重导受影响的族(按技能 → `base skill` → `group id` 反查)并加 `--force` | 短 |

## 工具链发现
- 查看器调试句柄 `window.swsaViewer.seek(t)`:暂停到动画时间 t,配合读取 `effects[i].mesh.position` 可做逐帧数值验收,比截图更可靠(内置浏览器面板隐藏时 rAF 暂停,截图计时不可信)。

## 关键代码/命令
```
# 二次贝塞尔:控制点 = 中点 + 偏移
P(k) = (1-k)^2 * A + 2k(1-k) * C + k^2 * B,  C = (A+B)/2 + dir(type) * curve_value
# 峰值在 k = 0.5,高度 = 偏移量 / 2
```

## 对本包的改进建议
- 表驱动类任务:"字段 X 取某值的行数"不等于"受影响的行数"——先把相关参数列一起分组计数,再估算改动范围。
- 遗留问题的假设在写进结论前,先做成员核对(目标样本是否落在假设覆盖的集合里)。

## 可复用的模式/脚本片段
- **按影响面重导**:由改动涉及的技能行反查单位 `base skill` → `group id`,只对这些族 `--force` 重导,避免全量同步。
- **数值验收几何**:对轨迹类改动,在 k = 0 / 0.5 / 1 读位置,与解析式(端点、峰值)对比。

## 进化动作
- [ ] 更新了路由矩阵
- [ ] 更新了 tool-index
- [ ] 更新了 bootstrap-manifest
- [ ] 更新了子 skill 文档
- [x] 新增了 pitfalls 记录
- [ ] 无需更新

## 环境信息
- OS: Windows 11
- 工具版本: Python 3.15, Three.js 0.162.0
- 目标平台/版本: Summoners War 客户端 9.3.6(Android)

## 脱敏要求
本文件不含账号、令牌、密钥、设备序列号或真实主机信息,也不记录客户端代码保护相关的获取方法。

---
<!-- [进化统计] 本包累计完成项目: 26 | 本次新增模式: 2 | 本次修复工具链问题: 0 -->
