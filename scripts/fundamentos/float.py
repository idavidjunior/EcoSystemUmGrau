#!/usr/bin/env python3
"""
Visualizador IEEE 754 interativo: bits ↔ valor, operações, casos especiais.
"""
import sys
import struct
import argparse


SPECIAL_CASES_32 = {
    0x00000000: '+0.0',
    0x80000000: '-0.0',
    0x7F800000: '+inf',
    0xFF800000: '-inf',
    0x7FC00000: 'qNaN',
    0xFFC00000: '-qNaN',
    0x7F800001: 'sNaN',
    0x3F800000: '1.0',
    0xBF800000: '-1.0',
    0x3F000000: '0.5',
    0x40000000: '2.0',
    0x40400000: '3.0',
    0x40800000: '4.0',
    0x00000001: 'min subnormal (~1.4e-45)',
    0x007FFFFF: 'max subnormal (~1.18e-38)',
    0x00800000: 'min normal (~1.18e-38)',
    0x7F7FFFFF: 'max normal (~3.4e38)',
}

SPECIAL_CASES_64 = {
    0x0000000000000000: '+0.0',
    0x8000000000000000: '-0.0',
    0x7FF0000000000000: '+inf',
    0xFFF0000000000000: '-inf',
    0x7FF8000000000000: 'qNaN',
    0xFFF8000000000000: '-qNaN',
    0x3FF0000000000000: '1.0',
    0xBFF0000000000000: '-1.0',
    0x3FE0000000000000: '0.5',
    0x4000000000000000: '2.0',
    0x4008000000000000: '3.0',
    0x4010000000000000: '4.0',
}


def parse_float32(bits: int) -> dict:
    sign = (bits >> 31) & 1
    exp = (bits >> 23) & 0xFF
    mant = bits & 0x7FFFFF

    if exp == 0:
        if mant == 0:
            cls = 'zero'
            val = -0.0 if sign else 0.0
        else:
            cls = 'subnormal'
            val = struct.unpack('>f', struct.pack('>I', bits))[0]
    elif exp == 0xFF:
        if mant == 0:
            cls = 'infinity'
            val = float('-inf') if sign else float('inf')
        elif mant & 0x400000:
            cls = 'quiet NaN'
            val = float('nan')
        else:
            cls = 'signaling NaN'
            val = float('nan')
    else:
        cls = 'normal'
        val = struct.unpack('>f', struct.pack('>I', bits))[0]

    unbiased = exp - 127 if exp != 0 else -126
    return {
        'bits': f'0x{bits:08X}',
        'binary': format(bits, '032b'),
        'sign': sign,
        'exponent': exp,
        'mantissa': mant,
        'biased_exp': exp,
        'unbiased_exp': unbiased,
        'class': cls,
        'value': val,
        'special': SPECIAL_CASES_32.get(bits),
    }


def parse_float64(bits: int) -> dict:
    sign = (bits >> 63) & 1
    exp = (bits >> 52) & 0x7FF
    mant = bits & 0xFFFFFFFFFFFFF

    if exp == 0:
        if mant == 0:
            cls = 'zero'
            val = -0.0 if sign else 0.0
        else:
            cls = 'subnormal'
            val = struct.unpack('>d', struct.pack('>Q', bits))[0]
    elif exp == 0x7FF:
        if mant == 0:
            cls = 'infinity'
            val = float('-inf') if sign else float('inf')
        elif mant & 0x8000000000000:
            cls = 'quiet NaN'
            val = float('nan')
        else:
            cls = 'signaling NaN'
            val = float('nan')
    else:
        cls = 'normal'
        val = struct.unpack('>d', struct.pack('>Q', bits))[0]

    unbiased = exp - 1023 if exp != 0 else -1022
    return {
        'bits': f'0x{bits:016X}',
        'binary': format(bits, '064b'),
        'sign': sign,
        'exponent': exp,
        'mantissa': mant,
        'biased_exp': exp,
        'unbiased_exp': unbiased,
        'class': cls,
        'value': val,
        'special': SPECIAL_CASES_64.get(bits),
    }


def float_to_bits32(f: float) -> int:
    return struct.unpack('>I', struct.pack('>f', f))[0]


def float_to_bits64(f: float) -> int:
    return struct.unpack('>Q', struct.pack('>d', f))[0]


def next_after(x: float, direction: float) -> float:
    import math
    return math.nextafter(x, direction)


def ulp(x: float) -> float:
    import math
    if math.isnan(x) or math.isinf(x) or x == 0.0:
        return float('nan')
    return abs(math.nextafter(x, math.inf) - x)


def main():
    parser = argparse.ArgumentParser(description='Visualizador IEEE 754')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('parse32', help='Parse bits float32')
    p.add_argument('bits', type=lambda x: int(x, 0))

    p = sub.add_parser('parse64', help='Parse bits float64')
    p.add_argument('bits', type=lambda x: int(x, 0))

    p = sub.add_parser('encode32', help='Float para bits float32')
    p.add_argument('value', type=float)

    p = sub.add_parser('encode64', help='Float para bits float64')
    p.add_argument('value', type=float)

    p = sub.add_parser('special', help='Lista casos especiais')
    p.add_argument('-p', '--precision', choices=['32', '64'], default='32')

    p = sub.add_parser('next', help='nextafter')
    p.add_argument('x', type=float)
    p.add_argument('y', type=float)

    p = sub.add_parser('ulp', help='ULP de um float')
    p.add_argument('x', type=float)

    args = parser.parse_args()

    if args.cmd == 'parse32':
        r = parse_float32(args.bits)
    elif args.cmd == 'parse64':
        r = parse_float64(args.bits)
    elif args.cmd == 'encode32':
        bits = float_to_bits32(args.value)
        r = parse_float32(bits)
    elif args.cmd == 'encode64':
        bits = float_to_bits64(args.value)
        r = parse_float64(bits)
    elif args.cmd == 'special':
        cases = SPECIAL_CASES_32 if args.precision == '32' else SPECIAL_CASES_64
        for bits, desc in cases.items():
            print(f"0x{bits:0{8 if args.precision=='32' else 16}X} -> {desc}")
        return
    elif args.cmd == 'next':
        print(next_after(args.x, args.y))
        return
    elif args.cmd == 'ulp':
        print(ulp(args.x))
        return

    for k, v in r.items():
        print(f"{k}: {v}")


if __name__ == '__main__':
    main()