"""Lyric timeline for Mili - world.execute(me);  (Miracle Milk, 2016, 3:32)

Timings come from the official synced lyric sheet of this album version
(3:31.9, i.e. exactly the length of assets/world-execute-me.m4a) and are
cross-checked against the audio file itself:

  * the song does NOT open with an instrumental intro -- the voice starts at
    0.10 s over the music box ("Switch on the power line"); the full band
    drops in at 15.00 s
  * 15.00 .. 29.71 s is the instrumental break, with the "world.execute(me);"
    hook sung at 16.00 s
  * BPM = 130 (beat 0.4615 s, bar 1.8462 s); the loud body ends ~191.6 s,
    the final whispered "Execution" is at 205.81 s, file ends 211.97 s

Each entry: (t_start, t_end, en, zh)
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
    # ---- verse 1 · 0:00   (voice over the music box; band at 0:15) --------
    ( 0.100,  1.660, "Switch on the power line", "接上电源"),
    ( 1.740,  3.793, "Remember to put on protection", "记得装备好绝缘护具"),
    ( 3.873,  5.411, "Lay down your pieces", "摆好棋子"),
    ( 5.491,  7.366, "And let's begin object creation", "开始吧 对象生成"),
    ( 7.446, 11.015, "Fill in my data parameters initialisation", "输入我的参数 完成初始化"),
    (11.095, 12.826, "Setup our new world", "建好我们的新世界"),
    (12.906, 15.600, "And let's begin the simulation", "然后开始这场模拟游戏"),
    # ---- instrumental break · 0:16   (hook, boot animation) ---------------
    (16.000, 17.900, "world.execute(me);", "「执行我；」"),
    # ---- verse 2 · 0:29 ---------------------------------------------------
    (29.709, 31.036, "If I'm a set of points", "如果我是一组点"),
    (31.116, 33.332, "Then I will give you my dimension", "那么我将献给你我的维度"),
    (33.412, 34.566, "If I'm a circle", "如果我是一个圆"),
    (34.646, 36.987, "Then I will give you my circumference", "那么我将献给你我的圆周"),
    (37.067, 38.516, "If I'm a sine wave", "如果我是一条正弦波"),
    (38.596, 40.626, "Then you can sit on all my tangents", "那你便能坐上我所有的切线"),
    (40.706, 42.266, "If I approach infinity", "如果我趋近于无限"),
    (42.346, 44.372, "Then you can be my limitations", "那么你就是我的极限"),
    # ---- pre-chorus 1 · 0:44 ----------------------------------------------
    (44.452, 45.770, "Switch my current", "切换我的电流"),
    (45.850, 47.592, "To AC to DC", "从交流到直流"),
    (47.672, 49.454, "And then blind my vision", "然后蒙上我的双眼"),
    (49.534, 51.283, "So dizzy so dizzy", "让我头晕目眩"),
    (51.363, 53.145, "Oh we can travel", "我们可以穿越时空"),
    (53.225, 54.975, "To A.D. to B.C.", "从公元后到公元前"),
    (55.083, 56.836, "And we can unite", "然后我们合而为一"),
    (56.916, 59.143, "So deeply so deeply", "深深地 深深地"),
    # ---- chorus 1 · 0:59 --------------------------------------------------
    (59.223, 59.607, "If I can", "如果我能"),
    (59.687, 62.509, "If I can give you all the stimulations", "如果我能给你所有的刺激"),
    (62.589, 63.455, "Then I can", "那么我就能"),
    (63.535, 66.521, "Then I can be your only satisfaction", "那么我就能成为你唯一的慰藉"),
    (66.601, 68.172, "If I can make you happy", "如果我能让你开心"),
    (68.252, 70.004, "I will run the execution", "我就运行这条执行指令"),
    (70.084, 71.684, "Though we are trapped", "尽管我们被困"),
    (71.764, 73.965, "In this strange strange simulation", "在这场异乎寻常的模拟之中"),
    # ---- verse 3 · 1:14 ---------------------------------------------------
    (74.045, 75.342, "If I'm an eggplant", "如果我是一根茄子"),
    (75.422, 77.496, "Then I will give you my nutrients", "那么我将献给你我的养分"),
    (77.576, 79.146, "If I'm a tomato", "如果我是一颗番茄"),
    (79.226, 81.271, "Then I'll give you antioxidants", "那么我将献给你我的抗氧化物"),
    (81.351, 82.753, "If I'm a tabby cat", "如果我是一只花猫"),
    (82.833, 84.998, "Then I will purr for your enjoyment", "那么我将为你咕噜咕噜 只要你喜欢"),
    (85.078, 86.458, "If I'm the only god", "如果我是唯一的神"),
    (86.538, 88.507, "Then you're the proof of my existence", "那么你就是我存在的证明"),
    # ---- pre-chorus 2 · 1:28 ----------------------------------------------
    (88.587, 90.117, "Switch my gender", "切换我的性别"),
    (90.197, 91.647, "To F to M", "从女到男"),
    (92.015, 93.873, "And then do whatever", "然后做任何想做的事"),
    (93.953, 95.385, "From AM to PM", "从清晨到夜晚"),
    (95.465, 97.659, "Oh switch my role", "切换我的角色"),
    (97.739, 99.189, "To S to M", "从施虐者到受虐者"),
    (99.349, 101.394, "So we can enter", "这样我们就可以"),
    (101.474, 103.409, "The trance the trance", "进入那恍惚 出神"),
    # ---- chorus 2 · 1:43 --------------------------------------------------
    (103.489, 104.117, "If I can", "如果我能"),
    (104.197, 107.140, "If I can feel your vibrations", "如果我能感受到你的振动"),
    (107.220, 107.823, "Then I can", "那么我就能"),
    (107.903, 110.820, "Then I can finally be completion", "那么我终于能够变得完整"),
    (110.900, 112.140, "Though you have left", "可是你离开了"),
    (112.220, 113.020, "You have left", "你还是离开了"),
    (113.100, 114.100, "You have left", "你对我说了再见"),
    (114.180, 114.840, "You have left", "你还是离开了"),
    (114.920, 115.700, "You have left", "你对我说了再见"),
    (115.780, 118.020, "You have left me in isolation", "你独留我于孤独之中"),
    # ---- bridge · 1:58 ----------------------------------------------------
    (118.333, 118.899, "If I can", "如果我能"),
    (118.979, 121.648, "If I can erase all the pointless fragments", "如果我能删除那些无用的碎片"),
    (121.728, 122.634, "Then maybe", "那么也许"),
    (122.714, 125.628, "Then maybe you won't leave me so disheartened", "那么也许你便不会离开 留我黯然神伤"),
    (125.708, 128.058, "Challenging your god", "与神作对"),
    (128.661, 133.824, "You have made some illegal arguments", "你给出的是非法参数"),
    # ---- countdown · 2:13   (no words: the build) -------------------------
    # ---- chant · 2:27 -----------------------------------------------------
    (147.660, 151.440, "Execution execution execution execution", "执行 执行 死刑"),
    (151.520, 155.120, "Execution execution execution execution", "执行 执行 死刑"),
    (155.200, 158.820, "Execution execution execution execution", "执行 执行 死刑"),
    (158.900, 161.504, "Ein dos trois ne fem liu", "一 二 三 四 五 六"),
    (161.584, 162.552, "Execution", "死刑"),
    # ---- final chorus · 2:42 ----------------------------------------------
    (162.632, 163.235, "If I can", "如果我能"),
    (163.315, 165.936, "If I can give them all the execution", "如果我能给他们全部的处刑"),
    (166.016, 166.942, "Then I can", "那么我就能"),
    (167.022, 169.744, "Then I can be your only execution", "那么我就能成为你唯一的执行"),
    (169.824, 171.788, "If I can have you back", "只要你能回到我身边"),
    (171.868, 173.563, "I will run the execution", "我就运行这场执行死刑"),
    (173.643, 174.895, "Though we are trapped", "尽管我们被困"),
    (174.975, 177.166, "We are trapped ah", "我们困于其中啊"),
    # ---- outro · 2:57 -----------------------------------------------------
    (177.246, 178.093, "I've studied", "我学会了"),
    (178.173, 180.777, "I've studied how to properly lo-o-ove", "我学会了如何好好去爱"),
    (180.857, 181.821, "Question me", "提问我吧"),
    (181.901, 184.460, "Question me I can answer all lo-o-ove", "提问我吧 爱的问题我全都能答对"),
    (184.540, 188.403, "I know the algebraic expression of lo-o-ove", "就连爱的代数表达式我都知道"),
    (188.483, 189.666, "Though you are free", "虽然你已自由"),
    (189.746, 190.721, "I am trapped", "我仍被困"),
    (190.801, 193.406, "Trapped in lo-o-ove", "困于爱里"),
    # ---- last whisper · 3:25 ----------------------------------------------
    (205.811, 207.400, "Execution", "……死刑。"),
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
