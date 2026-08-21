#!/usr/bin/env python3
"""
Parser ELF básico: headers, sections, symbols, relocations, dynamic.
"""
import sys
import struct
import argparse


ELF_MAGIC = b'\x7fELF'


class ELFParseError(Exception):
    pass


def parse_elf(filepath: str) -> dict:
    with open(filepath, 'rb') as f:
        data = f.read()

    if not data.startswith(ELF_MAGIC):
        raise ELFParseError("Não é um arquivo ELF válido")

    # ELF header
    ei_class = data[4]  # 1=32-bit, 2=64-bit
    ei_data = data[5]   # 1=little, 2=big
    ei_version = data[6]
    ei_osabi = data[7]

    if ei_class == 1:
        fmt = '<' if ei_data == 1 else '>'
        ehdr_fmt = fmt + 'HHIIIIIHHHHHH'
        ehdr_size = 52
    else:
        fmt = '<' if ei_data == 1 else '>'
        ehdr_fmt = fmt + 'HHIQQQIHHHHHH'
        ehdr_size = 64

    ehdr = struct.unpack(ehdr_fmt, data[16:16+ehdr_size])
    if ei_class == 1:
        (e_type, e_machine, e_version, e_entry, e_phoff, e_shoff,
         e_flags, e_ehsize, e_phentsize, e_phnum, e_shentsize,
         e_shnum, e_shstrndx) = ehdr
    else:
        (e_type, e_machine, e_version, e_entry, e_phoff, e_shoff,
         e_flags, e_ehsize, e_phentsize, e_phnum, e_shentsize,
         e_shnum, e_shstrndx) = ehdr

    # Section headers
    sections = []
    for i in range(e_shnum):
        offset = e_shoff + i * e_shentsize
        if ei_class == 1:
            shdr_fmt = fmt + 'IIIIIIIIII'
            shdr = struct.unpack(shdr_fmt, data[offset:offset+40])
            (sh_name, sh_type, sh_flags, sh_addr, sh_offset,
             sh_size, sh_link, sh_info, sh_addralign, sh_entsize) = shdr
        else:
            shdr_fmt = fmt + 'IIQQQQIIQQ'
            shdr = struct.unpack(shdr_fmt, data[offset:offset+64])
            (sh_name, sh_type, sh_flags, sh_addr, sh_offset,
             sh_size, sh_link, sh_info, sh_addralign, sh_entsize) = shdr
        sections.append({
            'index': i,
            'name_offset': sh_name,
            'type': sh_type,
            'flags': sh_flags,
            'addr': sh_addr,
            'offset': sh_offset,
            'size': sh_size,
            'link': sh_link,
            'info': sh_info,
            'addralign': sh_addralign,
            'entsize': sh_entsize,
        })

    # Section name string table
    shstrtab = sections[e_shstrndx]
    strtab_data = data[shstrtab['offset']:shstrtab['offset'] + shstrtab['size']]

    for sec in sections:
        name_end = strtab_data.find(b'\x00', sec['name_offset'])
        sec['name'] = strtab_data[sec['name_offset']:name_end].decode('utf-8', errors='replace')

    # Program headers
    phdrs = []
    for i in range(e_phnum):
        offset = e_phoff + i * e_phentsize
        if ei_class == 1:
            phdr_fmt = fmt + 'IIIIIIII'
            phdr = struct.unpack(phdr_fmt, data[offset:offset+32])
            (p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align) = phdr
        else:
            phdr_fmt = fmt + 'IIQQQQQQ'
            phdr = struct.unpack(phdr_fmt, data[offset:offset+56])
            (p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align) = phdr
        phdrs.append({
            'index': i,
            'type': p_type,
            'flags': p_flags,
            'offset': p_offset,
            'vaddr': p_vaddr,
            'paddr': p_paddr,
            'filesz': p_filesz,
            'memsz': p_memsz,
            'align': p_align,
        })

    # Symbols (from .symtab and .dynsym)
    symbols = []
    for sec in sections:
        if sec['type'] in (2, 11):  # SHT_SYMTAB=2, SHT_DYNSYM=11
            strtab_sec = sections[sec['link']]
            strtab = data[strtab_sec['offset']:strtab_sec['offset'] + strtab_sec['size']]
            for i in range(sec['size'] // sec['entsize']):
                sym_offset = sec['offset'] + i * sec['entsize']
                if ei_class == 1:
                    sym_fmt = fmt + 'IIIBBH'
                    sym = struct.unpack(sym_fmt, data[sym_offset:sym_offset+16])
                    (st_name, st_value, st_size, st_info, st_other, st_shndx) = sym
                else:
                    sym_fmt = fmt + 'IBBHQQ'
                    sym = struct.unpack(sym_fmt, data[sym_offset:sym_offset+24])
                    (st_name, st_info, st_other, st_shndx, st_value, st_size) = sym

                bind = st_info >> 4
                st_type = st_info & 0xF
                vis = st_other & 3

                name_end = strtab.find(b'\x00', st_name)
                name = strtab[st_name:name_end].decode('utf-8', errors='replace') if st_name else ''

                symbols.append({
                    'index': i,
                    'name': name,
                    'value': st_value,
                    'size': st_size,
                    'bind': bind,
                    'type': st_type,
                    'visibility': vis,
                    'shndx': st_shndx,
                    'section': sec['name'],
                })

    # Dynamic section
    dynamic = []
    for sec in sections:
        if sec['type'] == 6:  # SHT_DYNAMIC
            for i in range(sec['size'] // sec['entsize']):
                dyn_offset = sec['offset'] + i * sec['entsize']
                if ei_class == 1:
                    dyn_fmt = fmt + 'ii'
                    d_tag, d_val = struct.unpack(dyn_fmt, data[dyn_offset:dyn_offset+8])
                else:
                    dyn_fmt = fmt + 'qq'
                    d_tag, d_val = struct.unpack(dyn_fmt, data[dyn_offset:dyn_offset+16])
                dynamic.append({'tag': d_tag, 'val': d_val})

    return {
        'header': {
            'class': 'ELF32' if ei_class == 1 else 'ELF64',
            'endian': 'little' if ei_data == 1 else 'big',
            'type': e_type,
            'machine': e_machine,
            'entry': e_entry,
            'phoff': e_phoff,
            'shoff': e_shoff,
            'flags': e_flags,
            'ehsize': e_ehsize,
            'phentsize': e_phentsize,
            'phnum': e_phnum,
            'shentsize': e_shentsize,
            'shnum': e_shnum,
            'shstrndx': e_shstrndx,
        },
        'sections': sections,
        'segments': phdrs,
        'symbols': symbols,
        'dynamic': dynamic,
    }


def print_elf(elf: dict, verbose: bool = False):
    h = elf['header']
    print(f"ELF Header:")
    print(f"  Class: {h['class']}")
    print(f"  Endian: {h['endian']}")
    print(f"  Type: {h['type']}")
    print(f"  Machine: {h['machine']}")
    print(f"  Entry: 0x{h['entry']:X}")
    print(f"  PH offset: 0x{h['phoff']:X}, count: {h['phnum']}")
    print(f"  SH offset: 0x{h['shoff']:X}, count: {h['shnum']}")

    print(f"\nSections ({len(elf['sections'])}):")
    print(f"  {'Idx':>3} {'Name':<20} {'Type':>6} {'Flags':>8} {'Addr':>16} {'Off':>10} {'Size':>10}")
    for s in elf['sections']:
        print(f"  {s['index']:>3} {s['name']:<20} {s['type']:>6} {s['flags']:>8} 0x{s['addr']:>12X} 0x{s['offset']:>8X} {s['size']:>10}")

    if verbose:
        print(f"\nSegments ({len(elf['segments'])}):")
        for p in elf['segments']:
            print(f"  {p['index']:>2} type={p['type']} flags=0x{p['flags']:X} vaddr=0x{p['vaddr']:X} off=0x{p['offset']:X} filesz=0x{p['filesz']:X} memsz=0x{p['memsz']:X}")

        print(f"\nSymbols ({len(elf['symbols'])}):")
        for sym in elf['symbols'][:50]:
            bind_str = ['LOCAL', 'GLOBAL', 'WEAK'][sym['bind']] if sym['bind'] < 3 else str(sym['bind'])
            type_str = ['NOTYPE', 'OBJECT', 'FUNC', 'SECTION', 'FILE', 'COMMON', 'TLS'][sym['type']] if sym['type'] < 7 else str(sym['type'])
            print(f"  {sym['index']:>4} {bind_str:<6} {type_str:<8} 0x{sym['value']:>12X} {sym['size']:>6} {sym['section']:<20} {sym['name']}")

        if len(elf['symbols']) > 50:
            print(f"  ... e mais {len(elf['symbols']) - 50} símbolos")

        print(f"\nDynamic entries ({len(elf['dynamic'])}):")
        for d in elf['dynamic']:
            print(f"  tag=0x{d['tag']:X} val=0x{d['val']:X}")


def main():
    parser = argparse.ArgumentParser(description='Parser ELF')
    parser.add_argument('file', help='Arquivo ELF')
    parser.add_argument('-v', '--verbose', action='store_true', help='Saída detalhada')
    args = parser.parse_args()

    try:
        elf = parse_elf(args.file)
        print_elf(elf, args.verbose)
    except ELFParseError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()