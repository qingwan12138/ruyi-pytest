import pexpect

from typing import Dict

from tests.helpers import bind_gettext, ruyi_init_default_telemetry, spawn_ruyi


def test_ruyi_news(ruyi_exe: str, ruyi_dep: bool, isolated_env: Dict[str, str]):
    _ = bind_gettext(isolated_env, {
        "zh_CN.UTF-8": {
            " new news item(s):": "条新的新闻条目：",
            "News items:": "新闻条目：",
            "No.": "序号",
            "Title": "标题",
            "RuyiSDK now supports displaying news": "RuyiSDK 支持展示新闻了",
            "You can read them with ruyi news read.": "您可以使用 ruyi news read 阅读它们",
            "Thank you for supporting RuyiSDK!": "感谢您对 RuyiSDK 的支持！",
            "# Release notes": "# RuyiSDK 0.37 版本更新说明",
            "  (no unread item)": "  （无未读条目）",
        },
    })

    ruyi_init_default_telemetry(ruyi_exe, isolated_env)

    # ruyi update
    child = spawn_ruyi(
        ruyi_exe,
        ["update"],
        env=isolated_env,
        timeout=60,
    )
    try:
        child.expect_exact(_(" new news item(s):"))
        child.expect_exact(_("No."))
        child.expect_exact(_("ID"))
        child.expect_exact(_("Title"))
        child.expect_exact("─────")
        child.expect_exact(" 1 ")
        child.expect_exact("2024-01-14-ruyi-news")
        child.expect_exact(_("RuyiSDK now supports displaying news"))
        child.expect_exact(_("You can read them with ruyi news read."))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi news list
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "list"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("News items:"))
        child.expect_exact(_("No."))
        child.expect_exact(_("ID"))
        child.expect_exact(_("Title"))
        child.expect_exact("─────")
        child.expect_exact(" 1 ")
        child.expect_exact("2024-01-14-ruyi-news")
        child.expect_exact(_("RuyiSDK now supports displaying news"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi news read 1
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "read", "1"],
        env=isolated_env,
    )
    try:
        child.expect_exact("# " + _("RuyiSDK now supports displaying news"))
        child.expect_exact(_("Thank you for supporting RuyiSDK!"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi news list --new
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "list", "--new"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("News items:"))
        child.expect_exact(_("No."))
        child.expect_exact("─────")
        child.expect_exact("2024-01-15-new-board-images")
        between = child.before
        # news No. 1 already read
        assert " 1 " not in between
        assert _("RuyiSDK now supports displaying news") not in between
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi news read
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "read"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("# Release notes"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi news list --new
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "list", "--new"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("News items:"))
        child.expect_exact(_("  (no unread item)"))
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0

    # ruyi news list
    child = spawn_ruyi(
        ruyi_exe,
        ["news", "list"],
        env=isolated_env,
    )
    try:
        child.expect_exact(_("News items:"))
        child.expect_exact(_("No."))
        child.expect_exact("─────")
        child.expect_exact("2024-01-14-ruyi-news")
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
