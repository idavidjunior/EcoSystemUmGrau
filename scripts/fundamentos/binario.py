#!/usr/bin/env python3
"""
Utilitários de binário: conversão, aritmética, bitwise, IEEE 754, endianness.
Uso: python binario.py <comando> [args]
"""
import sys
import struct
import argparse


def int_to_bits(n: int, width: int = 8) -> str:
    return format(n & ((1 << width) - 1), f'0{width}b')


def bits_to_int(bits: str) -> int:
    return int(bits, 2)


def twos_complement(n: int, width: int) -> int:
    if n >= 0:
        return n
    return (1 << width) + n


def float_to_ieee754(f: float, precision: str = 'binary32') -> dict:
    if precision == 'binary32':
        fmt = '>f'
        bits = struct.unpack('>I', struct.pack(fmt, f))[0]
        return {
            'value': f,
            'hex': f'0x{bits:08X}',
            'binary': format(bits, '032b'),
            'sign': (bits >> 31) & 1,
            'exponent': (bits >> 23) & 0xFF,
            'mantissa': bits & 0x7FFFFF,
            'biased_exp': (bits >> 23) & 0xFF,
            'unbiased_exp': ((bits >> 23) & 0xFF) - 127 if ((bits >> 23) & 0xFF) != 0 else -126,
        }
    elif precision == 'binary64':
        fmt = '>d'
        bits = struct.unpack('>Q', struct.pack(fmt, f))[0]
        return {
            'value': f,
            'hex': f'0x{bits:016X}',
            'binary': format(bits, '064b'),
            'sign': (bits >> 63) & 1,
            'exponent': (bits >> 52) & 0x7FF,
            'mantissa': bits & 0xFFFFFFFFFFFFF,
            'biased_exp': (bits >> 52) & 0x7FF,
            'unbiased_exp': ((bits >> 52) & 0x7FF) - 1023 if ((bits >> 52) & 0x7FF) != 0 else -1022,
        }
    raise ValueError(f"Precisão não suportada: {precision}")


def ieee754_to_float(bits: int, precision: str = 'binary32') -> float:
    if precision == 'binary32':
        return struct.unpack('>f', struct.pack('>I', bits & 0xFFFFFFFF))[0]
    elif precision == 'binary64':
        return struct.unpack('>d', struct.pack('>Q', bits & 0xFFFFFFFFFFFFFFFF))[0]
    raise ValueError(f"Precisão não suportada: {precision}")


def endian_swap(value: int, width: int = 32) -> int:
    if width == 16:
        return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
    elif width == 32:
        return ((value & 0xFF) << 24) | ((value & 0xFF00) << 8) | ((value >> 8) & 0xFF00) | ((value >> 24) & 0xFF)
    elif width == 64:
        b = value.to_bytes(8, 'little')
        return int.from_bytes(b, 'big')
    raise ValueError(f"Largura não suportada: {width}")


def bitwise_ops(a: int, b: int, width: int = 32) -> dict:
    mask = (1 << width) - 1
    b_mod = b % width
    return {
        'AND': a & b,
        'OR': a | b,
        'XOR': a ^ b,
        'NOT_A': (~a) & mask,
        'NOT_B': (~b) & mask,
        'NAND': ~(a & b) & mask,
        'NOR': ~(a | b) & mask,
        'XNOR': ~(a ^ b) & mask,
        'SHL': (a << b_mod) & mask,
        'SHR': (a >> b_mod) & mask,
        'ROL': ((a << b_mod) | (a >> (width - b_mod))) & mask,
        'ROR': ((a >> b_mod) | (a << (width - b_mod))) & mask,
    }


def popcount(n: int) -> int:
    return bin(n).count('1')


def clz(n: int, width: int = 32) -> int:
    if n == 0:
        return width
    return width - n.bit_length()


def ctz(n: int) -> int:
    if n == 0:
        return 32
    return (n & -n).bit_length() - 1


