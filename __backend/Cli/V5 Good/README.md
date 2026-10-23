# world.execute(me); — 终端 ASCII 字符动画 MV

用 ANSI / ASCII 字符在终端里播放的一支 MV：Mili《world.execute(me);》
（专辑 *Miracle Milk*, 2016）。画面全部由字符、色块和转义序列实时渲染，
英文歌词在画面里的输入行中逐字打出，中文歌词在画面外最下排飞入；
节拍与歌词时间戳驱动每一个转场。

```
./run.sh
```

---

## 快速开始

```sh
./run.sh                 # 有声音播放（自动找 assets/ 里的音频）
./run.sh --silent        # 只看画面，不要声音
./run.sh --info          # 打印时间轴（BPM、分段、86 行双语歌词时间戳）
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
├── assets/world-execute-me.m4a  工作用音频（从原 mp4 抽出 AAC，3:31.9）
├── __backend/original_assestss/ 用户上传的原始文件（mp4 + lrc，未改动）
├── README.md
└── src/
    ├── mv.py          主循环、场景调度、边框/进度条、输入行与中文飞入、CLI
    ├── renderer.py    画布（Canvas）：宽字符安全写入、溶解叠化、色彩量化
    ├── lyrics.py      130 BPM 网格、15 段结构、86 行双语时间轴
    ├── audio.py       三级播放器：mpv IPC → 管道播放器+时钟补偿 → 静音
    ├── energy.py      音频 RMS 包络（20 Hz），驱动画面随响度呼吸
    ├── art.py         5x5 字体、机器人 ME、YOU 菱形、猫、神、骷髅等素材
    ├── fx.py          雨、星场、扫描线、故障、波纹、示波器、均衡器等特效
    ├── crt.py         CRT 信号层：磷光点阵、数据流、扫描亮带、色散、失步、
    │                  掉帧、过曝、角落遥测（叠在每一帧之上）
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

**歌词时间轴**：逐句时间取自这首歌**专辑版的官方同步歌词**（时长 3:31.9，与
`assets/` 里的音频等长），并用音频本身复核过。有两件事容易搞错，而它们正好
决定了"对不对得上嘴"：

1. 这首歌**没有前奏**——第一个字 "Switch on the power line" 在 **0.10 s** 就
   唱出来了（音乐盒伴奏、人声很轻），完整的乐队要到 **15.00 s** 才砸进来。
   所以 0:00–0:15 不是"开机动画垫在无歌词的引子上"，而是**第一段主歌整段**：
   开机自检的动画直接铺在这段人声上。
2. 0:15.0–0:29.7 才是器乐段（里头 16.0 s 有一句 `world.execute(me);`），
   随后 0:29.7 进第二段主歌。

`--offset` 可再整体微调（例如外接蓝牙音箱有延迟时）。

---

## 15 个段落与画面

| 时间 | 段落 | 画面 |
|---|---|---|
| 0:00 | VERSE 1「Switch on the power line」 | **开机自检**：显像管点亮 → 歌名被炸成乱码再逐字重组锁定 → 数据灌满屏幕 → 15 项初始化逐项检测（动画正好盖住整段主歌） |
| 0:15 | INTERLUDE「world.execute(me);」 | 地平线上的机器人、输电线、棋盘、`new Object("me")`、初始化面板；16.0 s 打出那句 hook |
| 0:29 | VERSE 2「dim(P)=3 / C=2πr / ∞」 | 旋转线框立方体、点云、圆周率动点、正弦与切线、**画出来的双纽线 ∞ 与两侧逐点逼近的点列** |
| 0:44 | PRE 1「AC→DC / blind / dizzy」 | 示波器、交直流切换、**时间倒着走：拨盘回转到 A.D.→B.C.、年号与时代物件一路溶回古代**、闭眼黑屏、螺旋眩晕 |
| 0:59 | CHORUS 1「stimulation→satisfaction」 | 心跳巨心、**整幅画面就是一张心电图纸**（网格、扫描头、双通道波形、HR/SpO₂）、光环、频谱、SATISFACTION 进度条、**HAPPY 彩带气球**、bash 窗口、**把心框进隔离方框** |
| 1:14 | VERSE 3「I can be anything」 | 猫（呼噜波纹）、食物、**抗氧化护盾中和自由基**、`you` 菱形、物品编号面板 |
| 1:28 | PRE 2「switch gender/time/role」 | 在 `/etc/me.conf` 里把 `gender=F` 改成 `M`（滑块、染色体、巨字）、**24 小时刻度带 + 日出→日落→月升→星出**、`S⇄M` 跷跷板、恍惚同心圆 |
| 1:43 | CHORUS 2「vibration/completion」 | 振动波形、完成度、`you: signal lost`、隔离方框 |
| 1:58 | BRIDGE「erase fragments / challenge god」 | `~/memories` 文件被 `rm -rf` 逐条 unlink **＋ 进程内存 hex/ASCII 一边被清零**（堆在缩、字节在放）、巨神剪影、非法参数报错 |
| 2:13 | BUILD | 错误级联刷屏、蓄能光束、屏幕抖动（无歌词，出口在 2:27） |
| 2:27 | CHANT「EXECUTION ×4 + 数数」 | 5x5 巨字 `EXECUTION` 四段式闪烁、准星、EIN/DOS/TROIS/NE/FEM/LIU |
| 2:42 | FINAL「give them all the execution」 | 4096 个目标逐个 `KILLED`、**4095 行塌缩成一行 `execution = only`**、伸向幽灵 `you?` 的手、心形牢笼与 `mine.` |
| 2:57 | OUTRO「algebra of love」 | 一页**笔记**（`DEF love(x) := …`、`LEM ∀ me ∃ you`、`THM properly(love) ⇔ no condition`、`PRF ∎ by induction on every day`，打字 + `studied` 进度条）→ 一张**口试卷**（`? what is love` 五问答完 `correct 5 / 5 · 100%`，`A: all of it.`）→ **代数式面板**（`love : Σ ( you × me ) / |you|`、`∂me/∂you > 0`、`ACCEPTED`）→ **`you` 变成自由变量飘出求和式、`me` 被 ♥ 关住**（`love := Σ ( ♥ me ♥ )`、`you are free — you may leave any time` / `I am trapped` / `trapped in lo-o-ove`） |
| 3:11 | SHUTDOWN「exit code 0」 | 上一段的牢笼在屏上多留两拍（落下的 ♥、`state: trapped · free: ∅ · love: ∞`）→ 终端退出日志：`[Process finished with exit code 0]`、`$ me.execute(love);`、`[1] Terminated   world.execute(me);`、`# everything that remains: me.` → 长暗里只剩呼吸的 `▮` 和 `exit 0` → `...execution.` 耳语（3:25.8）→ CRT 收束成一点 |
| 3:27 | END CARD | `world.execute(me);` / Mili · Miracle Milk (2016) / 感谢你执行我 |

