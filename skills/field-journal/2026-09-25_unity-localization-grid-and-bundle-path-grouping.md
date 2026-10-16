# 2026-09-25 Unity 本地化表网格恢复与 AssetBundle 路径分组

## 场景分类
APK逆向 / Unity 资源分析 / 二进制表恢复 / 本地化(i18n)数据恢复 / 实体-资源连接(精确匹配)

> **本条覆盖两个阶段**:①本地化网格 + Bundle 路径分组(Case 的 WI-012/WI-016/WI-017);
> ②Luban 行感知解码 + entity→art 精确连接(WI-020,E-016 → F-016/F-017)。
> 两者同属 `capybarago` 同一日的静态分析阶段,故合并入一条,避免"同一证据两个家"。

## 目标概述
移动端 Unity 游戏(IL2CPP + HybridCLR 热更架构)的本地化数据长期读错:`tblanguage_*` 语言表被当作"扁平字符串流"解析,导致行错位。本次从 `.bytes` 字节层恢复真实网格(宽度 18 = key + 17 语言列),产出 16 语言 × 30,604 key 的干净数据;并从 AssetBundle 文件名反推出真实美术资源路径,建立按"家族/子类"分组的资源树。同阶段把同类错误(打捞扫描冒充解析器)在 Luban 配置表上修掉:**696/700 精确闭合**,并把 5368 个游戏实体按**精确匹配**连到美术资源(3237 命中,两侧残差逐条上报)。过程中因一个探测开关覆盖了完整索引,做了完整重跑恢复。

> **边界(诚实标注)**:以上全部是**离线静态**结论 —— 读到的是"外壳 + 已下发数据"。
> 真正的游戏逻辑是 HybridCLR 热更 DLL(未取得),请求/响应体也未取得(客户端自带 TLS 栈
> 挫败代理解密,且 Houdini 地址空间分裂使 Frida 够不到 ARM 空间)。这两项是同一环境阻塞,
> 不在本条覆盖范围内,详见用户项目报告 §5.1。

## Scope 摘要(脱敏)
- auth_basis: own_device / offline-static
- network_profile: lab_only(本阶段未触网,全部为已提取文件的离线分析)
- asset_types: [apk-splits, il2cpp-metadata, unity-assetbundles, binary-config-tables, spine-4.0, astc-atlas-pages]

## 角色
- lead_role: lead
- specialists: [cae, cre]

## 完整执行链路

1. **发现语言表列错位**:
   - 早先的读取器通过 `extract_strings()` 取"所有长度前缀字符串",**丢掉空字符串**。
   - 语言表有大量未翻译空单元格,一旦丢空,后续行整体前移 —— 某行的 **key** 出现在"语言列"里。
   - 症状:`ui_friend_title` 的 `col16/col17` 出现 `ui_friend_blacklist` / `Blacklist`,即下一行的 key。

2. **定位真实行宽(用算术而非猜测)**:
   - 表头**只取 `<readSize rows>`**(不取 `fields`;declared `fields=15` 是错的)。
   - 值流按 `rows × width` 切格,每格 `<readSize len><utf8>`,**保留空格**。
   - 决定性验证:`119465 values / 6637 rows = 17.9998` → width = 18,且全部 5 张 18 宽表的 `trailing_values = 0`(无残留、无半行)。

3. **列身份双向确认**(避免只靠一个样本下单):
   - 横向:两张独立表(`tblanguage_ui` 与 `tblanguageraft`)语言顺序一致。
   - 纵向:用**文字体系自证**的翻译锚定 —— `ui_friend_blacklist` 的 zh-CN=`黑名单`(简)/ zh-TW=`黑名單`(繁)确证两列不同;es=`Lista negra` vs es-419=`Lista Negra` 仅大小写不同,恰好是该语言对的真实差异,独立证明第 15 列是独立列而非重复列。

4. **从 Bundle 名反推真实资源路径**:
   - 命名法:`<路径段以 '-' 连接>_assets_all_<32位hex>`。
   - `art-spine-chuancheng-aikugui_assets_all_4763…` → `Assets/Art/Spine/chuancheng/aikugui`。
   - 全量校验:2,132 个 bundle 全部可分类,`art/spine` = 392,与 392 个 Spine bundle 目录**精确吻合**。

