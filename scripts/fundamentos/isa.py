#!/usr/bin/env python3
"""
Referência rápida de ISA: x86-64, ARM64, RISC-V.
Opcodes, encoding, latência, throughput (baseado em Agner Fog / ARM Cortex / RISC-V spec).
"""
import argparse
import json


X86_64_COMMON = {
    'MOV': {'opcode': '89 / 8B / B8-BF', 'latency': 1, 'throughput': 0.5, 'desc': 'Move reg/mem'},
    'ADD': {'opcode': '01 / 03 / 81 / 83', 'latency': 1, 'throughput': 0.33, 'desc': 'Add'},
    'SUB': {'opcode': '29 / 2B / 81 / 83', 'latency': 1, 'throughput': 0.33, 'desc': 'Subtract'},
    'MUL': {'opcode': 'F7 /4', 'latency': 3, 'throughput': 1, 'desc': 'Unsigned multiply'},
    'IMUL': {'opcode': 'F7 /5 / 0F AF / 69 / 6B', 'latency': 3, 'throughput': 1, 'desc': 'Signed multiply'},
    'DIV': {'opcode': 'F7 /6', 'latency': 15, 'throughput': 10, 'desc': 'Unsigned divide'},
    'IDIV': {'opcode': 'F7 /7', 'latency': 15, 'throughput': 10, 'desc': 'Signed divide'},
    'AND': {'opcode': '21 / 23 / 81 / 83', 'latency': 1, 'throughput': 0.33, 'desc': 'Bitwise AND'},
    'OR': {'opcode': '09 / 0B / 81 / 83', 'latency': 1, 'throughput': 0.33, 'desc': 'Bitwise OR'},
    'XOR': {'opcode': '31 / 33 / 81 / 83', 'latency': 1, 'throughput': 0.33, 'desc': 'Bitwise XOR'},
    'NOT': {'opcode': 'F7 /2', 'latency': 1, 'throughput': 0.5, 'desc': 'Bitwise NOT'},
    'SHL': {'opcode': 'D1 /4 / D3 /4 / C1 /4', 'latency': 1, 'throughput': 0.5, 'desc': 'Shift left'},
    'SHR': {'opcode': 'D1 /5 / D3 /5 / C1 /5', 'latency': 1, 'throughput': 0.5, 'desc': 'Shift right logical'},
    'SAR': {'opcode': 'D1 /7 / D3 /7 / C1 /7', 'latency': 1, 'throughput': 0.5, 'desc': 'Shift right arithmetic'},
    'ROL': {'opcode': 'D1 /0 / D3 /0 / C1 /0', 'latency': 1, 'throughput': 1, 'desc': 'Rotate left'},
    'ROR': {'opcode': 'D1 /1 / D3 /1 / C1 /1', 'latency': 1, 'throughput': 1, 'desc': 'Rotate right'},
    'CMP': {'opcode': '39 / 3B / 81 / 83', 'latency': 1, 'throughput': 0.33, 'desc': 'Compare'},
    'TEST': {'opcode': '85 / F7 /0', 'latency': 1, 'throughput': 0.33, 'desc': 'Bit test'},
    'JMP': {'opcode': 'E9 / EB / FF /4', 'latency': 1, 'throughput': 0.5, 'desc': 'Unconditional jump'},
    'JCC': {'opcode': '0F 80-8F / 70-7F', 'latency': 1, 'throughput': 0.5, 'desc': 'Conditional jump'},
    'CALL': {'opcode': 'E8 / FF /2', 'latency': 1, 'throughput': 0.5, 'desc': 'Call'},
    'RET': {'opcode': 'C3 / C2', 'latency': 1, 'throughput': 0.5, 'desc': 'Return'},
    'PUSH': {'opcode': '50-57 / 68 / 6A / FF /6', 'latency': 1, 'throughput': 0.5, 'desc': 'Push to stack'},
    'POP': {'opcode': '58-5F / 8F /0', 'latency': 1, 'throughput': 0.5, 'desc': 'Pop from stack'},
    'LEA': {'opcode': '8D', 'latency': 1, 'throughput': 0.5, 'desc': 'Load effective address'},
    'NOP': {'opcode': '90', 'latency': 0, 'throughput': 0.25, 'desc': 'No operation'},
    'POPCNT': {'opcode': 'F3 0F B8', 'latency': 2, 'throughput': 1, 'desc': 'Population count (BMI1)'},
    'LZCNT': {'opcode': 'F3 0F BD', 'latency': 2, 'throughput': 1, 'desc': 'Leading zero count (BMI1)'},
    'TZCNT': {'opcode': 'F3 0F BC', 'latency': 2, 'throughput': 1, 'desc': 'Trailing zero count (BMI1)'},
    'BEXTR': {'opcode': 'F3 0F 38 F7', 'latency': 2, 'throughput': 1, 'desc': 'Bit extract (BMI1)'},
    'PDEP': {'opcode': 'F3 0F 38 F5', 'latency': 3, 'throughput': 1, 'desc': 'Parallel bit deposit (BMI2)'},
    'PEXT': {'opcode': 'F3 0F 38 F6', 'latency': 3, 'throughput': 1, 'desc': 'Parallel bit extract (BMI2)'},
    'ADDSS': {'opcode': 'F3 0F 58', 'latency': 4, 'throughput': 1, 'desc': 'Scalar FP add (SSE)'},
    'ADDPD': {'opcode': '66 0F 58', 'latency': 4, 'throughput': 0.5, 'desc': 'Packed FP add (SSE2)'},
    'MULSS': {'opcode': 'F3 0F 59', 'latency': 4, 'throughput': 0.5, 'desc': 'Scalar FP mul (SSE)'},
    'MULPD': {'opcode': '66 0F 59', 'latency': 4, 'throughput': 0.5, 'desc': 'Packed FP mul (SSE2)'},
    'FMA': {'opcode': 'VEX.NDS 66 0F 38 98-9F', 'latency': 4, 'throughput': 0.5, 'desc': 'Fused multiply-add (FMA)'},
    'AVX256_ADD': {'opcode': 'VEX.NDS 256 66 0F 58', 'latency': 4, 'throughput': 0.5, 'desc': 'AVX 256-bit FP add'},
    'AVX512_ADD': {'opcode': 'EVEX.NDS 512 66 0F 58', 'latency': 4, 'throughput': 0.5, 'desc': 'AVX-512 512-bit FP add'},
}

