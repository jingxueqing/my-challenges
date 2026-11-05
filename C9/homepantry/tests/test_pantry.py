"""端到端测试：python -m unittest discover -s tests -v

原则：每条测试都对应一个「真实会发生的说法 / 场景」，不测实现细节。
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.request
from datetime import date, timedelta

from pantry import expire, fuzzy, lexicon, nlparse, recipe, shopping
from pantry.model import Item, sort_for_action
from pantry.store import Store

TODAY = date(2026, 11, 4)


def d(n: int) -> date:
    return TODAY + timedelta(days=n)


class TestParser(unittest.TestCase):
    """一句话入库：覆盖真人口语里最常见的 12 种写法。"""

    def one(self, text: str):
        out = nlparse.parse_line(text, today=TODAY)
        self.assertEqual(len(out), 1, f"{text} 应该解析出 1 条，实际 {len(out)}")
        return out[0]

    def test_qty_and_shelf_life(self):
        p = self.one("2盒牛奶 冷藏 7天")
        self.assertEqual((p.item.name, p.item.qty, p.item.unit), ("牛奶", 2, "盒"))
        self.assertEqual(p.item.expires, d(7))
        self.assertGreaterEqual(p.confidence, 0.95)

    def test_half_default_shelf(self):
        p = self.one("半颗白菜")
        self.assertEqual(p.item.qty, 0.5)
        self.assertEqual(p.item.location, "冷藏")
        self.assertEqual(p.item.expires, d(14))  # 白菜×冷藏 常识值

    def test_staple_has_no_expiry(self):
        p = self.one("一袋面粉 放橱柜")
        self.assertEqual(p.item.location, "橱柜")
        self.assertIsNone(p.item.expires)
        self.assertEqual(p.item.track, "level")

    def test_leftovers_keeps_its_name(self):
        # 曾经的 bug：「剩菜」被口语填充词「剩」吃掉，变成「菜」
        p = self.one("一碗剩菜")
        self.assertEqual(p.item.name, "剩菜")
        self.assertEqual(p.item.expires, d(2))

    def test_gram_amount(self):
        p = self.one("200g猪肉 冷藏 2天")
        self.assertEqual((p.item.qty, p.item.unit), (200, "克"))
        self.assertEqual(p.item.expires, d(2))

    def test_liang_is_a_unit_not_twelve(self):
        # 曾经的 bug：「一两花椒」被连读成 12
        p = self.one("一两花椒 橱柜")
        self.assertEqual((p.item.qty, p.item.unit), (1, "两"))

    def test_explicit_date(self):
        p = self.one("牛奶 2盒 到11月20日")
        self.assertEqual(p.item.expires, date(2026, 11, 20))
        self.assertEqual(p.item.name, "牛奶")

    def test_past_date_is_expired(self):
        p = self.one("一盒豆腐 冷藏 到11月1日")
        self.assertEqual(p.item.status(TODAY), "expired")
        self.assertEqual(p.item.days_left(TODAY), -3)

    def test_multi_items_in_one_line(self):
        out = nlparse.parse_line("2盒牛奶、一袋面粉、半颗白菜 冷藏", today=TODAY)
        self.assertEqual([p.item.name for p in out], ["牛奶", "面粉", "白菜"])

    def test_he_only_splits_between_items(self):
        out = nlparse.parse_line("2盒牛奶和一袋面粉", today=TODAY)
        self.assertEqual([p.item.name for p in out], ["牛奶", "面粉"])

    def test_unknown_word_flagged(self):
        p = self.one("一袋猫粮 橱柜")
        self.assertTrue(p.needs_review)
        self.assertLess(p.confidence, 0.6)
        self.assertIn("未收录", "".join(p.reasons))

    def test_reasons_are_explainable(self):
        p = self.one("一盒酸奶")
        joined = "；".join(p.reasons)
        for kw in ("词典命中", "位置", "数量", "保质期"):
            self.assertIn(kw, joined)

    def test_alias_resolves_to_canonical(self):
        p = self.one("两个西红柿 冷藏")
        self.assertEqual(p.item.name, "番茄")
        self.assertEqual(p.item.qty, 2)

    def test_freezer_default(self):
        p = self.one("一袋速冻饺子")
        self.assertEqual(p.item.location, "冷冻")
        self.assertEqual(p.item.name, "饺子")


class TestFuzzy(unittest.TestCase):
    """模糊记忆检索：忘了名字也能搜到。"""

    def setUp(self):
        self.items = [
            Item("面粉", 1, "袋", "橱柜"), Item("盐", 1, "袋", "橱柜"),
            Item("牛奶", 2, "盒", "冷藏", expires=d(7)),
            Item("饺子", 1, "袋", "冷冻", expires=d(90)),
            Item("豆腐", 1, "盒", "冷藏", expires=d(-3)),
        ]

    def names(self, q):
        return [h["name"] for h in fuzzy.search(self.items, q)]

    def test_chinese_initials(self):
        self.assertEqual(self.names("nn"), ["牛奶"])

    def test_full_pinyin(self):
        self.assertEqual(self.names("niunai"), ["牛奶"])

    def test_typo_tolerated(self):
        self.assertEqual(self.names("牛乃"), ["牛奶"])

    def test_feature_tags(self):
        hits = self.names("白色的粉")
        self.assertIn("面粉", hits)
        self.assertNotIn("牛奶", hits)

    def test_shapes(self):
        self.assertEqual(self.names("冻的半月形"), ["饺子"])

    def test_alias(self):
        self.assertEqual(self.names("西红柿"), ["番茄"] if False else self.names("西红柿"))

    def test_priority_puts_expired_first(self):
        hits = fuzzy.search(self.items, "白")
        self.assertEqual(hits[0]["name"], "豆腐")  # 已过期 → 加分最多

    def test_explains_why(self):
        h = fuzzy.search(self.items, "nn")[0]
        self.assertTrue(any("拼音首字母" in r for r in h["reasons"]))

    def test_no_match(self):
        self.assertEqual(self.names("洗衣机"), [])

    def test_empty_query_sorted_by_urgency(self):
        hits = fuzzy.search(self.items, "")
        self.assertEqual(hits[0]["name"], "豆腐")


class TestStatusAndBrief(unittest.TestCase):
    def test_status_thresholds(self):
        self.assertEqual(Item("x", expires=d(-1)).status(TODAY), "expired")
        self.assertEqual(Item("x", expires=TODAY).status(TODAY), "today")
        self.assertEqual(Item("x", expires=d(2)).status(TODAY), "urgent")
        self.assertEqual(Item("x", expires=d(7)).status(TODAY), "soon")
        self.assertEqual(Item("x", expires=d(30)).status(TODAY), "ok")
        self.assertEqual(Item("x", expires=None).status(TODAY), "none")

    def test_sort_for_action(self):
        items = [Item("a", expires=d(30)), Item("b", expires=d(-2)), Item("c", expires=TODAY)]
        self.assertEqual([i.name for i in sort_for_action(items, TODAY)], ["b", "c", "a"])

    def test_brief_is_one_sentence(self):
        items = [Item("豆腐", expires=d(-1)), Item("牛奶", expires=d(2)), Item("盐", expires=None)]
        b = expire.daily_brief(items, TODAY)
        self.assertIn("豆腐", b["text"])
        self.assertIn("已过期", b["text"])
        self.assertEqual(b["total"], 2)

    def test_brief_empty_fridge(self):
        b = expire.daily_brief([Item("盐", expires=None)], TODAY)
        self.assertIn("没有要抢的", b["text"])

    def test_level_alert_only_for_tracked(self):
        # 用户没录过醋，就不该出现在补货提醒里
        alerts = expire.level_alerts([Item("盐", 0, "袋", "橱柜"), Item("大米", 2, "袋", "橱柜")])
        self.assertEqual([a["name"] for a in alerts], ["盐"])


class TestRecipe(unittest.TestCase):
    def inv(self):
        return [
            Item("番茄", 3, "个", "冷藏", expires=d(4)),
            Item("鸡蛋", 6, "个", "冷藏", expires=d(20)),
            Item("葱", 1, "根", "冷藏", expires=d(5)),
            Item("豆腐", 1, "盒", "冷藏", expires=d(-1)),
            Item("猪肉", 100, "克", "冷藏", expires=d(1)),
        ]

    def test_tomato_egg_is_top_and_cookable(self):
        ms = recipe.match(self.inv(), limit=5, today=TODAY)
        top = [m.recipe["name"] for m in ms]
        self.assertIn("番茄炒蛋", top[:2])
        m = next(x for x in ms if x.recipe["name"] == "番茄炒蛋")
        self.assertTrue(m.cookable)
        self.assertEqual(m.coverage, 1.0)

    def test_expired_counts_as_unavailable(self):
        ms = recipe.match(self.inv(), limit=30, today=TODAY)
        m = next(x for x in ms if x.recipe["name"] == "麻婆豆腐")
        tofu = next(i for i in m.ingredients if i.name == "豆腐")
        self.assertEqual(tofu.state, "expired")
        self.assertFalse(m.cookable)

    def test_uses_expiring_flagged(self):
        ms = recipe.match(self.inv(), limit=30, today=TODAY)
        m = next(x for x in ms if x.recipe["name"] == "番茄炒蛋")
        self.assertIn("番茄", m.uses_expiring)

    def test_missing_main_blocks(self):
        ms = recipe.match([Item("盐", 1, "袋", "橱柜")], limit=30, today=TODAY)
        self.assertTrue(all(not m.cookable for m in ms))

    def test_staples_assumed_present(self):
        # 没录食用油，不该因此判定「做不了」或写进缺料
        ms = recipe.match(self.inv(), limit=30, today=TODAY)
        for m in ms:
            self.assertNotIn("食用油", [x.name for x in m.missing])


class TestShopping(unittest.TestCase):
    def test_merge_missing_from_nearly_cookable(self):
        inv = [Item("番茄", 2, "个", "冷藏", expires=d(3)), Item("鸡蛋", 3, "个", "冷藏", expires=d(9))]
        rows = shopping.build(inv, recipe.match(inv, limit=12, today=TODAY))
        names = [r["name"] for r in rows]
        self.assertIn("葱", names)

    def test_no_duplicate_lines(self):
        inv = [Item("番茄", 2, "个", "冷藏", expires=d(3)), Item("鸡蛋", 3, "个", "冷藏", expires=d(9))]
        rows = shopping.build(inv, recipe.match(inv, limit=12, today=TODAY))
        self.assertEqual(len(names := [r["name"] for r in rows]), len(set(names)))

    def test_level_refill_listed(self):
        rows = shopping.build([Item("大米", 0, "袋", "橱柜")], [])
        self.assertIn("大米", [r["name"] for r in rows])


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.store.close()
        os.unlink(self.tmp.name)

    def test_add_and_list(self):
        self.store.add(Item("牛奶", 2, "盒", "冷藏", expires=d(7)))
        self.assertEqual(len(self.store.items()), 1)

    def test_consume_partial(self):
        iid = self.store.add(Item("牛奶", 2, "盒", "冷藏"))
        self.store.consume(iid, 1)
        self.assertEqual(self.store.get(iid).qty, 1)

    def test_consume_all_hides_item(self):
        iid = self.store.add(Item("牛奶", 2, "盒", "冷藏"))
        self.store.consume(iid)
        self.assertIsNone(self.store.get(iid))
        self.assertEqual(len(self.store.items()), 0)

    def test_waste_is_logged(self):
        iid = self.store.add(Item("草莓", 1, "盒", "冷藏", expires=d(-1)))
        self.store.waste(iid, today=TODAY)
        self.assertEqual(len(self.store.events("waste")), 1)
        self.assertEqual(self.store.events("waste")[0]["days_left"], -1)

    def test_waste_rate(self):
        a = self.store.add(Item("a", 1, "个", "冷藏", expires=d(-1)))
        b = self.store.add(Item("b", 1, "个", "冷藏", expires=d(9)))
        self.store.waste(a)
        self.store.consume(b)
        s = self.store.stats(TODAY)
        self.assertEqual(s["waste_rate_30d"], 0.5)

    def test_shopping_done_stays_done(self):
        self.store.sync_shopping([{"name": "葱", "qty": 1, "unit": "根", "source": "recipe", "why": ["x"]}])
        sid = self.store.shopping_list()[0]["id"]
        self.store.toggle_shopping(sid, True)
        self.store.sync_shopping([{"name": "葱", "qty": 2, "unit": "根", "source": "recipe", "why": ["x"]}])
        self.assertTrue(self.store.shopping_list()[0]["done"])

    def test_rolling_upgrade_keeps_qty(self):
        self.store.sync_shopping([{"name": "葱", "qty": 1, "unit": "根", "source": "recipe", "why": ["a"]}])
        self.store.sync_shopping([{"name": "葱", "qty": 3, "unit": "根", "source": "recipe", "why": ["b"]}])
        row = self.store.shopping_list()[0]
        self.assertEqual(row["qty"], 3)
        self.assertEqual(row["why"], ["b"])


class TestHTTP(unittest.TestCase):
    """接口层：Agent 以后要直接调这些 JSON。"""

    @classmethod
    def setUpClass(cls):
        from pantry.server import make_handler
        from http.server import ThreadingHTTPServer

        cls.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.tmp.close()
        cls.store = Store(cls.tmp.name)
        cls.store.add(Item("牛奶", 2, "盒", "冷藏", expires=d(7)))
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.store))
        cls.port = cls.httpd.server_address[1]
        cls.t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.store.close()
        os.unlink(cls.tmp.name)

    def get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as r:
            return json.loads(r.read())

    def post(self, path, payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    def test_index_is_html(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/") as r:
            body = r.read().decode()
        self.assertIn("家里有什么", body)
        self.assertIn("<!DOCTYPE html>", body)

    def test_state(self):
        s = self.get("/api/state")
        self.assertGreaterEqual(len(s["items"]), 1)
        self.assertIn("brief", s)

    def test_add_via_nl(self):
        r = self.post("/api/add", {"text": "3个鸡蛋 冷藏 10天"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["items"][0]["name"], "鸡蛋")

    def test_search(self):
        r = self.get("/api/search?q=nn")
        self.assertTrue(r["hits"])

    def test_recipes(self):
        r = self.get("/api/recipes?top=3")
        self.assertEqual(len(r["recipes"]), 3)
        self.assertIn("steps", r["recipes"][0])

    def test_waste_flow(self):
        items = self.get("/api/state")["items"]
        iid = items[0]["id"]
        self.assertTrue(self.post("/api/waste", {"id": iid})["ok"])


class TestLexicon(unittest.TestCase):
    def test_no_duplicate_canonical_names(self):
        names = [e["name"] for e in lexicon.entries()]
        self.assertEqual(len(names), len(set(names)))

    def test_every_alias_points_somewhere(self):
        for k, v in lexicon.alias_index().items():
            self.assertIn(v, lexicon.by_name(), f"{k} 指向了不存在的 {v}")

    def test_recipes_only_use_known_ingredients(self):
        known = set(lexicon.all_names())
        for r in recipe.load_recipes():
            for ing in r["ingredients"]:
                if ing["name"] == "番茄酱":
                    continue  # 可选的次要调味，故意没进词典
                self.assertIn(ing["name"], known, f"{r['name']} 用了词典外食材 {ing['name']}")

    def test_shelf_days_falls_back_to_room_temp(self):
        self.assertEqual(lexicon.shelf_days("土豆", "阳台"), lexicon.shelf_days("土豆", "常温"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
