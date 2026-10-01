"""用户数据的唯一入口：userdata 目录的位置与内部布局只由本模块定义。

userdata 在哪（只有这一条链，没有环境变量）：
    1. 仓库根的 `userdata_pointer` 文件里的那一行绝对路径（机器本地文件，不入 git）
    2. 该文件不存在 / 为空时：`./userdata`（相对仓库根，故 python 必须在仓库根运行）

想知道实际取值（人或 agent 都用这个命令）：`python entropy/cli/locate_userdata.py`。

目录布局（`UserData` 之外的地方不得自行拼接这些路径）：

    userdata/
      app_config.yaml     主配置（模板 entropy/conf/app_config.example.yaml）
      {arch}_loras.yaml   lora 库，arch 为 noob / anima
      episodes/           每个 episode 一个子目录（episode.json / images / timestep_*.md ...）
      workflows/          用户适配好的 comfyui workflow json
      cache/              临时缓存（lora_search / civitai-cache ...）

userdata 与 userdata_pointer 都不在 git 跟踪范围内（.gitignore）；用户可在 userdata 内部自行
git init，本仓库不关心其版本管理方式。
"""

from pathlib import Path

# 仓库根：本文件在 <repo>/entropy/infra/ 下，故上溯两级。
# 若本仓库被安装进 site-packages（非常规用法），退回 cwd（即"必须在仓库根运行"的约定）。
_REPO_ROOT_FROM_FILE = Path(__file__).resolve().parents[2]
REPO_ROOT = _REPO_ROOT_FROM_FILE if (_REPO_ROOT_FROM_FILE / "pyproject.toml").is_file() else Path.cwd().resolve()

# 指针文件（仓库根）。内容 = 一行绝对路径；不存在或为空即用默认 ./userdata。
# 注意：读取发生在调用时（不缓存），故测试可 monkeypatch 本模块属性 USERDATA_POINTER_PATH。
USERDATA_POINTER_PATH = REPO_ROOT / "userdata_pointer"

_DEFAULT_USERDATA_DIR_NAME = "userdata"

# locate() 的来源标记（供 CLI 展示判断过程）
POINTER = "userdata_pointer"
DEFAULT = "default"

# userdata 内部布局：展示顺序 = 用户最常打交道的路径，供 locate_userdata.py 逐条列出
# {展示用标签: userdata 下的相对路径}
ENTRIES: dict[str, str] = {
    "app_config.yaml": "app_config.yaml",
    "episodes/": "episodes",
    "workflows/": "workflows",
    "cache/": "cache",
    "noob_loras.yaml": "noob_loras.yaml",
    "anima_loras.yaml": "anima_loras.yaml",
}


class UserData:
    """userdata 布局的唯一真相来源：外部模块只准通过这里取路径，不要自行拼接。"""

    @classmethod
    def locate(cls) -> tuple[Path, str]:
        """返回 (userdata 绝对路径, 来源)。来源取 POINTER / DEFAULT，供 CLI 展示判断过程。"""
        pointer_file = USERDATA_POINTER_PATH

        if pointer_file.is_file():
            raw = pointer_file.read_text("utf8").strip()
            if raw:
                path = Path(raw).expanduser()
                if not path.is_absolute():
                    raise ValueError(
                        f"{pointer_file} 里必须是绝对路径，当前是相对路径: {raw!r}。"
                        f"（相对路径的基准会有歧义；可执行 python entropy/cli/locate_userdata.py 查看当前取值）"
                    )
                return path, POINTER

        return (REPO_ROOT / _DEFAULT_USERDATA_DIR_NAME).resolve(), DEFAULT

    @classmethod
    def userdata_dir(cls) -> Path:
        """userdata 根目录（绝对路径）。"""
        return cls.locate()[0]

    @classmethod
    def ensure(cls) -> Path:
        """建立 userdata 骨架（幂等）：首次启动时让用户一眼看到该往哪放东西。"""
        root = cls.userdata_dir()
        for d in (root, cls.episodes_dir(), cls.workflows_dir(), cls.cache_dir()):
            d.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def episodes_dir(cls) -> Path:
        """episodes/{episode_name}/ 的父目录；不存在则创建（写路径，调用即可用）。"""
        d = cls.userdata_dir() / "episodes"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def workflows_dir(cls) -> Path:
        """用户适配好的 comfyui workflow json 目录（本方法不建目录；骨架由 ensure() 建）。"""
        return cls.userdata_dir() / "workflows"

    @classmethod
    def cache_dir(cls) -> Path:
        """临时缓存根目录（如 cache/lora_search、cache/civitai-cache）。"""
        return cls.userdata_dir() / "cache"

    @classmethod
    def app_config_path(cls) -> Path:
        """主配置文件 userdata/app_config.yaml（模板在 entropy/conf/app_config.example.yaml）。"""
        return cls.userdata_dir() / "app_config.yaml"

    @classmethod
    def lora_library_path(cls, arch: str) -> Path:
        """lora 库 userdata/{arch}_loras.yaml，arch 为 noob / anima。"""
        return cls.userdata_dir() / f"{arch}_loras.yaml"
