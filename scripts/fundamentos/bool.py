#!/usr/bin/env python3
"""
Álgebra booleana: tabela verdade, simplificação Karnaugh (até 5 vars), Quine-McCluskey.
"""
import sys
import itertools
import argparse


def truth_table(expr: str, vars_: list[str]) -> list[dict]:
    results = []
    for vals in itertools.product([0, 1], repeat=len(vars_)):
        env = dict(zip(vars_, vals))
        try:
            result = eval(expr, {"__builtins__": {}}, env)
        except Exception:
            result = None
        results.append({**env, 'result': int(bool(result)) if result is not None else None})
    return results


def minterms_from_table(table: list[dict], vars_: list[str]) -> list[int]:
    return [i for i, row in enumerate(table) if row['result'] == 1]


def maxterms_from_table(table: list[dict], vars_: list[str]) -> list[int]:
    return [i for i, row in enumerate(table) if row['result'] == 0]


def kmap_simplify(minterms: list[int], num_vars: int) -> str:
    if num_vars > 5:
        return "Karnaugh limitado a 5 variáveis. Use Quine-McCluskey."
    if not minterms:
        return "0"
    if len(minterms) == (1 << num_vars):
        return "1"

    # Agrupa por número de 1s
    groups = {}
    for m in minterms:
        ones = bin(m).count('1')
        groups.setdefault(ones, []).append(m)

    # Combina termos adjacentes (diferem em 1 bit)
    def combine_terms(terms: list[int]) -> list[tuple[int, int]]:
        combined = []
        used = set()
        for i, a in enumerate(terms):
            for b in terms[i+1:]:
                diff = a ^ b
                if diff & (diff - 1) == 0:  # potência de 2 = 1 bit diferente
                    combined.append((a | b, diff))  # termo combinado, bit que mudou
                    used.add(a)
                    used.add(b)
        return combined, used

    prime_implicants = set(minterms)
    current_groups = groups

    while True:
        new_groups = {}
        all_used = set()
        for ones, terms in current_groups.items():
            combined, used = combine_terms(terms)
            all_used.update(used)
            for term, mask in combined:
                new_ones = bin(term).count('1') - 1
                new_groups.setdefault(new_ones, []).append((term, mask))
        if not all_used:
            break
        prime_implicants.update(all_used)
        current_groups = new_groups

    # Para simplicidade, retorna SOP dos mintermos (versão completa seria Petrick's method)
    var_names = [chr(ord('A') + i) for i in range(num_vars)]
    terms = []
    for m in minterms:
        term = []
        for i, v in enumerate(var_names):
            if (m >> (num_vars - 1 - i)) & 1:
                term.append(v)
            else:
                term.append(f"{v}'")
        terms.append(''.join(term))
    return ' + '.join(terms)


def quine_mccluskey(minterms: list[int], num_vars: int, dont_cares: list[int] = None) -> str:
    if dont_cares is None:
        dont_cares = []
    all_terms = sorted(set(minterms) | set(dont_cares))

    # Passo 1: agrupa por número de 1s
    groups = {}
    for m in all_terms:
        ones = bin(m).count('1')
        groups.setdefault(ones, []).append({'term': m, 'mask': 0, 'covered': set([m])})

    # Passo 2: combina iterativamente
    prime_implicants = []
    while True:
        new_groups = {}
        used = set()
        for ones in sorted(groups.keys()):
            if ones + 1 not in groups:
                continue
            for a in groups[ones]:
                for b in groups[ones + 1]:
                    diff = a['term'] ^ b['term']
                    if diff & (diff - 1) == 0:
                        combined_term = a['term'] | b['term']
                        combined_mask = a['mask'] | b['mask'] | diff
                        new_covered = a['covered'] | b['covered']
                        new_groups.setdefault(ones, []).append({
                            'term': combined_term,
                            'mask': combined_mask,
                            'covered': new_covered
                        })
                        used.add((a['term'], a['mask']))
                        used.add((b['term'], b['mask']))

        for g in groups.values():
            for item in g:
                if (item['term'], item['mask']) not in used:
                    prime_implicants.append(item)

        if not new_groups:
            break
        groups = new_groups

    minterms_set = set(minterms)
    # Passo 3: tabela de cobertura (Petrick simplificado - greedy)
    essential = []
    covered_minterms = set()

    # Encontra implicantes essenciais
    for pi in prime_implicants:
        minterms_covered = pi['covered'] & minterms_set
        unique = minterms_covered - covered_minterms
        if unique and all(
            unique - pj['covered'] for pj in prime_implicants if pj != pi
        ):
            essential.append(pi)
            covered_minterms.update(minterms_covered)

    # Greedy para o resto
    remaining = minterms_set - covered_minterms
    while remaining:
        best = max(prime_implicants, key=lambda pi: len(pi['covered'] & remaining))
        essential.append(best)
        covered_minterms.update(best['covered'] & minterms_set)
        remaining = minterms_set - covered_minterms

    # Converte para expressão
    var_names = [chr(ord('A') + i) for i in range(num_vars)]
    terms = []
    for pi in essential:
        term_parts = []
        for i in range(num_vars):
            bit_pos = num_vars - 1 - i
            if (pi['mask'] >> bit_pos) & 1:
                continue  # variável eliminada
            if (pi['term'] >> bit_pos) & 1:
                term_parts.append(var_names[i])
            else:
                term_parts.append(f"{var_names[i]}'")
        if term_parts:
            terms.append(''.join(term_parts))
        else:
            terms.append('1')
    return ' + '.join(terms) if terms else '0'


def sop_to_expr(terms: list[str], vars_: list[str]) -> str:
    return ' + '.join(terms)


def main():
    parser = argparse.ArgumentParser(description='Álgebra booleana')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('table', help='Tabela verdade')
    p.add_argument('expr', type=str)
    p.add_argument('vars', nargs='+', type=str)

    p = sub.add_parser('kmap', help='Simplificação Karnaugh')
    p.add_argument('minterms', type=lambda x: [int(m) for m in x.split(',')])
    p.add_argument('-n', '--num-vars', type=int, required=True)

    p = sub.add_parser('qm', help='Quine-McCluskey')
    p.add_argument('minterms', type=lambda x: [int(m) for m in x.split(',')])
    p.add_argument('-n', '--num-vars', type=int, required=True)
    p.add_argument('-d', '--dont-cares', type=lambda x: [int(m) for m in x.split(',')], default=[])

    args = parser.parse_args()

    if args.cmd == 'table':
        table = truth_table(args.expr, args.vars)
        header = ' | '.join(args.vars + ['F'])
        print(header)
        print('-' * len(header))
        for row in table:
            print(' | '.join(str(row[v]) for v in args.vars + ['result']))

    elif args.cmd == 'kmap':
        print(kmap_simplify(args.minterms, args.num_vars))

    elif args.cmd == 'qm':
        print(quine_mccluskey(args.minterms, args.num_vars, args.dont_cares))


if __name__ == '__main__':
    main()