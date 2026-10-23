"""Runtime switches shared by the player and the video exporter.

The player always draws both subtitle lines: English inside the frame and the
Chinese translation on the row below it.  The video has no room for that extra
row unless it is asked for (``video.py --zh``), so the intro card has to say
which version you are looking at.
"""

# True  -> the Chinese line below the frame is shown (terminal default)
# False -> English only (the exported film's default: 31 rows, no 32nd row)
ZH = True
