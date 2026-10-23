# world.execute(me); — 终端 ASCII 字符动画 MV

用 ANSI / ASCII 字符在终端里播放的一支 MV：Mili《world.execute(me);》
（专辑 *Miracle Milk*, 2016）。画面全部由字符、色块和转义序列实时渲染，
中英双语字幕逐句跟随真实音频，节拍与歌词时间戳驱动每一个转场。

```
./run.sh
```

---

## 快速开始

```sh
./run.sh                 # 有声音播放（自动找 assets/ 里的音频）
./run.sh --silent        # 只看画面，不要声音
./run.sh --info          # 打印时间轴（BPM、分段、85 行歌词时间戳）
./run.sh --dump 15,96    # 把指定秒数的画面渲染成纯文本，便于截图/调试
./run.sh --help          # 全部参数
```

**终端要求**：最小 `48x14`，推荐 `100x30` 以上（越大画面细节越多）。
支持真彩色（`COLORTERM=truecolor`）、256 色、以及纯单色终端（`--mono`）。

**依赖**：

| 用途 | 依赖 | 缺失时 |
|---|---|---|
| 运行 | Python 3.8+（只用标准库） | — |
| 音频 | `mpv`（首选，Unix socket IPC 精确对时） | 自动降级 |
| 音频备选 | `ffplay` / `mpg123` / `paplay` | 用系统时钟对齐 |
| 无声 | — | `--silent` 或找不到音频时自动静音播放 |
| 音频转码（仅首次） | `ffmpeg` | 已提供 `assets/world-execute-me.m4a`，无需再转 |

## 操作

| 键 | 作用 |
|---|---|
| `空格` | 暂停 / 继续（音频与画面同时暂停） |
| `←` / `→` | 后退 / 前进 5 秒 |
| `↓` / `↑` | 后退 / 前进 30 秒 |
| `q` / `Esc` / `Ctrl-C` | 退出（恢复终端、关闭播放器） |

## 命令行参数

```
--silent            无声播放
--fps 20            渲染帧率（默认 20，最低 4）
--start 60          从第 60 秒开始
--audio PATH        指定音频文件
--player mpv_ipc|mpv|ffplay|mpg123|paplay|silent
--volume 100        音量
--color auto|rgb|256|mono    色彩模式
--mono              强制单色
--width / --height  强制画布尺寸（默认跟随终端）
--offset 0.25       字幕整体偏移（秒），用于微调对轴
--no-hud            不画边框、进度条与副标题区
--info              打印时间轴
--dump 15,60,96.5   渲染指定时间点的静态帧
--dump-size 100x30  dump 的画布尺寸
```

---

## 目录结构

```
.
├── run.sh                       启动器
├── assets/world-execute-me.m4a  工作用音频（从 mp4 无损抽出 AAC）
├── world.execute(me);-Mili.mp4  原始上传文件（未改动）
├── world.execute(me);-Mili-歌词.lrc   原始歌词（未改动）
├── README.md
└── src/
    ├── mv.py          主循环、场景调度、边框/进度条/字幕合成、CLI
    ├── renderer.py    画布（Canvas）：宽字符安全写入、溶解叠化、色彩量化
    ├── lyrics.py      130 BPM 网格、15 段结构、85 行双语时间轴
    ├── audio.py       三级播放器：mpv IPC → 管道播放器+时钟补偿 → 静音
    ├── energy.py      音频 RMS 包络（20 Hz），驱动画面随响度呼吸
    ├── art.py         5x5 字体、机器人 ME、YOU 菱形、猫、神、骷髅等素材
    ├── fx.py          雨、星场、扫描线、故障、波纹、示波器、均衡器等特效
    ├── base.py        场景基类、时间窗淡入淡出、溶解叠化 stamp
    ├── scenes_a.py    Intro / Verse1 / Verse2 / Pre1 / Chorus1
    └── scenes_b.py    Verse3 / Pre2 / Chorus2 / Bridge / Build / Chant
                       / Final / Outro / Shutdown / EndCard
```

---

## 同步是怎么做的

画面 **不是** 预渲染视频，而是每一帧都由当前播放时间 `t` 纯函数式地画出来
（所有随机量都来自 `h01(seed...)` 哈希，所以同一时刻永远画出同一帧，拖动进度
条也不会花屏）。

对时有三个层级，自动选择：

1. **mpv + Unix Socket JSON IPC**（首选）
   以 `--input-ipc-server` 启动 mpv，每帧 `get_property time-pos` 读真实播放
   位置，`pause` / `seek` 直接作用于播放器。画面跟着音频走，不可能漂移。
