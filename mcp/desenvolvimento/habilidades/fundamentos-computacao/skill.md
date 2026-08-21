# Fundamentos de Computação — Binário, Lógica e Arquitetura

## Objetivo
Base teórica e prática para entender como computadores funcionam no nível mais baixo: representação binária, álgebra booleana, arquitetura de von Neumann, conjunto de instruções, memória, ponto flutuante, compilação e ligação.

## Quando ativar
- Qualquer tarefa que envolva: binário, bits, bytes, endianness, complemento de dois, ponto flutuante IEEE 754, assembly, registradores, stack, heap, cache, pipeline, branch prediction, microcódigo, bootloader, linker, ELF/PE, syscalls, interrupções, DMA, MMU, page tables, TLB, virtualização, containers (nível kernel), eBPF, firmware, bare metal.

## Conceitos centrais

### 1. Representação binária
- Bit, nibble, byte, word, dword, qword
- Endianness: little vs big, bi-endian (ARM)
- Inteiros: unsigned, signed (complemento de dois), offset binary
- Ponto flutuante: IEEE 754 (binary32, binary64, binary16, binary128), subnormais, NaN, infinito, rounding modes
- Caracteres: ASCII, UTF-8/16/32, code points, grapheme clusters
- Fixed-point: Q notation, scaling

### 2. Álgebra booleana e portas lógicas
- Operações: AND, OR, XOR, NOT, NAND, NOR, XNOR
- Leis: De Morgan, distributividade, absorção, consenso
- Formas normais: SOP, POS, mintermos, maxtermos
- Simplificação: Karnaugh (até 4-5 vars), Quine-McCluskey
- Circuitos combinacionais: MUX, DEMUX, encoder, decoder, adder (ripple-carry, carry-lookahead), ALU
- Circuitos sequenciais: latch SR, D, JK, T, flip-flop edge-triggered, registradores, contadores, FSM (Mealy/Moore)

### 3. Arquitetura de von Neumann / Harvard
- CPU: fetch-decode-execute, pipeline (5 estágios clássico: IF, ID, EX, MEM, WB), hazards (data, control, structural), forwarding, stall, branch prediction (static, dynamic, BTB, RAS)
- Registradores: GPR, PC, SP, FP, flags (ZF, SF, OF, CF, PF, AF), vetoriais (SSE/AVX/NEON/SVE), sistema (CR0-CR4, MSR, CPUID)
- Memória: hierarquia (L1/L2/L3, RAM, disk), cache (direct-mapped, set-associative, fully-associative, write-through/write-back, MESI/MOESI, cache lines, prefetch), virtual memory (paging, page tables multi-nível, huge pages, TLB, ASID, PCID), NUMA
- Barramentos: system bus, memory bus, PCIe, USB, I2C, SPI, UART, DMA
- Interrupções: maskable, NMI, exceptions, traps, syscalls, IDT, APIC, MSI/MSI-X

### 4. Conjuntos de instruções (ISA)
- CISC vs RISC vs VLIW vs EPIC
- x86-64: modos (real, protected, long, compatibility), prefixos (REX, VEX, EVEX), addressing modes, calling convention (System V AMD64, Microsoft x64), SIMD (MMX, SSE, AVX, AVX-512, AMX)
- ARM64/AArch64: registers (X0-X30, SP, PC, PSTATE), calling convention (AAPCS64), SVE/SVE2, pointer authentication (PAC), memory tagging (MTE)
- RISC-V: base (RV32I/RV64I), extensões (M, A, F, D, C, V, Z*), compressed, privileged spec
- Instruções comuns: MOV, arithmetic, logic, shift/rotate, compare, branch/jump, call/ret, push/pop, load/store, string, bit manipulation (BMI1/2, POPCNT, LZCNT, TZCNT, BEXTR, PDEP, PEXT)

### 5. Stack, heap e calling convention
- Frame pointer vs frame pointer omission (FPO)
- Shadow space / red zone
- Alinhamento de stack (16-byte x86-64, 16-byte ARM64)
- Variadics, alloca, VLA
- Heap: malloc/free, arenas, bins, tcache, jemalloc, mimalloc, fragmentation
- TLS, thread stacks, guard pages

### 6. Formatos de executável e linking
- ELF: header, program headers, section headers, .text, .data, .bss, .rodata, .got, .plt, .dynsym, .dynstr, .rela.*, .symtab, .strtab, .shstrtab, dynamic linking (PT_INTERP, DT_NEEDED, symbol versioning, IFUNC)
- PE/COFF: DOS header, NT headers, section table, imports/exports, delay load, TLS callbacks, CFG, CET
- Mach-O: load commands, segments/sections, dyld, two-level namespace
- Linking: static vs dynamic, relocation types (R_X86_64_*, R_AARCH64_*), GOT/PLT, lazy binding, binding now (LD_BIND_NOW), prelinking, LTO, ThinLTO
- Loader: rtld, ld.so, dyld, Windows loader, ASLR, RELRO, BIND_NOW, PIE/PIC