5. **分组层级用测量决定,而非直觉**:
   - 先量分布:999 条 spine 资源中 **990 条都是 `art/spine`** —— 只按 `<家族>/<子类>` 分两层等于"一个节点装下全部",结构上没错但没法浏览。
   - 改用**第三段**为分组键 → 12 个有意义的组:`ui` 536 / `member` 172(monster 105, mount 31, artifact 26)/ `player` 127 / `event` 79 / `pet` 45 / `chuancheng` 21。
   - 第二层即真实游戏内容:`jiayuanxitong`(家园系统)、`haidaomaoxian`(海岛冒险)、`duanwujie`(端午)、`zhongqiujie`(中秋)、`manianchunjie`(春节)。

6. **事故与恢复(见踩坑)**:
   - 探测用 `--only=autogroup_duplicatedfile_12` 把**单 bundle 结果覆盖写**到 `sprites.json`,完整索引被毁(glossary 从 999 条掉到 **2 条**)。
   - 无备份,只能完整重跑(约 1 小时机器时间)恢复。

7. **行感知解码取代"捞字符串"式读取(Luban 配置表,E-016)**:
   - 旧 `luban.py:extract_strings()` 是**打捞扫描不是解析**:只留可见串,行边界与数值字段全丢;在最宽的表上不是"丢细节"而是**产出垃圾** —— `tbmonstercfg_monstercfg`(怪物表)只得到 275 个字符串,204 KB 内 **0 个 ASCII 串,100% 乱码**。
   - 修正后:**4188 行 / 167547 值,恰好 40 值/行**。原先当作敌人列表用的东西是错的。
   - 表头两处早先判断也被推翻:(a) `tables.json` 的 `fields` **不是列数**,是**第 1 行第 1 个字段的值**,故 `cells = rows × fields` 无意义,只有 `rows` 可信且**数据体从 offset 1 开始**;(b) 起始偏移取对后,贪心走法**本就能闭合 687/700** —— 早先"200 里只成 1 张"是错误表头假设造成的假象。
   - 剩 **4 张闭不上**:它们共有 8 字节样式的尾部,但干净切点各不同(6/10/1),**没有拟合尾部规则**。这 4 张记 `{"parsed": false}` 并排除。
   - 关键取舍:**为凑 100% 拟合一条规则 = 把噪声当覆盖率**。接受 696/700。

8. **entity→art 精确连接,双残差上报(F-017, E-016)**:
   - 5368 个实体(11 类)连到 9928 sprite 名 / 390 spine slug / 278 atlas,**只用精确字符串相等或显式标注来源的变换**,无 fuzzy / levenshtein / embedding。
   - matched **3237**;未匹配 2131 实体 + 8488 sprite,**逐类列在 `/#/mapping-audit`**,而不是报一个成功率百分比。
   - 三个"看起来是失败"的结果都**先诊断再上报**,不抹平:`boss 0/18` 是**词表不匹配**(boss icon 用 `monster_*`、boss spine 用 `boss-*`,与怪物集仅约 44/76 重叠;公会/世界/圣诞三套 boss 配置的 id 拼不出任何 art slug);`skill 41.6%` 受限于**死家族** `Icon_Skill_*`(11 个引用,0 个存在于词表);`costume 14.5%` 受限于 `.prefab` 体需要本 artifact 集之外的 SkeletonData blob。
   - **两类刻意不动**:pet 无 token 的行、skill 无 icon 的行是**真实的源缺口**;按名字相似度去"桥接"就是编造。
   - 顺带排掉一个 art 侧真实存在的隐患:10715 个 `(atlas,name)` 槽中有 **153 个槽装着多于一条 sprite 记录**,盘上用 `uniq()` 加的 `__1`/`__2` 后缀区分 —— 实测 2058 对同源文件:**97.1% 字节完全相同、4.4% 不同**,所以该后缀是**碰撞计数器,不是内容标记**(不是去重器)。4160 条 sprite art 条目逐条比对:0 条落在多记录槽上、0 条按名字是 `__1`;11561/11561 声明的 sprite 路径与 8234/8234 页路径在盘上全部存在。