ARM64_COMMON = {
    'MOV': {'encoding': 'MOV <Wd>, #imm / MOV <Xd>, #imm', 'latency': 1, 'throughput': 1, 'desc': 'Move immediate'},
    'MOVK': {'encoding': 'MOVK <Xd>, #imm, LSL #shift', 'latency': 1, 'throughput': 1, 'desc': 'Move wide with keep'},
    'MOVZ': {'encoding': 'MOVZ <Xd>, #imm, LSL #shift', 'latency': 1, 'throughput': 1, 'desc': 'Move wide with zero'},
    'MOVN': {'encoding': 'MOVN <Xd>, #imm, LSL #shift', 'latency': 1, 'throughput': 1, 'desc': 'Move wide with NOT'},
    'ADD': {'encoding': 'ADD <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Add register'},
    'ADDS': {'encoding': 'ADDS <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Add with flags'},
    'SUB': {'encoding': 'SUB <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Subtract register'},
    'SUBS': {'encoding': 'SUBS <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Sub with flags'},
    'MUL': {'encoding': 'MUL <Xd>, <Xn>, <Xm>', 'latency': 3, 'throughput': 1, 'desc': 'Multiply'},
    'UDIV': {'encoding': 'UDIV <Xd>, <Xn>, <Xm>', 'latency': 15, 'throughput': 12, 'desc': 'Unsigned divide'},
    'SDIV': {'encoding': 'SDIV <Xd>, <Xn>, <Xm>', 'latency': 15, 'throughput': 12, 'desc': 'Signed divide'},
    'AND': {'encoding': 'AND <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Bitwise AND'},
    'ORR': {'encoding': 'ORR <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Bitwise OR'},
    'EOR': {'encoding': 'EOR <Xd>, <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Bitwise XOR'},
    'LSL': {'encoding': 'LSL <Xd>, <Xn>, #imm', 'latency': 1, 'throughput': 1, 'desc': 'Logical shift left'},
    'LSR': {'encoding': 'LSR <Xd>, <Xn>, #imm', 'latency': 1, 'throughput': 1, 'desc': 'Logical shift right'},
    'ASR': {'encoding': 'ASR <Xd>, <Xn>, #imm', 'latency': 1, 'throughput': 1, 'desc': 'Arithmetic shift right'},
    'ROR': {'encoding': 'ROR <Xd>, <Xn>, #imm', 'latency': 1, 'throughput': 1, 'desc': 'Rotate right'},
    'CMP': {'encoding': 'CMP <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Compare'},
    'TST': {'encoding': 'TST <Xn>, <Xm>{, <shift>}', 'latency': 1, 'throughput': 1, 'desc': 'Test bits'},
    'B': {'encoding': 'B <label>', 'latency': 1, 'throughput': 1, 'desc': 'Unconditional branch'},
    'B.COND': {'encoding': 'B.<cond> <label>', 'latency': 1, 'throughput': 1, 'desc': 'Conditional branch'},
    'CBZ': {'encoding': 'CBZ <Xn>, <label>', 'latency': 1, 'throughput': 1, 'desc': 'Compare and branch on zero'},
    'CBNZ': {'encoding': 'CBNZ <Xn>, <label>', 'latency': 1, 'throughput': 1, 'desc': 'Compare and branch on non-zero'},
    'BL': {'encoding': 'BL <label>', 'latency': 1, 'throughput': 1, 'desc': 'Branch with link'},
    'BLR': {'encoding': 'BLR <Xn>', 'latency': 1, 'throughput': 1, 'desc': 'Branch with link to register'},
    'RET': {'encoding': 'RET {<Xn>}', 'latency': 1, 'throughput': 1, 'desc': 'Return from subroutine'},
    'LDR': {'encoding': 'LDR <Xt>, [<Xn|SP>{, #imm}]', 'latency': 3, 'throughput': 1, 'desc': 'Load register'},
    'STR': {'encoding': 'STR <Xt>, [<Xn|SP>{, #imm}]', 'latency': 3, 'throughput': 1, 'desc': 'Store register'},
    'LDP': {'encoding': 'LDP <Xt1>, <Xt2>, [<Xn|SP>{, #imm}]', 'latency': 3, 'throughput': 1, 'desc': 'Load pair'},
    'STP': {'encoding': 'STP <Xt1>, <Xt2>, [<Xn|SP>{, #imm}]', 'latency': 3, 'throughput': 1, 'desc': 'Store pair'},
    'CNT': {'encoding': 'CNT <Vd>.<T>, <Vn>.<T>', 'latency': 2, 'throughput': 1, 'desc': 'Population count (SVE/NEON)'},
    'CLZ': {'encoding': 'CLZ <Xd>, <Xn>', 'latency': 2, 'throughput': 1, 'desc': 'Count leading zeros'},
    'RBIT': {'encoding': 'RBIT <Xd>, <Xn>', 'latency': 2, 'throughput': 1, 'desc': 'Reverse bit order'},
    'FADD': {'encoding': 'FADD <Vd>.<T>, <Vn>.<T>, <Vm>.<T>', 'latency': 3, 'throughput': 1, 'desc': 'FP add (NEON/SVE)'},
    'FMUL': {'encoding': 'FMUL <Vd>.<T>, <Vn>.<T>, <Vm>.<T>', 'latency': 3, 'throughput': 1, 'desc': 'FP multiply (NEON/SVE)'},
    'FMLA': {'encoding': 'FMLA <Vd>.<T>, <Vn>.<T>, <Vm>.<T>', 'latency': 4, 'throughput': 1, 'desc': 'FP multiply-add (NEON/SVE)'},
    'PACIA': {'encoding': 'PACIA <Xd>, <Xn>', 'latency': 1, 'throughput': 1, 'desc': 'Pointer authentication (PAC)'},
    'AUTIA': {'encoding': 'AUTIA <Xd>, <Xn>', 'latency': 1, 'throughput': 1, 'desc': 'Authenticate pointer (PAC)'},
}

