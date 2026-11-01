"""全局配置：模型、端点、设备信息、路径。

所有可调参数集中在此，便于在 Level 4 设备适配时做对比实验。
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- 路径
PKG_DIR = Path(__file__).resolve().parent
SKILL_DIR = PKG_DIR.parent
DATA_DIR = SKILL_DIR / "data"
STATE_PATH = DATA_DIR / "map_state.json"
TRAJECTORY_PATH = DATA_DIR / "trajectory.jsonl"

# ---------------------------------------------------------------- 服务
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_URL = OLLAMA_HOST.rstrip("/")


# ---------------------------------------------------------------- 模型档位
@dataclass(frozen=True)
class ModelProfile:
    """一个可复现的实验档位（模型 + 量化 + 运行参数）。"""

    key: str
    ollama_tag: str
    quantization: str
    num_ctx: int = 8192
    temperature: float = 0.1
    note: str = ""

    @property
    def label(self) -> str:
        return f"{self.ollama_tag} ({self.quantization}, ctx={self.num_ctx})"


# 主档位：M1 / 8GB 上唯一稳定可用的 Gemma 4 档位
DEFAULT_PROFILE = ModelProfile(
    key="e2b-q4",
    ollama_tag="gemma4:e2b-it-q4_K_M",
    quantization="Q4_K_M",
    num_ctx=8192,
    temperature=0.1,
    note="MacBook Air M1 / 8GB 主用；有效参数 2.3B，GGUF Q4_K_M",
)

# Level 4 对比档位
PROFILES: dict[str, ModelProfile] = {
    p.key: p
    for p in [
        DEFAULT_PROFILE,
        ModelProfile("e2b-q8", "gemma4:e2b-it-q8_0", "Q8_0", 8192, 0.1,
                     "同模型高量化对照组"),
        ModelProfile("e2b-mlx", "gemma4:e2b-mlx", "MLX 4bit", 8192, 0.1,
                     "Apple Silicon 原生 MLX 后端对照组"),
        ModelProfile("e4b-q4", "gemma4:e4b-it-q4_K_M", "Q4_K_M", 8192, 0.1,
                     "更大模型，8GB 机器上会触发 swap，仅作上限探测"),
    ]
}


@dataclass
class ServerInfo:
    """本地运行证据：模型 / 运行时 / 设备 / 速度。"""

    ollama_version: str = "unknown"
    models: list[dict[str, Any]] = field(default_factory=list)
    device: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sh(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (r.stdout or r.stderr).strip()
    except Exception:  # noqa: BLE001 - 证据采集，任何失败都不应中断主流程
        return ""


def collect_device_info() -> dict[str, Any]:
    """采集设备信息，全部来自本机命令，绝不手写。"""
    chip = _sh(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor()
    mem_bytes = 0
    for line in _sh(["sysctl", "-n", "hw.memsize"]).splitlines():
        if line.strip().isdigit():
            mem_bytes = int(line.strip())
    disk = _sh(["df", "-h", "/"]).splitlines()
    avail = disk[-1].split()[3] if len(disk) >= 2 else "?"
    return {
        "chip": chip,
        "logical_cores": os.cpu_count(),
        "memory_gb": round(mem_bytes / 1024**3, 1) if mem_bytes else None,
        "os": f"macOS {platform.mac_ver()[0]} ({platform.machine()})",
        "python": sys.version.split()[0],
        "disk_avail": avail,
    }


def collect_server_info(host: str = OLLAMA_URL) -> ServerInfo:
    """向本地 Ollama 服务要版本与已装模型清单。"""
    import urllib.request

    info = ServerInfo()
    info.device = collect_device_info()
    try:
        with urllib.request.urlopen(host + "/api/version", timeout=5) as r:
            info.ollama_version = json.loads(r.read()).get("version", "unknown")
    except Exception:  # noqa: BLE001
        pass
    try:
        with urllib.request.urlopen(host + "/api/tags", timeout=15) as r:
            info.models = json.loads(r.read()).get("models", [])
    except Exception:  # noqa: BLE001
        pass
    return info


def resolve_profile(name_or_tag: str | None = None) -> ModelProfile:
    """支持三种写法：档位 key / 完整 tag / 直接传 tag 兜底。"""
    if not name_or_tag:
        return DEFAULT_PROFILE
    if name_or_tag in PROFILES:
        return PROFILES[name_or_tag]
    quant = "?"
    for q in ("Q4_K_M", "Q8_0", "bf16", "MLX 4bit"):
        if q.split("_")[0].lower() in name_or_tag.lower():
            quant = q
            break
    return ModelProfile(key="adhoc", ollama_tag=name_or_tag, quantization=quant)
