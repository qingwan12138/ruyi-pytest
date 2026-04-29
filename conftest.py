
import os
import pytest
import shutil

from pathlib import Path
from typing import Dict


@pytest.fixture
def ruyi_exe() -> str:
    ruyi = shutil.which("ruyi")
    if ruyi is None:
        pytest.fail("`ruyi` not found in PATH")

    return ruyi


@pytest.fixture
def ruyi_dep() -> bool:
    deps = [
        "bash",
        "bzip2",
        "gunzip",
        "lz4",
        "tar",
        "xz",
        "zstd",
        "unzip"
    ]

    for d in deps:
        if not shutil.which(d):
            pytest.fail(f"`{d}` not found in PATH")

    return True


@pytest.fixture
def ruyi_dep_provisioning(ruyi_dep: bool) -> bool:
    deps = [
        "sudo",
        "dd",
        "fastboot"
    ]

    if not ruyi_dep:
        return False

    for d in deps:
        if not shutil.which(d):
            pytest.fail(f"`{d}` not found in PATH")

    return True


@pytest.fixture
def isolated_env(tmp_path: Path) -> Dict[str, str]:
    root = tmp_path

    home = root / "ruyisdk"
    config = home / "config"
    cache = home / "cache"
    data = home / "data"
    state = home / "state"

    for path in (home, config, cache, data, state):
        path.mkdir()

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(config)
    env["XDG_CACHE_HOME"] = str(cache)
    env["XDG_DATA_HOME"] = str(data)
    env["XDG_STATE_HOME"] = str(state)

    # disable rich text
    env["TERM"] = "dumb"

    return env
