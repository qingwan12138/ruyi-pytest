
import pexpect

from pathlib import Path
from typing import Callable, Dict, List, Union


def spawn_ruyi(
        ruyi_bin: str,
        args: List[str],
        env: Dict[str, str],
        timeout: int = 5,
        cwd: Union[str, None] = None
) -> pexpect.spawn:
    return pexpect.spawn(
        ruyi_bin,
        args,
        env=env, # type: ignore[arg-type]
        encoding="utf-8",
        timeout=timeout,
        cwd=cwd,
    )


def bind_gettext(env: Dict[str, str], catalog: Dict[str, Dict[str, str]]) -> Callable[[str], str]:
    locale = env.get("LC_ALL") or env.get("LANG") or "en_US.UTF-8"
    locale_map = catalog.get(locale) or catalog.get("en_US.UTF-8", {})

    def gettext(message: str) -> str:
        return locale_map.get(message, message)

    return gettext


def ruyi_config_iscas_mirror(key: str, env: dict[str, str]):
    xdg_config_home = env["XDG_CONFIG_HOME"]
    config_dir = Path(xdg_config_home) / "ruyi"
    config_dir.mkdir(parents=True, exist_ok=True)

    REPOs = {
        "ISCAS": "https://mirror.iscas.ac.cn/git/ruyisdk/packages-index.git",
        "GITEE": "https://gitee.com/ruyisdk/packages-index.git",
    }

    config_file = config_dir / "config.toml"
    config_file.write_text(
        '[repo]\n'
        f'remote = "{REPOs[key]}"\n',
        encoding="utf-8",
    )


def ruyi_init_default_telemetry(ruyi_bin: str, env: Dict[str, str]):
    myenv = env.copy()
    myenv["LANG"] = "en_US.UTF-8"

    # uncomment if fail to test locally with GitHub mirror
    # ruyi_config_iscas_mirror(myenv)
    if env.get("RUYI_REPO", "") in ["ISCAS", "GITEE", ]:
        ruyi_config_iscas_mirror(env.get("RUYI_REPO"), myenv)

    child = spawn_ruyi(
        ruyi_bin,
        ["update"],
        env=myenv,
        timeout=60
    )

    try:
        while True:
            idx = child.expect(["(y/N)", pexpect.EOF])
            if idx == 0:
                child.sendline("")
            else:
                break
    finally:
        child.close()

    assert child.exitstatus == 0


def ruyi_install(ruyi_bin: str, pkgs: List[str], env: Dict[str, str]):
    child = spawn_ruyi(
        ruyi_bin,
        ["install", *pkgs],
        env=env,
        timeout=10*60
    )

    try:
        child.expect(pexpect.EOF)
    finally:
        child.close()

    assert child.exitstatus == 0
