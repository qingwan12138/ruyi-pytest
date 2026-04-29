
import os
import pexpect
import platform
import pytest
import struct

from pathlib import Path
from typing import Dict

from tests.helpers import ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def write_hello_elf_x86_64(hello_elf: Path):
    message = b"hello world\n"

    ehdr_size = 64
    phdr_size = 56
    code_offset = ehdr_size + phdr_size
    base_vaddr = 0x400000

    # mov eax, 1          ; sys_write
    # mov edi, 1          ; fd = stdout
    # lea rsi, [rip+0x10] ; &message
    # mov edx, 12         ; len
    # syscall
    # mov eax, 60         ; sys_exit
    # xor edi, edi        ; status = 0
    # syscall
    code = bytes.fromhex(
        "b801000000"
        "bf01000000"
        "488d3510000000"
        "ba0c000000"
        "0f05"
        "b83c000000"
        "31ff"
        "0f05"
    )

    file_size = code_offset + len(code) + len(message)
    entry = base_vaddr + code_offset

    e_ident = b"\x7fELF" + bytes([2, 1, 1, 0, 0]) + bytes(7)

    ehdr = struct.pack(
        "<16sHHIQQQIHHHHHH",
        e_ident,
        2,              # ET_EXEC
        62,             # EM_X86_64
        1,              # EV_CURRENT
        entry,
        ehdr_size,
        0,              # e_shoff
        0,              # e_flags
        ehdr_size,
        phdr_size,
        1,              # e_phnum
        0,              # e_shentsize
        0,              # e_shnum
        0,              # e_shstrndx
    )

    phdr = struct.pack(
        "<IIQQQQQQ",
        1,              # PT_LOAD
        5,              # PF_R | PF_X
        0,              # p_offset
        base_vaddr,
        base_vaddr,
        file_size,
        file_size,
        0x1000,
    )

    hello_elf.write_bytes(ehdr + phdr + code + message)
    os.chmod(hello_elf, 0o755)


def _rv_addi(rd: int, rs1: int, imm: int) -> int:
    assert -2048 <= imm <= 2047
    imm &= 0xFFF
    return (imm << 20) | (rs1 << 15) | (0b000 << 12) | (rd << 7) | 0b0010011


def _rv_auipc(rd: int, imm20: int) -> int:
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | 0b0010111


def _rv_ecall() -> int:
    return 0x00000073


def _build_riscv_hello_code(code_offset: int, message: bytes) -> bytes:
    # a0 = 1                      ; stdout
    # a1 = &message               ; buffer
    # a2 = len(message)           ; size
    # a7 = 64                     ; sys_write
    # ecall
    # a0 = 0                      ; exit code
    # a7 = 93                     ; sys_exit
    # ecall
    #
    message_offset = code_offset + 9 * 4
    auipc_offset = code_offset + 4
    delta = message_offset - auipc_offset
    upper = (delta + 0x800) >> 12
    lower = delta - (upper << 12)

    instructions = [
        _rv_addi(10, 0, 1),         # addi a0, x0, 1
        _rv_auipc(11, upper),               # auipc a1, upper
        _rv_addi(11, 11, lower),        # addi a1, a1, lower
        _rv_addi(12, 0, len(message)),  # addi a2, x0, len
        _rv_addi(17, 0, 64),        # addi a7, x0, 64
        _rv_ecall(),                        # ecall
        _rv_addi(10, 0, 0),         # addi a0, x0, 0
        _rv_addi(17, 0, 93),        # addi a7, x0, 93
        _rv_ecall(),                            # ecall
    ]

    return b"".join(struct.pack("<I", insn) for insn in instructions)


def write_hello_elf_riscv64(hello_elf: Path):
    message = b"hello world\n"

    ehdr_size = 64
    phdr_size = 56
    code_offset = ehdr_size + phdr_size
    base_vaddr = 0x10000

    code = _build_riscv_hello_code(code_offset, message)
    file_size = code_offset + len(code) + len(message)
    entry = base_vaddr + code_offset

    e_ident = b"\x7fELF" + bytes([2, 1, 1, 0, 0]) + bytes(7)

    ehdr = struct.pack(
        "<16sHHIQQQIHHHHHH",
        e_ident,
        2,              # ET_EXEC
        243,            # EM_RISCV
        1,              # EV_CURRENT
        entry,
        ehdr_size,
        0,              # e_shoff
        0,              # e_flags
        ehdr_size,
        phdr_size,
        1,              # e_phnum
        0,              # e_shentsize
        0,              # e_shnum
        0,              # e_shstrndx
    )

    phdr = struct.pack(
        "<IIQQQQQQ",
        1,              # PT_LOAD
        5,              # PF_R | PF_X
        0,              # p_offset
        base_vaddr,
        base_vaddr,
        file_size,
        file_size,
        0x1000,
    )

    hello_elf.write_bytes(ehdr + phdr + code + message)
    os.chmod(hello_elf, 0o755)


