#!/usr/bin/env python3
"""技能包单元测试。纯标准库 unittest，不依赖模型，可离线运行。

    python3 -m unittest discover -s tests -v
    # 或
    python3 tests/test_agent_skill.py
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sias_agent import tools as T                     # noqa: E402
from sias_agent.agent import MapAgent, FINAL_SCHEMA   # noqa: E402
from sias_agent.llm import _extract_json, _repair, LocalLLM, iter_messages  # noqa: E402
from sias_agent.config import ModelProfile, resolve_profile, PROFILES      # noqa: E402
from sias_agent.map_render import build_html, CATEGORY_STYLE               # noqa: E402


class TestHaversine(unittest.TestCase):
    def test_one_degree_latitude(self):
        """1° 纬度 ≈ 111.19 km，这是距离计算的正确性锚点。"""
        d = T.haversine((34.0, 113.0), (35.0, 113.0))
        self.assertAlmostEqual(d, 111.19, delta=1.0)

    def test_zero(self):
        self.assertEqual(T.haversine((34.4, 113.7), (34.4, 113.7)), 0.0)

    def test_symmetric(self):
        a, b = (34.4166, 113.7530), (34.4270, 113.7620)
        self.assertAlmostEqual(T.haversine(a, b), T.haversine(b, a), places=9)

    def test_known_campus_distance(self):
        """图书馆 -> 郑州博物馆，实测应在 1~2km 量级。"""
        d = T.haversine((34.4166, 113.7530), (34.4270, 113.7620))
        self.assertTrue(1.0 < d < 2.0, f"得到 {d}")

    def test_antipodal(self):
        """对跖点距离约等于半周长 20015 km。"""
        d = T.haversine((0, 0), (0, 180))
        self.assertAlmostEqual(d, 20015.0, delta=5.0)


class TestGeocode(unittest.TestCase):
    def test_exact_zh(self):
        r = T.call("geocode_local", {"name": "郑州博物馆"})
        self.assertTrue(r["matched"])
        self.assertEqual(r["place"], "郑州博物馆")

    def test_no_hyphen_still_matches(self):
        """回归测试：库里是「西亚斯学院-图书馆」，查询不带连字符也必须命中。"""
        r = T.call("geocode_local", {"name": "西亚斯学院图书馆"})
        self.assertTrue(r["matched"], "去掉连字符后应命中")

    def test_english(self):
        r = T.call("geocode_local", {"name": "sias library"})
        self.assertTrue(r["matched"])

    def test_tag_match(self):
        r = T.call("geocode_local", {"name": "少林寺"})
        self.assertTrue(r["matched"])
        self.assertEqual(r["place"], "嵩山")

    def test_unknown_falls_back(self):
        r = T.call("geocode_local", {"name": "zzzz不存在的地方"})
        self.assertFalse(r["matched"])
        self.assertEqual(r["confidence"], 0.0)
        self.assertIn("latitude", r)  # 仍要有坐标，链路不能断

    def test_empty_raises(self):
        with self.assertRaises(T.ToolError):
            T.call("geocode_local", {"name": "   "})


class TestSearchAndReverse(unittest.TestCase):
    def test_search_by_category(self):
        r = T.call("search_poi", {"keyword": "", "category": "campus"})
        self.assertEqual(r["count"], 4)
        self.assertTrue(all(x["category"] == "campus" for x in r["results"]))

    def test_search_by_keyword(self):
        r = T.call("search_poi", {"keyword": "博物馆"})
        self.assertGreaterEqual(r["count"], 1)

    def test_search_limit_respected(self):
        r = T.call("search_poi", {"keyword": "", "limit": 2})
        self.assertLessEqual(len(r["results"]), 2)

    def test_search_relaxes_when_and_filter_empty(self):
        """回归测试：模型会传 category=sight + keyword=地名，严格 AND 返回空，
        导致 Agent 认为周边没景点。工具必须放宽为仅按类别。"""
        r = T.call("search_poi", {"keyword": "SIAS University", "category": "sight"})
        self.assertGreater(r["count"], 0, "应放宽后返回景点")
        self.assertTrue(r["relaxed"])
        self.assertTrue(all(x["category"] == "sight" for x in r["results"]))

    def test_search_strict_hit_is_not_relaxed(self):
        r = T.call("search_poi", {"keyword": "博物馆", "category": "museum"})
        self.assertGreater(r["count"], 0)
        self.assertFalse(r["relaxed"])

    def test_search_sorted_by_rating_desc(self):
        r = T.call("search_poi", {"keyword": "", "limit": 10})
        rs = [float(x["rating"]) for x in r["results"]]
        self.assertEqual(rs, sorted(rs, reverse=True))

    def test_reverse_nearest(self):
        r = T.call("reverse_geocode", {"lat": 34.4166, "longitude": 113.7530})
        self.assertEqual(r["nearest"], "西亚斯学院-图书馆")
        self.assertAlmostEqual(r["distance_km"], 0.0, delta=0.01)

    def test_reverse_invalid_coord_raises(self):
        with self.assertRaises(T.ToolError):
            T.call("reverse_geocode", {"lat": 999, "lng": 999})


class TestRoute(unittest.TestCase):
    def test_two_points(self):
        r = T.call("route_plan", {"points": [[34.4166, 113.7530], [34.4270, 113.7620]]})
        self.assertEqual(len(r["legs"]), 1)
        self.assertGreater(r["total_distance_km"], 0)
        self.assertGreater(r["total_minutes"], 0)

    def test_legs_sum_equals_total(self):
        r = T.call("route_plan", {"points": [[34.4166, 113.7530],
                                             [34.4270, 113.7620], [34.4520, 113.7180]]})
        self.assertEqual(len(r["legs"]), 2)
        self.assertAlmostEqual(sum(l["distance_km"] for l in r["legs"]),
                               r["total_distance_km"], delta=0.01)

    def test_mode_changes_time(self):
        pts = [[34.4166, 113.7530], [34.4270, 113.7620]]
        w = T.call("route_plan", {"points": pts, "mode": "walking"})
        d = T.call("route_plan", {"points": pts, "mode": "driving"})
        self.assertLess(d["total_minutes"], w["total_minutes"])

    def test_too_few_points_raises(self):
        with self.assertRaises(T.ToolError):
            T.call("route_plan", {"points": [[1, 1]]})


class TestScore(unittest.TestCase):
    def test_nearby_high_rating_scores_high(self):
        r = T.call("score_poi", {"latitude": 34.4166, "longitude": 113.7530, "rating": 5.0})
        self.assertGreater(r["score"], 85)

    def test_far_low_rating_scores_low(self):
        r = T.call("score_poi", {"latitude": 34.7460, "longitude": 113.6650, "rating": 1.0})
        self.assertLess(r["score"], 40)

    def test_explainable(self):
        r = T.call("score_poi", {"latitude": 34.4166, "longitude": 113.7530, "rating": 4.0})
        self.assertIn("rating_component", r["explain"])
        self.assertIn("access_component", r["explain"])
        self.assertAlmostEqual(
            r["explain"]["rating_component"] + r["explain"]["access_component"],
            r["score"] / 100, delta=0.005)


class TestJsonRepair(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(_extract_json('{"a":1}'), {"a": 1})

    def test_fenced(self):
        self.assertEqual(_extract_json('```json\n{"a":1}\n```'), {"a": 1})

    def test_preamble_text(self):
        self.assertEqual(_extract_json('好的，结果如下：{"a":1}'), {"a": 1})

    def test_trailing_comma(self):
        self.assertEqual(_extract_json('{"a":1,}'), {"a": 1})

    def test_python_literals(self):
        self.assertEqual(_extract_json("{'a': None, 'b': True}"), {"a": None, "b": True})

    def test_array(self):
        self.assertEqual(_extract_json("[1,2,3]"), [1, 2, 3])

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            _extract_json("   ")

    def test_repair_trailing_comma_array(self):
        self.assertEqual(_repair('{"a":[1,2,],}'), {"a": [1, 2]})

    def test_repair_none(self):
        self.assertEqual(_repair('{"a": None}'), {"a": None})


class TestMapState(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "state.json"

    def tearDown(self):
        self.td.cleanup()

    def test_add_and_persist(self):
        s = T.MapState(self.path)
        s.add({"id": "m1", "name_zh": "图书馆", "latitude": 1.0, "longitude": 2.0})
        self.assertEqual(len(T.MapState(self.path)), 1, "重新加载后应保留")

    def test_dedup_by_id(self):
        s = T.MapState(self.path)
        s.add({"id": "m1", "name_zh": "A"})
        s.add({"id": "m1", "name_zh": "B"})
        self.assertEqual(len(s), 1)

    def test_remove(self):
        s = T.MapState(self.path)
        s.add({"id": "m1"})
        self.assertTrue(s.remove("m1"))
        self.assertFalse(s.remove("m1"))
        self.assertEqual(len(s), 0)

    def test_corrupt_file_does_not_crash(self):
        self.path.write_text("{ broken json", "utf-8")
        self.assertEqual(len(T.MapState(self.path)), 0)


class TestSanitize(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.td = tempfile.TemporaryDirectory()
        self.agent = MapAgent.__new__(MapAgent)
        self.agent.llm = LocalLLM(ModelProfile("t", "gemma4:e2b", "Q4_K_M"))
        self.agent.grounding_fixes = []

    def tearDown(self):
        self.td.cleanup()

    def test_drops_invalid_coords(self):
        out = self.agent._sanitize([{"name_zh": "x", "latitude": "abc", "longitude": 1}])
        self.assertEqual(out, [])

    def test_pulls_hallucinated_coords_back(self):
        """2B 模型典型失败：把郑州点位吐到非洲。必须被拉回。"""
        out = self.agent._sanitize([{"name_zh": "图书馆",
                                    "latitude": 0.0, "longitude": 0.0}])
        self.assertEqual(len(out), 1)
        d = T.haversine((out[0]["latitude"], out[0]["longitude"]), (34.4166, 113.7530))
        self.assertLess(d, 100)

    def test_caps_at_12(self):
        many = [{"name_zh": f"p{i}", "latitude": 34.4, "longitude": 113.7} for i in range(30)]
        self.assertLessEqual(len(self.agent._sanitize(many)), 12)

    def test_assigns_ids_and_source(self):
        out = self.agent._sanitize([{"name_zh": "a", "latitude": 34.4, "longitude": 113.7}])
        self.assertEqual(out[0]["id"], "m1")
        self.assertTrue(out[0]["source"].startswith("local-gemma4"))

    def test_grounds_known_name_to_kb_coords(self):
        """回归测试：实测踩坑——模型给「开封」输出 34.5092,113.4050，
        而知识库权威值是 34.7970,114.3070，偏差约 50km。必须被吸附回权威坐标。"""
        out = self.agent._sanitize([{"name_zh": "开封", "name_en": "Kaifeng",
                                    "latitude": 34.5092, "longitude": 113.4050,
                                    "rating": 4.7}])[0]
        ref = next(p for p in T.KNOWLEDGE_BASE if p.name_zh == "开封")
        self.assertAlmostEqual(out["latitude"], ref.lat, places=5)
        self.assertAlmostEqual(out["longitude"], ref.lng, places=5)
        self.assertIn("grounded", out["source"])

    def test_grounding_records_fix(self):
        self.agent.grounding_fixes = []
        self.agent._sanitize([{"name_zh": "嵩山", "latitude": 30.0,
                               "longitude": 120.0, "rating": 4.9}])
        self.assertEqual(len(self.agent.grounding_fixes), 1)
        self.assertIn("嵩山", self.agent.grounding_fixes[0])

    def test_unknown_name_not_forced_to_kb(self):
        """不在知识库里的名称不能被强行吸附，否则会造出错误点位。"""
        out = self.agent._sanitize([{"name_zh": "某个虚构咖啡馆",
                                    "latitude": 34.45, "longitude": 113.76,
                                    "rating": 4.0}])[0]
        self.assertAlmostEqual(out["latitude"], 34.45, places=5)

    def test_source_marks_grounding(self):
        out = self.agent._sanitize([{"name_zh": "郑州博物馆",
                                    "latitude": 34.4270, "longitude": 113.7620,
                                    "rating": 4.6}])[0]
        self.assertIn("+grounded", out["source"])


class TestMapRender(unittest.TestCase):
    def setUp(self):
        self.markers = [{
            "id": "m1", "name_zh": "西亚斯学院图书馆", "name_en": "SIAS Library",
            "category": "campus", "latitude": 34.4166, "longitude": 113.7530,
            "desc_zh": "地标建筑", "desc_en": "Landmark", "rating": 4.7,
        }, {
            "id": "m2", "name_zh": "嵩山", "name_en": "Mount Song",
            "category": "nature", "latitude": 34.48, "longitude": 113.05,
            "desc_zh": "世界遗产", "desc_en": "Heritage", "rating": 4.9,
        }]
        self.html = build_html(self.markers, title="测试地图", summary="摘要",
                               evidence={"模型": "gemma4:e2b-it-q4_K_M"})

    def test_uses_tencent_not_osm(self):
        """合规红线：不得出现 OpenStreetMap / Google / Mapbox / Leaflet。"""
        for banned in ("openstreetmap", "googleapis", "mapbox", "leaflet",
                       "maps.googleapis", "tile.osm"):
            self.assertNotIn(banned, self.html.lower(), f"不应包含 {banned}")

    def test_uses_tmap_sdk(self):
        self.assertIn("map.qq.com/api/gljs", self.html)

    def test_no_api_key_leak(self):
        self.assertNotIn("?key=", self.html)

    def test_proxy_config_present(self):
        self.assertIn("_TMapSecurityConfig", self.html)
        self.assertIn("__WB_HTTP_PORT__", self.html)
        self.assertIn("__WB_TMAP_SECRET__", self.html)

    def test_no_map_style_id(self):
        """默认 key 未开通自定义样式，传 mapStyleId 会灰屏。"""
        self.assertNotIn("mapStyleId", self.html)

    def test_correct_class_names(self):
        """MultiMarker 有 Multi 前缀，MarkerStyle 没有。"""
        self.assertIn("TMap.MultiMarker", self.html)
        self.assertIn("TMap.MarkerStyle", self.html)
        self.assertNotIn("TMap.Marker({", self.html)

    def test_container_has_height(self):
        self.assertIn("height:100vh", self.html.replace(" ", ""))

    def test_bilingual_present(self):
        self.assertIn("西亚斯学院图书馆", self.html)
        self.assertIn("SIAS Library", self.html)

    def test_interactive_elements(self):
        self.assertIn("addEventListener('click'", self.html)
        self.assertIn("TMap.InfoWindow", self.html)
        self.assertIn("setZoom", self.html)

    def test_escapes_html(self):
        """XSS：地点名里的尖括号必须被转义。"""
        h = build_html([{"id": "x", "name_zh": "<script>alert(1)</script>",
                         "name_en": "x", "category": "poi",
                         "latitude": 34.4, "longitude": 113.7,
                         "desc_zh": "", "desc_en": "", "rating": 4}], title="t", summary="s")
        self.assertNotIn("<script>alert(1)</script>", h)

    def test_all_markers_present(self):
        self.assertIn("m1", self.html)
        self.assertIn("m2", self.html)


class TestToolSchemas(unittest.TestCase):
    def test_all_tools_have_schema(self):
        for t in T.TOOLS:
            o = t.ollama_tool()
            self.assertEqual(o["type"], "function")
            self.assertIn("parameters", o["function"])
            self.assertIn("description", o["function"])

    def test_tools_are_callable(self):
        for t in T.TOOLS:
            self.assertTrue(callable(t.fn))

    def test_unknown_tool_raises(self):
        with self.assertRaises(T.ToolError):
            T.call("does_not_exist", {})

    def test_bad_args_raise(self):
        with self.assertRaises(T.ToolError):
            T.call("geocode_local", {"wrong_param": 1})


class TestProfiles(unittest.TestCase):
    def test_default_is_e2b(self):
        from sias_agent.config import DEFAULT_PROFILE
        self.assertEqual(DEFAULT_PROFILE.ollama_tag, "gemma4:e2b-it-q4_K_M")

    def test_resolve_by_key(self):
        self.assertEqual(resolve_profile("e2b-q8").quantization, "Q8_0")

    def test_resolve_by_tag(self):
        p = resolve_profile("gemma4:e2b-it-q4_K_M")
        self.assertEqual(p.ollama_tag, "gemma4:e2b-it-q4_K_M")

    def test_resolve_none_is_default(self):
        self.assertEqual(resolve_profile(None).key, "e2b-q4")

    def test_label_readable(self):
        self.assertIn("ctx=", PROFILES["e2b-q4"].label)


class TestImages(unittest.TestCase):
    """多模态图片注入的回归测试。

    实测踩坑：早先的循环写成 `m = dict(m)`（只重绑局部变量），
    导致 images 根本没进 payload，模型回「未提供图片」，
    而外层还捕获到了 schema 合法的空结果 —— 看起来成功、实际全空。
    """

    def _capture(self, messages, **kw):
        import unittest.mock as mock
        llm = LocalLLM(ModelProfile("t", "m", "Q4_K_M"))
        box = {}

        def fake(_path, payload, timeout=600):
            box["payload"] = payload
            return {"message": {"content": "{}"}, "eval_count": 1,
                    "total_duration": 1e6}

        with mock.patch("sias_agent.llm._post", fake):
            llm.chat(messages, **kw)
        return llm, box["payload"]

    def test_image_attached_to_last_user_msg(self):
        _, p = self._capture([{"role": "system", "content": "s"},
                              {"role": "user", "content": "describe"}],
                             images=["B64"])
        self.assertEqual(p["messages"][-1]["images"], ["B64"])

    def test_original_messages_not_mutated(self):
        orig = [{"role": "user", "content": "describe"}]
        self._capture(orig, images=["B64"])
        self.assertNotIn("images", orig[0], "不应就地修改调用方的 messages")

    def test_appends_user_msg_if_none_exists(self):
        _, p = self._capture([{"role": "system", "content": "s"}], images=["B64"])
        self.assertEqual(p["messages"][-1]["role"], "user")
        self.assertEqual(p["messages"][-1]["images"], ["B64"])

    def test_no_images_key_when_not_requested(self):
        _, p = self._capture([{"role": "user", "content": "hi"}])
        self.assertNotIn("images", p["messages"][-1])


class TestSchemaAndMisc(unittest.TestCase):
    def test_final_schema_requires_markers(self):
        self.assertIn("markers", FINAL_SCHEMA["required"])

    def test_iter_messages_drops_empty(self):
        out = iter_messages([{"role": "user", "content": "hi"},
                             {"role": "assistant", "content": "  "}])
        self.assertEqual(len(out), 1)

    def test_known_categories_have_styles(self):
        for cat in ("campus", "sight", "museum", "heritage", "transit", "nature", "city"):
            self.assertIn(cat, CATEGORY_STYLE, f"{cat} 缺少样式")

    def test_knowledge_base_coords_valid(self):
        for p in T.KNOWLEDGE_BASE:
            self.assertTrue(-90 <= p.lat <= 90 and -180 <= p.lng <= 180, p.key)
            self.assertTrue(-1 <= p.rating <= 5, p.key)
            self.assertTrue(p.name_zh and p.name_en and p.desc_zh and p.desc_en, p.key)

    def test_knowledge_base_has_no_duplicate_keys(self):
        keys = [p.key for p in T.KNOWLEDGE_BASE]
        self.assertEqual(len(keys), len(set(keys)))

    def test_kb_has_at_least_5_for_challenge(self):
        """挑战要求地图至少 5 个标记点，知识库必须支撑。"""
        self.assertGreaterEqual(len(T.KNOWLEDGE_BASE), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
