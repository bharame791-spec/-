import os
from PIL import Image
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out9")
name, n = open(os.path.join(d, "_job.txt")).read().split()
tiles = [Image.open(os.path.join(d, f"_tile-{i}.png")).convert("RGBA") for i in range(int(n))]
out = Image.new("RGBA", (tiles[0].width, sum(t.height for t in tiles)))
y = 0
for t in tiles:
    out.paste(t, (0, y)); y += t.height
if "transparent" not in name:
    out = out.convert("RGB")
out.save(os.path.join(d, name), optimize=True)
for i in range(int(n)):
    os.remove(os.path.join(d, f"_tile-{i}.png"))
