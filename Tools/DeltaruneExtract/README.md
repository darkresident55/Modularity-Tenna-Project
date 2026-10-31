# Deltarune extraction tools

Pure-Python reader for GameMaker `data.win`, used to pull the Chapter 3 assets in
`Assets/Deltarune/`. Requires Pillow (`pip install Pillow`).

  gm.py       chunk/string/sprite/TPAG/TXTR/sound parsing
  qoi.py      GameMaker texture decoding (BZip2+QOI, original pre-1.0 opcodes)
  extract.py  selects sprites/sounds and writes them into Assets/

Edit `SPRITE_GROUPS` / `SOUND_GROUPS` at the top of extract.py to pull more, then:

    python extract.py --dry     # show what would be extracted
    python extract.py           # write into Assets/

`SRC` and `DEST` are absolute paths at the top of extract.py; update them if the
game install or project moves.