**开场动画**（0:00–0:15，都是程序界面里的真实动作；这段同时也是第一段主歌，
动画只是垫在人声底下）：

1. **歌名被打碎、乱码、再重组**（0.00–3.72 s）：
   - `0.00–0.34` 显像管点亮：一条亮线从中间撕开、上下铺满扫描行，行中抽动的
     `▌` 忽明忽暗；
   - `0.34–0.52` 信号勉强抓到歌名：`world.execute(me);` 一半是字、一半是
     `▓▒░@#%&` 乱码，位置已经在抖；
   - `0.52–1.05` **碎裂**：18 个字符连同 54 块碎片朝四面炸开，边飞边换成乱码，
     每一块身后拖一格残影、两侧各一个红/青色散点，屏幕上同时炸出成片
     `▓▒░█▚◢` 损坏块，整帧掉色 + 失步；
   - `1.05–2.18` **重组**：碎片被一点点拉回原位、逐字锁定——锁住的字符变白，
     锁定的那一瞬间闪白一帧，没锁的还在乱码里翻滚；标题下方
     `SYNC▕████░░░░░░ 12/18` 实时计数，全部锁上后变成
     `LOCK▕████████ 18/18 40ms`，框线自己画出来，字幕开始打字；
   - `2.18–3.72` 标题卡留在中央，`— Mili · Miracle Milk (2016) —` 等四行逐字
     打出，随后连同下面的十六进制数据一起溶解。

