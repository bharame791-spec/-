"""Splits the animated logo GIF into PNG frames (navy original + white version for dark shots),
cropped to the logo's bounding box. The GIF runs at 40 ms/frame = 25 fps, same as the video."""
import sys, numpy as np
from PIL import Image, ImageSequence
src, out, last = sys.argv[1], sys.argv[2], int(sys.argv[3])
frames = [f.convert('RGBA').copy() for f in ImageSequence.Iterator(Image.open(src))][:last + 1]
box = (15, 15, 555, 900)
for i, f in enumerate(frames):
    f = f.crop(box).resize((340, 557), Image.LANCZOS)  # 2x the on-screen size
    f.save(f'{out}/c_{i:03d}.png', optimize=True)
    a = np.array(f); a[..., :3] = (242, 237, 227)
    Image.fromarray(a).save(f'{out}/w_{i:03d}.png', optimize=True)
print(len(frames), 'logo frames', frames[0].crop(box).size)
