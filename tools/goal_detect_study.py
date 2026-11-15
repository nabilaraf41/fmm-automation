import subprocess, sys, numpy as np
V = sys.argv[1]
x0, y0, x1, y1 = 300, 34, 640, 100            # scoreboard strip (2340x1080 frames)
L, R, NAB = (440, 40, 482, 96), (560, 40, 606, 96), (318, 45, 398, 92)
fps = 4
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", V, "-vf", f"fps={fps},crop={x1-x0}:{y1-y0}:{x0}:{y0},format=gray",
                      "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, y1 - y0, x1 - x0).astype(np.int16)
cut = lambda f, b: f[b[1]-y0:b[3]-y0, b[0]-x0:b[2]-x0]
# reference "Nab" tag = the most common look of that area (median frame) -> scoreboard is on screen when it matches
ref = np.median(np.stack([cut(f, NAB) for f in fr[len(fr)//4: 3*len(fr)//4: 4]]), axis=0)
on = np.array([np.abs(cut(f, NAB) - ref).mean() < 12 for f in fr])
stable, events = {}, []
for i in range(len(fr) - 6):
    if not on[i: i + 6].all():          # scoreboard visible for 1.5 s
        continue
    for side, box in (("L", L), ("R", R)):
        cur = cut(fr[i], box)
        if side not in stable:
            stable[side] = cur; continue
        if np.abs(cur - stable[side]).mean() > 15 and max(np.abs(cut(fr[i+k], box) - cur).mean() for k in range(1, 6)) < 5:
            events.append((round(i / fps, 1), "scored" if side == "L" else "conceded"))
            stable[side] = cur
print(events)
