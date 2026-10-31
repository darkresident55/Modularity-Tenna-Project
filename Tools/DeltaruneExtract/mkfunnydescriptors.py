"""Write .png.spritesheet sidecars for the funnytext sheets.

Same rule as the main descriptors: the name must be "<image>.png.spritesheet",
because the inspector resolves a sidecar to its image with replace_extension().
"""
import os, json, datetime

OUT = r"C:/Users/sansg/ModularityProjects/Tenna Cosplay and costume Project/Assets/Sprites/Sheets/FunnyText"
sheets = json.load(open(os.path.join(OUT, 'sheets.json')))
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

for name, m in sorted(sheets.items()):
    cols, fw, fh, n = m['columns'], m['frameWidth'], m['frameHeight'], m['frames']
    L = [
        'LinkedSpriteName = "";',
        'SpriteVersion = 1;',
        f'LastSavedUtc = "{now}";',
        '',
        'ExpectedMinimumModuEngineVersionOrHigher = "";',
        'Expect_Layers = 1;',
        f'Expect_rects = {n};',
        '',
        'Confirmation.StrictValidation = false;',
        '',
        f'// {name}: {n} frame(s), {fw}x{fh} each, packed {cols} across.',
        'info AtlasInfo',
        '{',
        '    rects',
        '    {',
    ]
    for i in range(n):
        L.append(f'        {(i % cols) * fw},{(i // cols) * fh},{fw},{fh};')
    L += ['    }', '', '    names', '    {']
    for i in range(n):
        L.append(f'        {name}_{i:03d};')
    L += ['    }', '', '    scales', '    {']
    for _ in range(n):
        L.append('        1,1;')
    L += ['    }', '}', '', 'info Layers', '{', '}']
    open(os.path.join(OUT, name + '.png.spritesheet'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')

print(f"wrote {len(sheets)} sidecars")
bad = [n for n in sheets if not os.path.exists(os.path.join(OUT, n + '.png'))]
print("sidecars whose image is missing:", bad if bad else "none")
