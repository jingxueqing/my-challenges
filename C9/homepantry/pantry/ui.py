"""本地 Web 界面：单文件 HTML，无构建、无 CDN、离线可用。

为什么不用框架：这是一个给家里人用的东西，打开要快、要能在旧手机上跑，
而且我希望任何人拿到源码就能改。一个 index.html + 一堆 fetch 就够。
"""

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>家里有什么</title>
<style>
  :root{
    --bg:#f6f5f0; --card:#ffffff; --ink:#1c1b18; --ink2:#6b6960; --line:#e6e3da;
    --green:#0f766e; --green-bg:#e6f4f1;
    --red:#b4342a; --red-bg:#fbeae8;
    --amber:#a86a09; --amber-bg:#fdf2dd;
    --gray:#8b8981; --gray-bg:#f0eee8;
    --radius:14px;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);overflow-x:hidden;
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
  .wrap{max-width:820px;margin:0 auto;padding:22px 16px 80px}
  header{display:flex;align-items:baseline;gap:10px;margin-bottom:4px;flex-wrap:wrap}
  h1{font-size:22px;margin:0;letter-spacing:-.4px}
  .sub{color:var(--ink2);font-size:12.5px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
    padding:16px;margin-top:14px;overflow:hidden}
  .brief{background:linear-gradient(180deg,#fff7e8,#fffdf8);border-color:#f0e0bd}
  .brief b{color:#8a5200}
  .brief .more{color:var(--ink2);font-size:12.5px;margin-top:6px}
  input,button,textarea{font-family:inherit;font-size:15px}
  .row{display:flex;gap:8px}
  input[type=text]{flex:1;min-width:0;padding:12px 14px;border:1px solid var(--line);border-radius:11px;
    background:#fdfdfb;outline:none;transition:.15s}
  input[type=text]:focus{border-color:var(--green);box-shadow:0 0 0 3px var(--green-bg)}
  button{cursor:pointer;border:1px solid var(--line);background:#fbfaf7;color:var(--ink);
    padding:11px 15px;border-radius:11px;transition:.15s;white-space:nowrap}
  button:hover{background:#f2f0e9}
  button.primary{background:var(--green);border-color:var(--green);color:#fff;font-weight:600}
  button.primary:hover{background:#0c655e}
  button.mini{padding:6px 10px;font-size:12.5px;border-radius:8px}
  .hint{color:var(--ink2);font-size:12.5px;margin-top:8px}
  .chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;
    background:var(--gray-bg);color:var(--ink2);margin-right:6px}
  .tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11.5px;font-weight:600}
  .t-expired,.t-today{background:var(--red-bg);color:var(--red)}
  .t-urgent,.t-soon{background:var(--amber-bg);color:var(--amber)}
  .t-ok{background:var(--green-bg);color:var(--green)}
  .t-none{background:var(--gray-bg);color:var(--gray)}
  .item{display:flex;align-items:center;gap:10px;padding:11px 2px;border-bottom:1px dashed var(--line)}
  .item:last-child{border-bottom:none}
  .item .nm{font-weight:600;min-width:74px}
  .item .meta{color:var(--ink2);font-size:12.5px;flex:1;min-width:0}
  .item .meta .l1{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .nw{white-space:nowrap}
  .item .acts{display:flex;gap:6px}
  .bar{height:4px;border-radius:2px;margin-top:2px}
  .why{color:var(--ink2);font-size:12px;margin-top:2px}
  .sec-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
  .sec-title h2{font-size:15px;margin:0}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  @media(max-width:640px){.grid2{grid-template-columns:1fr}}
  @media(max-width:560px){
    .wrap{padding:18px 13px 70px}
    .sec-title{flex-wrap:wrap;gap:2px}
    h1{font-size:20px}
    .item{flex-wrap:wrap;row-gap:6px;padding:12px 0}
    .item > div:first-child{flex:1 1 100% !important;display:flex;align-items:center;gap:9px}
    .item .nm{min-width:0}
    .item .bar{flex:1;margin-top:0}
    .item .meta{order:2;flex:1 1 55%;min-width:0}
    .item .tag{order:3;flex:0 0 auto}
    .item .acts{order:4;flex:0 0 auto}
    .kpi{gap:12px}
  }
  .recipe{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fdfdfb}
  .recipe h3{margin:0 0 4px;font-size:14.5px}
  .recipe .steps{font-size:12.5px;color:var(--ink2);margin:8px 0 0;padding-left:16px}
  .recipe .steps li{margin-bottom:3px}
  .empty{color:var(--ink2);font-size:13.5px;padding:10px 0}
  .kpi{display:flex;gap:16px;flex-wrap:wrap;color:var(--ink2);font-size:12.5px}
  .kpi b{color:var(--ink);font-size:17px;display:block;line-height:1.2}
  .toast{position:fixed;left:50%;transform:translateX(-50%);bottom:22px;background:#1c1b18;color:#fff;
    padding:11px 16px;border-radius:11px;font-size:13.5px;max-width:90vw;opacity:0;transition:.25s;
    pointer-events:none;z-index:99;box-shadow:0 8px 24px rgba(0,0,0,.18)}
  .toast.on{opacity:1;bottom:32px}
  label.chk{display:flex;align-items:center;gap:9px;padding:8px 0;cursor:pointer}
  label.chk input{width:17px;height:17px;accent-color:var(--green)}
  .done{text-decoration:line-through;color:var(--gray)}
  .foot{color:var(--gray);font-size:11.5px;text-align:center;margin-top:26px}
  a{color:var(--green)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>家里有什么</h1>
    <span class="sub">库存 · 记忆检索 · 清冰箱</span>
  </header>
  <div class="sub" id="greet"></div>

  <div class="card brief" id="brief">
    <b>正在读取冰箱状态…</b>
  </div>

  <div class="card">
    <div class="sec-title"><h2>说一句话入库</h2><span class="hint" style="margin:0">3 秒一条</span></div>
    <div class="row">
      <input type="text" id="addInput" placeholder="2盒牛奶 冷藏 7天 ／ 半颗白菜 ／ 一碗剩菜">
      <button class="primary" id="addBtn">入库</button>
    </div>
    <div class="hint">位置、保质期都可以不说：说了就按你说的，不说就按品类常识推断，并告诉你推断依据。</div>
  </div>

  <div class="card">
    <div class="sec-title"><h2>我记得有…</h2><span class="hint" style="margin:0">忘了名字也能搜</span></div>
    <div class="row">
      <input type="text" id="q" placeholder="白色的粉 ／ nn ／ 冻的半月形 ／ 牛乃">
      <button id="qBtn">搜</button>
    </div>
    <div id="results" class="hint"></div>
  </div>

  <div class="card">
    <div class="sec-title"><h2>库存</h2><span class="hint" style="margin:0" id="invCount"></span></div>
    <div id="inventory"><div class="empty">加载中…</div></div>
  </div>

  <div class="card">
    <div class="sec-title"><h2>现在能做什么</h2><span class="hint" style="margin:0">按「现有食材覆盖率」排</span></div>
    <div id="recipes" class="grid2"><div class="empty">加载中…</div></div>
  </div>

  <div class="card">
    <div class="sec-title"><h2>购物清单</h2><button class="mini" id="syncBtn">按冰箱重算</button></div>
    <div id="shop"><div class="empty">加载中…</div></div>
  </div>

  <div class="card">
    <div class="sec-title"><h2>账本</h2><span class="hint" style="margin:0">近 30 天</span></div>
    <div class="kpi" id="kpi"></div>
  </div>

  <div class="foot">数据存在这台机器的 SQLite 里，不上云。<br>家里有什么 · v1.0</div>
</div>
<div class="toast" id="toast"></div>

<script>
const $ = s => document.querySelector(s);
const S = {};
let TOAST_T = null;
function toast(msg){
  const t = $('#toast'); t.textContent = msg; t.classList.add('on');
  clearTimeout(TOAST_T); TOAST_T = setTimeout(()=>t.classList.remove('on'), 3200);
}
function esc(s){ return (s==null?'':String(s)).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
const STATUS_CLS = {expired:'t-expired',today:'t-today',urgent:'t-urgent',soon:'t-soon',ok:'t-ok',none:'t-none'};
const STATUS_TEXT = {expired:'已过期',today:'今天到期',urgent:'3天内',soon:'7天内',ok:'还早',none:'常备'};

async function api(path, opt){
  const r = await fetch(path, opt);
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

function renderBrief(d){
  const b = d.brief;
  const wrap = $('#brief');
  if(!b.total){
    wrap.innerHTML = '<b>今天没有要抢的食材。</b><div class="more">冰箱状态良好 · 在库 ' + d.stats.items + ' 条</div>';
  } else {
    wrap.innerHTML = '<b>' + esc(b.text) + '</b><div class="more">已过期 ' + d.counts.expired +
      ' · 今天到期 ' + d.counts.today + ' · 3 天内 ' + d.counts.urgent + ' · 7 天内 ' + d.counts.soon + '</div>';
  }
  $('#greet').textContent = '在库 ' + d.stats.items + ' 条，' + (d.stats.expired ? '其中有 ' + d.stats.expired + ' 条已经过期' : '目前没有过期食材');
  $('#kpi').innerHTML = [
    ['用过', d.stats.use_30d + ' 次'],
    ['扔掉', d.stats.waste_30d + ' 次'],
    ['浪费率', Math.round(d.stats.waste_rate_30d*100) + '%'],
    ['常备待补', d.stats.level_low + ' 样'],
    ['词典', d.stats.catalog_size + ' 种'],
  ].map(([k,v])=>'<div><b>'+esc(v)+'</b>'+esc(k)+'</div>').join('');
  $('#invCount').textContent = d.items.length + ' 条，按「该先吃」排序';
}

function itemRow(it, withWhy){
  const dl = it.days_left;
  const dlText = dl===null ? '不设到期' : (dl<0 ? '过期 '+(-dl)+' 天' : (dl===0 ? '今天到期' : dl+' 天后到期'));
  const barColor = {expired:'#b4342a',today:'#b4342a',urgent:'#a86a09',soon:'#a86a09',ok:'#0f766e',none:'#c9c6bd'}[it.status];
  return `<div class="item">
    <div style="flex:0 0 96px">
      <div class="nm">${esc(it.name)}</div>
      <div class="bar" style="background:${barColor}"></div>
    </div>
    <div class="meta">
      <div class="l1">${it.qty}${esc(it.unit)} · ${esc(it.location)} · <span class="nw">${esc(it.expires||'—')}</span>${it.note ? ' · ' + esc(it.note) : ''}</div>
      <div class="why">${esc(dlText)}${withWhy ? ' ｜' + esc(it.reasons.join('；')) : ''}</div>
    </div>
    <span class="tag ${STATUS_CLS[it.status]}">${STATUS_TEXT[it.status]}</span>
    <div class="acts">
      <button class="mini" data-eat="${it.id}">用掉</button>
      <button class="mini" data-waste="${it.id}">扔掉</button>
    </div>
  </div>`;
}

function renderInventory(items){
  const el = $('#inventory');
  el.innerHTML = items.length ? items.map(it=>itemRow(it,false)).join('') :
    '<div class="empty">空的。上面写一句「2盒牛奶 冷藏 7天」试试。</div>';
}

function renderRecipes(list){
  const el = $('#recipes');
  if(!list.length){ el.innerHTML = '<div class="empty">库存太少，先录几样。</div>'; return; }
  el.innerHTML = list.map(r=>{
    const miss = r.missing.length ? '<div class="why" style="color:var(--amber)">缺：' +
      r.missing.map(m=>esc(m.name)+m.need+m.unit).join('、') + '</div>' : '';
    const use = r.uses_expiring.length ? '<div class="why" style="color:var(--red)">顺手用掉临期：' +
      r.uses_expiring.map(esc).join('、') + '</div>' : '';
    return `<div class="recipe">
      <h3>${esc(r.name)} <span class="tag ${r.cookable?'t-ok':'t-soon'}">${r.cookable?'现在能做':'差料'}</span></h3>
      <div class="why">${r.time_min} 分钟 · 覆盖 ${Math.round(r.coverage*100)}% · ${esc(r.tags.join(' / '))}</div>
      ${miss}${use}
      <ol class="steps">${r.steps.map(s=>'<li>'+esc(s)+'</li>').join('')}</ol>
      ${r.tip ? '<div class="why" style="margin-top:6px">💡 ' + esc(r.tip) + '</div>' : ''}
    </div>`;
  }).join('');
}

function renderShop(rows){
  const el = $('#shop');
  if(!rows.length){ el.innerHTML = '<div class="empty">清单是空的：冰箱够满，常备品也都在水位以上。</div>'; return; }
  el.innerHTML = rows.map(r=>`<label class="chk">
      <input type="checkbox" data-shop="${r.id}" ${r.done?'checked':''}>
      <span class="${r.done?'done':''}">${esc(r.name)} ${r.qty}${esc(r.unit)}</span>
      <span class="why">${esc(r.source==='recipe'?'做菜缺料':'常备补货')} ｜ ${esc(r.why.join('、'))}</span>
    </label>`).join('');
}

async function load(){
  const d = await api('/api/state');
  S.state = d;
  renderBrief(d);
  renderInventory(d.items);
  renderShop(d.shopping);
  const rc = await api('/api/recipes?top=4');
  renderRecipes(rc.recipes);
}

async function addItem(){
  const v = $('#addInput').value.trim();
  if(!v) return;
  const res = await api('/api/add', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:v})});
  if(!res.ok){ toast('没看懂，试着写成：2盒牛奶 冷藏 7天'); return; }
  const first = res.items[0];
  toast('记下了：' + first.name + ' ' + first.qty + first.unit + ' 放' + first.location +
        '，' + (first.expires ? first.expires + ' 到期' : '不设到期') + '（' + first.reasons[first.reasons.length-1] + '）');
  $('#addInput').value = '';
  await load();
}

async function doSearch(){
  const q = $('#q').value.trim();
  if(!q){ $('#results').textContent = ''; return; }
  const r = await api('/api/search?q=' + encodeURIComponent(q));
  if(!r.hits.length){ $('#results').innerHTML = '没找到「' + esc(q) + '」。试试更短的词，或只说特征（白色 / 粉末 / 袋装）。'; return; }
  $('#results').innerHTML = r.hits.map(h=>`<div style="margin-top:10px">
      <span class="tag ${STATUS_CLS[h.status]}">${h.score.toFixed(1)} 分</span>
      <b>${esc(h.name)}</b> ${h.qty}${esc(h.unit)} · ${esc(h.location)}
      <div class="why">${esc(h.reasons.join('；'))}</div>
    </div>`).join('');
}

document.addEventListener('click', async e=>{
  const eat = e.target.dataset.eat, waste = e.target.dataset.waste;
  if(eat){ const r = await api('/api/consume',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:+eat})});
    toast(r.left>0 ? r.name+' 还剩 '+r.left : r.name+' 用完了'); await load(); }
  if(waste){ const r = await api('/api/waste',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:+waste})});
    toast('记了笔浪费：'+r.name); await load(); }
});
document.addEventListener('change', async e=>{
  if(e.target.dataset.shop){
    await api('/api/shopping/toggle',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id:+e.target.dataset.shop, done:e.target.checked})});
  }
});
$('#addBtn').onclick = addItem;
$('#addInput').addEventListener('keydown', e=>{ if(e.key==='Enter') addItem(); });
$('#qBtn').onclick = doSearch;
$('#q').addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(); });
$('#syncBtn').onclick = async ()=>{ await api('/api/shopping/sync',{method:'POST'}); await load(); toast('按当前冰箱重算了一遍'); };
load().catch(err=>{ $('#brief').innerHTML = '<b style="color:#b4342a">连不上后端</b><div class="more">'+esc(err.message)+'</div>'; });
</script>
</body>
</html>
"""
