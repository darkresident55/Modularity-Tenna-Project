"""Minimal GameMaker data.win reader: chunks, strings, sprites, TPAG, TXTR, sounds."""
import struct, io, bz2

U = lambda d,o: struct.unpack_from('<I', d, o)[0]
I = lambda d,o: struct.unpack_from('<i', d, o)[0]
H = lambda d,o: struct.unpack_from('<H', d, o)[0]
h = lambda d,o: struct.unpack_from('<h', d, o)[0]
F = lambda d,o: struct.unpack_from('<f', d, o)[0]

class GM:
    def __init__(self, path):
        self.data = open(path,'rb').read()
        d = self.data
        assert d[:4]==b'FORM'
        self.chunks = {}
        off, end = 8, 8+U(d,4)
        while off < end:
            nm = d[off:off+4].decode('latin1'); sz = U(d,off+4)
            self.chunks[nm] = (off+8, sz); off += 8+sz
        self.strings = {}
        if 'STRG' in self.chunks: self._strings()

    def _strings(self):
        d = self.data; base,_ = self.chunks['STRG']
        n = U(d,base)
        for i in range(n):
            p = U(d, base+4+i*4)
            ln = U(d,p)
            # references elsewhere point at the char data (p+4)
            self.strings[p+4] = d[p+4:p+4+ln].decode('utf-8','replace')

    def s(self, ptr):
        return self.strings.get(ptr, '') if ptr else ''

    def plist(self, chunk):
        """Return list of absolute offsets for a standard pointer-list chunk."""
        if chunk not in self.chunks: return []
        d = self.data; base,_ = self.chunks[chunk]
        n = U(d,base)
        return [U(d, base+4+i*4) for i in range(n)]

    # ---------- TPAG ----------
    def tpag(self):
        """abs offset -> dict of texture page item."""
        d = self.data; out = {}
        for i,p in enumerate(self.plist('TPAG')):
            out[p] = dict(idx=i, sx=H(d,p), sy=H(d,p+2), sw=H(d,p+4), sh=H(d,p+6),
                          tx=H(d,p+8), ty=H(d,p+10), tw=H(d,p+12), th=H(d,p+14),
                          bw=H(d,p+16), bh=H(d,p+18), page=h(d,p+20))
        return out

    # ---------- TXTR ----------
    def txtr_entries(self):
        """List of (entry_offset, data_pointer). Data pointer = last uint of entry."""
        ps = self.plist('TXTR')
        if not ps: return []
        step = ps[1]-ps[0] if len(ps)>1 else 8
        d = self.data
        return [(p, U(d, p+step-4), step) for p in ps]

    def txtr_blob(self, i):
        ents = self.txtr_entries()
        p = ents[i][1]
        # blob runs to next blob start (or chunk end)
        starts = sorted(e[1] for e in ents)
        base,size = self.chunks['TXTR']
        nxt = base+size
        for s_ in starts:
            if s_ > p: nxt = s_; break
        return self.data[p:nxt]

    # ---------- SPRT ----------
    def sprites(self):
        d = self.data; out = []
        for p in self.plist('SPRT'):
            o = p
            name = self.s(U(d,o)); o += 4
            w = I(d,o); h_ = I(d,o+4); o += 8
            ml, mr, mb, mt = I(d,o), I(d,o+4), I(d,o+8), I(d,o+12)
            o += 16                       # margins l/r/b/t
            o += 12                       # transparent, smooth, preload
            bbm = U(d,o); o += 4          # bboxmode
            o += 4                        # sepmasks
            ox = I(d,o); oy = I(d,o+4); o += 8
            if I(d,o) == -1:
                o += 4
                sver = U(d,o); stype = U(d,o+4); o += 8
                o += 8                    # playback speed + type
                if sver >= 2: o += 4      # sequence offset
                if sver >= 3: o += 4      # nine slice offset
                if stype != 0:
                    out.append(dict(name=name,w=w,h=h_,ox=ox,oy=oy,frames=[],special=stype,margins=(ml,mr,mb,mt),bbox=bbm))
                    continue
            n = U(d,o); o += 4
            frames = [U(d,o+j*4) for j in range(n)]
            out.append(dict(name=name,w=w,h=h_,ox=ox,oy=oy,frames=frames,special=0,margins=(ml,mr,mb,mt),bbox=bbm))
        return out

    def backgrounds(self):
        d = self.data; out=[]
        for p in self.plist('BGND'):
            name = self.s(U(d,p))
            out.append(dict(name=name, tpag=U(d,p+16)))
        return out

    # ---------- SOND ----------
    def sounds(self):
        ps = self.plist('SOND')
        if not ps: return []
        step = ps[1]-ps[0] if len(ps)>1 else 36
        d = self.data; out=[]
        for p in ps:
            e = dict(name=self.s(U(d,p)), flags=U(d,p+4), type=self.s(U(d,p+8)),
                     file=self.s(U(d,p+12)), effects=U(d,p+16),
                     volume=F(d,p+20), pitch=F(d,p+24),
                     group=I(d,p+28), audio=I(d,p+32), step=step)
            if step >= 40: e['length'] = F(d,p+36)
            out.append(e)
        return out

    def audo(self, i):
        ps = self.plist('AUDO')
        p = ps[i]; ln = U(self.data,p)
        return self.data[p+4:p+4+ln]

    def audo_count(self):
        return len(self.plist('AUDO'))