def write_hello_elf_riscv32(hello_elf: Path):
    message = b"hello world\n"

    ehdr_size = 52
    phdr_size = 32
    code_offset = ehdr_size + phdr_size
    base_vaddr = 0x10000

    code = _build_riscv_hello_code(code_offset, message)
    file_size = code_offset + len(code) + len(message)
    entry = base_vaddr + code_offset

    e_ident = b"\x7fELF" + bytes([1, 1, 1, 0, 0]) + bytes(7)

    ehdr = struct.pack(
        "<16sHHIIIIIHHHHHH",
        e_ident,
        2,              # ET_EXEC
        243,            # EM_RISCV
        1,              # EV_CURRENT
        entry,
        ehdr_size,
        0,              # e_shoff
        0,              # e_flags
        ehdr_size,
        phdr_size,
        1,              # e_phnum
        0,              # e_shentsize
        0,              # e_shnum
        0,              # e_shstrndx
    )

    phdr = struct.pack(
        "<IIIIIIII",
        1,              # PT_LOAD
        0,              # p_offset
        base_vaddr,
        base_vaddr,
        file_size,
        file_size,
        5,              # PF_R | PF_X
        0x1000,
    )

    hello_elf.write_bytes(ehdr + phdr + code + message)
    os.chmod(hello_elf, 0o755)


@pytest.mark.skipif(platform.machine() not in ["riscv64", "aarch64"], reason="riscv64/aarch64 only")
def test_box64(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_install(ruyi_exe, ["box64-upstream"], env=isolated_env)

    box64_bins = list(
        (Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries" / "riscv64").glob("box64-upstream-*/bin/box64")
    )
    assert box64_bins, "box64 binary not found"
    assert len(box64_bins) == 1

    child = spawn_ruyi(
        str(box64_bins[0]),
        ["--version"],
        env=isolated_env,
    )
    try:
        child.expect_exact("Box64")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # test hello_elf run
    hello_elf = tmp_path / "hello-x86_64"
    write_hello_elf_x86_64(hello_elf)

    child = spawn_ruyi(
        str(box64_bins[0]),
        args=[str(hello_elf)],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello world")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


@pytest.mark.skipif(platform.machine() != "x86_64", reason="x86_64 only")
def test_qemu_user_riscv(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_install(ruyi_exe, ["qemu-user-riscv-upstream", "qemu-user-riscv-xthead"], env=isolated_env)

    rv64_bins = list(
        (Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries" / "x86_64").glob("qemu-user-riscv-*/bin/qemu-riscv64")
    )
    rv32_bins = list(
        (Path(isolated_env["XDG_DATA_HOME"]) / "ruyi" / "binaries" / "x86_64").glob("qemu-user-riscv-*/bin/qemu-riscv32")
    )
    assert rv64_bins, "qemu-riscv64 binary not found"
    assert rv32_bins, "qemu-riscv32 binary not found"
    assert len(rv64_bins) == 2
    assert len(rv32_bins) == 2

    for bb in [*rv64_bins, *rv32_bins]:
        child = spawn_ruyi(
            str(bb),
            ["--version"],
            env=isolated_env,
        )
        try:
            child.expect_exact("qemu")
            child.expect(pexpect.EOF)
        finally:
            child.close()

        assert child.exitstatus == 0

    hello_rv64 = tmp_path / "hello-riscv64"
    write_hello_elf_riscv64(hello_rv64)
    hello_rv32 = tmp_path / "hello-riscv32"
    write_hello_elf_riscv32(hello_rv32)

    for bb in rv64_bins:
        child = spawn_ruyi(
            str(bb),
            [str(hello_rv64)],
            env=isolated_env,
        )
        try:
            child.expect_exact("hello world")
            child.expect(pexpect.EOF)
        finally:
            child.close()

        assert child.exitstatus == 0

    for bb in rv32_bins:
        child = spawn_ruyi(
            str(bb),
            [str(hello_rv32)],
            env=isolated_env,
        )
        try:
            child.expect_exact("hello world")
            child.expect(pexpect.EOF)
        finally:
            child.close()

        assert child.exitstatus == 0


@pytest.mark.skipif(platform.machine() != "x86_64", reason="x86_64 only")
def test_hello_elf_x86_64(isolated_env: Dict[str, str], tmp_path: Path):
    """
    check hello_elf runnable
    :param isolated_env:
    :param tmp_path:
    :return:
    """

    hello_elf = tmp_path / "hello-x86_64"
    write_hello_elf_x86_64(hello_elf)

    child = spawn_ruyi(
        str(hello_elf),
        args=[],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello world")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0


@pytest.mark.skipif(platform.machine() != "riscv64", reason="riscv64 only")
def test_hello_elf_riscv64(isolated_env: Dict[str, str], tmp_path: Path):
    """
    check hello_elf runnable
    :param isolated_env:
    :param tmp_path:
    :return:
    """

    hello_elf = tmp_path / "hello-riscv64"
    write_hello_elf_x86_64(hello_elf)

    child = spawn_ruyi(
        str(hello_elf),
        args=[],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello world")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
