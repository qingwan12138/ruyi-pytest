import platform
import pexpect

from pathlib import Path
from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_venv(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str], tmp_path: Path):
    """
    test venv
    :param ruyi_exe:
    :param ruyi_dep:
    :param isolated_env:
    :param tmp_path:
    :return:
    """
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            r"info: Creating a Ruyi virtual environment at .*": r"信息：正在在 .* 创建 Ruyi 虚拟环境...",
            "info: The virtual environment is now created.": "信息：现已创建完成虚拟环境。",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    pkgs = ["llvm-upstream", "gnu-plct"]
    if platform.machine() != "riscv64":
        pkgs.append("qemu-user-riscv-upstream")

    ruyi_install(
        ruyi_exe,
        pkgs=pkgs,
        env=isolated_env,
    )

    # venv
    venv_path = tmp_path / "rit-ruyi-basic-ruyi-venv"

    child = spawn_ruyi(
        ruyi_exe,
        ["venv", "--toolchain", "gnu-plct", "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment at .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect_exact("ruyi-deactivate")
        child.expect_exact(str((venv_path / "sysroot").absolute()))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # venv cmdline
    shell_env = isolated_env.copy()
    shell_env["PS1"] = "$ "
    child = spawn_ruyi(
        "bash",
        ["--noprofile", "--norc", "-i"],
        env=shell_env,
    )
    try:
        child.expect_exact("$ ")
        child.sendline('oldps1="$PS1"')

        child.sendline(f'source "{venv_path}/bin/ruyi-activate"')
        child.expect_exact(f"«Ruyi {venv_path.name}» $ ")

        child.sendline("riscv64-plct-linux-gnu-gcc --version")
        child.expect_exact("riscv64-plct-linux-gnu-gcc")
        child.expect_exact("Copyright")

        child.sendline("ruyi-deactivate")
        child.expect_exact("$ ")

        child.sendline('[[ "$PS1" == "$oldps1" ]]; echo $?')
        child.expect_exact("0")

        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # --sysroot-from
    args = ["venv", "-t", "llvm-upstream", "--sysroot-from", "gnu-plct", ]
    # -e qemu-user-riscv
    if platform.machine() != "riscv64":
        args.extend(["-e", "qemu-user-riscv-upstream", ])

    venv_path = tmp_path / "rit-ruyi-basic-ruyi-llvm"
    child = spawn_ruyi(
        ruyi_exe,
        [*args, "generic", str(venv_path)],
        env=isolated_env,
    )
    try:
        child.expect(_(r"info: Creating a Ruyi virtual environment at .*"))
        child.expect_exact(_("info: The virtual environment is now created."))
        child.expect_exact("ruyi-deactivate")
        child.expect_exact(str((venv_path / "sysroot").absolute()))
        child.expect(pexpect.EOF)
    finally:
        child.close()
    assert child.exitstatus == 0
    assert (venv_path / "sysroot").exists()
    assert (venv_path / "bin" / "clang").exists()
    if platform.machine() != "riscv64":
        assert (venv_path / "bin" / "ruyi-qemu").exists()

    hello_c = tmp_path / "hello_ruyi.c"
    hello_c.write_text(
        '#include <stdio.h>\n\n'
        'int main()\n'
        '{\n'
        '    printf("hello, ruyi\\n");\n\n'
        '    return 0;\n'
        '}\n',
        encoding="utf-8",
    )

    # clang build
    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'source "{venv_path}/bin/ruyi-activate" && '
            f'clang -O3 "{hello_c}" -o "{tmp_path / "hello_ruyi.o"}" && '
            'echo "ret $?" && '
            'ruyi-deactivate',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("ret 0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # run
    child = spawn_ruyi(
        "bash",
        [
            "-c",
            f'source "{venv_path}/bin/ruyi-activate" && ' +
            ("" if platform.machine() == "riscv64" else "ruyi-qemu ") +
            f'"{tmp_path / "hello_ruyi.o"}" && '
            'echo "ret $?" && '
            'ruyi-deactivate',
        ],
        env=isolated_env,
    )
    try:
        child.expect_exact("hello, ruyi")
        child.expect_exact("ret 0")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
