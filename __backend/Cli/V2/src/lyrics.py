"""Lyric timeline for Mili - world.execute(me);  (Miracle Milk, 2016, 3:32)

Timings were derived from the audio itself:
  * BPM = 130  (beat 0.4615 s, bar 1.8462 s), downbeat of verse 1 lands on 15.00 s
  * verse 1 = 8 bars  15.00 .. 29.77
  * verse 2 = 8 bars  29.77 .. 44.62
  * pre-chorus 1 / chorus 1 / verse 3 / pre-chorus 2 / chorus 2 ...
  * loud section ends 191.6, whisper "Execution" at 205.0, file ends 211.97

Each entry: (t_start, t_end_or_None, en, zh)
If t_end is None the next line's start is used.
"""

BPM = 130.0
BEAT = 60.0 / BPM          # 0.46154
BAR = BEAT * 4            # 1.84615
DURATION = 211.97
V1_START = 15.0

# (t0, t1, key, chapter_en, chapter_zh, accent-key)
SECTIONS = [
    (0.00,   15.00, "intro",    "POWER ON",          "开机",        "phos"),
    (15.00,  29.77, "verse1",   "OBJECT CREATION",    "对象生成",    "phos"),
    (29.77,  44.62, "verse2",   "MATHEMATICS",        "数学自白",    "cyan"),
    (44.62,  59.54, "pre1",     "ALTERNATING",        "电流与时空",  "blue"),
    (59.54,  74.31, "chorus1",  "STIMULATION",        "刺激与满足",  "pink"),
    (74.31,  88.92, "verse3",   "I CAN BE ANYTHING",  "万物皆我",    "magenta"),
    (88.92, 103.54, "pre2",     "SWITCH",             "切换",        "violet"),
    (103.54, 118.15, "chorus2", "VIBRATION",          "振动与离别",  "ice"),
    (118.15, 133.10, "bridge",  "ILLEGAL ARGUMENTS",  "非法参数",    "amber"),
    (133.10, 147.90, "build",   "EXECUTION PENDING",  "执行倒计时",  "red"),
    (147.90, 162.73, "chant",   "EXECUTION",          "执行死刑",    "red"),
    (162.73, 177.27, "final",   "THE ONLY EXECUTION", "唯一的执行",  "rose"),
    (177.27, 191.60, "outro",   "ALGEBRA OF LOVE",    "爱的代数式",  "gold"),
    (191.60, 207.00, "shutdown", "TERMINATED",        "进程终止",    "grey"),
    (207.00, DURATION, "endcard", "EXIT 0",           "结束",        "grey_dim"),
]

