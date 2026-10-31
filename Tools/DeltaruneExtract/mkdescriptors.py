"""Write .spritesheet sidecars next to the generated grid sheets.

Name them "<image>.png.spritesheet". InspectorWindow resolves a sidecar to its
image with replace_extension(), so "foo.spritesheet" would resolve to "foo",
which does not exist, and the assignment silently fails.

The sidecar lists one rect per REAL frame, so the engine sees exactly the frames
that exist rather than cols*rows (the intro grid is 12x14 = 168 slots for 164
frames, and the 4 padding slots would otherwise show as blank clips).
"""
import os, json, datetime

OUT = r"C:/Users/sansg/ModularityProjects/Tenna Cosplay and costume Project/Assets/Sprites/Sheets"
sheets = json.load(open(os.path.join(OUT, 'sheets.json')))
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

for name, m in sheets.items():
    cols, fw, fh, n = m['columns'], m['frameWidth'], m['frameHeight'], m['frames']
    rects = [((i % cols) * fw, (i // cols) * fh, fw, fh) for i in range(n)]
    L = []
    L.append('LinkedSpriteName = "";')
    L.append('SpriteVersion = 1;')
    L.append(f'LastSavedUtc = "{now}";')
    L.append('')
    L.append('ExpectedMinimumModuEngineVersionOrHigher = "";')
    L.append('Expect_Layers = 1;')
    L.append(f'Expect_rects = {n};')
    L.append('')
    L.append('Confirmation.StrictValidation = false;')
    L.append('')
    tail = m.get('tailFrames', 0)
    main = m.get('mainFrames', n)
    L.append(f'// {name}: {n} frames, {fw}x{fh} each, packed {cols} across at {m["fps"]} fps.')
    if tail:
        L.append(f'// frames 0-{main - 1} are the animation; {main}-{n - 1} are the hold loop')
        L.append(f'// from {m.get("tailSprite")} (set tailLoopFrames = {tail} on SpriteSheetPlayer).')
    L.append('info AtlasInfo')
    L.append('{')
    L.append('    rects')
    L.append('    {')
    for r in rects:
        L.append(f'        {r[0]},{r[1]},{r[2]},{r[3]};')
    L.append('    }')
    L.append('')
    L.append('    names')
    L.append('    {')
    for i in range(n):
        # Tail frames get their own prefix so the hold loop is obvious in the
        # clip list rather than looking like two more animation frames.
        if tail and i >= main:
            L.append(f'        {name}_loop_{i - main:03d};')
        else:
            L.append(f'        {name}_{i:03d};')
    L.append('    }')
    L.append('')
    L.append('    scales')
    L.append('    {')
    for _ in range(n):
        L.append('        1,1;')
    L.append('    }')
    L.append('}')
    L.append('')
    L.append('info Layers')
    L.append('{')
    L.append('}')
    open(os.path.join(OUT, name + '.png.spritesheet'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(f"  {name+'.spritesheet':<44} {n:>4} rects")
print(f"\nwrote {len(sheets)} descriptors")
