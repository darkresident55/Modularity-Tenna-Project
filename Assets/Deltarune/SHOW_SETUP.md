# Tenna show: intro, dialogue and animation previews

What was added, and how to wire it in the editor.

## 1. Sprite sheets (new)

Modularity animates 2D art from a grid sheet and never from a folder of loose
frames, so the extracted sequences were packed into sheets in
`Assets/Sprites/Sheets/`:

| sheet | frames | frame size | grid | fps |
|---|---|---|---|---|
| `spr_dw_tv_time_intro` | 166 | 320x240 | 12x14 | 30 |
| `spr_tenna_battle` | 10 | 104x134 | 4x3 | 12 |
| `spr_tenna_dance_cabbage` | 93 | 88x146 | 13x8 | 20 |
| `spr_tenna_freakout` | 81 | 129x152 | 10x9 | 20 |
| `spr_tenna_dance_cane` | 59 | 123x145 | 9x7 | 20 |
| `spr_tenna_kick` | 40 | 138x148 | 7x6 | 18 |
| `spr_tenna_t_pose` | 15 | 131x149 | 5x3 | 12 |
| `spr_tenna_snap` | 5 | 74x120 | 3x2 | 12 |
| `spr_tenna_hooray_alt` | 4 | 119x123 | 3x2 | 10 |
| `spr_tenna_grasp_anim` | 4 | 97x136 | 3x2 | 10 |
| `spr_tenna_battle_face` | 4 | 93x132 | 3x2 | 10 |

Each `.png` has a matching sidecar named `<name>.png.spritesheet`. That exact
name matters: the inspector resolves a sidecar to its image with
`replace_extension()`, so `foo.spritesheet` would resolve to `foo` (no such file)
and the assignment silently fails. It must be `foo.png.spritesheet`.

**You do not use the extracted frame folders for playback.** Those 164 loose PNGs
in `Sprites/Deltarune/Gameshow/spr_dw_tv_time_intro/` are the raw extraction kept
for reference. The engine plays the single packed sheet, and the sidecar tells it
where each frame sits. There is no image-list field to fill in, and nothing to
multi-select.

The intro sheet is 166 frames, not 164: `spr_dw_tv_time_intro_loop`'s two frames
are packed on the end. In game the intro plays out and then flickers between
those two until something disables it, so they live in the same sheet and
`SpriteSheetPlayer.tailLoopFrames` cycles them. The sidecar names them
`spr_dw_tv_time_intro_loop_000/001` so they stand out from the animation frames.

To give any other animation a hold, add a `tail` sprite to its row in
`Tools/DeltaruneExtract/mksheets.py` and re-run it plus `mkdescriptors.py`. The
tail must share the main sprite's canvas size or the grid stops being uniform;
the script checks and warns rather than producing a broken sheet.

`sheets.json` carries the same numbers if you need them in code, including
`mainFrames` and `tailFrames`.

## 2. Scripts (new)

`Assets/Scripts/Runtime/SpriteSheetPlayer.moducpp`
Plays one sheet on the object it is attached to. Fields: `fps`, `loop`,
`playOnBegin`, `frameCount` (leave 0 when a sidecar is assigned), `tailLoopFrames`,
`startAudioClip`, `disableSelfOnFinish`, `enableOnFinish`, `disableOnFinish`.

`tailLoopFrames` is how many frames at the *end* of the sheet keep cycling once
the run finishes, instead of stopping on the last frame. The finish actions still
fire exactly once, at the moment the hold begins, so a fade or handoff triggers on
cue while the flicker carries on. Leave `disableSelfOnFinish` **off** when using
it, or the object switches itself off and the hold is never seen.

`Assets/Scripts/Runtime/TennaShow.moducpp`
The controller: intro handoff, dialogue typing with voice blips, animation
cycling, and the touch zones.

The engine cannot rebind a sprite's texture at runtime (`SetObjectSprite` warns
"cross-sheet image swap not yet wired"), so **each animation needs its own
object**. Switching = enabling one and disabling the rest, which the player
detects and restarts from.

## 3. Wiring

