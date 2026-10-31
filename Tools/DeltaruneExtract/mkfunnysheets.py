"""Pack every funnytext word into a sheet so SpriteSheetPlayer can play them all.

The extracted words are a mix: some are folders of frames, some a single PNG.
That means two different players and two different setups per object. Packing
everything - single-frame words included - gives one uniform asset type: assign
the .png, the sidecar fills the frame table, SpriteSheetPlayer plays it.

Also picks up spr_dw_tv_time_funnytext, which is a funnytext by nature but sorts
into the Gameshow group by name.
"""
import os, json, math
from PIL import Image

DEST = r"C:/Users/sansg/ModularityProjects/Tenna Cosplay and costume Project/Assets"
SRC_GROUPS = [("FunnyText", None), ("Gameshow", {"spr_dw_tv_time_funnytext"})]
OUT = os.path.join(DEST, 'Sprites', 'Sheets', 'FunnyText')
MAX_DIM = 8192
DEFAULT_FPS = 20.0


def collect():
    """(name, [frame paths]) for every funnytext word, folder or single image."""
    found = []
    for group, whitelist in SRC_GROUPS:
        base = os.path.join(DEST, 'Sprites', 'Deltarune', group)
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            full = os.path.join(base, entry)
            name = entry[:-4] if entry.endswith('.png') else entry
            if whitelist is not None:
                if name not in whitelist:
                    continue
            elif not name.startswith('spr_funnytext_'):
                continue
            if os.path.isdir(full):
                frames = [os.path.join(full, f) for f in sorted(os.listdir(full)) if f.endswith('.png')]
            elif entry.endswith('.png'):
                frames = [full]
            else:
                continue
            if frames:
                found.append((name, frames))
    return found


os.makedirs(OUT, exist_ok=True)
manifest = {}
for name, paths in collect():
    images = [Image.open(p).convert('RGBA') for p in paths]
    fw = max(i.width for i in images)
    fh = max(i.height for i in images)
    n = len(images)

    cols = max(1, min(n, int(math.ceil(math.sqrt(n * fh / max(fw, 1))))))
    while cols * fw > MAX_DIM and cols > 1:
        cols -= 1
    rows = int(math.ceil(n / cols))
    while rows * fh > MAX_DIM and cols < n:
        cols += 1
        rows = int(math.ceil(n / cols))

    sheet = Image.new('RGBA', (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, im in enumerate(images):
        sheet.paste(im, ((i % cols) * fw, (i // cols) * fh))
    sheet.save(os.path.join(OUT, name + '.png'))

    manifest[name] = dict(columns=cols, rows=rows, frames=n, frameWidth=fw,
                          frameHeight=fh, fps=DEFAULT_FPS,
                          sheetWidth=sheet.width, sheetHeight=sheet.height,
                          animated=n > 1)
    for im in images:
        im.close()
    sheet.close()

with open(os.path.join(OUT, 'sheets.json'), 'w') as f:
    json.dump(manifest, f, indent=1)

animated = sum(1 for m in manifest.values() if m['animated'])
print(f"packed {len(manifest)} funnytext sheets -> Sprites/Sheets/FunnyText/")
print(f"   animated: {animated}    single-frame: {len(manifest) - animated}")
biggest = sorted(manifest.items(), key=lambda kv: -kv[1]['sheetWidth'] * kv[1]['sheetHeight'])[:5]
print("   largest sheets:")
for k, m in biggest:
    print(f"      {k:<40} {m['frames']:>3} frames  {m['sheetWidth']}x{m['sheetHeight']}")