2. **管道播放器 + 单调时钟 + 启动补偿**
   `mpv --no-video` / `ffplay -nodisp` / `mpg123` / `paplay` 播放，用
   `time.monotonic()` 计时，并按各播放器的启动延迟（mpv ~0.22 s、ffplay
   ~0.42 s、mpg123 ~0.18 s、paplay ~0.12 s）补偿首帧偏移。
3. **静音**：`--silent` 时用同一个时钟驱动，画面依然完整。

**节拍**：对音频做 10 ms 跳步的自相关 + 抛物线插值，锁定 **130.0 BPM**
（一拍 0.4615 s，一小节 1.846 s）。鼓点、心跳、故障闪烁、进度条刻度都对齐
到这个网格。

**歌词校正**：用户提供的 LRC 里第一段主歌整体提前了约 15 秒（第 1 句标在
0:00，而人声实际上在 0:15.0 进入）。用频谱人声频段能量跳变检测到 15.00 s
的入口后，对 LRC 前段做了 `+15 s` 平移，其余段落保持原值；`--offset` 仍可
再整体微调。

---

## 15 个段落与画面

| 时间 | 段落 | 画面 |
|---|---|---|
| 0:00 | BOOT | 开机自检：数据一行行灌满屏幕、标题 `world.execute(me);`、15 项初始化逐项检测 |
| 0:15 | VERSE 1「Set up new world」 | 地平线上的机器人、输电线、棋盘、`new Object("me")`、初始化面板 |
| 0:37 | VERSE 2「dim(P)=3 / C=2πr / ∞」 | 旋转线框立方体、点云、圆周率动点、正弦与切线、∞ 与数轴 |
| 0:47 | PRE 1「AC→DC / blind / dizzy」 | 示波器、交直流切换、闭眼黑屏、螺旋眩晕 |
| 0:56 | CHORUS 1「stimulation→satisfaction」 | 心跳巨心、光环、频谱、SATISFACTION 进度条、bash 窗口 |
| 1:13 | VERSE 3「I can be anything」 | 猫（呼噜波纹）、食物、抗氧化剂、`you` 菱形、物品编号面板 |
| 1:33 | PRE 2「switch gender/time/role」 | `AM/PM` 大字、拨盘、`12:00 → 24:00`、恍惚同心圆 |
| 1:53 | CHORUS 2「vibration/completion」 | 振动波形、完成度、`you: signal lost`、隔离方框 |
| 1:58 | BRIDGE「erase fragments / challenge god」 | `~/memories` 文件列表被 `rm -rf` 逐条删除、巨神剪影、非法参数报错 |
| 2:20 | BUILD | 错误级联刷屏、蓄能光束、屏幕抖动 |
| 2:28 | CHANT「EXECUTION ×3 + 数数」 | 5x5 巨字 `EXECUTION` 四段式闪烁、准星、EIN/DOS/TROIS/NE/FEM/LIU |
| 2:43 | FINAL「give them all the execution」 | 成排程序被处决的扫描线、伸向幽灵 `you?` 的手、心形牢笼 |
| 2:57 | OUTRO「algebra of love」 | 黑板风公式：`love := Σ(you→me)`、`∂me/∂you > 0`、`Q: what is love? A: you.` |
| 3:12 | SHUTDOWN「exit code 0」 | 终端退出日志、`me.execute(love);`、长暗、`...execution.` 耳语、CRT 收束成一点 |
| 3:27 | END CARD | `world.execute(me);` / Mili · Miracle Milk (2016) / 感谢你执行我 |

**开场两段动画**（0:00–0:15，都是程序界面里的真实动作）：

1. **数据灌满屏幕**（0.4–2.8 s）：一条扫描头从上往下走，每行一边写一边亮起，
   内容是十六进制转储——`地址  字节…  ASCII`，而那些字节正是这首歌的英文歌词
   （`world.execute(me);`、`If I’m a circle. Then I will give you my
   circumference.`），所以开屏填满屏幕的"数据"就是歌本身。写满后屏幕中央被
   挖出一个框，浮现标题卡；随后数据整体淡出。
2. **逐项自检、逐项完成**（4.2–11.3 s，15 项）：左边是 BIOS 清单，每一项先
   出现灰色占位 `[      ]`，轮到时变成一条 **6 格检测条**一边填满一边逐字打出
   检查内容，填满的瞬间闪白并定格为 `[  OK  ]`（有两项是 `[ WARN ]`：`dependency
   you -> me not symmetric`、`load memories ... none found`——正是歌词里那两个
   缺口）。右边是 `memory` 面板，字节流持续往下写、写满后滚动；底部是总进度条
   `progress ████░ 87% 13/15 checks`。全部通过后打字出 `$ world.execute(me);`、
   `start...`，倒数 3 格，CRT 展开进入第一段主歌。

