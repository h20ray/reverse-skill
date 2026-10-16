# 项目经验索引

> 本文件用于在新任务开始前快速检索历史经验。
> 带 `[种子]` 标记的条目是预置参考案例，不计入真实完成项目。
> 真实项目使用日期文件名（例如 `2026-05-16_*`），种子案例使用 `seed-*`。

## 统计

- 真实项目数：25
- 种子参考数：17
- 总条目数：42
- 最近更新：2026-10-13

## 按场景分类

### APK / Android 逆向

- [2026-10-13 Summoners War 3D 资源管线:模型/骨骼/特效(PEFT)格式全量恢复、Steam/模拟器双源分层与特效挂点(dummy 编号)还原](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)
- [2026-09-26 Unity HybridCLR 热更 DLL 定位与自实现 AES 解密恢复(随包下发资源包 → 明文兄弟程序集即解密器 → 142 万行 C#)](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)
- [2026-09-26 Unity 全链路静态分析:配置表判定、协议 id 空间、Addressables 旧目录格式、资源覆盖边界(先量边界再开工)](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [2026-09-25 Unity 本地化表网格恢复(行宽 18)、AssetBundle 路径反推分组与 Luban 表精确闭合解析](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)
- [2026-09-23 游戏贴图集（Texture Atlas）无损切分、邻元溢出消除与母版素材回溯取证](./2026-09-23_game-sprite-atlas-forensics-and-master-cut-recovery.md)
- [2026-08-20 Flutter AOT 服务端驱动广告去除（Blutter + 等长字符串替换）](./2026-08-20_apk-flutter-banner-ad-removal.md)
- [2026-05-15-cellular-pro-mumu-ksad-fragment-fix](./2026-05-15-cellular-pro-mumu-ksad-fragment-fix.md)
- [[种子] seed-008_apk-okhttp-ssl-pin-bypass](./seed-008_apk-okhttp-ssl-pin-bypass.md)

### 二进制 / 固件 / CTF

- [2026-08-06_cortex-m-msc-firmware-self-keyed-rotate-xor](./2026-08-06_cortex-m-msc-firmware-self-keyed-rotate-xor.md)
- [2026-07-22 Electron Bytenode 特权更新链分析](./2026-07-22_electron-bytenode-privileged-update-chain.md)
- [2026-07-14_android-arm64-self-extract-source-recovery](./2026-07-14_android-arm64-self-extract-source-recovery.md)
- [2026-05-15_lumine-go-reverse](./2026-05-15_lumine-go-reverse.md)
- [[种子] seed-001_elf-packed-loader](./seed-001_elf-packed-loader.md)
- [[种子] seed-002_go-malware-stripped](./seed-002_go-malware-stripped.md)
- [[种子] seed-010_ctf-pwn-rop-x64](./seed-010_ctf-pwn-rop-x64.md)
- [[种子] seed-011_pcap-protocol-reverse](./seed-011_pcap-protocol-reverse.md)
- [[种子] seed-014_unity-il2cpp-reverse](./seed-014_unity-il2cpp-reverse.md)
- [[种子] seed-015_iot-firmware-uart](./seed-015_iot-firmware-uart.md)

### Web / API / 渗透测试

- [2026-08-01 Next.js CDK 契约保真本地重建](./2026-08-01_nextjs-cdk-contract-faithful-local-reconstruction.md)
- [2026-08-01_pentest-encryption-oracle-public-template-sql-admin-takeover: .NET CMS 通用加密 oracle、公开密文模板消费者、完整 STL/模板解析、原始 SQL `UPDATE RETURNING`、官方管理员验证器新旧口令差分与隔离 PostgreSQL 清理闭环](./2026-08-01_pentest-encryption-oracle-public-template-sql-admin-takeover.md)

- [2026-07-18_gin-juice-client-friction](./2026-07-18_gin-juice-client-friction.md)
- [2026-07-05_dsl-vm-captcha-reverse](./2026-07-05_dsl-vm-captcha-reverse.md)
- [2026-06-29_burp-mcp-full-test-and-fix](./2026-06-29_burp-mcp-full-test-and-fix.md)
- [2026-05-26_pentest-newapi-rate-limit-bypass](./2026-05-26_pentest-newapi-rate-limit-bypass.md)
- [2026-05-25_pentest-cf-access-sibling-subdomain-cookie-poisoning](./2026-05-25_pentest-cf-access-sibling-subdomain-cookie-poisoning.md)
- [2026-05-17_pentest-vue-spa-actuator-leak](./2026-05-17_pentest-vue-spa-actuator-leak.md)
- [2026-05-16_pentest-personalblog-fun-mass-assignment](./2026-05-16_pentest-personalblog-fun-mass-assignment.md)
- [[种子] seed-003_web-api-auth-bypass](./seed-003_web-api-auth-bypass.md)
- [[种子] seed-004_js-sign-webpack](./seed-004_js-sign-webpack.md)
- [[种子] seed-006_ssrf-cloud-metadata](./seed-006_ssrf-cloud-metadata.md)
- [[种子] seed-017_xxe-oob-exfil](./seed-017_xxe-oob-exfil.md)

### 企业内网 / 云安全

- [[种子] seed-005_ad-certipy-esc1](./seed-005_ad-certipy-esc1.md)
- [[种子] seed-007_ntlm-relay-coercer](./seed-007_ntlm-relay-coercer.md)
- [[种子] seed-013_kerberoasting-spn](./seed-013_kerberoasting-spn.md)
- [[种子] seed-016_k8s-container-escape](./seed-016_k8s-container-escape.md)

### iOS 逆向

- [[种子] seed-009_ios-jailbreak-detect-bypass](./seed-009_ios-jailbreak-detect-bypass.md)

### 工具链与环境

- [2026-08-17 tool-index r2 fallback 与 powershell/pwsh 子进程入口统一](./2026-08-17_tool-index-r2-fallback-powershell-pwsh-host-fix.md)
- [2026-08-14 Windows PowerShell 原生命令退出码 PR 审查](./2026-08-14_windows-powershell-native-exit-code-pr-review.md)
- [2026-08-08 平台无关结构化路由 PR 集成](./2026-08-08_client-neutral-structured-routing-pr-integration.md)
- [2026-07-20_reverse-toolchain-windows-bootstrap](./2026-07-20_reverse-toolchain-windows-bootstrap.md)

### 其他

- [2026-08-08 开放 PR 价值分级与安全集成](./2026-08-08_pr-value-triage-and-safe-integration.md)
- [[种子] seed-012_log4shell-jndi-rce](./seed-012_log4shell-jndi-rce.md)

## 高频成功模式（按技术）

### 平台无关路由与供应链门禁

- [Resolve-ReverseHostExe 统一子进程入口、r2 .bat fallback、StrictMode hashtable 安全访问](./2026-08-17_tool-index-r2-fallback-powershell-pwsh-host-fix.md)
- [原生命令后立即保存退出码、Windows PowerShell 5.1 实宿主复现、PR head 固定](./2026-08-14_windows-powershell-native-exit-code-pr-review.md)
- [单一 routing.json、多入口 parity、实际安装命令 pin](./2026-08-08_client-neutral-structured-routing-pr-integration.md)

### 固件自定义封装

- [1 KiB 自带掩码 ROR/XOR、Cortex-M 向量 crib、跨固件验证](./2026-08-06_cortex-m-msc-firmware-self-keyed-rotate-xor.md)

### 定长格二进制表与 i18n 列验证

- [只读 `<rows>` 头定行宽、保留空单元格防错行、用 `trailing==0` 自证；文字体系/大小写差异锚定语言列](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)
- [无 schema 配置表:以"字节级精确闭合"为验收判据(自带反作弊);闭不上就报闭不上,不拟合尾部规则](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)

### 无 schema 二进制配置表(Luban)与实体-资源连接

- [打捞字符串 ≠ 解析表:以"字节级精确闭合"为验收判据(自带反作弊);`fields` 头不可信、数据体自 offset 1 起](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)
- [连接只做精确匹配,两侧残差逐条上报而非折算百分比;能解释的 0% 比说不清的 90% 有价值](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)

### Unity AssetBundle 路径反推

- [`<path_segments>_assets_all_<hash>` 命名法还原真实资源路径，先量分布再定分组层级](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)

### HybridCLR 热更程序集恢复与自实现加密还原

- [按体积在资源包里定位热更载荷：`dll_assets_all_<hash>` bundle → `TextAsset.m_Name` 即程序集名；热更 DLL 常随包下发，先找包内再假设下载](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)
- [明文的同族程序集就是解密器：反编译它比任何爆破都便宜；“只有主程序集加密”是常见的不对称保护，先逐文件体检再上密码学](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)
- [自实现密钥派生常是 UTF8 + 零填充（无 KDF/盐/迭代）；验收用独立手段（`MZ`/`PE\0\0`/CLR 目录/`BSJB`），不是“解出来不像乱码”](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)

### 可行性普查与覆盖边界取证

- [开工前先输出对象类型直方图:目标类型计数为 0 ⇒ 结论是"边界"而非"待办";先量边界再开工](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [覆盖边界做成可信否定:统计全体样本(703/703)而非抽样,给精确直方图,并**成对**交出解锁条件](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)

### 宿主环境定性（决定动态阶段可行性）

- [guest ABI 与 `primaryCpuAbi` 不一致 ⇒ 存在翻译层（Intel Houdini），ARM 代码被翻译执行；结论是换真机而非继续调 Frida attach 参数](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)
- [多实例模拟器：先按 `name` 核对实例再读 `adb_port`，不要凭默认端口假设目标](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)

### 二进制资源格式:以格式自带冗余做验收

- [trailer 重复计数 / 包围盒 == 解码坐标精确 min/max / 位掩码 set-bit 数 == 数据长度;剩余失败用"能解释全部失败样本的单一位"定位(PEFT 19,062/19,168)](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)
- [未知比例因子:骨骼世界坐标 ↔ 绑定顶点质心的中位残差扫描,并与已知正确样本基线比较(float 骨骼 ×65536/divider)](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)
- [同列数值多命名空间:按模式分组统计"命中 A / 命中 B"比例判定语义(dummy 编号 882/892 vs bone id 2648)](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)

### 多源资源分层(安装包 / 下载补丁 / 平台差异)

- [先逐字节比对各源(Steam bundle == APK 安装期资源包),再定优先级:下载层是补丁层(86 个基础模型被重制),必须优先;源优先级要压过文件名拼写变体](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)
- [adb 增量拉取:`find -exec stat` 清单 → 设备侧 `tar -T` 流式 → `tarfile` `filter="data"` 解包;217 文件 12 秒](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)

## 实体倒排（按目标特征）

### 多宿主安全技能路由包

- [核心/适配器边界与大 PR 选择性集成](./2026-08-08_client-neutral-structured-routing-pr-integration.md)

### Windows PowerShell 供应链引导脚本

- [powershell/pwsh 子进程入口统一、tool-index .bat fallback、pin gate StrictMode](./2026-08-17_tool-index-r2-fallback-powershell-pwsh-host-fix.md)
- [原生命令输出经过对象管道后退出码失真](./2026-08-14_windows-powershell-native-exit-code-pr-review.md)

### Cortex-M USB MSC 升级器

- [应用/驻留 bootloader 边界与虚拟磁盘写入链路](./2026-08-06_cortex-m-msc-firmware-self-keyed-rotate-xor.md)

### Unity 手游本地化表 / AssetBundle

- [语言表 declared `fields` 与实际行宽不符；探测开关缺少写保护导致索引被覆盖](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)
- [Luban 配置表打捞扫描产出 100% 乱码;`fields` 头非列数、数据体自 offset 1 起;精确连接 3237/5368 且两侧残差逐条上报](./2026-09-25_unity-localization-grid-and-bundle-path-grouping.md)

### Unity 手游 HybridCLR 热更程序集 / 私有 TLS 栈

- [IL2CPP + HybridCLR 目标的真实游戏逻辑不在 `libil2cpp.so`,而在随包下发的 `dll` bundle;`global-metadata.dat` 未必加密(本例为明文 v31)](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)
- [识别私有 TLS 的最高效信号是 `files/` 下的 SDK 命名目录(Best HTTP/3),而非 `.so` 字符串扫描;`.so` 扫 BoringSSL 标记一无所获且具误导性](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)
- [熵只能排除"可见块结构",不能识别算法;均匀熵被误判为流密码,实为 AES-256-CBC](./2026-09-26_unity-hybridclr-hotfix-dll-recovery.md)

### Unity Addressables 旧目录 / Luban 配置表 / 覆盖边界

- [Addressables 旧目录(非 BinaryStorageBuffer):`bucket.keyIndex` 是**绝对字节偏移**;entry 记录 = 7 个 int32 固定列序;`Hash128`/`Type` 长度是**单字节**。连错四次都"看着合理",应停止拟合去读对应版本的 `ContentCatalogData.cs`](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- ["包数 ≠ 资产数":UnityFS bundle 常是"单资产信封"(本例 702/703 = 1 个 AssetBundle + 1 个 TextAsset),不要用包数估工作量](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [Spine 可能是主流动画路径(955 `SkeletonDataAsset` ≈ AnimationClip 的 6 倍);只按类型计数下结论会指向少数派系统](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [资源覆盖边界:目录**声明**了 154 AnimationClip / 3820 GameObject / 3930 Texture2D,磁盘上计数**全为 0** ⇒ 表现层对任何读法都不可答](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [脱敏只作用于**记录**,绝不作用于**记录之源**(哈希锁定的产物);弄脏后从原始样本重建并**核对原哈希**](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [按**声明类型**限定成员访问:裸字段名在百万行反编译产物上命中 0;先收集"类型确为 T"的变量名再编译单条交替正则](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)

### 覆盖边界被推翻 / 设备自带缓存 / 运行时优先 · 2026-09-26(补充)

- [**"边界"只在你查找过的那个位置成立**。上一条"磁盘计数全为 0 ⇒ 不可答"**只对 APK 成立**,不是可用性断言:游戏自己首启就下载,设备 `files/UnityCache/Shared/<32hex>/<32hex>/__data` 里躺着 **289 个 bundle / 568,724 个对象**(含 188 Camera / 6,637 ParticleSystem / 143,633 GameObject —— 正是先前报"全为 0"的那些量)。证明"覆盖边界"必须覆盖**材料可能存在的并集**,而不是你恰好查看的那一处。`__info` 侧车是 `<status>\r\n<unixtime>\r\n<字段>\r\n__data\r\n`;第 3 字段恒为 `1`,**不是字节数**(0/289 命中)。`adb pull` 在 Git Bash 下会把 `/sdcard/...` 重写成 `C:/Program Files/Git/sdcard/...` 而 stat 失败 —— 每次调用都要 `MSYS_NO_PATHCONV=1`](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [缓存与目录**无法按名字/哈希**关联(0/2132),因为缓存键在 Addressables/UnityWebRequest 层计算,而该层**不在**已恢复的程序集里(1.43M 行里 `Hash128`/`AssetBundleCache`/`AssetBundleRequestOptions` 命中 0)。改用**按内容识别**:154/289 个 bundle 内含一个 TextAsset,其自身名字就是配置表名(`tbcapymon_capymon`)。关联不可能时,把它记为局限,别用相似度糊过去](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**"未获得"要分清是"没权限"还是"不存在"**。声明了 1431 个远程 bundle 的那个 CDN 主机 **NXDOMAIN**(DoH Status 3 / 0 answers,而同一 shell 同一时刻 `example.com`、`google.com` 正常解析)⇒ 对**任何人**都取不到,不是授权问题。一个**带确定成因的否定结论**优于一个挂着"等更多权限"的 `blocked`:前者把案子里的悬置项清掉了](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**二进制格式啃不动时,用权威实现,别拟合字节**。Spine `.skel` 手写解析连错五次,每次都"看着像数据"(浮动payload把可打印串扫描切碎;加控制字节边界仍过采;修好头部后 45 根骨骼的 rig 读出 `parent=114`)。真正的坑是 `readString` 的**减一**语义(`byteCount = len+1`,0=null,1=""),照 `SkeletonBinary.ts` 实现后头部与字符串表**精确**对齐;随后骨骼表仍不服从,于是直接上权威运行时 `@esotericsoftware/spine-core`(配 stub texture 即可,动画名不依赖像素)。同一个修法已经在 Addressables 目录上奏效过一次](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**静默丢一半语料**是配对 bug:同 bundle 内所有骨架都叫 `skeleton_xs.*`,按名字落盘每个 bundle 只留一对;实测真实顺序是 119 个 `.atlas` **在前**、119 个 `.skel` **在后**,交替假设不成立(v1 写出 113 对,而实际有 231 对)。改为**按内容配对**(骨架串表 ∩ 图集区域名,取最大重合;重合为 0 报"未配对"而非随意指派)→ 231/231 配对,OK 从 8 涨到 152。任何**静默下降的计数**都是 bug,不是"剩下一部分难啃"](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**验证器绿灯 ≠ 已验证**。报告里的 finding/path 必须是 `###` 三级标题**并带字段块**才会被 `review_case.py` 解析(FINDING_HEADING / PATH_HEADING);我把 7 个 finding、2 个 path 写成 `##` 散文标题且无字段块,于是它们**不是无效,而是不可见** —— 验证器一直绿着报 `39 findings / 2 paths PASS`,而真实是 **45 / 4**。**"确认检查是绿的"不等于"确认它检查了什么"**:验证器的 pass 只是关于它解析到的那个子集的证据。写完后要**断言计数按写入量增加**,而不是把绿灯当成确认](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**"资产里存在"不等于"会被播放"**。枚举出动画名只是"存在"的陈述;要回答"何时播放",必须回到**代码路径 + 配置表**。判据链:名字是否为**字符串字面量**(本例 65 个中 48 个)→ 播放点是否按**声明类型**检索(裸成员名误命中率极高,`Play` 单字有 12,121 处)→ 名字是否为**配置表的键**。本例名字是 `tbartanimation_animation` 的键,其 `hideWeapon` 字段在播放时决定**是否隐藏手持武器节点**;而武器变体族(`Battle/Attack_{Sword,Bow,Spear,Magic}`)由 `EquipSubType` 从**玩家当前装备**解析 —— 这就把"表现层"接回了"游戏状态"](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**三方交叉一致才有分量:资产 × 代码 × 配置**。三者由三个工具读三个不同文件产出,彼此无推导关系;8 个武器变体名在三方**全部命中**,这类一致性不是自证。反之,**不一致的 17 个名字要如实记为残留**(1 个 + 16 个方向名,前缀在 42MB 客户端里 0 命中),不要用相似度补上](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**小表也要断言精确闭合**:`tbartanimation_animation` 首字节是**行数**(0x18=24)而非串长前缀;读错后仍打印出一张"像数据"的表(4 行 / 消耗 346 字节 ≠ 390)。**同时**从 JSON 提取失败让我误判 8 个名字"不存在",实际全在。两次都无异常、无告警 —— 与本案统一失效模式同源。防御:**断言精确闭合** + **读产物自己声明的结构**,不要假设](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**别把"信号"当成"事实":目录名 ≠ 能力**。本案把"客户端自带 TLS 栈 + 证书固定"写进阻塞项,依据只是 `files/` 下存在 `com.Tivadar.Best.HTTP.v3/` 这个**目录名**,此后**历经 11 次 workitem 修订无人复核**,还被写进收尾报告当成定论。实测三点全部推翻:(1) APK 里 23 个 `.so` **没有任何 TLS 库**(`libunity.so` 带的是 Unity 标配 `mbedtls`;`libil2cpp.so` 的 BoringSSL/OpenSSL 标记为 **0**);(2) 全客户端只有一个 `CertificateHandler`,实现为 `protected override bool ValidateCertificate(byte[] d) { return true; }` —— 固定的公钥/证书哈希**存了却从不读取**,即**根本没做校验**;(3) 真实 API 走 `UnityWebRequest.Put` + 该空校验器,响应在 `downloadHandler.data` 处**已是明文**。**教训:证据若是"名字"(目录 / 数字 / 类型计数),结论就只能是"位置",不能是"能力"。** 复核成本极低,误判代价是 11 轮口径污染](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)
- [**关键词命中数会"证实"一个错误前提**:在 42MB 客户端里搜 `pinning` 得 **46 处**命中,看似是对上述结论的有力佐证 —— 实际**全部**是 `isSpinning`/`endSpinning`(幸运转盘 UI)。若信这个计数,就会"确认"一个代码已推翻的前提。**计数不是证据,读每一处命中才是**;这与"按声明类型限定成员访问"是同一条纪律](./2026-09-26_unity-config-protocol-and-asset-coverage-boundary.md)

### Summoners War 客户端资源 (PMM / PLM / PEFT / localvalue)

- [模型 UV 双重翻转、蒙皮包围盒首帧塌缩、技能部件停放在 -1000 单位;PLM `%`+ 头块 0x11、`'`+ 为 float(×65536/divider)](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)
- [单位表按表头等宽收行;`collection view`=可玩、`awaken=-1`=副本变体;皮肤表 55;英文皮肤名在 `text_eng.dat` 连续记录](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)
- [特效挂点:模式 3=bone id,模式 0/1=dummy 编号(骨骼 flag),0=地面原点;layer 1/2=公告板;透明画布上加法混合需只加颜色不动 alpha](./2026-10-13_sw-3d-asset-pipeline-format-recovery-and-effect-attachment.md)

## 使用说明

1. 新任务开始前，先按场景分类查找是否有相似记录。
2. 命中真实项目时，优先复用已验证的流程和踩坑记录。
3. 命中种子案例时，只作为方法参考，不视为真实成功记录。
4. 新增经验后，请按 PR 流程更新本索引，避免直接改动共享主线。