RISCV_COMMON = {
    'LUI': {'opcode': '0b0110111', 'format': 'U', 'latency': 1, 'desc': 'Load upper immediate'},
    'AUIPC': {'opcode': '0b0010111', 'format': 'U', 'latency': 1, 'desc': 'Add upper immediate to PC'},
    'JAL': {'opcode': '0b1101111', 'format': 'J', 'latency': 1, 'desc': 'Jump and link'},
    'JALR': {'opcode': '0b1100111', 'format': 'I', 'latency': 1, 'desc': 'Jump and link register'},
    'BEQ': {'opcode': '0b1100011', 'format': 'B', 'funct3': '0b000', 'latency': 1, 'desc': 'Branch if equal'},
    'BNE': {'opcode': '0b1100011', 'format': 'B', 'funct3': '0b001', 'latency': 1, 'desc': 'Branch if not equal'},
    'BLT': {'opcode': '0b1100011', 'format': 'B', 'funct3': '0b100', 'latency': 1, 'desc': 'Branch if less than (signed)'},
    'BGE': {'opcode': '0b1100011', 'format': 'B', 'funct3': '0b101', 'latency': 1, 'desc': 'Branch if greater/equal (signed)'},
    'BLTU': {'opcode': '0b1100011', 'format': 'B', 'funct3': '0b110', 'latency': 1, 'desc': 'Branch if less than (unsigned)'},
    'BGEU': {'opcode': '0b1100011', 'format': 'B', 'funct3': '0b111', 'latency': 1, 'desc': 'Branch if greater/equal (unsigned)'},
    'LB': {'opcode': '0b0000011', 'format': 'I', 'funct3': '0b000', 'latency': 2, 'desc': 'Load byte'},
    'LH': {'opcode': '0b0000011', 'format': 'I', 'funct3': '0b001', 'latency': 2, 'desc': 'Load half'},
    'LW': {'opcode': '0b0000011', 'format': 'I', 'funct3': '0b010', 'latency': 2, 'desc': 'Load word'},
    'LBU': {'opcode': '0b0000011', 'format': 'I', 'funct3': '0b100', 'latency': 2, 'desc': 'Load byte unsigned'},
    'LHU': {'opcode': '0b0000011', 'format': 'I', 'funct3': '0b101', 'latency': 2, 'desc': 'Load half unsigned'},
    'SB': {'opcode': '0b0100011', 'format': 'S', 'funct3': '0b000', 'latency': 2, 'desc': 'Store byte'},
    'SH': {'opcode': '0b0100011', 'format': 'S', 'funct3': '0b001', 'latency': 2, 'desc': 'Store half'},
    'SW': {'opcode': '0b0100011', 'format': 'S', 'funct3': '0b010', 'latency': 2, 'desc': 'Store word'},
    'ADDI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b000', 'latency': 1, 'desc': 'Add immediate'},
    'SLTI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b010', 'latency': 1, 'desc': 'Set less than immediate (signed)'},
    'SLTIU': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b011', 'latency': 1, 'desc': 'Set less than immediate (unsigned)'},
    'XORI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b100', 'latency': 1, 'desc': 'XOR immediate'},
    'ORI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b110', 'latency': 1, 'desc': 'OR immediate'},
    'ANDI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b111', 'latency': 1, 'desc': 'AND immediate'},
    'SLLI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b001', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Shift left logical immediate'},
    'SRLI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b101', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Shift right logical immediate'},
    'SRAI': {'opcode': '0b0010011', 'format': 'I', 'funct3': '0b101', 'funct7': '0b0100000', 'latency': 1, 'desc': 'Shift right arithmetic immediate'},
    'ADD': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b000', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Add'},
    'SUB': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b000', 'funct7': '0b0100000', 'latency': 1, 'desc': 'Subtract'},
    'SLL': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b001', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Shift left logical'},
    'SLT': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b010', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Set less than (signed)'},
    'SLTU': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b011', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Set less than (unsigned)'},
    'XOR': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b100', 'funct7': '0b0000000', 'latency': 1, 'desc': 'XOR'},
    'SRL': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b101', 'funct7': '0b0000000', 'latency': 1, 'desc': 'Shift right logical'},
    'SRA': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b101', 'funct7': '0b0100000', 'latency': 1, 'desc': 'Shift right arithmetic'},
    'OR': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b110', 'funct7': '0b0000000', 'latency': 1, 'desc': 'OR'},
    'AND': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b111', 'funct7': '0b0000000', 'latency': 1, 'desc': 'AND'},
    'MUL': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b000', 'funct7': '0b0000001', 'latency': 3, 'desc': 'Multiply (M extension)'},
    'MULH': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b001', 'funct7': '0b0000001', 'latency': 3, 'desc': 'Multiply high (signed)'},
    'MULHU': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b011', 'funct7': '0b0000001', 'latency': 3, 'desc': 'Multiply high (unsigned)'},
    'DIV': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b100', 'funct7': '0b0000001', 'latency': 15, 'desc': 'Divide (signed)'},
    'DIVU': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b101', 'funct7': '0b0000001', 'latency': 15, 'desc': 'Divide (unsigned)'},
    'REM': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b110', 'funct7': '0b0000001', 'latency': 15, 'desc': 'Remainder (signed)'},
    'REMU': {'opcode': '0b0110011', 'format': 'R', 'funct3': '0b111', 'funct7': '0b0000001', 'latency': 15, 'desc': 'Remainder (unsigned)'},
    'FENCE': {'opcode': '0b0001111', 'format': 'I', 'funct3': '0b000', 'latency': 1, 'desc': 'Memory fence'},
    'ECALL': {'opcode': '0b1110011', 'format': 'I', 'funct3': '0b000', 'latency': 1, 'desc': 'Environment call'},
    'EBREAK': {'opcode': '0b1110011', 'format': 'I', 'funct3': '0b000', 'latency': 1, 'desc': 'Breakpoint'},
    # V extension (vector)
    'VSETVLI': {'opcode': '0b1010111', 'format': 'I', 'latency': 1, 'desc': 'Set vector length'},
    'VADD': {'opcode': '0b1010111', 'format': 'R', 'latency': 2, 'desc': 'Vector add'},
    'VMUL': {'opcode': '0b1010111', 'format': 'R', 'latency': 4, 'desc': 'Vector multiply'},
    'VFMADD': {'opcode': '0b1010111', 'format': 'R', 'latency': 4, 'desc': 'Vector fused multiply-add'},
}