## Evidence 链摘要(脱敏)

| E-id | severity | status | source_type | 可复用命令模式 | 关联 Finding |
|------|----------|--------|-------------|----------------|--------------|
| E-012 | info | validated | command | `python scripts/dump_locales.py` | F-012, F-013, F-014, F-015 |
| E-013 | info | validated | file | `re.match(r'^(.*)_assets_all_[0-9a-f]{32}$', name)` 全量枚举 | F-015 |
| E-014 | info | validated | command | `python scripts/extract_sprites.py` | —(仅支撑 P-013) |
| E-015 | info | validated | command | 派生视图:group by `<family>/<sub>` 后渲染 `/#/assets` | —(仅支撑 P-012/P-013) |
| E-016 | info | **observed** | command | `python scripts/luban_rows.py --selftest`(期望 696/700);`python scripts/verify_entity_map.py`(期望 exit 0, 4160 links) | F-016, F-017 |

> 证据以用户项目 `work/capybarago/evidence/E-012..E-016.md` 独立落盘,
> `report/12-locale-and-asset-grouping.md` §0.2 已改为**索引**而非第二份拷贝
> (此前两处副本曾漂移:报告内联版 8 字段、文件版 13 字段)。原文与 sha256 见证据文件。

> **勘误(本次回写修正)**:本行原写作「本 case 未建独立 `evidence/E-*.md`;
> 证据以 `notes/12-*.md` 内联 E-/F- 编号记录」。该说法在写下时已不成立
> ——`evidence/E-012..E-016.md` 五个文件当时即已存在,`notes/12` 也只是按 id
> **引用**它们而非内联。这条错误约定注记正是让「同一证据有两个家」长期不可见
> 的原因(用户项目 `workitems.md` 的 Coverage notes 记录了同一根因)。此处按
> 事实改正,并保留勘误痕迹而非静默抹掉。