### 7. Sistema operacional (kernel interface)
- Syscalls: números, calling convention, vDSO, vsyscall
- Processos: fork, clone, vfork, execve, posix_spawn, waitpid, exit_group
- Threads: clone(CLONE_*), futex, pthreads, TLS
- Memória: mmap, munmap, mprotect, madvise, mremap, userfaultfd, huge pages, hugetlbfs
- Arquivos: openat, readv/writev, sendfile, splice, io_uring, epoll, kqueue, IOCP
- Sinais: signal, sigaction, sigaltstack, signalfd, real-time signals
- Namespaces: pid, net, mnt, uts, ipc, user, cgroup, time
- Cgroups: v1 vs v2, controllers (cpu, memory, io, pids, cpuset, hugetlb, rdma, misc)
- eBPF: verifier, maps, helpers, BTF, CO-RE, XDP, tc, kprobes/uprobes, USDT, fentry/fexit, struct_ops, LSM, cgroup hooks

### 8. Boot e firmware
- BIOS vs UEFI: boot services, runtime services, GPT, ESP, Secure Boot, measured boot (TPM, PCR), DXE drivers
- Bootloader: GRUB2, systemd-boot, limine, U-Boot, EDK2
- Kernel: initramfs, initrd, dracut, mkinitcpio, kernel command line, early userspace
- Init: systemd, OpenRC, runit, s6, sysvinit, launchd

### 9. Ferramentas de análise baixa nível
- Disassembly: objdump, gdb, radare2, Ghidra, IDA Pro, Binary Ninja, Hopper, Cutter
- Debugging: gdb, lldb, WinDbg, rr (record/replay), qemu-user, qemu-system
- Profiling: perf, VTune, Instruments, samply, flamegraph, bpftrace, eBPF tools
- Binary analysis: readelf, objdump, nm, strip, patchelf, ldd, dumpbin, otool, codesign
- Assembly: nasm, yasmasm, gas (GNU as), MASM, armasm, llvm-mc, clang -S

## Scripts utilitários (em `scripts/fundamentos/`)

| Script | Função | Status |
|--------|--------|--------|
| `binario.py` | Conversão, aritmética, bitwise, IEEE 754, endianness | ✅ testado |
| `bool.py` | Tabela verdade, simplificação Karnaugh, Quine-McCluskey | ✅ testado |
| `isa.py` | Referência rápida x86-64 / ARM64 / RISC-V (opcode, encoding, latência) | ✅ testado |
| `elf.py` | Parse ELF: headers, sections, symbols, relocations, dynamic | ✅ pronto (Linux) |
| `stack.py` | Análise de stack frame, calling convention, shadow space | 📋 planejado |
| `cache.py` | Simulador de cache (políticas, associatividade, miss rate) | 📋 planejado |
| `float.py` | Visualizador IEEE 754 (bits → valor, valor → bits, operações) | ✅ testado |

## Referências canônicas
- Intel SDM (vol 1-4) — x86-64 architecture
- ARM ARM (ARM Architecture Reference Manual) — AArch64
- RISC-V ISA Spec (unprivileged + privileged)
- IEEE 754-2019 / IEEE 754-2008
- "Computer Organization and Design" (Patterson & Hennessy)
- "Hacker's Delight" (Warren) — bit twiddling
- "What Every Programmer Should Know About Memory" (Drepper)
- OSDev Wiki — boot, kernel, drivers
- Agner Fog — optimization manuals, instruction tables

## Integração com ecossistema
- Skills que se beneficiam (carregam `fundamentos-computacao` como pré-requisito):
  - `debugging-expertise` — crash analysis, memory leaks, race conditions, performance debugging
  - `performance-testing` — ISA latência/throughput, cache hierarchy, memory model, SIMD, branch prediction
  - `resilience-engineering` — kernel interface, memory hierarchy, CPU scheduling, hardware faults
  - `backend-patterns` — syscalls, network stack, file I/O, process model, virtual memory, ELF linking
  - `golang-patterns` — ABI, stack frames, goroutine scheduling, memory allocator, channels, escape analysis
  - `python-patterns` — CPython internals, GIL, bytecode, memory allocator, async, C extensions, profiling
- Agentes: `03-realista` (viabilidade hardware), `05-futuro` (tendências ISA), `08-revisor` (baixo nível)
- Scripts: `architecture_integrity_monitor.py`, `observability_reliability.py`

## Validação
Antes de usar: `python scripts/fundamentos/binario.py --selftest`