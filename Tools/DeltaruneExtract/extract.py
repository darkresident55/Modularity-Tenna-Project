import sys, os, re, json, shutil, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gm import GM
from qoi import decode_gm_texture
from PIL import Image

SRC  = r"C:/Users/sansg/Downloads/Archive/Very Linuxy Drive Things/KernalTest/games/Deltarune/chapter3_windows"
DEST = r"C:/Users/sansg/ModularityProjects/Tenna Cosplay and costume Project/Assets"
DRY  = '--dry' in sys.argv

# ---- what to pull, and where it lands -------------------------------------
SPRITE_GROUPS = [
    ("Tenna",     lambda n: 'tenna' in n.lower()),
    ("FunnyText", lambda n: n.startswith('spr_funnytext_')),
    ("Textbox",   lambda n: n.startswith('spr_textbox_')),
    ("Gameshow",  lambda n: n.startswith(('spr_quiz_', 'spr_gameshow_', 'spr_dw_tv_'))),
]
SOUND_GROUPS = [
    ("Tenna", re.compile(r'^snd_(tenna_|tv_|tvturnoff)')),
    ("Text",  re.compile(r'^snd_(txt|text$)')),
    ("Show",  re.compile(r'^snd_(ftext_|applause|crowd_cheer|buzzerwrong|tm_quiz_|stardrop|scorecollect|bell($|_)|moss_fanfare)')),
]

g = GM(os.path.join(SRC, 'data.win'))
tp = g.tpag()
sprites = g.sprites()

# assign each sprite to the first matching group
chosen, seen = collections.defaultdict(list), set()
for s in sprites:
    n = s['name']
    if n.startswith('spr_ja_') or n in seen:
        continue
    for grp, test in SPRITE_GROUPS:
        if test(n):
            chosen[grp].append(s); seen.add(n); break

print("=== SPRITES ===")
tot_spr = tot_frm = 0
for grp, _ in SPRITE_GROUPS:
    lst = chosen[grp]; f = sum(len(s['frames']) for s in lst)
    tot_spr += len(lst); tot_frm += f
    print(f"  {grp:<10} {len(lst):>4} sprites  {f:>5} frames")
print(f"  {'TOTAL':<10} {tot_spr:>4} sprites  {tot_frm:>5} frames")

sounds = g.sounds()
snd_chosen, sseen = collections.defaultdict(list), set()
for s in sounds:
    if s['name'] in sseen:
        continue
    for grp, rx in SOUND_GROUPS:
        if rx.match(s['name']):
            snd_chosen[grp].append(s); sseen.add(s['name']); break
print("=== SOUNDS ===")
for grp, _ in SOUND_GROUPS:
    print(f"  {grp:<10} {len(snd_chosen[grp]):>4}")
print(f"  TOTAL      {sum(len(v) for v in snd_chosen.values()):>4}")

if DRY:
    for grp, _ in SPRITE_GROUPS:
        print(f"\n-- {grp} sample:", [s['name'] for s in chosen[grp][:6]])
    sys.exit()

# ---- pass 1: group every needed frame by texture page ---------------------
tasks = collections.defaultdict(list)          # page -> [(key, tpag entry)]
for grp, _ in SPRITE_GROUPS:
    for s in chosen[grp]:
        for i, fp in enumerate(s['frames']):
            e = tp.get(fp)
            if e:
                tasks[e['page']].append(((grp, s['name'], i), e))

crops = {}
for page in sorted(tasks):
    if page < 0:
        continue
    kind, res = decode_gm_texture(g.txtr_blob(page))
    w, h, px = res[0], res[1], res[2]
    img = Image.frombytes('RGBA', (w, h), px)
    for key, e in tasks[page]:
        crops[key] = img.crop((e['sx'], e['sy'], e['sx'] + e['sw'], e['sy'] + e['sh'])), e
    img.close()
    print(f"  page {page:>2} decoded ({w}x{h}) -> {len(tasks[page])} frames")