1. Under the Canvas, add one UI Image object per animation, plus one for the
   intro. Name them after their sheet.
2. On each: select `Assets/Sprites/Sheets/<name>.png` in the Project browser and
   click **Use Select** on the object's Texture field. The matching
   `.png.spritesheet` sidecar is picked up automatically and fills in the frame
   table. Then attach `SpriteSheetPlayer` and set `fps` from the table.
3. On the intro object only: set `fps` to **30**, `startAudioClip` to
   `Assets/Audio/Deltarune/Tenna/snd_its_tv_time.wav`, turn `loop` **off**, set
   `tailLoopFrames` to **2**, and leave `disableSelfOnFinish` **off**. That clip
   is 5.53s and the 164 animation frames at 30fps are 5.47s, so picture and sound
   land together, then the hold takes over. Leave `frameCount` at 0 - the sidecar
   reports all 166 and `tailLoopFrames` carves the last two off the end.
   `TennaShow` disables the intro object when it hands over, so nothing else has
   to switch it off.
4. Add two UI Text objects for the dialogue box: a name label and a body label.
5. Attach `TennaShow` to an empty controller object and fill in `introRef`,
   `dialogueTextRef`, `nameTextRef`, `debugMenuRef`, and `animationRefs`
   (the animation objects, in the order you want to cycle them).

`TennaShow` disables every animation and the debug menu at `Begin`, plays the
intro, and swaps to the show when the intro reports finished. Because a tail loop
reports finished the instant the hold starts, set `introHoldSeconds` on
`TennaShow` to however long you want the flicker (and any fade started by the
intro's finish actions) to run before the show takes over. 0 hands off at once.

## 4. Controls

Matching the concept screens:

| input | action |
|---|---|
| tap left edge (upper) | next animation |
| tap left edge (lower) | pause / resume animation |
| tap right edge (upper) | next dialogue line |
| tap right edge (lower) | pause / resume dialogue |
| tap centre | next line (completes the line first, then advances) |
| 2-finger tap | previous line and previous animation |
| 2-finger double tap | reinitialise to line 1 / animation 1 |
| 3-finger double tap | toggle debug menu |

Zone sizes are `sideZoneWidth` and `zoneSplitY` in the inspector.

Desktop keys for testing: arrows (left/right = dialogue, up/down = animation),
`P` pause animation, `O` pause dialogue, `R` reinitialise. Note multi-touch only
reports more than one finger on Android; on desktop `GetTouch` is the mouse, so
the gesture rows above need the phone.

## 5. Starter dialogue

Paste into the `lines` array on `TennaShow` (text / animationRef / typingSpeed):

| text | animationRef |
|---|---|
| `IT'S TV TIME!!!` | `spr_tenna_hooray_alt` |
| `WELCOME, WELCOME, WELCOME! YOU'RE LOOKING AT THE ONE AND ONLY... TENNA!` | `spr_tenna_battle` |
| `AND TRUST ME, FOLKS -- I KNOW TV.` | `spr_tenna_battle_face` |
| `TONIGHT'S SPECIAL GUEST? WHY, IT'S YOU!` | `spr_tenna_grasp_anim` |
| `DON'T BE SHY! GIVE 'EM A WAVE!` | `spr_tenna_snap` |
| `NOW THAT'S WHAT I CALL ENTERTAINMENT!` | `spr_tenna_dance_cane` |
| `WHAT'S THAT? YOU WANT MORE?!` | `spr_tenna_freakout` |
| `THEN LET'S KEEP THIS SHOW ROLLING!` | `spr_tenna_dance_cabbage` |

Leave `animationRef` empty on a line to keep the current animation running.

**Already loaded in the scene:** 14 of Tenna's own lines, pulled from Chapter 3's
string table. `Assets/Deltarune/tenna_lines.txt` holds all 163 that were found if
you want to swap any in.

How they were attributed: STRG interleaves dialogue with GML code-location ids
like `obj_ch3_GSA02_slash_Step_0_gml_461_0`, so the nearest id says which object
spoke a line. Tenna hosts the gameshow rooms, and inside those rooms lines that
carry a portrait code belong to whoever has the portrait (Susie, Ralsei, Lancer)
while Tenna announces without one - so gameshow lines with no portrait code are
his. Control codes (`^1` pauses, `\E` portraits, `&` newlines) are stripped.

## 5c. Typing feel

`prefixAsterisk` puts `* ` in front of every line and hangs the wrap underneath
the text rather than the bullet:

```
* WELCOME back, everyone, to the show
  that'll make you SCREAM at your SCREEN!
```

Lines are pre-wrapped at `wrapColumns` when they start, so the layout never
reflows while characters appear. **Turn the text object's own Wrap off**, or it
wraps the already-wrapped text a second time.

`commaPause` holds after `,` `:` `;` and `sentencePause` after `.` `?`, both
counted in characters so they track the line's typing speed rather than being
wall-clock. At the defaults a punctuation-free line is unaffected and a heavily
punctuated one gains about a second.

The voice blip defaults to `snd_tv_voice_short.wav`. Set **`blipVariants` to 10**
and it picks one of his ten barks per blip, never the same twice in a row. It
derives the names from `blipClip` by inserting `_N` before the extension, which
is exactly how they sit on disk (`snd_tv_voice_short.wav`,
`snd_tv_voice_short_2.wav` ... `_10.wav`), so there is no list to fill in. Point
`blipClip` at any similarly-named set and it works the same. `blipEveryNChars`
controls how busy it sounds.

## 5b. Mouth

Set `mouthRef` to the mouth piece and it rotates between `mouthClosedAngle` and
`mouthOpenAngle` at `mouthFlapsPerSecond` while a line types out, shutting when
the line lands.

Set the mouth object's **Anchor to Bottom Left** (or whichever corner it should
hinge from). The engine rotates a UI element about its geometric centre and the
anchor only affects placement, so the script compensates: each frame it offsets
`ui.position` by `R(angle)*d - d`, where `d` is centre-minus-anchor. The net
effect is the anchor corner stays put and the rest of the mouth swings around it,
which is what you want for a jaw. Verified to pin the corner exactly (0.000000 px
drift) for every anchor across -45 to +90 degrees.

