"""GameMaker texture decoding: BZip2+QOI ('2zoq') / raw QOI ('fioq') / PNG.

GameMaker uses the ORIGINAL pre-1.0 QOI draft opcodes, not final QOI 1.0:
  QOI_INDEX   00xxxxxx
  QOI_RUN_8   010xxxxx
  QOI_RUN_16  011xxxxx yyyyyyyy
  QOI_DIFF_8  10rrggbb
  QOI_DIFF_16 110rrrrr ggggbbbb
  QOI_DIFF_24 1110rrrr rgggggbb bbbaaaaa
  QOI_COLOR   1111rgba  (one byte per set flag)
Hash is (r ^ g ^ b ^ a) % 64.  Channel order on disk is BGRA.
"""
import struct, bz2


def decode_gm_texture(blob):
    if blob[:4] == b'\x89PNG':
        return ('png', blob)
    if blob[:4] == b'2zoq':
        w, h = struct.unpack_from('<HH', blob, 4)
        return ('qoi', qoi_decode(bz2.decompress(blob[12:]), w, h))
    if blob[:4] == b'fioq':
        w, h = struct.unpack_from('<HH', blob, 4)
        return ('qoi', qoi_decode(blob, w, h))
    raise ValueError('unknown texture magic %r' % blob[:4])


def qoi_decode(data, width=0, height=0):
    assert data[:4] == b'fioq', data[:4]
    w, h = struct.unpack_from('<HH', data, 4)
    if width:
        w, h = width, height
    n = w * h
    out = bytearray(n * 4)
    index = [(0, 0, 0, 0)] * 64
    b = g = r = 0
    a = 255
    p = 12
    o = 0
    end = len(data)
    while o < n * 4 and p < end:
        b1 = data[p]; p += 1
        top = b1 & 0xC0
        run = 0
        if top == 0x00:                                   # INDEX
            b, g, r, a = index[b1]
        elif top == 0x40:                                 # RUN_8 / RUN_16
            if b1 & 0x20:                                 # 011xxxxx -> RUN_16
                run = (((b1 & 0x1F) << 8) | data[p]) + 32; p += 1
            else:                                         # 010xxxxx -> RUN_8
                run = b1 & 0x1F
        elif top == 0x80:                                 # DIFF_8
            b = (b + ((b1 >> 4) & 3) - 2) & 255
            g = (g + ((b1 >> 2) & 3) - 2) & 255
            r = (r + (b1 & 3) - 2) & 255
        else:
            if (b1 & 0xE0) == 0xC0:                       # DIFF_16
                b2 = data[p]; p += 1
                b = (b + (b1 & 0x1F) - 16) & 255
                g = (g + (b2 >> 4) - 8) & 255
                r = (r + (b2 & 0x0F) - 8) & 255
            elif (b1 & 0xF0) == 0xE0:                     # DIFF_24
                b2 = data[p]; b3 = data[p+1]; p += 2
                b = (b + ((((b1 & 0x0F) << 1) | (b2 >> 7)) - 16)) & 255
                g = (g + (((b2 & 0x7C) >> 2) - 16)) & 255
                r = (r + ((((b2 & 0x03) << 3) | ((b3 & 0xE0) >> 5)) - 16)) & 255
                a = (a + ((b3 & 0x1F) - 16)) & 255
            else:                                         # COLOR 1111rgba
                if b1 & 8: b = data[p]; p += 1
                if b1 & 4: g = data[p]; p += 1
                if b1 & 2: r = data[p]; p += 1
                if b1 & 1: a = data[p]; p += 1
        index[(r ^ g ^ b ^ a) & 63] = (b, g, r, a)
        px = bytes((b, g, r, a))   # first channel read is R
        if run:
            cnt = run + 1
            out[o:o + cnt * 4] = px * cnt; o += cnt * 4
        else:
            out[o:o + 4] = px; o += 4
    return (w, h, bytes(out[:n * 4]), p, end)
