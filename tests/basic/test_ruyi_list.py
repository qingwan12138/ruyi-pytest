
import pexpect
import re

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, ruyi_install, spawn_ruyi


def test_ruyi_list(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            "List of available packages:": "可用软件包列表：",
            "(latest)": "(最新)",
            "Package declares": "软件包声明了",
            "distfile(s):": "个分发文件：",
            "* Slug: (none)": "* Slug：（无）",
            "* Package kind: [": "* 软件包类型：[",
            "* Vendor: PLCT": "* 供应商：PLCT",
            "* Upstream version number:": "* 上游版本号：",
            "### Binary artifacts": "### 二进制制品",
            "### Toolchain metadata": "### 工具链元数据",
            "* Target:": "* 目标：",
            "* Quirks:": "* 特殊特性：",
            "* Components:": "* 组件：",
            "installed": "已安装",
            "arch:": "架构：",
            "needs quirks:": "需要特殊特性：",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi list --name-contains ""
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", ""],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("* toolchain")
        child.expect_exact(_("(latest)"))
        between = child.before
        assert _("Package declares") not in between
        child.expect(pexpect.EOF)
        after = child.before
        assert _("Package declares") not in after
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains "gnu-plct-xthead" --verbose
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-plct-xthead", "--verbose"],
        env=isolated_env,
    )
    try:
        child.expect(r"## toolchain/gnu-plct-xthead .*")
        child.expect_exact(_("* Slug: (none)"))
        child.expect_exact(_("* Package kind: ["))
        child.expect_exact(_("* Vendor: PLCT"))
        child.expect_exact(_("* Upstream version number:"))
        child.expect(
            rf"{re.escape(_('Package declares'))} \d+ {re.escape(_('distfile(s):'))}"
        )
        child.expect_exact(_("### Binary artifacts"))
        child.expect_exact(_("### Toolchain metadata"))
        child.expect_exact(_("* Target:"))
        child.expect_exact(_("* Quirks:"))
        child.expect_exact(_("* Components:"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed y
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect(pexpect.EOF)
        after = child.before
        assert _("installed") not in after
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed n
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "n"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("toolchain/gnu-milkv-milkv-duo-bin")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi install gnu-milkv-milkv-duo-bin
    ruyi_install(ruyi_exe, ["gnu-milkv-milkv-duo-bin"], env=isolated_env)

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed y
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "y"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact(_("installed"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --name-contains 'gnu-milkv-milkv-duo-bin' --is-installed n
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--name-contains", "gnu-milkv-milkv-duo-bin", "--is-installed", "n"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect(pexpect.EOF)
        after = child.before
        assert "toolchain/gnu-milkv-milkv-duo-bin" not in after
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --category-is source
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--category-is", "source"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("source/coremark")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list --category-contains sourc
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "--category-contains", "sourc"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("List of available packages:"))
        child.expect_exact("source/coremark")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi list profiles
    child = spawn_ruyi(
        ruyi_exe,
        ["list", "profiles"],
        env=isolated_env,
        timeout=5,
    )
    try:
        child.expect_exact(_("arch:"))
        child.expect_exact(_("needs quirks:"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
