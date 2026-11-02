/* C6A 提交数据仪表盘 —— 纯静态、零依赖（无 CDN，可离线双击打开） */
(() => {
  "use strict";

  const DATA = JSON.parse(document.getElementById("c6a-data").textContent);
  const STATUS = {
    complete: { mark: "✅", text: "完整", cls: "complete" },
    partial: { mark: "⚠️", text: "缺件", cls: "partial" },
    missing: { mark: "❌", text: "无记录", cls: "missing" },
  };
  const state = { tab: "overview", q: "", status: "all" };

  /* ---------------------------------------------------------- utils */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pct = (v) => `${Math.round((v || 0) * 100)}%`;
  const chKey = (c) => (Number(c.replace(/\D/g, "")) * 100 + (c.replace(/[^A-Z]/g, "").charCodeAt(0) || 0));
  const fmtTime = (iso) => (iso ? iso.slice(0, 16).replace("T", " ") : "—");
  const fmtSize = (b) => (b > 1048576 ? `${(b / 1048576).toFixed(1)}MB` : b > 1024 ? `${Math.round(b / 1024)}KB` : `${b}B`);

  const recIndex = new Map();
  DATA.records.forEach((r) => recIndex.set(`${r.student}|${r.challenge_id}`, r));
  const challenges = [...DATA.challenges].sort((a, b) => chKey(a.id) - chKey(b.id));
  const chTitle = new Map(challenges.map((c) => [c.id, c.title]));

  function matchQ(...fields) {
    if (!state.q) return true;
    const q = state.q.toLowerCase();
    return fields.some((f) => String(f || "").toLowerCase().includes(q));
  }
  function matchStatus(rec) {
    return state.status === "all" || rec.status === state.status;
  }

  /* ---------------------------------------------------------- overview */
  function viewOverview() {
    const s = DATA.stats;
    const coverage = s.n_records / Math.max(1, s.n_students * s.n_challenges);
    const kpis = [
      { label: "提交者", value: s.n_students, foot: `${s.n_packages} 个提交包`, accent: true },
      { label: "挑战", value: s.n_challenges, foot: "规格来自官方 CHALLENGE.md" },
      { label: "有数据记录", value: s.n_records, foot: `共 ${s.n_files} 个文件` },
      { label: "必填项全齐", value: s.n_complete, foot: `缺件 ${s.n_partial} 条` },
      { label: "平均完整度", value: pct(s.avg_completeness), foot: `计 ${s.n_files} 个文件` },
      { label: "覆盖率", value: pct(coverage), foot: `${s.n_records} / ${s.n_students * s.n_challenges} 格（人 × 挑战）` },
    ];
    const kpiHtml = kpis.map((k) => `
      <div class="kpi ${k.accent ? "accent" : ""}">
        <div class="label">${esc(k.label)}</div>
        <div class="value num">${esc(k.value)}</div>
        <div class="foot">${esc(k.foot)}</div>
      </div>`).join("");

    const insightHtml = DATA.insights.map((i) => `
      <div class="insight ${esc(i.level)}">
        <div class="bar"></div>
        <div class="body">
          <h3>${esc(i.title)}</h3>
          <div class="ev">${esc(i.evidence)}</div>
          <div class="imp">${esc(i.implication)}</div>
        </div>
      </div>`).join("");

    const head = challenges.map((c) => `<th class="cid" title="${esc(c.title)}">${esc(c.id)}</th>`).join("");
    const rows = DATA.matrix.rows.map((row) => {
      const cells = row.cells.map((cell) => {
        const st = STATUS[cell.status] || STATUS.missing;
        const tip = cell.status === "missing"
          ? `${row.student} · ${cell.challenge}：本机无提交记录`
          : `${row.student} · ${cell.challenge}：${st.text} ${pct(cell.completeness)}${cell.missing.length ? "，缺 " + cell.missing.join("、") : ""}`;
        return `<td><div class="cell ${st.cls}" role="button" tabindex="0" title="${esc(tip)}"
          data-stu="${esc(row.student)}" data-chal="${esc(cell.challenge)}">${st.mark}</div></td>`;
      }).join("");
      const stu = DATA.students.find((x) => x.name === row.student) || {};
      return `<tr>
        <th class="rowhead"><div class="student-name">${esc(row.student)}<small>${esc(stu.student_id || stu.major || "")}</small></div></th>
        ${cells}
      </tr>`;
    }).join("");

    const allChal = challenges.map((c) => {
      const recs = DATA.records.filter((r) => r.challenge_id === c.id);
      const avg = recs.length ? recs.reduce((a, r) => a + r.completeness, 0) / recs.length : 0;
      return { id: c.id, title: c.title, n: recs.length, avg, complete: recs.filter((r) => r.status === "complete").length };
    });
    const byChal = allChal.filter((c) => c.n).sort((a, b) => b.n - a.n || b.avg - a.avg);
    const zeroChal = allChal.filter((c) => !c.n).map((c) => c.id);
    const barHtml = byChal.map((c) => `
      <div class="bar-row" data-goto="${esc(c.id)}">
        <div class="name">${esc(c.id)}<small>${c.complete}/${c.n} 完整</small></div>
        <div class="track"><div class="fill ${c.avg >= 0.99 ? "" : "warn"}" style="width:${Math.max(2, c.avg * 100)}%"></div></div>
        <div class="pct">${pct(c.avg)}</div>
      </div>`).join("") + (zeroChal.length
        ? `<div class="foot-note">另有 ${zeroChal.length} 个挑战本机无数据（${esc(zeroChal.join("、"))}）：规格已抽取，等数据。</div>` : "");

    const missingRecs = DATA.records.filter((r) => r.missing.length);
    const remindHtml = missingRecs.length
      ? missingRecs.map((r) => `
        <div class="rec" data-stu="${esc(r.student)}" data-chal="${esc(r.challenge_id)}">
          <div class="chip-id">${esc(r.challenge_id)}</div>
          <div><div class="title">${esc(r.student)} · ${esc(r.challenge_title)}</div>
          <div class="sub">缺：${esc(r.missing.join("、"))}</div></div>
          <div class="right"><span class="pill partial">${r.missing.length} 项</span></div>
        </div>`).join("")
      : `<div class="empty">没有缺件记录。</div>`;

    return `
      <div class="grid-kpi">${kpiHtml}</div>
      <div class="insights">${insightHtml}</div>
      <section class="card" style="margin-bottom:16px">
        <div class="card-head"><h2>提交矩阵</h2>
          <span class="hint">${DATA.stats.n_students} 行 × ${challenges.length} 列 ｜ 点格子看该条记录</span></div>
        <div class="matrix-wrap">
          <table class="matrix">
            <thead><tr><th class="rowhead">学生 \\ 挑战</th>${head}</tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        <div class="legend">
          <span><i class="sw" style="background:var(--ok-bg);border-color:#cfe8db"></i>✅ 必填齐全</span>
          <span><i class="sw" style="background:var(--warn-bg);border-color:#f0dcb6"></i>⚠️ 缺件</span>
          <span><i class="sw" style="background:#f4f5f7;border-color:#ebedf0"></i>❌ 本机无记录（≠ 判定未交）</span>
        </div>
      </section>
      <div style="display:grid;grid-template-columns:1.1fr .9fr;gap:16px" class="ov-grid">
        <section class="card card-pad">
          <div class="card-head" style="padding:0 0 6px"><h2>各挑战完整度</h2><span class="hint">按提交人数排序</span></div>
          ${barHtml}
        </section>
        <div>
          <section class="card">
            <div class="card-head"><h2>缺件提醒</h2><span class="hint">该补什么，一目了然</span></div>
            <div style="padding:6px 0 10px">${remindHtml}</div>
          </section>
          <section class="card card-pad" style="margin-top:16px">
            <div class="card-head" style="padding:0 0 8px"><h2>怎么读这个看板</h2></div>
            <ul class="readguide">
              <li><b>✅ 完整</b>：该挑战的必填项全部命中，且每个命中都能点回具体文件。</li>
              <li><b>⚠️ 缺件</b>：有产出但少必填项，鼠标移到格子上能直接看到缺哪几项。</li>
              <li><b>❌ 无记录</b>：本机磁盘上没有这个包。这是「采集不到」，<b>不是</b>「判定未交」。</li>
              <li><b>时间</b>：取包内文件最后修改时间，属近似值；复制或解压会刷新它。</li>
              <li><b>完整度</b>＝命中的必填项 ÷ 必填项总数；一个文件只算一个交付项。</li>
            </ul>
          </section>
        </div>
      </div>`;
  }

  /* ---------------------------------------------------------- students */
  function viewStudents() {
    const cards = DATA.students.map((student) => {
      const recs = DATA.records
        .filter((r) => r.student === student.name)
        .filter((r) => matchStatus(r) && matchQ(r.student, r.challenge_id, r.challenge_title, r.missing.join(" ")))
        .sort((a, b) => chKey(a.challenge_id) - chKey(b.challenge_id));
      if (!recs.length && (state.q || state.status !== "all")) return "";
      const allRecs = DATA.records.filter((r) => r.student === student.name);
      const avg = allRecs.length ? allRecs.reduce((a, r) => a + r.completeness, 0) / allRecs.length : 0;
      const rows = recs.length
        ? recs.map((r) => {
            const st = STATUS[r.status];
            return `<div class="rec" data-stu="${esc(r.student)}" data-chal="${esc(r.challenge_id)}">
              <div class="chip-id">${esc(r.challenge_id)}</div>
              <div><div class="title">${esc(r.challenge_title)}</div>
                <div class="sub">${fmtTime(r.submitted_at)} ｜ ${r.n_files} 个文件${r.missing.length ? " ｜ 缺 " + esc(r.missing.join("、")) : ""}</div></div>
              <div class="right">
                <div class="mini-track"><div class="mini-fill ${r.status === "complete" ? "" : "partial"}" style="width:${Math.max(4, r.completeness * 100)}%"></div></div>
                <span class="pill ${st.cls}">${st.text}</span>
              </div>
            </div>`;
          }).join("")
        : `<div class="empty">本机没有该同学的提交记录。</div>`;
      return `<section class="stu">
        <div class="stu-head">
          <div class="row"><h3>${esc(student.name)}</h3>
            <span class="meta">${esc(student.student_id || student.major || "")}</span></div>
          <div class="stats">
            <div class="stat"><div class="k">已提交</div><div class="v num">${allRecs.length}<small> 个挑战</small></div></div>
            <div class="stat"><div class="k">必填全齐</div><div class="v num">${allRecs.filter((r) => r.status === "complete").length}</div></div>
            <div class="stat"><div class="k">平均完整度</div><div class="v num">${pct(avg)}</div></div>
          </div>
        </div>
        ${rows}
      </section>`;
    }).join("");
    return `<div class="stu-grid">${cards || `<div class="empty">没有匹配的提交者。</div>`}</div>`;
  }

  /* ---------------------------------------------------------- challenges */
  function viewChallenges() {
    const items = challenges
      .filter((c) => matchQ(c.id, c.title))
      .map((c) => {
        const recs = DATA.records.filter((r) => r.challenge_id === c.id && matchStatus(r));
        const avg = recs.length ? recs.reduce((a, r) => a + r.completeness, 0) / recs.length : 0;
        const slots = c.items.filter((i) => i.required).map((i) => {
          const hit = DATA.records.filter((r) => r.challenge_id === c.id && r.items.some((x) => x.label === i.label && x.present)).length;
          const total = DATA.records.filter((r) => r.challenge_id === c.id).length;
          const cls = !total ? "" : hit === total ? "hit" : hit ? "" : "miss";
          return `<span class="slot ${cls}" title="${esc(i.label)}">
            ${esc(i.label)}${total ? `<span class="n">${hit}/${total}</span>` : ""}</span>`;
        }).join("");
        return `<div class="chal-item">
          <div class="chal-top">
            <span class="id">${esc(c.id)}</span>
            <span class="t">${esc(c.title)}</span>
            <span class="spacer"></span>
            <span class="chal-meta">必填 ${c.n_required} 项 ｜ 提交 ${recs.length} 人 ｜ 平均 ${recs.length ? pct(avg) : "—"}</span>
            ${recs.length ? `<div class="mini-track" style="width:80px"><div class="mini-fill ${avg >= 0.99 ? "" : "partial"}" style="width:${Math.max(3, avg * 100)}%"></div></div>` : ""}
          </div>
          <div class="slot-grid">${slots || `<span class="chal-meta">无必填项规格</span>`}</div>
          ${recs.length ? `<div class="slot-grid" style="margin-top:6px">${recs.map((r) => `
            <span class="pill ${r.status}" style="cursor:pointer" data-stu="${esc(r.student)}" data-chal="${esc(c.id)}">${esc(r.student)} ${pct(r.completeness)}</span>`).join("")}</div>`
            : `<div class="chal-meta" style="margin-top:6px">本机没有该挑战的提交记录——规格已就绪，等数据。</div>`}
        </div>`;
      }).join("");
    return `<section class="card"><div class="chal">${items || `<div class="empty">没有匹配的挑战。</div>`}</div></section>`;
  }

  /* ---------------------------------------------------------- timeline */
  function viewTimeline() {
    const recs = DATA.records
      .filter((r) => matchStatus(r) && matchQ(r.student, r.challenge_id, r.challenge_title))
      .sort((a, b) => (a.submitted_at < b.submitted_at ? 1 : -1));
    if (!recs.length) return `<section class="card"><div class="empty">没有匹配的记录。</div></section>`;
    const groups = new Map();
    recs.forEach((r) => {
      const m = (r.submitted_at || "").slice(0, 7);
      if (!groups.has(m)) groups.set(m, []);
      groups.get(m).push(r);
    });
    const html = [...groups.entries()].map(([month, list]) => `
      <div class="tl-month">${esc(month)}</div>
      ${list.map((r) => `
        <div class="tl-row ${r.status}" data-stu="${esc(r.student)}" data-chal="${esc(r.challenge_id)}" style="cursor:pointer">
          <span class="when">${esc(fmtTime(r.submitted_at))}</span>
          <span class="who">${esc(r.student)}</span>
          <span class="what">${esc(r.challenge_id)} · ${esc(r.challenge_title)}</span>
          <span class="pill ${STATUS[r.status].cls}">${STATUS[r.status].text}</span>
        </div>`).join("")}
    `).join("");
    return `<section class="card card-pad"><div class="tl">${html}</div>
      <div class="note" style="margin-top:18px">口径：时间为提交包内文件的最后修改时间（本地没有平台时间戳）。同一学生同一挑战有多份副本时，取最新那份。</div>
    </section>`;
  }

  /* ---------------------------------------------------------- missing */
  function viewMissing() {
    const recs = DATA.records
      .filter((r) => r.missing.length)
      .filter((r) => matchQ(r.student, r.challenge_id, r.challenge_title, r.missing.join(" ")));
    const counter = new Map();
    recs.forEach((r) => r.missing.forEach((m) => counter.set(m, (counter.get(m) || 0) + 1)));
    const topMiss = [...counter.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    const rows = recs.map((r) => `
      <tr data-stu="${esc(r.student)}" data-chal="${esc(r.challenge_id)}" style="cursor:pointer">
        <td><strong>${esc(r.student)}</strong></td>
        <td class="num">${esc(r.challenge_id)}</td>
        <td>${esc(r.challenge_title)}</td>
        <td class="miss">${esc(r.missing.join("、"))}</td>
        <td>${esc(r.present_required.join("、") || "—")}</td>
        <td class="num">${pct(r.completeness)}</td>
      </tr>`).join("");
    return `
      <section class="card card-pad" style="margin-bottom:16px">
        <div class="card-head" style="padding:0 0 8px"><h2>最常缺的交付项</h2><span class="hint">出现次数越多，越可能是规则或提醒的问题</span></div>
        <div class="slot-grid">${topMiss.map(([k, v]) => `<span class="slot miss">${esc(k)}<span class="n">${v}</span></span>`).join("") || `<span class="chal-meta">没有缺件</span>`}</div>
      </section>
      <section class="card">
        <div class="card-head"><h2>缺件记录</h2><span class="hint">${recs.length} 条</span></div>
        <div style="padding:8px 8px 16px">
          <table class="data">
            <thead><tr><th>学生</th><th>挑战</th><th>挑战名</th><th>缺失的必填项</th><th>已交必填项</th><th>完整度</th></tr></thead>
            <tbody>${rows || `<tr><td colspan="6"><div class="empty">没有缺件记录。</div></td></tr>`}</tbody>
          </table>
        </div>
      </section>`;
  }

  /* ---------------------------------------------------------- method */
  function viewMethod() {
    const prov = DATA.provenance;
    const roots = prov.roots.map((r) => `<li><strong>${esc(r.label)}</strong><br><span class="num" style="font-size:11px;color:var(--muted);word-break:break-all">${esc(r.path)}</span></li>`).join("");
    const caveats = prov.caveats.map((c) => `<li>${esc(c)}</li>`).join("");
    const specRows = challenges.map((c) => `
      <tr><td class="num">${esc(c.id)}</td><td>${esc(c.title)}</td>
      <td class="num">${c.n_required}/${c.n_items}</td>
      <td><span class="tag ${c.origin.includes("patch") ? "req" : ""}">${esc(c.origin)}</span></td>
      <td style="font-size:11.5px;color:var(--ink-2)">${esc(c.items.filter((i) => i.required).map((i) => i.label).join("、"))}</td></tr>`).join("");
    const fmtVal = (v) => (Array.isArray(v) ? v.join("、") : typeof v === "object" ? JSON.stringify(v) : String(v));
    const rules = Object.entries(prov.scan_rules).map(([k, v]) => `<li><b>${esc(k)}</b>：${esc(fmtVal(v))}</li>`).join("");
    return `
      <div class="method">
        <section class="card"><h3>数据从哪来</h3><ul>${roots}</ul>
          <div class="note" style="margin-top:10px">挑战规格来自：<span class="num" style="font-size:11px">${esc(prov.challenge_doc_root)}</span> 下的 20 份 CHALLENGE.md。</div></section>
        <section class="card"><h3>扫描与判定规则</h3><ul>${rules}</ul></section>
        <section class="card"><h3>已知局限（不影响可复核）</h3><ul>${caveats}</ul></section>
        <section class="card"><h3>怎么更新数据</h3>
          <pre class="code"><span class="c"># 1. 把新提交包放进数据根目录（命名：姓名_C4B_xxx.md）</span>
cd JingXueQing_C6A_pipeline
python3 run.py all</pre>
          <div class="note">整条链路：规格抽取 → 扫描 → 匹配 → JSON/CSV → Excel → 网站，全部脚本化，改数据不用改代码。</div></section>
      </div>
      <section class="card" style="margin-top:14px">
        <div class="card-head"><h2>挑战规格明细</h2><span class="hint">origin=challenge_doc 自动抽取；patch 为人工补丁（补丁理由见 specs.py）</span></div>
        <div style="padding:8px 8px 16px">
          <table class="data">
            <thead><tr><th>挑战</th><th>标题</th><th>必填/全部</th><th>规格来源</th><th>必填项</th></tr></thead>
            <tbody>${specRows}</tbody>
          </table>
        </div>
      </section>`;
  }

  /* ---------------------------------------------------------- drawer */
  function openRecord(student, challenge) {
    const rec = recIndex.get(`${student}|${challenge}`);
    const spec = challenges.find((c) => c.id === challenge);
    const items = rec ? rec.items : (spec ? spec.items : []).map((i) => ({ ...i, present: false, file: null }));
    const st = rec ? STATUS[rec.status] : STATUS.missing;
    const checklist = items.map((i) => `
      <div class="chk ${i.present ? "on" : ""}">
        <span class="mark">${i.present ? "✅" : "❌"}</span>
        <span><span class="lbl">${esc(i.label)}</span>
          ${i.file ? `<div class="f">${esc(i.file)}</div>` : `<div class="f">未匹配到文件</div>`}</span>
        <span class="tag ${i.required ? "req" : ""}">${i.required ? "必填" : "可选"}</span>
      </div>`).join("");
    const files = rec ? rec.files.slice(0, 60).map((f) => `
      <div class="file-row">
        <div><div class="p">${esc(f.rel_path)}</div>
          <div class="sz">${f.is_dir ? "目录" : fmtSize(f.size)} ｜ ${esc(f.category)}${f.matched_item ? " ｜ 命中：" + esc(f.matched_item) : ""}</div></div>
        <button class="copy" data-copy="${esc(f.rel_path)}">复制路径</button>
      </div>`).join("") : "";
    const kv = rec ? `
      <dl class="kv">
        <dt>状态</dt><dd><span class="pill ${st.cls}">${st.text}</span> ${pct(rec.completeness)}</dd>
        <dt>提交时间</dt><dd class="num">${fmtTime(rec.submitted_at)}</dd>
        <dt>文件数</dt><dd class="num">${rec.n_files}${rec.deep_files_not_counted ? `（另有 ${rec.deep_files_not_counted} 个深层文件未计入）` : ""}</dd>
        <dt>提交包</dt><dd>${rec.packages.map((p) => `<div class="num" style="font-size:11px">${esc(p)}</div>`).join("")}${rec.duplicate_package ? `<div style="color:var(--warn);font-size:11.5px">⚠️ 存在重复提交包</div>` : ""}</dd>
        <dt>命名合规</dt><dd class="num">${pct(rec.quality.naming_compliance)}（${rec.quality.n_matched} 个命中文件）</dd>
        <dt>AI 日志</dt><dd>${rec.quality.ai_log_ok ? "✅ 可用" : "⚠️ 缺失或过短"} ${rec.quality.ai_log_size ? `<span class="num" style="font-size:11px;color:var(--muted)">${fmtSize(rec.quality.ai_log_size)}</span>` : ""}</dd>
        ${rec.review ? `<dt>C4A 评审</dt><dd>质量分 <b class="num">${rec.review.composite}</b>（completeness ${rec.review.completeness_score}，${esc(rec.review.verdict || "")}）</dd>` : ""}
      </dl>` : `<div class="note">本机没有这条记录。不是「判定未交」，而是「采集不到」——需要把该同学的提交包放进数据根目录再跑一次。</div>`;

    $("#drawer-title").textContent = `${student} · ${challenge}`;
    $("#drawer-sub").textContent = spec ? spec.title : "";
    $("#drawer-body").innerHTML = `
      <div class="sec-title">基本信息</div>${kv}
      <div class="sec-title">交付项清单（${items.filter((i) => i.present).length}/${items.length}）</div>
      <div class="checklist">${checklist}</div>
      ${files ? `<div class="sec-title">文件清单（前 60 个）</div>${files}` : ""}`;
    $("#overlay").classList.add("on");
    $("#drawer").classList.add("on");
    $("#drawer").setAttribute("aria-hidden", "false");
  }

  function closeDrawer() {
    $("#overlay").classList.remove("on");
    $("#drawer").classList.remove("on");
    $("#drawer").setAttribute("aria-hidden", "true");
  }

  /* ---------------------------------------------------------- render */
  const VIEWS = { overview: viewOverview, students: viewStudents, challenges: viewChallenges, timeline: viewTimeline, missing: viewMissing, method: viewMethod };

  function render() {
    const fn = VIEWS[state.tab] || viewOverview;
    $("#view").innerHTML = fn();
    $$("nav.tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === state.tab)));
    $("#filters").style.display = ["students", "timeline", "missing", "challenges"].includes(state.tab) ? "flex" : "none";
    if (location.hash.slice(1) !== state.tab) history.replaceState(null, "", `#${state.tab}`);
    bindDynamic();
  }

  function bindDynamic() {
    $$("#view [data-stu]").forEach((el) => {
      const open = () => openRecord(el.dataset.stu, el.dataset.chal);
      el.addEventListener("click", open);
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
      });
    });
    $$("#view [data-goto]").forEach((el) => el.addEventListener("click", () => {
      state.tab = "challenges"; state.q = el.dataset.goto; $("#q").value = state.q; render();
    }));
    $$("[data-copy]").forEach((el) => el.addEventListener("click", (e) => {
      e.stopPropagation();
      const p = el.dataset.copy;
      const done = () => { el.textContent = "已复制"; setTimeout(() => (el.textContent = "复制路径"), 1200); };
      if (navigator.clipboard) navigator.clipboard.writeText(p).then(done).catch(done);
      else done();
    }));
  }

  function initTabs() {
    const counts = {
      students: DATA.students.length,
      challenges: challenges.length,
      timeline: DATA.records.length,
      missing: DATA.records.filter((r) => r.missing.length).length,
    };
    const labels = { overview: "总览", students: "按学生", challenges: "按挑战", timeline: "时间线", missing: "缺失项", method: "方法与口径" };
    $$("nav.tabs button").forEach((b) => {
      const c = counts[b.dataset.tab];
      b.innerHTML = `${labels[b.dataset.tab]}${c !== undefined ? `<span class="count">${c}</span>` : ""}`;
      b.addEventListener("click", () => { state.tab = b.dataset.tab; render(); window.scrollTo({ top: 0, behavior: "smooth" }); });
    });
  }

  function initFilters() {
    $("#q").addEventListener("input", (e) => { state.q = e.target.value.trim(); render(); });
    $$("#filters .chip").forEach((chip) => chip.addEventListener("click", () => {
      state.status = chip.dataset.status;
      $$("#filters .chip").forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      render();
    }));
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
    if (e.key === "/" && document.activeElement !== $("#q")) { e.preventDefault(); $("#q").focus(); }
  });
  $("#overlay").addEventListener("click", closeDrawer);
  $("#drawer-close").addEventListener("click", closeDrawer);

  // 头部信息
  const s = DATA.stats;
  $("#gen-time").textContent = fmtTime(DATA.generated_at);
  $("#ds-brief").textContent = `${s.n_packages} 个真实提交包 ｜ ${s.n_files} 个文件 ｜ schema ${DATA.schema_version}`;

  initTabs();
  initFilters();
  const rawHash = decodeURIComponent((location.hash || "#overview").slice(1));
  const hash = rawHash;
  const deep = rawHash.match(/^record=(.+?)\|(.+)$/);
  state.tab = VIEWS[hash] ? hash : "overview";
  render();
  if (deep) openRecord(decodeURIComponent(deep[1]), decodeURIComponent(deep[2]));
})();
