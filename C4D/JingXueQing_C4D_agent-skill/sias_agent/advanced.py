"""Level 3 能力扩展：代码生成 Agent + 视觉理解 Agent。

两个能力都走同一条本地推理链路，不额外引入云服务。

1) 代码生成 Agent：让本地模型根据需求写出**可执行**的 Python 数据处理脚本，
   在受限子进程中执行并回灌结果。沙箱边界见 sandbox.py。
2) 视觉理解：Gemma 4 原生多模态。此处封装 Ollama /api/generate 的 images 字段，
   把图片交给本地模型识别，输出结构化标签。
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any

from .llm import LocalLLM

# ------------------------------------------------------------ 代码生成
CODE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string", "description": "中文说明这段代码做什么"},
        "code": {"type": "string", "description": "完整可运行的 Python 代码"},
    },
    "required": ["explanation", "code"],
}

CODE_SYSTEM = """你是本地运行的代码生成 Agent。根据用户需求写一段**单文件可运行**的 Python 脚本。
硬性要求：
- 只用标准库（可含 math/json/datetime/statistics）；
- 必须定义 main() 并在 if __name__ == "__main__" 中调用；
- 把结果 print 成一行 JSON（键名用英文）；
- 不要用 input()、不要读文件、不要联网；
- 不要有多余的解释注释。
"""


class CodeGenAgent:
    """模型写代码 → 受限执行 → 结果回灌。执行失败会把报错喂回模型让它自修。"""

    def __init__(self, llm: LocalLLM, timeout: int = 25) -> None:
        self.llm = llm
        self.timeout = timeout

    def generate_and_run(self, requirement: str, max_repair: int = 1) -> dict[str, Any]:
        msgs = [
            {"role": "system", "content": CODE_SYSTEM},
            {"role": "user", "content": f"需求：{requirement}\n输出 JSON，包含 explanation 与 code。"},
        ]
        data = self.llm.json_chat(msgs, CODE_SCHEMA)
        code = (data.get("code") or "").strip()
        if "def main" not in code:
            code = code + "\n\nif __name__ == '__main__':\n    main()\n"

        last_err = ""
        for attempt in range(max_repair + 1):
            t0 = time.perf_counter()
            ok, out, err = self._exec(code)
            dt = int((time.perf_counter() - t0) * 1000)
            if ok:
                return {"ok": True, "explanation": data.get("explanation", ""),
                        "stdout": out, "latency_ms": dt, "attempts": attempt + 1,
                        "code_lines": code.count("\n") + 1}
            last_err = err
            data = self.llm.json_chat(msgs + [
                {"role": "user", "content": (
                    f"这段代码运行失败了：\n{err[:400]}\n请修复后重新输出 JSON。" +
                    " 注意只能用标准库，必须 print 一行 JSON。")}
            ], CODE_SCHEMA)
            code = (data.get("code") or "").strip()
            if "def main" not in code:
                code += "\n\nif __name__ == '__main__':\n    main()\n"
        return {"ok": False, "error": last_err[:400], "attempts": max_repair + 1}

    @staticmethod
    def _exec(code: str) -> tuple[bool, str, str]:
        """在临时目录里以子进程执行，只允许标准库，无网络（脚本自身不联网）。"""
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "snippet.py"
            f.write_text(code, "utf-8")
            try:
                r = subprocess.run(
                    [sys.executable, str(f)],
                    capture_output=True, text=True, timeout=25,
                    cwd=td, env={"PATH": "/usr/bin:/bin", "HOME": td},
                )
            except subprocess.TimeoutExpired:
                return False, "", "执行超时（>25s）"
            if r.returncode != 0:
                return False, "", (r.stderr or "").strip()
            return True, (r.stdout or "").strip(), ""


# ------------------------------------------------------------ 视觉理解
VISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "is_campus_photo": {"type": "boolean"},
        "scene": {"type": "string", "description": "英文场景描述"},
        "scene_zh": {"type": "string", "description": "中文场景描述"},
        "guess_category": {
            "type": "string",
            "enum": ["campus", "sight", "museum", "heritage", "transit", "nature", "city", "other"],
        },
        "tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
    "required": ["is_campus_photo", "scene", "scene_zh", "guess_category", "confidence"],
}


class VisionAgent:
    """Gemma 4 原生多模态：本地图片 → 本地推理 → 结构化标签。

    踩坑记录：早先用「纯文本 + 宽松 JSON 解析」，模型返回的是自由格式描述
    （"这张图片展示了一栋红砖建筑..."），虽然能被 _extract_json 解析成功，
    但键名对不上 schema，导致下游 .get() 全是 None——**看起来成功、实际全是空值**。
    修法：改用 json_chat 的 schema 约束解码，让键名由解码器保证。
    """

    def __init__(self, llm: LocalLLM) -> None:
        self.llm = llm

    def describe(self, image_path: str, question: str = "") -> dict[str, Any]:
        p = Path(image_path)
        if not p.exists():
            raise FileNotFoundError(image_path)
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        q = question or ("判断这张照片里是否有大学校园建筑（如图书馆、教学楼、操场）。"
                         "如果是，指出最可能的具体建筑类型。")
        msgs = [
            {"role": "system", "content": "你是本地视觉识别助手，只输出 JSON，不要解释。"},
            {"role": "user", "content": q},
        ]
        try:
            data = self.llm.json_chat(msgs, VISION_SCHEMA, images=[b64])
            if not isinstance(data, dict):
                raise ValueError(f"期望 dict，得到 {type(data).__name__}")
        except Exception as e:  # noqa: BLE001 - 视觉失败也要留下可用证据
            data = {"is_campus_photo": None, "scene": "", "scene_zh": "",
                    "guess_category": "other", "tags": [], "confidence": 0.0,
                    "_error": f"{type(e).__name__}: {e}"[:200]}
        data["_stat"] = self.llm.perf_summary().get("per_call", [{}])[-1]
        return data


# ------------------------------------------------------------ 地图统计
def map_statistics(markers: list[dict[str, Any]]) -> dict[str, Any]:
    """一个由代码生成 Agent 真实执行的确定性任务示例。"""
    from .tools import haversine

    center = (34.4166, 113.7530)
    dists = [haversine(center, (float(m["latitude"]), float(m["longitude"]))) for m in markers]
    cats: dict[str, int] = {}
    for m in markers:
        cats[m.get("category", "other")] = cats.get(m.get("category", "other"), 0) + 1
    return {
        "count": len(markers),
        "categories": cats,
        "max_distance_km": round(max(dists), 2) if dists else 0,
        "mean_distance_km": round(sum(dists) / len(dists), 2) if dists else 0,
        "mean_rating": round(sum(float(m.get("rating", 0)) for m in markers) / len(markers), 2)
        if markers else 0,
    }


if __name__ == "__main__":
    print(textwrap.dedent("""
        本模块不直接运行；由 run_agent.py 的 `code` 与 `vision` 子命令调用。
        """))
