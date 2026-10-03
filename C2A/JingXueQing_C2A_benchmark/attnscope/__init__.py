"""AttnScope — 用「抗干扰效率阶梯」衡量机器注意力 (Track 3 · Attention)。"""

__version__ = "0.1.0"

from .world import generate_l1_item, L1Item, Record
from .ladders import (generate_l2_sequence, generate_l3_item, build_l1_suite,
                      L2Item, L3Item)
from .scoring import (score_l1, score_l2, score_l3, evaluate_l1_response,
                      aes_slope, breakpoint_b70, sdt, lure_capture_rate,
                      split_half_reliability)
from .runners import MockRunner, OpenAICompatibleRunner

__all__ = [
    "generate_l1_item", "L1Item", "Record",
    "generate_l2_sequence", "generate_l3_item", "build_l1_suite",
    "L2Item", "L3Item",
    "score_l1", "score_l2", "score_l3", "evaluate_l1_response",
    "aes_slope", "breakpoint_b70", "sdt", "lure_capture_rate",
    "split_half_reliability",
    "MockRunner", "OpenAICompatibleRunner",
]