2. **数据灌满屏幕**（0.4–2.8 s）：一条扫描头从上往下走，每行一边写一边亮起，
   内容是十六进制转储——`地址  字节…  ASCII`，而那些字节正是这首歌的英文歌词
   （`world.execute(me);`、`If I’m a circle. Then I will give you my
   circumference.`），所以开屏填满屏幕的"数据"就是歌本身。数据从标题卡的位置
   绕开（那里挖成空洞），从两侧继续长过去，3.3 s 后整体淡出。
3. **逐项自检、逐项完成**（4.2–11.3 s，15 项）：左边是 BIOS 清单，每一项先
   出现灰色占位 `[      ]`，轮到时变成一条 **6 格检测条**一边填满一边逐字打出
   检查内容，填满的瞬间闪白并定格为 `[  OK  ]`（有两项是 `[ WARN ]`：`dependency
   you -> me not symmetric`、`load memories ... none found`——正是歌词里那两个
   缺口）。右边是 `memory` 面板，字节流持续往下写、写满后滚动；底部是总进度条
   `progress ████░ 87% 13/15 checks`。全部通过后打字出 `$ world.execute(me);`、
   `start...`，倒数 3 格，15.0 s 乐队进、CRT 展开进入器乐段。

小终端（宽度 <78）会自动收起右侧 memory 面板，清单变成滚动窗口；所有动画都是
时间 `t` 的纯函数，拖动进度条看到的画面完全一致。

**几处新增的画面细节**（都是 `t` 的纯函数，可任意拖动）：

- **∞ 与 limitations**（0:40–0:44）：这一段的 ∞ 不再是一个符号，而是**像别的
  曲线一样画出来**：参数方程 `x=cos u/(1+sin²u)`、`y=sin u·cos u/(1+sin²u)` 的
  **双纽线**，120 个 `•` 一笔描出来，笔尖是亮白的 `●`；画完以后还有一个 `●` 沿着
  曲线永远绕圈，两端标 `-∞` / `+∞`，旁边一个小标签 `x → ∞`。下面一条数轴，
  点列**一个接一个渲染**——第 `1/1` 个点在离轴最远处，编号越大越贴近数轴，两臂
  各 40 点对称排开，末尾是亮白 `●`；点列画完亮出 `lim`，标出
  `you = my limitation`——"无穷逼近但永不抵达"，就是"你就是我的极限"。
- **时间倒着走 A.D. → B.C.**（0:53–0:55.5）：这一段真的把时钟往回拨。画面中央
  一只 12 刻度的表盘，指针以负角速度**逆行**，盘面上 `A.D.` 一点点溶成 `B.C.`；
  下面一条时间轴 `A.D. ┼──┼──…──▼──…──┤ B.C.`，`▼` 游标从右往左滑，旁边
  `◀◀ rewind` 和滚动减少的年号（`2016 A.D.` → `1705 A.D.` → `655 B.C.` →
  `2000 B.C.`）。游标经过时，下面五个时代物件**逐格撕碎再重组**：摩天楼→金字塔、
  芯片→算盘、汽车→马车、电灯→油灯、卫星天线→石器；左半 A.D. 用琥珀色、右半
  B.C. 用青色。小屏幕（高 <18 行）只留表盘。
