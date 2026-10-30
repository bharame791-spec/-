"""VO alignment without ASR: DP-aligns text phrases to speech segments (split by detected pauses)
by matching character counts to durations. Prints the start/end time of each phrase."""
import re, subprocess, sys
F, TXT = sys.argv[1], sys.argv[2]
text = open(TXT, encoding='utf-8').read()
phr = [p.strip() for p in re.split(r'\.\.\.|[،.:\n]', text) if p.strip()]
out = subprocess.run(['ffmpeg', '-i', F, '-af', 'silencedetect=noise=-32dB:d=0.12', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
seg, t = [], 0.0
for a, b in zip(st, en):
    if a - t > .15: seg.append((t, a))
    t = b
dur_total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', F], capture_output=True, text=True).stdout)
if dur_total - t > .15: seg.append((t, dur_total))
L = [len(re.sub(r'[\sًٌٍَُِّْـ]', '', p)) for p in phr]
r = sum(L) / sum(b - a for a, b in seg)
INF = 1e18; n, m = len(phr), len(seg)
D = [[INF] * (m + 1) for _ in range(n + 1)]; P = [[None] * (m + 1) for _ in range(n + 1)]
D[0][0] = 0
for i in range(n + 1):
    for j in range(m + 1):
        if D[i][j] >= INF: continue
        for a in range(1, 4):
            for b in range(1, 4):
                if i + a > n or j + b > m: continue
                if a > 1 and b > 1: continue
                ch = sum(L[i:i + a]); d = sum(e - s for s, e in seg[j:j + b])
                c = (d - ch / r) ** 2 / max(d, .5) + .35 * (a - 1) + .25 * (b - 1)
                if D[i][j] + c < D[i + a][j + b]:
                    D[i + a][j + b] = D[i][j] + c; P[i + a][j + b] = (i, j)
i, j, groups = n, m, []
while i or j:
    pi, pj = P[i][j]; groups.append((pi, i, pj, j)); i, j = pi, pj
for pi, i, pj, j in reversed(groups):
    s, e = seg[pj][0], seg[j - 1][1]
    tot = sum(L[pi:i]); acc = 0
    for k in range(pi, i):  # split merged phrases proportionally
        ps = s + (e - s) * acc / tot; acc += L[k]; pe = s + (e - s) * acc / tot
        print(f'{ps:6.2f} {pe:6.2f}  {phr[k]}')
