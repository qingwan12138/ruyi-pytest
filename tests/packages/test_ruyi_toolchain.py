import platform
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_toolchain_xthead(ruyi_exe: str, ruyi_build_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):
    pkgs = ["gnu-plct-xthead", ]
    cmd = ["venv", "-t", "gnu-plct-xthead", ]
    if platform.machine() == "x86_64":
        pkgs.append("qemu-user-riscv-xthead")
        cmd.extend(["-e", "qemu-user-riscv-xthead"])

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_install(ruyi_exe, pkgs, env=isolated_env)

    venv_path = tmp_path / "rit-ruyi-basic-ruyi-xthead"
    child = spawn_ruyi(
        ruyi_exe,
        [*cmd, "sipeed-lpi4a", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    source_path = tmp_path / "coremark"
    source_path.mkdir()
    child = spawn_ruyi(
        ruyi_exe,
        ["extract", "--extract-without-subdir", "coremark(1.0.1)", ],
        env=isolated_env,
        timeout=10 * 60,
        cwd=str(source_path),
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'''
source "{venv_path}/bin/ruyi-activate"
sed -i 's/\\bgcc\\b/riscv64-plctxthead-linux-gnu-gcc/g' linux64/core_portme.mak
make PORT_DIR=linux64 link
riscv64-plctxthead-linux-gnu-readelf -h ./coremark.exe
ruyi-deactivate
''',
        ],
        env=isolated_env,
        timeout=60,
        cwd=str(source_path),
    )
    try:
        child.expect_exact("riscv64-plctxthead-linux-gnu-gcc")
        child.expect_exact("Link performed along with compile")
        child.expect_exact("ELF Header:")
        child.expect_exact("ELF64")
        child.expect_exact("RISC-V")
        child.expect(pexpect.EOF)
        output = child.before
    finally:
        child.close()

    if platform.machine() == "x86_64":
        child = spawn_ruyi(
            "bash",
            [
                "-c",
                f'''
source "{venv_path}/bin/ruyi-activate"
ruyi-qemu ./coremark.exe
ruyi-deactivate
    ''',
            ],
            env=isolated_env,
            timeout=600,
            cwd=str(source_path),
        )
        try:
            child.expect_exact("CoreMark Size")
            child.expect_exact("Total ticks")
            child.expect_exact("Compiler flags")
            child.expect_exact("Memory location")
            child.expect_exact("Correct operation validated.")
            child.expect_exact("CoreMark 1.0")
            child.expect(pexpect.EOF)
            output = child.before
        finally:
            child.close()


def test_ruyi_toolchain_gnu_milkv(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):
    ruyi_init_default_telemetry(ruyi_exe, isolated_env)
    ruyi_install(
        ruyi_exe,
        ["gnu-milkv-milkv-duo-bin", "gnu-milkv-milkv-duo-musl-bin", "gnu-milkv-milkv-duo-elf-bin", ],
        env=isolated_env,
    )

    venv_path = tmp_path / "rit-ruyi-basic-ruyi-toolchain_gnu-milkv_musl"

    child = spawn_ruyi(
        ruyi_exe,
        [
            "venv",
            "-t",
            "gnu-milkv-milkv-duo-musl-bin",
            "-t",
            "gnu-milkv-milkv-duo-elf-bin",
            "--sysroot-from",
            "gnu-milkv-milkv-duo-musl-bin",
            "generic",
            str(venv_path),
        ],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    test_tmp = tmp_path / "test_tmp"
    test_tmp.mkdir()
    test_c = test_tmp / "test.c"
    test_c.write_text("int main() {return 0;}\n", encoding="utf-8")

    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'''
source "{venv_path}/bin/ruyi-activate"
riscv64-unknown-elf-gcc -O2 -o "{test_tmp / "test.o"}" "{test_c}"
echo $?
riscv64-unknown-linux-musl-gcc -O2 -o "{test_tmp / "test.o"}" "{test_c}"
echo $?
ruyi-deactivate
        ''',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("0")
        child.expect_exact("0")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    venv_path = tmp_path / "rit-ruyi-basic-ruyi-toolchain_gnu-milkv"
    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "-t", "gnu-milkv-milkv-duo-bin", "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0

    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'''
source "{venv_path}/bin/ruyi-activate"
riscv64-unknown-linux-gnu-gcc -O2 -o "{test_tmp / "test.o"}" "{test_c}"
echo $?
ruyi-deactivate
        ''',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("0")
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