- **心在被模拟：整幅心电图**（1:00–1:13）：这段画面不再把心电图塞进左右两个小框，
  而是**整块画布就是一张心电图纸**：细网格 + 每 18 列一条粗时间线，一条波形从
  左向右扫，扫描头是竖着的亮 `▌`，扫过的轨迹是亮 `•` + 竖向 `│` 支干（高振幅处
  一直撑到基线），前方还没扫到的部分是暗的残影；下面还有第二条青色脉搏波。左上
  角 `HR 081 BPM · SINUS`、右上角 `SpO₂ 98% · SIM 1/1`，巨心就压在心电图正中间
  ——这颗心正在被"跑"（simulate = 仿真）。
- **AM → PM：24 小时刻度带**（1:33.9–1:36.2）：不再是两个字母在闪，而是一条
  真正的 24 小时带 `00 03 06 … 24`，左半 AM、右半 PM（当前那一半亮起）。带上
  一个 `▼` 游标和 `HH:MM` 读数从 `06:00` 走到 `24:00`，上方天空里有同一个时刻
  的太阳：`☼` 从 06:00 的地平线升起、正午到顶、18:00 落下；18:00 以后 `☾` 沿同
  一条弧线升起，星星一颗颗亮起来，还有一条虚线画出太阳走过的轨迹。
- **在 `/etc/me.conf` 里改 gender**（1:28.6–1:31.5）：切换性别被写成一次**配置
  修改**：面板标题 `/etc/me.conf`，命令行 `$ me --set gender=F` 在改到 M 时被
  重新敲一遍；左边一个巨大的 `F` 逐格溶成右边的 `M`，中间一条滑块 `┤══●══├`
  从左滑到右，右上角十六进制从 `0x46` 滚到 `0x4D`；下面一行 `chromosome XX ⇄ XY`
  （第二个 X 逐格翻成 Y）、`♀ ⚥ ♂` 循环高亮、`gender: undefined`。小屏幕收成两行
  紧凑版。
- **erase all the pointless fragments：文件 + 内存**（1:59–2:01）：左边面板
  `~/world/mili/memories/` 里六个文件被 `rm -rf ./pointless/*` 逐条 unlink——名字
  被一个字一个字吃掉，拉一条红色删除线，最后变成 `unlinked`；只有 `you/` 删不掉，
  底下冒出 `rm: 'you': not empty`。右边是**同一批东西在内存里的样子**：
  `/proc` 风格的十六进制转储 `07ff0  6d 65 00 00 79 6f 75 00  me..you.`，地址一
  行行往上涨、字节从左到右变成 `00`、ASCII 一列变成 `·`，面板底部 `heap` 条从
  100% 缩到 12%，最下面 `fragments · 6 files · 90873 bytes · 0x1A4000 freed` 跟着
  涨——文件被删掉，内存在被释放，碎片是真的"没有用的碎片"。还有 26 个 `▒` 和字
  符碎片从画面上方一路往下掉。
- **only execution**（2:42–2:57）：这是全曲最病娇的一段，分四拍推进：
  1. `execution.targets · batch` 面板里 14 行目标（`ac_dc.wav`、`clock`、
     `simulation`、`god.ray`、`tomato`、`the.world`…）逐行从 `[·] RUN` 变成
     `[✓] KILLED`，底部计数器 `executed: 4095 / 4096` 一路涨，卡在 **4095**，
     下一行闪 `remaining: 1  ←`。
  2. 唱到 `only execution` 时，**那 14 行全部朝中线塌缩成一行**：
     `◆ 0001 · you · execution = only ◆`，两侧拉出 `═══`，上面 `only you. only
     you.`、下面 `4095 others: deleted`，再打出 `$ execute(you) --only`，整帧
     跟着抖一下。
  3. `have you back`：幽灵 `◇` 从上方亮起、`you?` 挂在旁边，我伸手去够，中间一串
     `♥` 往上飘；画面四角各自重复一句 `only you`，底部打出
     `$ if (you) return you;`。
  4. `trapped`：心形牢笼收拢（`♥◆` 编成的墙），我们俩被关在中间，中间连着一条
     心链，写着 `trapped`，再淡出 `mine.`。