# ---- pass 2: compose + write ---------------------------------------------
manifest = {}
for grp, _ in SPRITE_GROUPS:
    for s in chosen[grp]:
        name, nf = s['name'], len(s['frames'])
        if nf == 0:
            continue
        base = os.path.join(DEST, 'Sprites', 'Deltarune', grp)
        outdir = os.path.join(base, name) if nf > 1 else base
        os.makedirs(outdir, exist_ok=True)
        written = []
        for i in range(nf):
            got = crops.get((grp, name, i))
            if not got:
                continue
            sub, e = got
            canvas = Image.new('RGBA', (max(s['w'], 1), max(s['h'], 1)), (0, 0, 0, 0))
            if (e['tw'], e['th']) != (e['sw'], e['sh']) and e['tw'] and e['th']:
                sub = sub.resize((e['tw'], e['th']), Image.NEAREST)
            canvas.paste(sub, (e['tx'], e['ty']))
            # Clip to GameMaker's own recorded content bounds. The atlas can carry
            # packer padding outside a sprite's real extents; margins are the union
            # box across every frame, so this never touches genuine artwork.
            if s.get('bbox') == 0 and s.get('margins'):
                ml, mr, mb, mt = s['margins']
                if 0 <= ml <= mr < canvas.width and 0 <= mt <= mb < canvas.height:
                    clipped = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
                    clipped.paste(canvas.crop((ml, mt, mr + 1, mb + 1)), (ml, mt))
                    canvas = clipped
            fn = os.path.join(outdir, (f"{i:03d}.png" if nf > 1 else f"{name}.png"))
            canvas.save(fn)
            written.append(os.path.relpath(fn, DEST).replace(os.sep, '/'))
        manifest[name] = dict(group=grp, width=s['w'], height=s['h'],
                              originX=s['ox'], originY=s['oy'], margins=s.get('margins'),
                              frames=len(written), files=written)

# ---- sounds ---------------------------------------------------------------
grp_files = {1: os.path.join(SRC, 'audiogroup1.dat')}
grp_gm = {}
def audio_blob(s):
    if s['group'] == 0:
        return g.audo(s['audio'])
    path = grp_files.get(s['group'])
    if not path or not os.path.exists(path):
        return None
    if s['group'] not in grp_gm:
        grp_gm[s['group']] = GM(path)
    return grp_gm[s['group']].audo(s['audio'])

snd_manifest = {}
for grp, _ in SOUND_GROUPS:
    outdir = os.path.join(DEST, 'Audio', 'Deltarune', grp)
    os.makedirs(outdir, exist_ok=True)
    for s in snd_chosen[grp]:
        try:
            blob = audio_blob(s)
        except Exception as ex:
            print(f"  !! {s['name']}: {ex}"); continue
        if not blob:
            # streamed from a loose file on disk
            loose = os.path.join(SRC, s['file'])
            if os.path.exists(loose):
                shutil.copy2(loose, os.path.join(outdir, os.path.basename(loose)))
                snd_manifest[s['name']] = dict(group=grp, source='loose')
            continue
        ext = '.ogg' if blob[:4] == b'OggS' else '.wav' if blob[:4] == b'RIFF' else '.bin'
        fn = os.path.join(outdir, s['name'] + ext)
        open(fn, 'wb').write(blob)
        snd_manifest[s['name']] = dict(group=grp, file=os.path.relpath(fn, DEST).replace(os.sep, '/'),
                                       volume=round(s['volume'], 3), embedded=True)

os.makedirs(os.path.join(DEST, 'Deltarune'), exist_ok=True)
with open(os.path.join(DEST, 'Deltarune', 'sprites.json'), 'w') as f:
    json.dump(manifest, f, indent=1)
with open(os.path.join(DEST, 'Deltarune', 'sounds.json'), 'w') as f:
    json.dump(snd_manifest, f, indent=1)
print(f"\nwrote {len(manifest)} sprites, {len(snd_manifest)} sounds")