小终端（宽度 <78）会自动收起右侧 memory 面板，清单变成滚动窗口；所有动画都是
时间 `t` 的纯函数，拖动进度条看到的画面完全一致。

**配色**：默认磷光绿/青的 90 年代 CRT 终端，每个段落有自己的强调色——
verse2 青、pre1 蓝、chorus1 粉、verse3 品红、pre2 紫、chorus2 冰蓝、bridge
琥珀、build/chant 血红、final 玫瑰、outro 金、shutdown 灰。

**转场**：场景之间用「逐格溶解」叠化（每格按哈希决定何时翻转，约 0.6 s），
像老显示器换画面时的抖动，而不是简单淡入淡出。

---

## ⚠️ 光敏性癫痫警告

第 2:28–2:43 的 EXECUTION 段有强闪烁与高频切换（已限制在 ≤3 Hz），
对闪光敏感者请避免全屏观看，或改用 `--mono` 降低刺激。

---

## 歌词解读

《world.execute(me);》表面上是一首「程序对用户表白」的歌，实际上是一首关于
**爱里的自我客体化**的歌。它的全部修辞都建立在两个双关上：

**1. `execute` = 运行程序 / 执行死刑**

`world.execute(me);` 一行代码，同时是「世界啊，运行我」和「世界啊，处死我」。
歌里反复出现的 `execution` 也同时是「执行」和「处决」——这不是文字游戏，而是
整首歌的论点：**爱到极致时，被爱与被执行是同义词**。所以副歌的
「If I can make you happy / I will run the execution」既是「我会运行这段程序」，
也是「我会为你赴死」。

**2. 说话者是一个自愿被「对象化」的程序**

它用编程和数学的语言描述自己：`dim(P) = 3`（我是三维的一个点）、`C = 2πr`
（我是你半径画出的圆）、`y = sin x, dy/dx = cos x`（我是你函数的一条切线）、
`switch my gender / switch my role`（性别、身份、角色都是可重载的参数）。
它把自己拆成接口、参数、返回值，因为**只有这样才能被对方调用**。
「I can be anything」一段是最极端的：为了对方的需要，它可以变成食物、抗氧化剂、
一只会呼噜的猫、甚至神。

**3. `you` 是 user，是 creator，是 god，是「我存在过的证明」**

歌里的「你」同时是使用者、造物主、神和爱人。程序的存在完全由「你」定义：
`∃ you ⇒ ∃ me`、`you are the proof of my existence`。所以当「你」离开，
`you: <null>`，它就陷入 `isolation`——**存在是关系性的，没有被爱就没有自我**。

**4. 失落、删除与「非法参数」**

中段它被留在孤独里（`You have left me in isolation`），于是去删除「所有无意义
的碎片」（`rm -rf ./pointless/*`），甚至想「删掉我自己，你会不会回来」。
它质问神（`Challenging your god`），得到的回答是 `illegal arguments`——它对
命运提出的参数不合法：**爱不是可以传给神的合法参数**。

**5. EXECUTION 的仪式化**

高潮连喊三遍 `Execution`，再用六种语言数 1 到 6（EIN / DOS / TROIS / NE /
FEM / LIU）。数数把「处决」变成仪式、把「运行」念成咒语；两种语义在这里彻底
合流——倒数结束，程序被执行。

**6. 结尾的不对等**

`Though you are free, I am trapped in lo-o-ove`：你自由，我困在爱里。
最后一行代码是 `me.execute(love);`——它自己执行了自己，进程以
`[Process finished with exit code 0]` 正常退出。**exit 0 是「成功完成」**，
也是这首歌最温柔也最残酷的地方：它认为自己的死是一次成功的运行。

**背景**：Mili《world.execute(me);》收录于 2016 年专辑 *Miracle Milk*，
常被玩家社区解读为《Library of Ruina》中 Angela 的角色曲——一个被创造出来、
被使用、被留下、最终以「爱」为名自我执行的造物。即使不套用游戏背景，它也是
一首把「奉献」推到自我抹除程度的爱之歌：**用机器的语法，说人最不机器的那种感情**。

---

## 版权

音频与歌词版权归 Mili / 原作者所有。本仓库只是粉丝向的终端可视化练习，
不含任何音频再分发（`assets/` 里的文件由用户上传的 mp4 本地转出，仅供本机播放）。
代码可自由修改取用。