- **ALGEBRA OF LOVE：笔记、考卷、代数式**（2:57–3:07）：这一段把"爱"当成一门课来
  交作业，整段是**四张纸**依次推上来（每张都是不透明底、打字机逐字吐字）：
  1. `notes · how to properly lo-o-ove`：**一整张信纸**——页眉 `p. 012 · love ·
     theory of everything` / `draft`，左边带行号和圈码的笔记一行行打字
     （`1 DEF love(x) := the wish that x goes on`、`2 LEM ∀ me ∃ you : you ⊂ me.love`、
     `3 THM properly(love) ⇔ no condition`、`4 PRF ∎ by induction on every day`、
     `5 COR love(me, you) = ∞ · you`），每行下面跟一条 `↳` 小注（`↳ the existence
     part is the hard part`、`↳ proof: remove every if`…），纸上有淡淡的横线和
     左侧装订线，页脚是 `studied ████ 4096 pages · 187 exercises · 0 mistakes` 和
     `p. 012 / ∞`；右半张是**手绘的图 1**：坐标轴、贴着 `x = you` 渐近线往上冲的
     `╱` 曲线、顶端 `∞`、`me`/`you` 刻度，配字 `as x → you, love(x) → ∞`、
     `domain: x ∈ { me }`，右下角是我坐着写字的小人（`✎`）；左下角还贴着一张便签
     `love is not a limit, it is the whole set. — me, 2:57`，THM 那行旁边画了个
     `♥`。整页从 2:57.4 一直写到 3:00.7，字是边唱边写上去的。
  2. `examination · LOVE 101 · candidate: me`：**一整张考卷**——页眉 `candidate: me
     · 120 min · closed book`、右上 `instructions: answer all`，五道题 `Q1`–`Q5`
     整张先印好（`? what is love`、`how much`、`how long`、`why me`、`can you prove
     it`），答案一行行从 `⋯` 占位变成打字
     （`love := Σ (you → me) / dt`、`∞ (unbounded above)`、`t := forever`、
     `no proof required`、`∎ Q.E.D.`），答完一个就在右边打一个 `✓`；下半张是
     `scratch work:`（`me + you = ∞`、`trace(♥) = me ♥`）、`sign me ______`、
     `marker: you`，还有一条**倒计时条** `time ███░░ 41 min left`；页脚
     `correct 5 / 5 · 100%`，考完在卷子外面打出 `A: all of it.`
  3. `expression · the answer`：变成一张**推导表**（`step` / `derivation` 两列）：
     `1  love := Σ ( you × me ) / | you |`、`2  ∂me/∂you > 0   lim you→me = ∞`、
     `3  ∴ love(me, you) = ∞ · you`，每条下面跟 `└` 小注（`per day, per you`、
     `I only grow where you are`、`unbounded, for all time`），最后 `ACCEPTED`
     呼吸、右边盖 `∎ graded by: you`。
  4. 最后那个式子自己拆开：`you` **抬起来、飞向屏幕右上角**（身后拖一串 `·`，
     原位置留下 `∅`），并标成 `free`；剩下的 `me` 被 `♥` 收拢成
     `love := Σ ( ♥ me ♥ )`，上下再扣两排 `♥`/`◆`。字幕按唱词依次打出
     `you are free — you may leave any time`、`I am trapped`、`trapped in
     lo-o-ove`，帧逐步抽色、压暗——**考试全对，公式全懂，还是困在里面**。