def selftest() -> bool:
    ok = True
    assert int_to_bits(255, 8) == '11111111'
    assert bits_to_int('11111111') == 255
    assert twos_complement(-1, 8) == 255
    assert twos_complement(-128, 8) == 128
    f32 = float_to_ieee754(1.5, 'binary32')
    assert f32['hex'] == '0x3FC00000'
    assert ieee754_to_float(0x3FC00000, 'binary32') == 1.5
    f64 = float_to_ieee754(1.5, 'binary64')
    assert f64['hex'] == '0x3FF8000000000000'
    assert endian_swap(0x12345678, 32) == 0x78563412
    ops = bitwise_ops(0b1100, 0b1010, 8)
    assert ops['AND'] == 0b1000
    assert ops['OR'] == 0b1110
    assert ops['XOR'] == 0b0110
    assert popcount(0b101010) == 3
    assert clz(0b1000, 8) == 4
    assert ctz(0b1000) == 3
    print("Todos os testes passaram.")
    return True


def main():
    parser = argparse.ArgumentParser(description='Utilitários de binário')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('int', help='Int para binário')
    p.add_argument('value', type=int)
    p.add_argument('-w', '--width', type=int, default=32)

    p = sub.add_parser('bits', help='Binário para int')
    p.add_argument('bits', type=str)

    p = sub.add_parser('twos', help='Complemento de dois')
    p.add_argument('value', type=int)
    p.add_argument('-w', '--width', type=int, default=32)

    p = sub.add_parser('float', help='Float para IEEE 754')
    p.add_argument('value', type=float)
    p.add_argument('-p', '--precision', choices=['binary32', 'binary64'], default='binary32')

    p = sub.add_parser('ieee', help='IEEE 754 bits para float')
    p.add_argument('bits', type=lambda x: int(x, 0))
    p.add_argument('-p', '--precision', choices=['binary32', 'binary64'], default='binary32')

    p = sub.add_parser('endian', help='Troca endianness')
    p.add_argument('value', type=lambda x: int(x, 0))
    p.add_argument('-w', '--width', type=int, choices=[16, 32, 64], default=32)

    p = sub.add_parser('bitwise', help='Operações bitwise')
    p.add_argument('a', type=lambda x: int(x, 0))
    p.add_argument('b', type=lambda x: int(x, 0))
    p.add_argument('-w', '--width', type=int, default=32)

    p = sub.add_parser('popcount', help='Contagem de bits 1')
    p.add_argument('value', type=lambda x: int(x, 0))

    p = sub.add_parser('clz', help='Leading zeros')
    p.add_argument('value', type=lambda x: int(x, 0))
    p.add_argument('-w', '--width', type=int, default=32)

    p = sub.add_parser('ctz', help='Trailing zeros')
    p.add_argument('value', type=lambda x: int(x, 0))

    p = sub.add_parser('selftest', help='Executa auto-teste')

    args = parser.parse_args()

    if args.cmd == 'selftest':
        selftest()
        return

    if args.cmd == 'int':
        print(int_to_bits(args.value, args.width))
    elif args.cmd == 'bits':
        print(bits_to_int(args.bits))
    elif args.cmd == 'twos':
        print(twos_complement(args.value, args.width))
    elif args.cmd == 'float':
        r = float_to_ieee754(args.value, args.precision)
        for k, v in r.items():
            print(f"{k}: {v}")
    elif args.cmd == 'ieee':
        print(ieee754_to_float(args.bits, args.precision))
    elif args.cmd == 'endian':
        print(hex(endian_swap(args.value, args.width)))
    elif args.cmd == 'bitwise':
        r = bitwise_ops(args.a, args.b, args.width)
        for k, v in r.items():
            print(f"{k}: {v} (0x{v:X})")
    elif args.cmd == 'popcount':
        print(popcount(args.value))
    elif args.cmd == 'clz':
        print(clz(args.value, args.width))
    elif args.cmd == 'ctz':
        print(ctz(args.value))


if __name__ == '__main__':
    main()