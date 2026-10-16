# 2026-09-23 游戏贴图集（Texture Atlas）无损切分、邻元溢出消除与母版素材回溯取证

## 目标与场景
- 目标：Summoners War 异界之门（Dimension Hole）关卡缩略图贴图集 `gui_dimhole_thumb_list.png`（512x512 RGBA）与对应的独立素材。
- 工具链：Python 3.14 (Pillow, NumPy), Android ADB Shell / Root, Steam PC 客户端解包。
- 场景分类：游戏客户端逆向 / 图像取证 / 贴图集（Atlas）还原 / 自动化资产构建。

## 发现与证据链

1. **朴素网格裁切陷阱（The Naive Slicing Pitfall）**：
   - 贴图集规格为 $512 \times 512\text{ px}$，视觉呈现为 4 列 $\times$ 6 行（共 24 格，其中 23 格有效，右下角 1 格空白）。
   - 若按纯数学 UV 边界网格裁切（列宽 128px，行高 85.33px），会产生严重的**边缘溢出与附属物截断**：
     - 格子 01（Karzhan Golem）：右侧边缘附带狮鹫（Griffon）的绿色翅膀羽毛；
     - 格子 02（Griffon）：左侧翅膀尖被截断，右侧边缘附带暗狼（Inugami）的紫色毛发；
     - 格子 03（Inugami）：左侧被截断，右侧边缘附带战熊（Warbear）的爪子；
     - 格子 04（Warbear）：左爪截断，左下角附带下排怪物的绿叶；
     - 格子 06（Fairy）：右侧附带树人首领的树枝犄角。
   - **根本原因**：游戏美工在构建 UI 贴图集时，为节省贴图面积未保留透明 Gutter 间隙，邻近精灵的羽毛/犄角羽化边缘直接重叠在相邻精灵的标称矩形区域内。

2. **母版素材发现（Master Assets Discovery）**：
   - 在游戏本体资源包（Steam `Base_Contents.bundle` 与 Android `/sdcard/Android/data/com.com2us.../files/Downloads/Resource/di/`）中检索，发现了官方原始的独立图标：`dimhole_boss_icon_00_01.png` 至 `dimhole_boss_icon_00_24.png`（其中 `11` 缺失，刚好为 23 个文件）。
   - 格式为 Com2uS 自研 Joker 格式（`Joker\0` + uint32 len1 RGB JPEG + uint32 len2 Alpha L），解包后为 $256 \times 128$ 贴图画布，有效内容位于 $144 \times 104$ 区域。
   - **关键特征**：每个母版图标在边缘均完整羽化至 $\alpha = 0$，**100% 完整无截断，且完全不存在任何相邻素材的溢出污染**。

3. **映射次序断层与重排序（Index Mapping Discrepancy）**：
   - 母版文件编号基于内部地下城 ID（如 `01` 为森林守护者 Ellunia，`04` 为石巨人 Karzhan），并非贴图集的视觉顺序。
   - 通过生成 Contact Sheet 矩阵图比对，确认贴图集视觉自左向右、自上而下的 $01 \to 23$ 与母版文件的精确对应关系：
     - 01: `dimhole_boss_icon_00_04.png` (Karzhan Golem)
     - 02: `dimhole_boss_icon_00_10.png` (Griffon 2A)
     - 03: `dimhole_boss_icon_00_06.png` (Inugami 2A)
     - 04: `dimhole_boss_icon_00_05.png` (Warbear 2A)
     - 05: `dimhole_boss_icon_00_01.png` (Ellunia Protector Boss)
     - 06: `dimhole_boss_icon_00_02.png` (Fairy 2A)
     - 07: `dimhole_boss_icon_00_03.png` (Pixie 2A)
     - 08: `dimhole_boss_icon_00_07.png` (Lumel Minotaur Boss)
     - 09: `dimhole_boss_icon_00_09.png` (Martial Cat 2A)
     - 10: `dimhole_boss_icon_00_08.png` (Werewolf 2A)
     - 11: `dimhole_boss_icon_00_12.png` (Khalderun Death Boss)
     - 12: `dimhole_boss_icon_00_14.png` (Grim Reaper 2A)
     - 13: `dimhole_boss_icon_00_13.png` (Howl 2A)
     - 14: `dimhole_boss_icon_00_15.png` (High Elemental 2A)
     - 15: `dimhole_boss_icon_00_16.png` (Frankenstein 2A)
     - 16: `dimhole_boss_icon_00_17.png` (Vagabond 2A)
     - 17: `dimhole_boss_icon_00_18.png` (Mystic Witch 2A)
     - 18: `dimhole_boss_icon_00_19.png` (Sacreon Centurion Boss)
     - 19: `dimhole_boss_icon_00_20.png` (Living Armor 2A)
     - 20: `dimhole_boss_icon_00_21.png` (Harpu 2A)
     - 21: `dimhole_boss_icon_00_22.png` (Inferas Flame Boss)
     - 22: `dimhole_boss_icon_00_23.png` (Inferno 2A)
     - 23: `dimhole_boss_icon_00_24.png` (Hellhound 2A)

4. **1:1 视觉差分验证**：
   - 将这 23 个母版素材重新按贴图集网格排布并缩放拼回 $512 \times 512$ 图像，与原始 `gui_dimhole_thumb_list.png` 并排像素比对，证实整体构图与相对空间位置 100% 一致，但彻底消除了网格边缘溢出。

## 产出物与标准工具

1. **产出目录**：
   - 紧致抠图母版：`work/dimhole_assets_01_to_23/tight_cutouts/`（23 个 PNG，保持母版原始分辨率与完整肢体）
   - 标准画布裁切：`work/dimhole_assets_01_to_23/standard_144x104/`
   - 网格对齐瓷砖：`work/dimhole_assets_01_to_23/atlas_tiles_128x85/`
2. **可视化验证图**：
   - `work/reference_vs_reconstructed.png`