LINES = [
    # ---- verse 1 ---------------------------------------------------------
    (15.000, None, "Switch on the power line", "接上电源"),
    (16.850, None, "Remember to put on protection", "记得装备好绝缘护具"),
    (18.690, None, "Lay down your pieces", "摆好棋子"),
    (20.540, None, "And let's begin object creation", "开始吧 对象生成"),
    (22.380, None, "Fill in my data parameters initialisation", "输入我的参数 完成初始化"),
    (26.080, None, "Setup our new world", "建好我们的新世界"),
    (27.920, 29.77, "And let's begin the simulation", "然后开始这场模拟游戏"),
    # ---- verse 2 ---------------------------------------------------------
    (29.770, None, "If I'm a set of points", "如果我是一组点"),
    (31.620, None, "Then I will give you my dimension", "那么我将献给你我的维度"),
    (33.460, None, "If I'm a circle", "如果我是一个圆"),
    (35.310, None, "Then I will give you my circumference", "那么我将献给你我的圆周"),
    (37.150, None, "If I'm a sine wave", "如果我是一条正弦波"),
    (39.000, None, "Then you can sit on all my tangents", "那你便能坐上我所有的切线"),
    (40.850, None, "If I approach infinity", "如果我趋近于无限"),
    (42.690, 44.62, "Then you can be my limitations", "那么你就是我的极限"),
    # ---- pre chorus 1 ----------------------------------------------------
    (44.620, None, "Switch my current", "切换我的电流"),
    (46.460, None, "To AC to DC", "从交流到直流"),
    (48.310, None, "And then blind my vision", "然后蒙上我的双眼"),
    (50.150, None, "So dizzy so dizzy", "让我头晕目眩"),
    (52.000, None, "Oh we can travel", "我们可以穿越时空"),
    (53.850, None, "To A.D. to B.C.", "从公元后到公元前"),
    (55.690, None, "And we can unite", "然后我们合而为一"),
    (57.540, 59.54, "So deeply so deeply", "深深地 深深地"),
    # ---- chorus 1 --------------------------------------------------------
    (59.540, None, "If I can", "如果我能"),
    (61.380, None, "If I can give you all the stimulations", "如果我能给你所有的刺激"),
    (63.230, None, "Then I can", "那么我就能"),
    (65.080, None, "Then I can be your only satisfaction", "那么我就能成为你唯一的慰藉"),
    (66.920, None, "If I can make you happy", "如果我能让你开心"),
    (68.770, None, "I will run the execution", "我就运行这条执行指令"),
    (70.620, None, "Though we are trapped", "尽管我们被困"),
    (72.460, 74.31, "In this strange strange simulation", "在这场异乎寻常的模拟之中"),
    # ---- verse 3 ---------------------------------------------------------
    (74.310, None, "If I'm an eggplant", "如果我是一根茄子"),
    (76.150, None, "Then I will give you my nutrients", "那么我将献给你我的养分"),
    (78.000, None, "If I'm a tomato", "如果我是一颗番茄"),
    (79.850, None, "Then I'll give you antioxidants", "那么我将献给你我的抗氧化物"),
    (81.690, None, "If I'm a tabby cat", "如果我是一只花猫"),
    (83.540, None, "Then I will purr for your enjoyment", "那么我将为你咕噜咕噜 只要你喜欢"),
    (85.380, None, "If I'm the only god", "如果我是唯一的神"),
    (87.230, 88.92, "Then you're the proof of my existence", "那么你就是我存在的证明"),
    # ---- pre chorus 2 ----------------------------------------------------
    (88.920, None, "Switch my gender", "切换我的性别"),
    (90.770, None, "To F to M", "从女到男"),
    (92.620, None, "And then do whatever", "然后做任何想做的事"),
    (94.460, None, "From AM to PM", "从清晨到夜晚"),
    (96.310, None, "Oh switch my role", "切换我的角色"),
    (98.150, None, "To S to M", "从施虐者到受虐者"),
    (100.000, None, "So we can enter", "这样我们就可以"),
    (101.850, 103.54, "The trance the trance", "进入那恍惚 出神"),
    # ---- chorus 2 + breakdown -------------------------------------------
    (103.540, None, "If I can", "如果我能"),
    (105.380, None, "If I can feel your vibrations", "如果我能感受到你的振动"),
    (107.230, None, "Then I can", "那么我就能"),
    (109.080, None, "Then I can finally be completion", "那么我终于能够变得完整"),
    (110.920, None, "Though you have left", "可是你离开了"),
    (112.420, None, "You have left", "你还是离开了"),
    (113.385, None, "You have left", "你对我说了再见"),
    (114.350, None, "You have left", "你还是离开了"),
    (115.315, None, "You have left", "你对我说了再见"),
    (116.280, 118.15, "You have left me in isolation", "你独留我于孤独之中"),
    # ---- bridge ----------------------------------------------------------
    (118.150, None, "If I can", "如果我能"),
    (120.000, None, "If I can erase all the pointless fragments", "如果我能删除那些无用的碎片"),
    (123.690, None, "Then maybe", "那么也许"),
    (125.540, None, "Then maybe you won't leave me so disheartened", "那么也许你便不会离开 留我黯然神伤"),
    (129.540, None, "Challenging your god", "与神作对"),
    (131.380, 133.10, "You have made some illegal arguments", "你给出的是非法参数"),
    # ---- chant -----------------------------------------------------------
    (147.900, None, "Execution execution execution execution", "执行 执行 死刑"),
    (151.590, None, "Execution execution execution execution", "执行 执行 死刑"),
    (155.280, None, "Execution execution execution execution", "执行 执行 死刑"),
    (158.970, None, "Ein dos trois ne fem liu", "一 二 三 四 五 六"),
    (161.660, 162.73, "Execution", "死刑"),
    # ---- final chorus ----------------------------------------------------
    (162.730, None, "If I can", "如果我能"),
    (164.570, None, "If I can give them all the execution", "如果我能给他们全部的处刑"),
    (166.420, None, "Then I can", "那么我就能"),
    (168.270, None, "Then I can be your only execution", "那么我就能成为你唯一的执行"),
    (170.120, None, "If I can have you back", "只要你能回到我身边"),
    (171.960, None, "I will run the execution", "我就运行这场执行死刑"),
    (173.810, None, "Though we are trapped", "尽管我们被困"),
    (175.650, 177.27, "We are trapped ah", "我们困于其中啊"),
    # ---- outro verse -----------------------------------------------------
    (177.270, None, "I've studied", "我学会了"),
    (178.580, None, "I've studied how to properly lo-o-ove", "我学会了如何好好去爱"),
    (182.190, None, "Question me", "提问我吧"),
    (183.500, None, "Question me I can answer all lo-o-ove", "提问我吧 爱的问题我全都能答对"),
    (185.810, None, "I know the algebraic expression of lo-o-ove", "就连爱的代数表达式我都知道"),
    (188.730, None, "Though you are free", "虽然你已自由"),
    (189.660, None, "I am trapped", "我仍被困"),
    (190.580, 192.60, "Trapped in lo-o-ove", "困于爱里"),
    # ---- last whisper ----------------------------------------------------
    (205.000, 207.20, "Execution", "……死刑。"),
]


def _resolve():
    out = []
    n = len(LINES)
    for i, (t0, t1, en, zh) in enumerate(LINES):
        if t1 is None:
            t1 = LINES[i + 1][0] - 0.06 if i + 1 < n else t0 + 2.0
        out.append((t0, t1, en, zh))
    return out


_L = _resolve()
_L.sort(key=lambda e: e[0])


def line_at(t):
    """Return (en, zh, t0, t1, age, remain) for the line active at time t."""
    lo, hi = 0, len(_L) - 1
    idx = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if _L[mid][0] <= t:
            idx = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if idx < 0:
        return None
    e = _L[idx]
    if t > e[1]:
        return None
    return (e[2], e[3], e[0], e[1], t - e[0], e[1] - t)


def section_at(t):
    """Return the SECTIONS entry active at t."""
    cur = SECTIONS[0]
    for s in SECTIONS:
        if t >= s[0]:
            cur = s
        else:
            break
    return cur