The mouth's authored position is re-read at `Begin`, so nudging it in the editor
between runs is fine - every flap offsets from wherever you left it.

Other show audio pulled alongside the intro: `snd_nes_intro`,
`snd_nes_intro_extended` (6.98s) and `snd_nes_intro_extended_part2` (27.85s) in
`Audio/Deltarune/Tenna/`, plus `snd_boxing_round1..3` (the announcer's "ROUND
ONE!") and `snd_creepyjingle` in `Audio/Deltarune/Show/`.

## 6. Known blocker: scripts do not currently link

Script compilation in this project fails before any of the above can run:

```
PlayerController2D.wrap.obj : error LNK2019: unresolved external symbol Modu_Begin
  Hint: "void __cdecl Modu_Begin(struct ModuScriptContext *,float)"
```

Cause: the generated `<Script>.capi.wrap.cpp` declares the entry points inside an
`extern "C" {` block, but the generated `<Script>.moducpp.gen.c` is compiled as
C++ (`/TP`) without `extern "C"`, so it exports a mangled symbol the wrapper
never asks for.

Fix is in the engine, at `Modularity/src/ModuCPPTranspiler.cpp:6070`:

```cpp
out << "void " << hook.exportName << "(ModuScriptContext* ctx";
```

needs to emit `extern "C"` (same for `Modu_OnInspector`, emitted at line 6083),
or the `.gen.c` needs compiling as C rather than with `/TP`. This is pre-existing
and unrelated to the asset work - the stub `PlayerController2D` fails the same
way.


## 7. Funny text per line

**Every funnytext word is now a sheet**, in `Assets/Sprites/Sheets/FunnyText/` -
51 of them, including the single-frame ones. That means one uniform setup: assign
the `.png`, the matching `.png.spritesheet` sidecar fills the frame table, and
`SpriteSheetPlayer` plays it. No `FrameListPlayer`, no folder paths, no frame
counts to type. Verified by unpacking every sheet through its own sidecar and
comparing to the source frames: 51/51 pixel-identical.

`spr_dw_tv_time_funnytext` is in there too - it is a funnytext by nature but
sorts into the Gameshow group by name, so it would otherwise be easy to miss.

The dialogue block tags 10 of its 14 lines. Create one UI Image per row, **named
exactly as the object column** (`TennaShow` matches the `[Tag]` against the
object's name), and add them all to `funnyTextRefs`.

**The tag is positional.** It fires when typing reaches the spot it sits in, not
when the line starts, so the word pops as Tenna says it:

```
* WELCOME back, everyone, to the [FT_TvTime]show that'll make you SCREAM...
                                 ^ pops here, 33 characters in
```

Put the tag immediately before the word it should land on. Mechanically: tags are
swapped for an invisible sentinel byte before the line is wrapped, so they travel
with their word through the word wrap; afterwards the sentinels are removed and
their landing positions recorded. Doing it after wrapping is what keeps the
positions right once newlines and the hanging indent are inserted, and the
sentinel is excluded from the width measurement so a tagged word does not wrap a
character early. Skipping a line with a tap still fires every word it contained.

| object | sheet | frames | grid | fps | stinger |
|---|---|---|---|---|---|
| `FT_TvTime` | `spr_funnytext_tv_time.png` | 1 | 1x1 | - | `snd_ftext_enter.wav` |
| `FT_Names` | `spr_funnytext_names.png` | 30 | 3x10 | 20 | `snd_ftext_names.wav` |
| `FT_Round1` | `spr_funnytext_round_1.png` | 1 | 1x1 | - | `snd_ftext_bounce.wav` |
| `FT_Flames` | `spr_funnytext_flames.png` | 30 | 3x10 | 20 | `snd_ftext_gunshot.wav` |
| `FT_Stop` | `spr_funnytext_stop.png` | 1 | 1x1 | - | `snd_ftext_woodblock.wav` |
| `FT_FunOMeter` | `spr_funnytext_fun_o_meter.png` | 1 | 1x1 | - | `snd_ftext_vibraphones.wav` |
| `FT_Stars` | `spr_funnytext_stars.png` | 1 | 1x1 | - | `snd_ftext_bounce.wav` |
| `FT_Big` | `spr_funnytext_big.png` | 1 | 1x1 | - | `snd_ftext_woodblock.wav` |
| `FT_KnowTv` | `spr_funnytext_know_tv.png` | 1 | 1x1 | - | `snd_ftext_woodblock.wav` |
| `FT_GrandPrize` | `spr_funnytext_grand_prize.png` | 1 | 1x1 | - | `snd_ftext_prize.wav` |

Per object: assign the sheet, attach `SpriteSheetPlayer`, turn `loop` **off** so
the word plays once and holds, and put the stinger in `startAudioClip`. It fires
on restart, and `TennaShow` restarts the word each time its line comes up, so the
sound lands with the pop. Single-frame words need no fps.

**The stingers are in `Assets/Audio/Deltarune/Show/`**, not beside the art - all
11 `snd_ftext_*` are already extracted, nothing is missing.

A caveat on the pairing: the exact in-game choice is **not** recoverable. The 50
word sprites sit in one contiguous asset-name table in the string data with no
dialogue near them, and the selection happens in bytecode. So these are paired by
meaning. Where a word owns a stinger of the same name the real one is used
(`spr_funnytext_names` -> `snd_ftext_names`); the rest borrow a generic one.
`brother`, `dark_fountain`, `susiezilla` and `toriel` are the other genuine pairs
if you add those words later.

To repack after changing anything, run `Tools/DeltaruneExtract/mkfunnysheets.py`
then `mkfunnydescriptors.py`.

## 8. Gotcha: two folder names

The extractor assigns a sprite to the first group that matches, and the Tenna
test runs before the Gameshow one, so three gameshow-named sprites live under
`Tenna/`:

    spr_gameshow_screen_tenna_run
    spr_gameshow_screen_tenna_peace
    spr_gameshow_screen_tenna_peacefixedAnchor

Their path is `Assets/Sprites/Deltarune/Tenna/<name>/`, not `.../Gameshow/<name>/`.
A path that does not resolve loads no texture and the sprite draws as a blank
bordered quad, which is what a wrong folder here looks like.


## 9. Backdrops per line

A `[BG:Name]` tag swaps the backdrop, matched against an object's name in
`backgroundRefs`. `defaultBackgroundRef` is the one shown the rest of the time
(Tenna BG).

Nothing has to switch it back. `StartLine` restores the default before applying
the new line's tags, so a scene change lasts exactly as long as the lines that
ask for it:

| line | backdrop |
|---|---|
| 8 | default |
| 9 `[BG:TennaRealTV]` | real-world TV |
| 10 `[BG:TennaRealTVSepia]` | real-world TV, sun-faded |
| 11 | default (automatic) |

Two objects to create, both from art already extracted:

| object | sprite | note |
|---|---|---|
| `TennaRealTV` | `Sprites/Deltarune/Gameshow/spr_gameshow_screen_tv.png` | 212x90, the living room and old set |
| `TennaRealTVSepia` | `Sprites/Deltarune/Gameshow/spr_gameshow_screen_tv_sepia.png` | 212x90, washed out with the glow |

Add both to `backgroundRefs`, point `defaultBackgroundRef` at Tenna BG, and leave
the alternates disabled - the script enables whichever the line asks for.

`[BG:...]` rides the same positional trigger as the word sprites, so putting the
tag mid-sentence swaps the backdrop mid-sentence. At the front of the line, as
here, it swaps as the line begins.

## 10. Spawn flourish

Each word sprite pops in and shivers as it lands, matching how the TV TIME logo
arrives. Tunable on the FunnyText tab:

| field | default | what it does |
|---|---|---|
| `popDuration` | 0.22s | length of the scale pop |
| `popOvershoot` | 1.18 | how far past full size it snaps before settling |
| `shakeStrength` | 3.0 px | jitter amplitude at the moment of impact |
| `shakeDuration` | 0.35s | how long the shiver takes to die out |

The curve runs 0.00 -> 1.18 -> 1.00: up past full size through the first half,
easing back down through the second. The shake uses two different frequencies so
it reads as a shiver rather than a clean wobble, decaying to nothing.

The authored size and position are captured when the word appears and restored
when the flourish ends, so the pop never leaves an object at the wrong scale. A
word already mid-pop is restored before a new one starts, which is what stops a
fast line change stranding one at pop size.

A note on line 1 and 2: in game the "TV TIME!" box is its **own** dialogue, not
part of the WELCOME line - the first box ends on the comma, then the next box is
just the word sprite and its `!!`. The block reflects that now.

### Still to do: inline word placement

In the real game the word sprites sit **inside** the sentence and the text flows
around them:

```
* To today's [STAR] contestants!!!
* The [FUN-O-METER]'s still only at 80%!!
```

Right now a tagged word is a separate object that appears at whatever position it
was placed at, so it pops on cue but does not sit in the text run. Closing that
gap means measuring the text up to the tag and moving the sprite there each
frame, which also has to survive the wrap and the hanging indent.


## 11. Use the Lines array, not dialogueBlock

`dialogueBlock` was a workaround for the array arriving with empty text. It has a
hard problem of its own: the inspector's string editor uses a fixed **512-char
buffer**, so editing the field truncates everything past that. It had already
lost six lines and cut one mid-sentence before this was spotted.

The dialogue now lives in the **Lines** array, 16 entries. The longest single
line is 100 characters, so no entry comes near the limit. `dialogueBlock` is
cleared, and the script prefers the array whenever the block is empty.

Do not paste the whole script back into `dialogueBlock` - anything past ~511
characters is silently dropped.

**If the array shows empty text again:** that is the older SubScript bug, not the
truncation one. The two look different - truncation loses the *tail*, that bug
empties *every* entry and the box shows only the bullet. Say so and it gets
diagnosed properly rather than worked around; the block is a poor fallback now
that its own limit is known.