def search_isa(isa: str, query: str):
    data = {'x86': X86_64_COMMON, 'arm': ARM64_COMMON, 'riscv': RISCV_COMMON}[isa.lower()]
    query = query.lower()
    results = {k: v for k, v in data.items() if query in k.lower() or query in v.get('desc', '').lower()}
    return results


def main():
    parser = argparse.ArgumentParser(description='Referência ISA')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('x86', help='Buscar x86-64')
    p.add_argument('query', nargs='?', default='')

    p = sub.add_parser('arm', help='Buscar ARM64')
    p.add_argument('query', nargs='?', default='')

    p = sub.add_parser('riscv', help='Buscar RISC-V')
    p.add_argument('query', nargs='?', default='')

    p = sub.add_parser('list', help='Listar todos de uma ISA')
    p.add_argument('isa', choices=['x86', 'arm', 'riscv'])

    args = parser.parse_args()

    if args.cmd == 'list':
        data = {'x86': X86_64_COMMON, 'arm': ARM64_COMMON, 'riscv': RISCV_COMMON}[args.isa]
        for k, v in sorted(data.items()):
            print(f"{k}: {v.get('desc', '')}")
        return

    if args.cmd in ('x86', 'arm', 'riscv'):
        results = search_isa(args.cmd, args.query)
        if not results:
            print(f"Nenhum resultado para '{args.query}' em {args.cmd.upper()}")
            return
        for k, v in sorted(results.items()):
            print(f"\n{k}:")
            for k2, v2 in v.items():
                print(f"  {k2}: {v2}")


if __name__ == '__main__':
    main()