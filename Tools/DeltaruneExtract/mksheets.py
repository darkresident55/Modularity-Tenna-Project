"""Pack extracted PNG frame sequences into uniform grid sprite sheets.

Modularity animates 2D art from a grid sheet (spriteSheetColumns / Rows / Fps),
not a folder of frames, so each animation becomes one PNG plus its grid metadata.
Every frame in an extracted sprite folder is already composited onto the sprite's
full canvas, so the grid is uniform and frame N sits at (N % cols, N / cols).

An entry may name a `tail` sprite. Its frames are appended after the main ones so
the hold-loop lives in the same sheet, and SpriteSheetPlayer's `tailLoopFrames`
keeps cycling them once the main run finishes. The TV TIME intro does this: it
plays 164 frames, then flickers between two until something disables it.
"""
import os, json, math
from PIL import Image

DEST = r"C:/Users/sansg/ModularityProjects/Tenna Cosplay and costume Project/Assets"
OUT = os.path.join(DEST, 'Sprites', 'Sheets')
MAX_DIM = 8192

# name, source group folder, fps, optional tail sprite appended after the main run
WANTED = [
    ('spr_dw_tv_time_intro',      'Gameshow', 30.0, 'spr_dw_tv_time_intro_loop'),
    ('spr_tenna_battle',          'Tenna',    12.0, None),
    ('spr_tenna_dance_cabbage',   'Tenna',    20.0, None),
    ('spr_tenna_freakout',        'Tenna',    20.0, None),
    ('spr_tenna_dance_cane',      'Tenna',    20.0, None),
    ('spr_tenna_kick',            'Tenna',    18.0, None),
    ('spr_tenna_t_pose',          'Tenna',    12.0, None),
    ('spr_tenna_snap',            'Tenna',    12.0, None),
    ('spr_tenna_hooray_alt',      'Tenna',    10.0, None),
    ('spr_tenna_grasp_anim',      'Tenna',    10.0, None),
    ('spr_tenna_battle_face',     'Tenna',    10.0, None),
]


def load_frames(group, name):
    src = os.path.join(DEST, 'Sprites', 'Deltarune', group, name)
    if not os.path.isdir(src):
        return []
    files = sorted(f for f in os.listdir(src) if f.endswith('.png'))
    return [Image.open(os.path.join(src, f)).convert('RGBA') for f in files]


os.makedirs(OUT, exist_ok=True)
manifest = {}
for name, group, fps, tail in WANTED:
    frames = load_frames(group, name)
    if not frames:
        print(f"  !! missing {name}")
        continue
    main_count = len(frames)
    tail_count = 0
    if tail:
        tail_frames = load_frames(group, tail)
        if not tail_frames:
            print(f"  !! tail {tail} not found for {name}")
        elif tail_frames[0].size != frames[0].size:
            # A different canvas size would break the uniform grid.
            print(f"  !! tail {tail} is {tail_frames[0].size}, expected {frames[0].size}; skipped")
            for i in tail_frames:
                i.close()
        else:
            frames += tail_frames
            tail_count = len(tail_frames)

    fw = max(i.width for i in frames)
    fh = max(i.height for i in frames)
    n = len(frames)
    cols = max(1, min(n, int(math.ceil(math.sqrt(n * fh / max(fw, 1))))))
    while cols * fw > MAX_DIM and cols > 1:
        cols -= 1
    rows = int(math.ceil(n / cols))
    while rows * fh > MAX_DIM and cols < n:
        cols += 1
        rows = int(math.ceil(n / cols))

    sheet = Image.new('RGBA', (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        sheet.paste(im, ((i % cols) * fw, (i // cols) * fh))
    path = os.path.join(OUT, name + '.png')
    sheet.save(path)
    rel = os.path.relpath(path, os.path.dirname(DEST)).replace(os.sep, '/')
    manifest[name] = dict(sheet=rel, columns=cols, rows=rows, frames=n,
                          mainFrames=main_count, tailFrames=tail_count,
                          tailSprite=tail if tail_count else None,
                          frameWidth=fw, frameHeight=fh, fps=fps,
                          sheetWidth=sheet.width, sheetHeight=sheet.height)
    extra = f"  (+{tail_count} tail)" if tail_count else ""
    print(f"  {name:<30} {n:>4} frames  {fw}x{fh}  grid {cols}x{rows}  sheet {sheet.width}x{sheet.height}{extra}")
    for im in frames:
        im.close()
    sheet.close()

with open(os.path.join(OUT, 'sheets.json'), 'w') as f:
    json.dump(manifest, f, indent=1)
print(f"\nwrote {len(manifest)} sheets -> {OUT}")