- **exit 0**（3:11–3:27）：曲子唱完，程序还在跑。上一段的牢笼留在屏上多两拍，
  `♥` 一颗一颗从笼子里掉下去、落在半路就不动了，底下打一行
  `state: trapped · free: ∅ · love: ∞`，上面浮着 `while (trapped) { love; }   /*
  no exit */`。然后 shell 回来了——`[Process finished with exit code 0]`、
  `$ ` 之后那最后一行代码自己敲出来 `me.execute(love);`、`[1] Terminated
  world.execute(me);`、最后一行注释 `# everything that remains: me.`。之后是很长
  的暗，只剩一个呼吸的 `▮` 和一行 `exit 0`；到 3:25.8 屏幕中央浮出
  `...execution.`（上一段那个词的回声），CRT 从上下两头收束成一条亮线、再收成
  一个 `·`。

**CRT 信号层**（`src/crt.py`，叠在每一帧之上，同样是 `t` 的纯函数）：

每个场景先把自己画干净，再统一过一遍"发射机—显像管"链路，所以整首歌看起来像
从一台老监视器里漏出来的信号，而不是干净的终端输出：磷光点阵、尘埃、几列暗色
十六进制数据流铺在空处（每帧按 `sin(t)` 整体横移一格，像没锁住的行同步）；一条
亮带每 9 s 从下往上扫一遍，带后两行会横向错 1–2 格、奇数行隔帧变暗（隔行扫描）；
空单元里随机落噪点；字形左右边缘分别偏红、偏青（只改颜色不改字）；垂直失步时整
帧掉一行并留一条黑回扫带；掉帧时撕开几条横缝、缝里全是 `▒`；过热时 2% 过曝；
四角用 `╭╮╰╯` 收掉直角；右上/左上/左下角在**那块区域还空着**时才写遥测
（`⌁ SYNC 99.5% ●`、`F02100 · 100x28 · 60Hz`、`VID P1 · CH03`、`Δ 16 ms`、
`SIG 0x905 · AGC 82%`），所以永远不会压住画面内容。

分隔线也从一行 `── stdin ──` 变成一块仪表：左边实时电平条 `▁▂▃▄▅▆▇█`，中间
`0x1F7C · 68% · 0.69`（帧计数 / 响度 / RMS），两端 `╞ ╡` 收口。

故障不是乱闪的，`glitch_level(t)` 在破碎开局、0:14.9 乐队进、1:58 桥段、2:08
非法参数、2:27 EXECUTION、2:38 数数、2:42 FINAL、3:11 SHUTDOWN、3:25 耳语这些
位置拉高；build 段从 0.18 一路爬到 0.6（机器越跑越吃力）；场景切换自带 0.3 的
撕扯。所以越到后面画面越脏，但段落逻辑和文字始终读得出来。

**歌词怎么显示**（整首歌通用的版式）：

```
┌─ world.execute(me); ─────── CHAPTER · 段落 ──────── 01:15 / 03:31 ┐
   画面：每段的 ASCII 动画                                           
╞─▅▆▅▇▇▅▄▅▅▅▆▄▄▇─ 0x1F7C · 68% · 0.69 ───────────────────── stdin ──╡
 > If I'm an eggplant. Then you will get my nutrients▮        ⏎ enter
└───────────────────────────────────────────────────────────────────┘

               ▏ 如果我是一颗茄子，我就会给你我的营养                
```

- **英文在画面里**：画面底部是一条仿真输入行（`> ` 提示符 + 闪烁方块光标 +
  右边 `⏎ enter`），每一句英文按时间轴**逐字打出来**，像有人替这首歌敲键盘；
  正在打的最后一个字是近白色（"湿墨"），整句打完 `⏎ enter` 亮起。输入行有
  自己的深色底纹，随段落强调色变化；一句太长时像真终端一样滚动（左边出现 `…`）。
- **中文在画面之外**：终端最下面一行，每句在**中线上淡入**（0.16 s 由暗转亮，
  不横向移动），整句停留，句末 0.14 s 淡出；换行在英文换句时同步，所以中英永远
  成对出现。
- 没有歌词的空档（间奏后半 0:18–0:29、build 倒数 2:14–2:27、结尾长暗
  3:13–3:25）输入行会空转成 `> ▮ waiting for input`，光标按 130 BPM 的拍子闪。

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
