# Deltarune Chapter 3 assets (Tenna)

Extracted from the local Chapter 3 install for this costume project.
Source: `chapter3_windows/data.win` (GameMaker archive), `audiogroup1.dat`,
loose `.ogg` files, and `vid/`.

## Contents

Sprites - 435 sprites, 2284 PNG frames, under `Sprites/Deltarune/`:
  - `FunnyText/` - 50 sprites
  - `Gameshow/` - 173 sprites
  - `Tenna/` - 209 sprites
  - `Textbox/` - 3 sprites

Single-frame sprites are written as `<name>.png`. Multi-frame sprites become a
folder `<name>/000.png, 001.png, ...` in animation order.

Audio - 95 files under `Audio/Deltarune/` (69 pulled from the archive and
listed in `sounds.json`, plus 26 the game already ships loose on disk):
  - `Tenna/`  Tenna's TV voice barks (`snd_tv_voice_short*`), power-on/off,
              static, alarm, `snd_tenna_beep_loop`, and `AUDIO_INTRONOISE.ogg`
              (the intro noise, shipped loose by the game).
  - `Text/`   Typing/text blip sounds (`snd_txt*`, `snd_text`).
  - `Show/`   Game-show set: `snd_ftext_*` (the stingers that play under the
              big word sprites), applause, crowd cheers, buzzer, quiz jingles.
  - `Misc/`   Loose dark-world/transition sounds shipped next to the game exe.

Video - `Video/Deltarune/tenna_intro.mp4` (the Chapter 3 Tenna intro).

## Manifests

`sprites.json` - per sprite: group, width/height, origin (`originX`/`originY`,
the pivot the game draws around), frame count, file list, and `margins`
(GameMaker's recorded content bounds as left, right, bottom, top).

`sounds.json` - per sound: group, file path, and the game's default volume.

## Notes on fidelity

Textures in `data.win` are BZip2-compressed QOI using the *original pre-1.0 QOI
draft opcodes* (INDEX / RUN_8 / RUN_16 / DIFF_8 / DIFF_16 / DIFF_24 / COLOR), a
64-entry index hashed `(r ^ g ^ b ^ a) & 63` and updated after every opcode.

The one thing that is easy to get wrong: **the DIFF deltas are two's-complement
signed, not the bias-subtracted values of the published QOI draft.** The draft
computes `field - 16`; GameMaker sign-extends the field, so a field of 0 means
"no change" rather than "-16". Field widths are 2/2/2 bits for DIFF_8, 5/4/4 for
DIFF_16, and 5/5/5/5 (including alpha) for DIFF_24.

Decoding those as biased deltas makes every channel drift in fixed steps. That is
not merely a colour shift: a drifted value can XOR-hash into the same index slot
as fully transparent, displacing it, so later INDEX+RUN pairs that should paint
an empty atlas row instead paint a solid coloured band clean across the page,
through unrelated sprites. This matches UndertaleModLib/Util/QoiConverter.cs.

Verification:

  - all 33 texture pages decode to exactly their declared byte and pixel counts;
  - the Deltarune SOUL decodes to exactly (255, 0, 0, 255);
  - 408 of 411 auto-bounded sprites (99.3%) reproduce GameMaker's own recorded
    content bounds exactly; the 3 exceptions have content *smaller* than their
    recorded box, which is benign - corruption enlarges content, never shrinks it;
  - non-binary alpha across all pages is 2.5%, all of it genuine soft artwork.

Frames are then clipped to the recorded bounds, which is lossless (the margins are
the union of every frame's real content) and strips any packer edge padding.

Audio is copied byte-for-byte out of the archive (no re-encoding); extensions are
set from each blob's actual magic bytes, so some clips the game lists as `.ogg`
are really WAV and are named accordingly.

These are Toby Fox / Deltarune assets, kept here for a personal costume build.
