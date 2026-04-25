#!/usr/bin/env python3
"""MK1 Linker — reads vasm vobj files and produces MK1 binary."""

import sys, argparse

def read_vobj(filename):
    with open(filename, 'rb') as f:
        raw = f.read()
    pos = 0

    def byte():
        nonlocal pos
        v = raw[pos]; pos += 1; return v

    def number():
        """Read vobj variable-length number (taddr)."""
        nonlocal pos
        b = raw[pos]; pos += 1
        if b < 128:
            return b
        elif b < 192:
            nbytes = b - 128
            val = 0
            for i in range(nbytes):
                val |= raw[pos] << (i * 8); pos += 1
            return val
        else:
            nbytes = b - 192
            val = -1  # fill with 0xFF
            for i in range(nbytes):
                mask = 0xFF << (i * 8)
                val = (val & ~mask) | (raw[pos] << (i * 8)); pos += 1
            return val

    def string():
        nonlocal pos
        s = b''
        while raw[pos] != 0:
            s += bytes([raw[pos]]); pos += 1
        pos += 1
        return s.decode('ascii', errors='replace')

    assert raw[0:4] == b'VOBJ', "Not a vobj file"
    pos = 4
    flags = byte()
    version = (flags >> 2) & 0x3F
    bpb = number()
    bpt = number()
    cpu = string()
    nsections = number()
    nsymbols = number()

    symbols = []
    for i in range(nsymbols):
        name = string()
        stype = number()
        sflags = number()
        sec_idx = number()
        val = number()
        size = number()
        symbols.append({'name': name, 'section': sec_idx, 'value': val})

    sections = []
    for i in range(nsections):
        sec_name = string()
        sec_attr = string()
        sec_flags = number()
        if version >= 3 and (sec_flags & 0x80):  # ABSOLUTE flag
            sec_addr = number()
        sec_align = number()
        sec_size = number()
        nrelocs = number()
        databytes = number()
        sec_data = bytearray(raw[pos:pos+databytes])
        pos += databytes

        relocs = []
        for j in range(nrelocs):
            rtype = number()
            if rtype >= 128:  # special reloc
                rsize = number()
                if rsize > 0:
                    pos += rsize  # skip special data
                continue
            byteoff = number()
            bitoff = number()
            rsize = number()
            rmask = number()
            addend = number()
            sym_idx = number()
            relocs.append({'byteoff': byteoff, 'addend': addend, 'sym_idx': sym_idx})

        sections.append({'name': sec_name, 'data': sec_data, 'relocs': relocs})

    return symbols, sections

def link(symbols, sections):
    code_idx = data_idx = None
    for i, sec in enumerate(sections):
        if sec['name'] == 'code' and code_idx is None: code_idx = i
        elif sec['name'] == 'data' and data_idx is None: data_idx = i
    if code_idx is None and sections: code_idx = 0

    code = bytearray(sections[code_idx]['data']) if code_idx is not None else bytearray()
    data = bytearray(sections[data_idx]['data']) if data_idx is not None else bytearray()

    # Resolve relocations in code section
    if code_idx is not None:
        for r in sections[code_idx]['relocs']:
            sym_idx = r["sym_idx"]
            if sym_idx == 0:
                val = r["addend"]  # section base
                off = r["byteoff"]
                if off < len(code): code[off] = val & 0xFF
                continue
            sym = symbols[sym_idx - 1]  # 1-based
            # Skip relocations to section base symbols — values already resolved in data
            if sym['name'] in ('code', 'data'):
                continue
            val = sym['value'] + r['addend']
            off = r['byteoff']
            if off < len(code):
                code[off] = val & 0xFF

    return bytes(code), bytes(data)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('-o', '--output', default='a.bin')
    args = ap.parse_args()

    syms, secs = [], []
    for inp in args.inputs:
        s, sc = read_vobj(inp)
        syms.extend(s); secs.extend(sc)

    code, data = link(syms, secs)

    with open(args.output, 'wb') as f:
        f.write(code)
        if data:
            f.write(b'\x00' * (256 - len(code)))
            f.write(data)

    print(f"Code: {len(code)}/256 bytes ({len(code)*100//256}%)")
    if data: print(f"Data: {len(data)}/256 bytes")

if __name__ == '__main__':
    main()