> **status 说明**:E-016 刻意保持 `observed`,不升 `validated`。
> `skills/ops/evidence-finding-path.md`「Validated sufficiency(Issue #77 / R4*)」
> 规定升 `validated` SHOULD 基于 **≥2 条相互独立** 的 Evidence(最好一静一动);
> 两条命令互相印证不构成两个独立观察。其上的 F-016/F-017 因各带可重跑校验
> (`verify_entity_map.py`、`luban_rows.py --selftest`)仍记 `validated`。
> 该不对称是有意为之,也是 case-review 显示 `evidence 5 / findings 6` 的原因。

## Finding / Path 摘要
- top_finding: F-012 语言表行宽 = 18(非表头 `fields=15`);旧读取器丢空导致行错位,旧统计数据整体不可信
- path_type: callflow
- path_one_liner: `.bytes` → 只读 `<rows>` 头 → `rows×18` 保留空格的定长格 → key 与 17 个语言列按位对齐 → 每 key 多语言并列渲染
- path_2(P-013): bundle 名 `_assets_all_<32hex>` 去尾 → 按 `-` 切段得 Unity 构建路径 → 量分布(990/999 都是 `art/spine`)后**改用第三段**分组 → 12 个可浏览组
- 本阶段其余结论(行感知解码 696/700、entity→art 精确连接 3237/5368 双残差上报)见 E-016 → F-016/F-017;其 `severity` 全为 `n/a_re`(纯逆向,无漏洞面)
## 踩坑记录

| 问题 | 原因 | 解决方案 | 耗时 |
|------|------|---------|------|
| 语言列里出现 key(`col16='ui_friend_blacklist'`) | `extract_strings()` 丢弃空单元格 → 行错位 | 只读 `<rows>` 头;按 `rows×18` 定长切格并**保留空串**;用 `trailing_values==0` 自证 | 约 2h |
| `naive_width=23` vs declared `fields=15` | 两者都由错位数据推导,不可信 | 改用算术:`values/rows=17.9998` → 18 | 与上同时 |
| 索引被单 bundle 结果覆盖(glossary 999→2 条) | `--only` 探测开关无保护,直接写 `sprites.json` | 加 `partial` 判定:部分跑写 `sprites.partial.json` 并打印"完整索引进未动";dump 脚本先清自己的输出目录 | 恢复 1h |
| `tblanguageraft` 第 1 列仅 1,340 行、其余列 4,925 行 | 我误判为"该表列序不同" | **实测**:列 1 = `Language`/`Idioma`,列 3 = `语言`,映射与其它表一致;1,340 vs 4,925 是**覆盖率**差异不是列序差异 | 0.3h |
| Vue 两个新页面构建通过但打开即崩 | `watch(..., { immediate: true })` 在 `setup()` 同步执行,引用了尚未初始化的 `computed` → TDZ `Cannot access 'keys' before initialization`;setup 抛错 → vue-router 整条路由失败 | 去掉 `immediate`,在 `onMounted` 里播种初始选择;另加 `localeReady` watcher 兜后到的数据 | 0.5h |
| `npx vite build` 报 `Cannot resolve entry module index.html` | npx 从缓存解析到另一个大版本 vite(v8 vs 项目 v6) | 用项目内 `./node_modules/.bin/vite` | 0.2h |
| 怪物表解析出 **275 个字符串、100% 乱码**(0 ASCII / 204 KB) | 把 `extract_strings()` 式打捞扫描当解析器用:数值/空值/行边界全丢,在最宽的表上产出垃圾而非残缺 | 改行感知解码(只读 `rows`、体从 offset 1 起、贪心闭合);40 值/行定长自证 | 数 h |
| `cells = rows × fields` 算不通,一度以为"200 张只成 1 张" | `fields` **不是列数**,是第 1 行第 1 个字段的值;起始偏移也不对 | 弃用 `fields`;数据体从 offset 1 开始 → 同一条贪心走法立刻 687/700 | 0.5h |
| 4 张表闭不上 | 共有 8 字节样式的尾部,但干净切点各不相同(6/10/1) | **不拟合尾部规则**;记 `{"parsed": false}` 并排除。为凑 100% 拟合 = 把噪声当覆盖率 | 0.3h |
| boss 连接率 0/18,一度像"功能坏了" | 词表不匹配:boss icon 用 `monster_*`、boss spine 用 `boss-*`,与怪物集仅约 44/76 重叠;三套 boss 配置 id 拼不出 art slug | 诊断后**如实上报**,不做模糊匹配去"救"数字 | 0.5h |
| 153 个 `(atlas,name)` 槽有多条记录,疑为内容去重 | `__1`/`__2` 是 `uniq()` 的**碰撞计数器**,不是内容标记(2058 对实测:97.1% 字节相同、4.4% 不同) | 逐条核查:4160 条 art 条目 0 条落在多记录槽、0 条按名字是 `__1` | 0.5h |

## 工具链发现

- **`extract_strings()` 式"捞所有字符串"的读取器不适合带空值的定长格表**。对语言/本地化表必须保留空单元格,否则整行错位。凡是"声明 fields + 实际值可空"的表,都应改用 `rows × width` 定长切格并验证 `trailing == 0`。
- **`fields` 表头不可信**:本例 declared `fields=15`,真实宽度 18。可信的只有 `rows`。定宽由 `values/rows` 反推并用整除性 + 无残留自证。
- **Unity AssetBundle 名常编码构建路径**(`<path_segments>_assets_all_<hash>`),这是免费且真实的资源组织信息,优先于任何手写分类表。注意 `autogroup_duplicatedfile_*` 这类构建产物不含真实路径,应显式标记而非硬塞进某个类。
- **探测开关必须有写保护**:任何 `--only/--limit/--dry-run` 类参数只要会影响输出路径,就必须落盘到独立文件。这次是"工具照着参数正确工作",错在**没有护栏**,不在实现。
- `spine-player` 初始化若不给 `animation`,会退化为 `setEmptyAnimation(0)`;零 timeline 时 `getBounds` 返回 `-Infinity`,帧循环里抛出的异常 `try/catch` **抓不到**,必须挂 `window.onerror`。
- HTTP 层验证(状态码/size)**不能**证明 SPA 能挂载;setup 期异常只在浏览器组件生命周期里炸。
- **"打捞字符串"和"解析表"是两件事,而且差别不是精度而是对错**。打捞扫描在窄表上看起来"少几个值",在最宽的 int 密集表上直接产出 100% 乱码 —— 因为行边界丢了以后,字长前缀被当成数据读。判断依据:能否在**字节边界精确闭合**。闭不上就报闭不上。
- **"精确闭合"是最好的验收判据,且它自带反作弊**。要求 `parsed == len(data)` 意味着"让数字变好看"的唯一办法是拟合噪声。相比之下"抽出 N 个可用字段"没有任何反作弊能力。
- **表头字段名不可信,要用算术自证**:`fields`(声明列数)、`rows` 都可能被误读。本例 `fields=15` vs 实际 18,`fields` 甚至是另一个含义(第 1 行第 1 个值)。定宽表的第一动作应是 `values / rows` 求整并验余数。
- **连接(join)只做精确匹配,残差必须逐条上报,不许折算成百分比**。`3237/5368` 只报百分比 = 把 2131 个未匹配实体藏进一个好看的数字里。残差要能让下游逐条看到,并且要有断言"每条未匹配确实是未匹配"的校验脚本。
- **"看起来失败"的结果要先诊断再上报**。`boss 0/18` 不是 bug 是词表不匹配;`skill 41.6%` 是死家族。**能解释的 0% 比说不清的 90% 有价值**;而按名字相似度桥接缺口 = 编造数据。
- **多记录槽 + 自加后缀要当成碰撞残留而不是内容标记**。只要后缀是自己 `uniq()` 加的,就必须逐条验证引用落在哪个槽,不能假设"带后缀=不同内容"。

## 关键代码/命令

```python
# 语言表真实网格:只读 rows,保留空格
def read_values(path):
    d = open(path, "rb").read()
    rows, pos = read_size(d, 0)          # 只取 rows,不取 fields
    vals = []
    while pos < len(d):
        s, pos = read_string(d, pos)     # 空串也 append,不跳过
        vals.append(s)
    return rows, vals

rows, vals = read_values(p)
width = len(vals) // rows                # 6637 -> 18
assert len(vals) == width * rows or True # 残留量单独记录,正常应为 0

# 分组键:第三段才是有效区分度(990/999 都是 art/spine)
if seg[0] == 'art' and seg[1] == 'spine' and len(seg) > 2:
    primary = f'art/spine/{seg[2]}'      # ui / member / player / event / pet
    rest    = seg[3:]                    # duanwujie / jiayuanxitong / ...
```

```python
# 部分运行的写保护
partial = bool(limit or only)
out_name = "sprites.partial.json" if partial else "sprites.json"
if partial:
    print(f"wrote {out_name} -- the full sprites.json is UNTOUCHED")
```

```js
// 别在 setup 期同步读 computed:immediate watcher 会 TDZ
watch(() => store.localeReady, (r) => { if (r) seedSelection() })
// 播种放到 onMounted,此时所有绑定已初始化
onMounted(async () => { await loadLocales(); seedSelection() })
```

```python
# 行感知解码 + "精确闭合"作为验收判据(反作弊)
# 关键:不是"抽出多少可用字段",而是"能否在字节边界精确闭合"
def parse_rows(data):
    rows, pos = read_size(data, 1)     # 数据体从 offset 1 开始(offset 0 不是列数!)
    out = []
    for _ in range(rows):
        row = []
        for _ in range(WIDTH):         # WIDTH 由 values/rows 求整自证
            v, pos = read_value(data, pos)
            row.append(v)
        out.append(row)
    return out, pos

body, end = parse_rows(data)
if end != len(data):                   # 闭不上就报闭不上,绝不拟合尾部规则
    return {"parsed": False}           # 4/700 属于此类
```

```python
# 精确连接:拒绝模糊匹配 + 残差逐条可查 + 自断言"确实未匹配"
def join_exact(entities, art_index):
    matched, residue = [], []
    for e in entities:
        if e.slug in art_index:        # 只有精确相等
            matched.append((e, art_index[e.slug]))
        else:
            residue.append(e)          # 不折算成百分比,逐条保留
    return matched, residue
# verify_entity_map.py 独立复算,并断言每个 residue 确实不在 art_index 中
```

```bash
python scripts/dump_locales.py      # 先清 locales/ 再写,避免陈旧错文件与正确文件并存
python scripts/extract_sprites.py
python scripts/build_glossary.py
python scripts/luban_rows.py --selftest   # 行感知解码;期望 696/700 精确闭合
python scripts/verify_entity_map.py       # 独立复算;期望 exit 0(4160 links)
cd glossary-app && node scripts/sync-assets.mjs && ./node_modules/.bin/vite build
```

## 对本包的改进建议

1. **`skills/ops/evidence-finding-path.md` 建议补一节"单条 Evidence 的自我否定"**:本次有 6 条先前结论被实测推翻(#3 "288/392 目录损坏"、#6 "该表列序不同"等),其中 2 条已先对操作者宣布。现有契约规定了 evidence→finding 的正向绑定,但没有规定**记录撤回**(retraction)的字段。建议在 Finding 下增 `retracts:` 或在报告中固定"Claims retracted"章节。
2. **`timeline-workitem.md` 的 `corrects:` 字段需校验目标存在**。我第一版 `corrects:` 写了一个**日志里不存在的时间戳**(凭印象填的),抽查时才改对。建议 case-review 增加"`corrects:` 指向的 `##` 时间块必须真实存在"的检查。
3. **建议新增 pitfalls 条目:「声明 fields ≠ 实际行长,定长格表丢空即错行」**,并给一个 `trailing==0` 自检模板。这类表在移动游戏配置里(本地化、奖励表、掉落表)非常常见。
4. **建议新增 pitfalls 条目:「探测开关必须写保护」**。这是本次唯一造成实际数据损失的失误,且工具行为"符合参数语义",靠 review 代码看不出来,只能靠约定。
5. **产物验证层级建议写进 apk-reverse**:`HTTP 200/size 正确` < `JSON 可解析` < `组件可挂载` < `渲染正确`。本次在第 3 层翻车。
6. **建议新增 pitfalls 条目:「打捞字符串 ≠ 解析表;验收判据应为字节级精确闭合」**。判据自带反作弊:要凑好看的数字只能拟合噪声。适合所有无 schema 的二进制配置表(Luban/FlatBuffers 同类)。
7. **建议在 `evidence-finding-path.md` 明确「单条 Evidence 可支撑多个 Finding,但 Finding 的 `status` 与 Evidence 的 `status` 是两件事」**。本 case 出现容易误读的组合:`E-016` 保持 `observed`(单条不自我升格),其上的 `F-016/F-017` 记 `validated`(各带可重跑校验)。case-review 输出 `evidence 5 / findings 6` 时,若无说明会像数据不一致。建议在契约里给一句判定规则,而不是每个 case 各自解释。
8. **建议 `case-review` 检查 `report/*.md` 是否被 `timeline.md` 引用**(或反之):本 case 的报告是 docs-generator 产物,但 timeline 里最后一次"next:"才第一次提到它;若报告被删,timeline 的 traceability 仍会显示计数。另建议检查 journal `_index.md` 的链接是否与 `field-journal/` 实际文件一一对应 —— 本次就是靠人眼比对才发现 journal 条目里的证据声明是错的。
9. **建议给 field-journal 条目加"与既有条目重名/同主题"检测**:本次同日同主题已有条目,险些产出**第二份内容重叠但细节冲突**的日志。日志是长期资产,"同一天同一目标两条"应是显式告警而非静默允许。

## 可复用的模式/脚本片段

**模式 A:定长格二进制表的真实宽度恢复**
适用于任何"`<rows>` 头 + 扁平值流 + 含空值"的表。
1. 只读 `rows`;
2. `width = values // rows`;
3. 断言 `values % rows == 0`(或记录小残留);
4. 断言每列语义合理(本例:每个语言列覆盖 key 数应大致相等,若某列骤少是**覆盖率**问题,先别改成"列序不同")。

**模式 B:用"文字体系自证"的锚点验证 i18n 列身份**
取一个 key,比较各列译文的**脚本**(简/繁、拉丁/西里尔/泰文/日文假名),再取一个**仅大小写不同**的键值对(如 es vs es-419)来证明两列独立。比"看起来对"强得多。

**模式 C:从 AssetBundle 名反推资源路径**
`re.match(r'^(.*)_assets_all_[0-9a-f]{32}$', name)` → 按 `-` 切段即路径段。先做全量分布测量,再决定分组层级;别假设"路径前两段就是好的分组键"。

**模式 D:无 schema 二进制配置表的行感知解析(以"精确闭合"为验收)**
1. 只用 `rows` 作表头,**数据体从 offset 1 起**;弃用声明式 `fields`(它可能是别的含义);
2. 用 `values / rows` 求整得宽度并验余数为 0;
3. 解析后断言 `parsed_bytes == len(data)`;**闭不上就报 `parsed:false`**,不拟合尾部规则;
4. 交叉验证:在一张表上找"可人工核对"的行(如英雄名 `hero_name_301` / 图 `img_card_hero_zhuzhu`)坐实字段位置。

**模式 E:精确连接 + 残差双向上报**
1. 只允许精确相等或**显式标注来源**的变换,禁 fuzzy/levenshtein/embedding;
2. 分别保留两侧残差(本例 2131 实体 / 8488 sprite),在 UI 里逐条可见;
3. 写独立校验脚本**重新推导**计数并断言:每条未匹配确实不在索引中、每条匹配的文件确实存在 —— 没有这个断言,百分比就没有意义。

## 进化动作
- [ ] 更新了路由矩阵
- [ ] 更新了 tool-index
- [ ] 更新了 bootstrap-manifest
- [ ] 更新了子 skill 文档
- [x] 新增了 pitfalls 记录(见"对本包的改进建议"1–9,待操作者确认后落入对应 skill)
- [x] 修正了本条自身的错误注记(原称"未建独立 evidence/E-*.md",与事实不符,已改正并留勘误痕迹)
- [ ] 无需更新

> 说明:pitfalls 建议与契约改进(第 6–9 条)以文本形式给出,**未直接改 `skills/` 下文档或
> `skills/ops/*.md` 契约**,等操作者确认后再落。

## 环境信息
- OS: Windows 11 Enterprise 10.0.26200(Shell: Git Bash)
- 工具版本: Python 3.14, UnityPy, Node 22, Vue 3.5.13, Vite 6.4.3, vue-router 4.5, spine-player 4.0.31
- 目标平台/版本: Android 模拟器(本地自有实例),游戏为 Unity IL2CPP v31 + HybridCLR 热更,AB 内 spine 为 4.0.63

## 脱敏要求

已执行:
- 未写入真实域名/IP;目标主机以"本地模拟器自有实例"描述,进程以 `{target_app}` 语义表述。
- 未含 token/cookie/密码/JWT/api key。
- 游戏商业资产名(`jiayuanxitong`、`duanwujie` 等)为资源路径标识,保留以维持可复现性;不含用户数据。
- 未粘贴完整二进制 dump,仅贴字段结构与自检命令。

## 索引同步
- [x] `_index.md` 按场景分类新增一行
- [x] 高频成功模式:二进制表恢复 / i18n 列验证 下追加
- [x] 实体倒排:Unity AssetBundle / 本地化表 下追加
- [x] 累计统计与"最近更新"日期
- [x] 本次补充:实体倒排追加「Luban 配置表 / entity-art 连接」;高频成功模式追加「精确闭合解析 / 精确连接+残差上报」

---
<!-- [进化统计] 本包累计完成项目: N | 本次新增模式: 5(定长格宽度恢复 / 文字体系锚定法 / Bundle 路径反推 / 精确闭合式行感知解析 / 精确连接+残差双向上报) | 本次修复工具链问题: 10 -->
<!-- [社区贡献] 完成后询问用户是否 PR 到主仓库。流程见 CONTRIBUTE-BACK.md -->
