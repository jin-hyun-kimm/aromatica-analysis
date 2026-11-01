# -*- coding: utf-8 -*-
"""
05_build_dashboard.py — 대시보드 생성

metrics.json과 data/*.csv에서 수치를 읽어 index.html을 만든다.
보고서와 같은 계산 결과를 쓰므로 대시보드와 보고서의 숫자가 어긋날 수 없다.

실행:  python3 code/05_build_dashboard.py
출력:  index.html  (단일 파일, 외부 의존성 없음)
"""
import csv, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "metrics.json"), encoding="utf-8") as f:
    D = json.load(f)
M = D["metrics"]
BR = {b["item"]: b for b in D["bridge_2024"]}
FC = D["finance_cost_2023"]


def load(name):
    with open(os.path.join(BASE, "data", name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


seg = {}
for r in load("segment_revenue.csv"):
    seg.setdefault(int(r["year"]), {})[r["segment"]] = int(r["revenue_million_krw"])
prod = {}
for r in load("product_revenue.csv"):
    prod.setdefault(r["product"], {})[int(r["year"])] = int(r["revenue_million_krw"])
vlog = list(csv.DictReader(open(os.path.join(BASE, "verification_log.csv"), encoding="utf-8-sig")))
srcs = load("sources.csv")

YEARS = ["2023", "2024", "2025"]
TOT = {y: seg[int(y)]["헤어&스칼프"] + seg[int(y)]["스킨&바디"] for y in YEARS}

# 히어로: 당기순이익 변화를 영업 / 재무 / 기타 세 갈래로 묶는다
op_part = BR["영업이익"]["value"]
fin_part = BR["금융원가 감소"]["value"]
total = D["bridge_2024_total"]
etc_part = total - op_part - fin_part

PAYLOAD = {
    "years": YEARS,
    "metrics": {y: {k: M[y][k] for k in (
        "revenue", "operating_income", "net_income", "finance_cost", "ocf",
        "operating_margin", "net_margin", "finance_cost_ratio", "debt_ratio",
        "ocf_to_op", "ocf_to_ni", "revenue_growth", "op_growth", "ni_growth", "ocf_growth",
        "sga", "cash_from_operations",
    )} for y in YEARS},
    "bridge": D["bridge_2024"],
    "bridgeTotal": total,
    "hero": {"op": op_part, "fin": fin_part, "etc": etc_part, "total": total},
    "financeCost2023": FC,
    "segments": {y: {"hair": seg[int(y)]["헤어&스칼프"],
                     "skin": seg[int(y)]["스킨&바디"],
                     "total": TOT[y]} for y in YEARS},
    "products": {k: {str(y): v[y] for y in (2023, 2024, 2025)} for k, v in prod.items()},
    "exportDomestic": D["export_domestic"],
    "verification": {"total": len(vlog),
                     "passed": sum(1 for c in vlog if c["result"] == "통과"),
                     "derived": sum(1 for c in vlog if c["kind"] == "도출값 재현"),
                     "crossChecked": sum(1 for c in vlog if c["kind"] != "도출값 재현")},
    "sources": [{"report": r["report"], "rcp": r["rcp_no"], "date": r["receipt_date"]}
                for r in srcs],
}

HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>아로마티카 이익의 출처</title>
<meta name="description" content="2023~2025년 아로마티카의 이익 개선이 영업 성과에서 왔는지 재무구조 변화에서 왔는지를 DART 공시 원문으로 확인한 분석.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  color-scheme: light;
  --bg:#f7f8f5; --panel:#ffffff; --ink:#1a1c1a; --ink2:#5a5f5c; --ink3:#8b918c;
  --rule:#dfe3dd; --rule-strong:#c3c9c1;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;
  --quiet:#9aa09b;
  --measure:62ch;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --bg:#14171a; --panel:#1a1e22; --ink:#eef1ee; --ink2:#b6bdb8; --ink3:#848b86;
    --rule:#2b3137; --rule-strong:#3c444b;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70;
    --quiet:#6f7873;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --bg:#14171a; --panel:#1a1e22; --ink:#eef1ee; --ink2:#b6bdb8; --ink3:#848b86;
  --rule:#2b3137; --rule-strong:#3c444b;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70;
  --quiet:#6f7873;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans KR",system-ui,-apple-system,sans-serif;
  font-weight:400; line-height:1.65; font-size:16px;
  font-variant-numeric:tabular-nums;
  word-break:keep-all; overflow-wrap:anywhere;
  -webkit-font-smoothing:antialiased;
}
.wrap{
  max-width:62rem;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
}
@media(min-width:48rem){.wrap{padding-left:max(2.5rem,env(safe-area-inset-left,0px));padding-right:max(2.5rem,env(safe-area-inset-right,0px))}}

/* ── 머리말 ── */
.masthead{padding:3.5rem 0 0}
.kicker{font-size:.8rem;letter-spacing:.01em;color:var(--ink3);font-weight:500;margin:0 0 1.75rem}
.kicker b{font-weight:600;color:var(--ink2)}
h1{
  font-size:clamp(2rem,6.2vw,3.5rem); line-height:1.12; font-weight:700;
  letter-spacing:-.022em; margin:0 0 1.1rem; max-width:21ch;
}
h1 .turn{display:block;color:var(--ink3);font-weight:300}
.standfirst{font-size:1.0625rem;color:var(--ink2);max-width:var(--measure);margin:0 0 2.75rem;font-weight:300}

/* ── 히어로 ── */
.hero{border-top:1px solid var(--rule-strong);padding-top:1.5rem;margin-bottom:3.5rem}
.hero-q{font-size:.8125rem;color:var(--ink3);margin:0 0 1.4rem;font-weight:500}
.hero-q strong{color:var(--ink2);font-weight:600}
.split{display:grid;gap:1.1rem}
.lane{display:grid;grid-template-columns:7.5rem 1fr;gap:.9rem;align-items:center}
@media(max-width:34rem){.lane{grid-template-columns:1fr;gap:.35rem}}
.lane-label{font-size:.875rem;color:var(--ink2);font-weight:500;line-height:1.3}
.lane-label em{display:block;font-style:normal;font-size:.75rem;color:var(--ink3);font-weight:400}
.lane-bar{display:flex;align-items:center;gap:.7rem}
.lane-track{position:relative;flex:1;min-width:0;height:2.5rem}
.lane-fill{position:absolute;inset-block:0;left:0;border-radius:0 3px 3px 0}
.lane-fill.neg{background:var(--quiet)}
.lane-val{flex:none;font-size:.9375rem;font-weight:600;white-space:nowrap;color:var(--ink)}
.lane-val i{font-style:normal;font-weight:400;color:var(--ink3)}
.hero-note{font-size:.8125rem;color:var(--ink3);margin:1.5rem 0 0;max-width:var(--measure)}

/* ── 지표 줄 ── */
.strip{display:grid;grid-template-columns:repeat(2,1fr);gap:0;border-top:1px solid var(--rule);margin-bottom:3.5rem}
@media(min-width:40rem){.strip{grid-template-columns:repeat(4,1fr)}}
.stat{padding:1.1rem 1.1rem 1.25rem 0;border-bottom:1px solid var(--rule)}
@media(min-width:40rem){.stat{border-bottom:none}}
.stat-k{font-size:.75rem;color:var(--ink3);margin:0 0 .35rem;font-weight:500}
.stat-v{font-size:1.5rem;font-weight:600;letter-spacing:-.015em;line-height:1.15;margin:0}
.stat-v small{font-size:.8125rem;font-weight:400;color:var(--ink3);margin-left:.2rem}
.stat-d{font-size:.75rem;margin:.3rem 0 0;color:var(--ink3)}
.stat-d.up{color:var(--s3)} .stat-d.down{color:var(--s2)}

/* ── 섹션 ── */
section{margin-bottom:3.75rem}
.sec-h{display:flex;align-items:baseline;gap:.7rem;margin:0 0 .5rem;flex-wrap:wrap}
.sec-n{font-size:.75rem;color:var(--ink3);font-weight:600;letter-spacing:.02em}
h2{font-size:1.1875rem;font-weight:600;letter-spacing:-.012em;margin:0}
.sec-p{font-size:.9375rem;color:var(--ink2);max-width:var(--measure);margin:0 0 1.5rem;font-weight:300}

figure{margin:0}
.plot{background:var(--panel);border:1px solid var(--rule);border-radius:4px;padding:1.1rem .85rem .7rem}
.plot svg{display:block;width:100%;height:auto;overflow:visible}
figcaption{font-size:.75rem;color:var(--ink3);margin-top:.65rem;max-width:var(--measure)}
.legend{display:flex;flex-wrap:wrap;gap:.3rem 1.1rem;margin:0 0 .9rem;padding:0 .25rem}
.legend li{list-style:none;display:flex;align-items:center;gap:.4rem;font-size:.8125rem;color:var(--ink2)}
.swatch{width:.7rem;height:.7rem;border-radius:2px;flex:none}

/* SVG */
.grid-line{stroke:var(--rule);stroke-width:1}
.axis-line{stroke:var(--rule-strong);stroke-width:1}
.tick{fill:var(--ink3);font-size:11px}
.dlabel{fill:var(--ink2);font-size:11px;font-weight:500}
.dlabel.inv{fill:#fff}
.hit{fill:transparent;cursor:crosshair}
.mark{transition:opacity .12s ease}
.dim .mark{opacity:.3}
.mark.on{opacity:1}
@media(prefers-reduced-motion:reduce){.mark{transition:none}}

.tip{
  position:fixed;pointer-events:none;z-index:40;opacity:0;transform:translate(-50%,-115%);
  background:var(--ink);color:var(--bg);border-radius:4px;padding:.45rem .6rem;
  font-size:.75rem;line-height:1.5;white-space:nowrap;transition:opacity .1s ease;
}
.tip.show{opacity:1}
.tip b{font-weight:600}
.tip i{font-style:normal;opacity:.7}

/* 표 */
table{width:100%;border-collapse:collapse;font-size:.875rem}
caption{text-align:left;font-size:.75rem;color:var(--ink3);margin-bottom:.5rem}
th,td{padding:.5rem .55rem;border-bottom:1px solid var(--rule);text-align:right}
th:first-child,td:first-child{text-align:left}
thead th{font-weight:600;font-size:.75rem;color:var(--ink2);border-bottom:1px solid var(--rule-strong)}
tbody tr:last-child td{border-bottom:none}
td.em{font-weight:600}
.neg{color:var(--s2)}

/* 문제 후보 */
.finding{border-left:2px solid var(--s1);padding:.1rem 0 .1rem 1.1rem;margin:0 0 1.5rem;max-width:var(--measure)}
.finding h3{font-size:.9375rem;font-weight:600;margin:0 0 .3rem}
.finding p{font-size:.875rem;color:var(--ink2);margin:0;font-weight:300}
.stack{display:grid;gap:1.4rem}
@media(min-width:52rem){.stack.three{grid-template-columns:repeat(3,1fr)}}
.block h3{font-size:.8125rem;color:var(--ink3);font-weight:600;margin:0 0 .6rem;padding-bottom:.4rem;border-bottom:1px solid var(--rule)}
.block ul{margin:0;padding:0;list-style:none}
.block li{font-size:.8125rem;color:var(--ink2);margin-bottom:.6rem;font-weight:300;line-height:1.55}
.block li b{font-weight:600;color:var(--ink)}

/* 꼬리말 */
footer{border-top:1px solid var(--rule-strong);padding:1.5rem 0 4rem;font-size:.8125rem;color:var(--ink3)}
footer p{margin:0 0 .6rem;max-width:var(--measure);font-weight:300}
footer a{color:var(--s1);text-decoration:none;border-bottom:1px solid transparent}
footer a:hover,footer a:focus-visible{border-bottom-color:currentColor}
.srcs{display:grid;gap:.15rem;margin:.9rem 0 0;padding:0;list-style:none}
.srcs li{display:flex;gap:.6rem;flex-wrap:wrap;font-size:.75rem}
.srcs b{font-weight:500;color:var(--ink2);min-width:11rem}
:focus-visible{outline:2px solid var(--s1);outline-offset:2px;border-radius:2px}
.toggle{
  position:fixed;top:calc(.85rem + env(safe-area-inset-top,0px));right:calc(.85rem + env(safe-area-inset-right,0px));z-index:50;background:var(--panel);
  border:1px solid var(--rule-strong);color:var(--ink2);border-radius:999px;
  padding:.3rem .75rem;font:inherit;font-size:.75rem;cursor:pointer;
}
.toggle:hover{color:var(--ink)}
</style>
</head>
<body>
<button class="toggle" id="themeBtn" type="button">야간</button>
<div class="wrap">

<header class="masthead">
  <p class="kicker">아로마티카(주) · 2023~2025 사업연도 · <b>DART 공시 원문 기준</b></p>
  <h1>이익은 좋아졌다<span class="turn">그 원천은 대부분 영업 밖에 있었다</span></h1>
  <p class="standfirst" id="stand"></p>
</header>

<div class="hero">
  <p class="hero-q">2024년 당기순이익 변화 <strong>+__TOTAL__억원</strong>은 어디서 왔는가</p>
  <div class="split" id="hero"></div>
  <p class="hero-note" id="heronote"></p>
</div>

<div class="strip" id="strip"></div>

<section>
  <div class="sec-h"><span class="sec-n">그림 1</span><h2>수익성은 거의 그대로, 금융원가만 사라졌다</h2></div>
  <p class="sec-p" id="sec2p"></p>
  <figure>
    <ul class="legend" id="lg1"></ul>
    <div class="plot"><svg id="c1" viewBox="0 0 720 300" role="img" aria-label="2023~2025년 영업이익률·당기순이익률·금융원가율 추이"></svg></div>
    <figcaption>단위 %. 출처: 2025 사업보고서(20260320001362) III-4-2 포괄손익계산서.</figcaption>
  </figure>
</section>

<section>
  <div class="sec-h"><span class="sec-n">그림 2</span><h2>흑자 전환을 만든 것</h2></div>
  <p class="sec-p">2023년 순손실에서 2024년 순이익까지의 경로. 각 항목의 산술적 기여도이며, 항목 사이의 인과관계를 뜻하지는 않는다.</p>
  <figure>
    <div class="plot"><svg id="c2" viewBox="0 0 720 330" role="img" aria-label="2024년 당기순이익 변화의 항목별 분해"></svg></div>
    <figcaption>단위 억원. 비용 항목은 감소가 이익 증가로 작용하므로 부호를 반전했다.</figcaption>
  </figure>
</section>

<section>
  <div class="sec-h"><span class="sec-n">그림 3</span><h2>2025년에는 이익과 현금이 엇갈린다</h2></div>
  <p class="sec-p" id="sec3p"></p>
  <figure>
    <ul class="legend" id="lg3"></ul>
    <div class="plot"><svg id="c3" viewBox="0 0 720 300" role="img" aria-label="영업이익·당기순이익·영업활동현금흐름 비교"></svg></div>
    <figcaption>단위 억원. 출처: 2025 사업보고서 III-4-2·4-4.</figcaption>
  </figure>
</section>

<section>
  <div class="sec-h"><span class="sec-n">그림 4</span><h2>매출 정체 안에서 구성이 바뀌고 있다</h2></div>
  <p class="sec-p" id="sec4p"></p>
  <figure>
    <ul class="legend" id="lg4"></ul>
    <div class="plot"><svg id="c4" viewBox="0 0 720 260" role="img" aria-label="사업부문별 매출 구성 변화"></svg></div>
    <figcaption>단위 백만원. 출처: 2025 사업보고서 II-2 주요 제품 및 서비스.</figcaption>
  </figure>
  <div style="margin-top:1.4rem">
    <table>
      <caption>같은 매출액을 사업부문 &times; 수출·내수로 교차한 2025년 실적 (백만원, 괄호는 2024→2025 증감)</caption>
      <thead><tr><th>구분</th><th>수출</th><th>내수</th><th>합계</th></tr></thead>
      <tbody id="xtb"></tbody>
    </table>
    <p class="sec-p" id="xnote" style="margin-top:.7rem"></p>
  </div>
  <div style="margin-top:1.4rem">
    <table>
      <caption>헤어&amp;스칼프 부문 주요 품목 (백만원)</caption>
      <thead><tr><th>제품</th><th>2023</th><th>2024</th><th>2025</th><th>2024→2025</th></tr></thead>
      <tbody id="ptb"></tbody>
    </table>
  </div>
</section>

<section>
  <div class="sec-h"><span class="sec-n">진단</span><h2>문제 후보</h2></div>
  <div class="finding">
    <h3>외형 성장의 둔화가 재무구조 개선 효과에 가려져 있을 가능성</h3>
    <p>2024년 흑자 전환과 2025년 당기순이익 증가는 지표상 개선으로 보이지만, 그 변화의 상당 부분이 영업 외 항목에서 발생했고 같은 기간 매출액과 영업활동현금흐름은 줄었다.</p>
  </div>
  <div class="stack three">
    <div class="block">
      <h3>관찰된 사실</h3>
      <ul id="obs"></ul>
    </div>
    <div class="block">
      <h3>가능한 원인 가설</h3>
      <ul>
        <li><b>일회성 효과</b> 상환전환우선주의 자본 전환과 금융자산 손상 종료에 따른 것일 수 있다. 두 항목의 잔액이 모두 0이므로 같은 항목에서 같은 크기의 개선이 다시 생길 여지는 없다. 다른 자산의 손상 가능성까지 배제되지는 않는다.</li>
        <li id="hyp2"></li>
        <li id="hyp3"></li>
      </ul>
    </div>
    <div class="block">
      <h3>확인 방법</h3>
      <ul>
        <li><b>2026년 3분기 보고서</b> 금융원가가 2025년 수준에서 유지되는지, 누적 추세가 이어지는지 확인한다.</li>
        <li><b>2024년 채널별 매출</b> 2025년 채널별 매출은 위 교차표 아래 출처에서 확보했으나 전년 수치가 없어 채널별 증감을 낼 수 없다. 증권신고서(2025.11) 또는 2026 사업보고서에서 전년 수치를 확보해 부문&times;수출·내수 증감과 대조한다.</li>
        <li><b>판관비 주석과 현금흐름표 간접법 조정</b> 계정별 증감을 분리하고 운전자본 변동을 OCF 감소분과 대조한다.</li>
      </ul>
    </div>
  </div>
</section>

<footer>
  <p>모든 수치는 DART 전자공시시스템에 제출된 공시서류 원문에서 확인했다. 언론 보도와 기업정보 사이트는 쓰지 않았다. 2023~2025년은 별도재무제표·K-IFRS 기준이다. 아로마티카는 해당 기간에 연결재무제표를 작성하지 않으며, 종속회사 설립으로 2026년부터 연결이 작성된다.</p>
  <p id="vinfo"></p>
  <ul class="srcs" id="srcs"></ul>
  <p style="margin-top:1.2rem">이 페이지의 수치는 보고서와 같은 계산 결과 파일에서 생성된다. <a href="https://dart.fss.or.kr" target="_blank" rel="noopener">DART 전자공시시스템</a></p>
</footer>

</div>
<div class="tip" id="tip" role="status" aria-live="polite"></div>

<script>
const DATA = __DATA__;
const Y = DATA.years;
const S = {s1:'var(--s1)', s2:'var(--s2)', s3:'var(--s3)'};
const eok = v => v/1e8;
const f1 = v => v.toLocaleString('ko-KR',{minimumFractionDigits:1,maximumFractionDigits:1});
const f2 = v => v.toLocaleString('ko-KR',{minimumFractionDigits:2,maximumFractionDigits:2});
const NS = 'http://www.w3.org/2000/svg';
const el = (n,a={}) => { const e=document.createElementNS(NS,n); for(const k in a) e.setAttribute(k,a[k]); return e; };

/* ── 툴팁 ── */
const tip = document.getElementById('tip');
function showTip(e, html){ tip.innerHTML = html; tip.classList.add('show');
  tip.style.left = e.clientX+'px'; tip.style.top = e.clientY+'px'; }
function hideTip(){ tip.classList.remove('show'); }
document.addEventListener('scroll', hideTip, {passive:true});

/* ── 히어로 ── */
(function(){
  const h = DATA.hero, box = document.getElementById('hero');
  const max = Math.max(h.op, h.fin);
  const lanes = [
    {k:'재무에서', s:'금융원가가 줄어서', v:h.fin, c:S.s1},
    {k:'영업에서', s:'영업이익이 늘어서', v:h.op, c:S.s3},
    {k:'그 밖에', s:'기타수익·비용·법인세 합계', v:h.etc, c:null},
  ];
  lanes.forEach(L=>{
    const pct = L.v/h.total*100;
    const w = Math.max(Math.abs(L.v)/max*100, 2);
    box.insertAdjacentHTML('beforeend',
      `<div class="lane">
         <div class="lane-label">${L.k}<em>${L.s}</em></div>
         <div class="lane-bar">
           <div class="lane-track">
             <div class="lane-fill ${L.c?'':'neg'}" style="width:${w}%;${L.c?`background:${L.c}`:''}"></div>
           </div>
           <div class="lane-val">${L.v>0?'+':'−'}${f1(Math.abs(eok(L.v)))}억 <i>${L.v>0?'':'−'}${f1(Math.abs(pct))}%</i></div>
         </div>
       </div>`);
  });
})();

/* ── 지표 줄 ── */
(function(){
  const m = DATA.metrics, s = document.getElementById('strip');
  const items = [
    {k:'매출액', v:f1(eok(m['2025'].revenue))+'억', d:m['2025'].revenue_growth},
    {k:'영업이익', v:f1(eok(m['2025'].operating_income))+'억', d:m['2025'].op_growth},
    {k:'당기순이익', v:f1(eok(m['2025'].net_income))+'억', d:m['2025'].ni_growth},
    {k:'영업활동현금흐름', v:f1(eok(m['2025'].ocf))+'억', d:m['2025'].ocf_growth},
  ];
  items.forEach(i=>{
    const cls = i.d>0?'up':'down';
    const arrow = i.d>0?'▲':'▼';
    s.insertAdjacentHTML('beforeend',
      `<div class="stat"><p class="stat-k">${i.k} <small>2025</small></p>
       <p class="stat-v">${i.v}</p>
       <p class="stat-d ${cls}">${arrow} ${f2(Math.abs(i.d))}% <span style="color:var(--ink3)">전년 대비</span></p></div>`);
  });
})();

/* ── 범례 ── */
function legend(id, items){
  const ul = document.getElementById(id);
  items.forEach(i=> ul.insertAdjacentHTML('beforeend',
    `<li><span class="swatch" style="background:${i.c}"></span>${i.k}</li>`));
}

/* ── 그림 1: 비율 추이 ── */
(function(){
  const svg = document.getElementById('c1');
  const W=720,H=300,L=46,R=18,T=18,B=34;
  const m = DATA.metrics;
  const series = [
    {k:'영업이익률', key:'operating_margin', c:S.s1},
    {k:'당기순이익률', key:'net_margin', c:S.s2},
    {k:'금융원가율', key:'finance_cost_ratio', c:S.s3},
  ];
  legend('lg1', series);
  const vals = series.flatMap(s=>Y.map(y=>m[y][s.key]));
  const lo = Math.min(...vals,0), hi = Math.max(...vals);
  const pad = (hi-lo)*0.16;
  const y0=lo-pad, y1=hi+pad;
  const X = i => L + i*(W-L-R)/(Y.length-1);
  const Yp = v => T + (1-(v-y0)/(y1-y0))*(H-T-B);
  [-10,0,10,20].forEach(t=>{
    if(t<y0||t>y1) return;
    svg.appendChild(el('line',{x1:L,x2:W-R,y1:Yp(t),y2:Yp(t),class:t===0?'axis-line':'grid-line'}));
    const tx=el('text',{x:L-8,y:Yp(t)+4,class:'tick','text-anchor':'end'}); tx.textContent=t+'%'; svg.appendChild(tx);
  });
  Y.forEach((y,i)=>{ const t=el('text',{x:X(i),y:H-10,class:'tick','text-anchor':'middle'}); t.textContent=y; svg.appendChild(t); });
  series.forEach(s=>{
    const d = Y.map((y,i)=>`${i?'L':'M'}${X(i)},${Yp(m[y][s.key])}`).join(' ');
    svg.appendChild(el('path',{d,fill:'none',stroke:s.c,'stroke-width':2.5,'stroke-linejoin':'round',class:'mark'}));
    Y.forEach((y,i)=>{
      svg.appendChild(el('circle',{cx:X(i),cy:Yp(m[y][s.key]),r:4.5,fill:s.c,stroke:'var(--panel)','stroke-width':2,class:'mark'}));
    });
    [0,Y.length-1].forEach(i=>{
      const v=m[Y[i]][s.key];
      const t=el('text',{x:X(i),y:Yp(v)+(s.key==='net_margin'?18:-12),class:'dlabel','text-anchor':i?'end':'start'});
      t.textContent=f1(v)+'%'; svg.appendChild(t);
    });
  });
  Y.forEach((y,i)=>{
    const hit = el('rect',{x:X(i)-(W-L-R)/4,y:T,width:(W-L-R)/2,height:H-T-B,class:'hit'});
    hit.addEventListener('mousemove',e=>showTip(e,
      `<b>${y}</b><br>`+series.map(s=>`<i>${s.k}</i> ${f2(m[y][s.key])}%`).join('<br>')));
    hit.addEventListener('mouseleave',hideTip);
    svg.appendChild(hit);
  });
})();

/* ── 그림 2: 폭포 ── */
(function(){
  const svg = document.getElementById('c2');
  const W=720,H=330,L=46,R=18,T=26,B=56;
  const m = DATA.metrics;
  const steps = DATA.bridge;
  const bars = [{k:'2023년\n당기순이익', v:eok(m['2023'].net_income), kind:'end'}]
    .concat(steps.map(s=>({k:s.item, v:eok(s.value), share:s.share, kind:'step'})))
    .concat([{k:'2024년\n당기순이익', v:eok(m['2024'].net_income), kind:'end'}]);
  let cum = eok(m['2023'].net_income);
  const tops=[cum,0];
  steps.forEach(s=>{ cum+=eok(s.value); tops.push(cum); });
  const lo=Math.min(...tops,0)*1.18, hi=Math.max(...tops,0)*1.3;
  const n=bars.length, bw=(W-L-R)/n*0.56;
  const X=i=>L+(i+0.5)*(W-L-R)/n;
  const Yp=v=>T+(1-(v-lo)/(hi-lo))*(H-T-B);
  [-50,0,50].forEach(t=>{
    if(t<lo||t>hi) return;
    svg.appendChild(el('line',{x1:L,x2:W-R,y1:Yp(t),y2:Yp(t),class:t===0?'axis-line':'grid-line'}));
    const tx=el('text',{x:L-8,y:Yp(t)+4,class:'tick','text-anchor':'end'}); tx.textContent=t; svg.appendChild(tx);
  });
  let run = 0;
  bars.forEach((b,i)=>{
    let y,h,col,base;
    if(b.kind==='end'){ base=0; y=Yp(Math.max(b.v,0)); h=Math.abs(Yp(b.v)-Yp(0)); col='var(--quiet)'; run=b.v; }
    else { base=run; const top=Math.max(run,run+b.v); y=Yp(top); h=Math.abs(Yp(run+b.v)-Yp(run)); col=b.v>=0?S.s1:S.s2; run+=b.v; }
    const r=el('rect',{x:X(i)-bw/2,y,width:bw,height:Math.max(h,1.5),fill:col,rx:2,class:'mark'});
    svg.appendChild(r);
    const lab=el('text',{x:X(i),y:y-7,class:'dlabel','text-anchor':'middle'});
    lab.textContent = b.kind==='end' ? f1(b.v) : (b.v>0?'+':'')+f1(b.v);
    svg.appendChild(lab);
    b.k.split('\n').forEach((ln,j)=>{
      const t=el('text',{x:X(i),y:H-B+22+j*13,class:'tick','text-anchor':'middle'});
      t.textContent=ln; svg.appendChild(t);
    });
    r.addEventListener('mousemove',e=>showTip(e, b.kind==='end'
      ? `<b>${b.k.replace('\n',' ')}</b><br>${f1(b.v)}억원`
      : `<b>${b.k}</b><br>${(b.v>0?'+':'')}${f1(b.v)}억원 <i>기여도 ${f1(b.share)}%</i>`));
    r.addEventListener('mouseleave',hideTip);
  });
})();

/* ── 그림 3: 묶음 막대 ── */
(function(){
  const svg = document.getElementById('c3');
  const W=720,H=300,L=46,R=18,T=22,B=34;
  const m = DATA.metrics;
  const series=[{k:'영업이익',key:'operating_income',c:S.s1},
                {k:'당기순이익',key:'net_income',c:S.s2},
                {k:'영업활동현금흐름',key:'ocf',c:S.s3}];
  legend('lg3', series);
  const vals=series.flatMap(s=>Y.map(y=>eok(m[y][s.key])));
  const lo=Math.min(...vals,0)*1.2, hi=Math.max(...vals)*1.2;
  const gw=(W-L-R)/Y.length, bw=gw*0.2;
  const Yp=v=>T+(1-(v-lo)/(hi-lo))*(H-T-B);
  [-50,0,50].forEach(t=>{
    if(t<lo||t>hi) return;
    svg.appendChild(el('line',{x1:L,x2:W-R,y1:Yp(t),y2:Yp(t),class:t===0?'axis-line':'grid-line'}));
    const tx=el('text',{x:L-8,y:Yp(t)+4,class:'tick','text-anchor':'end'}); tx.textContent=t; svg.appendChild(tx);
  });
  Y.forEach((y,gi)=>{
    const cx=L+gi*gw+gw/2;
    series.forEach((s,si)=>{
      const v=eok(m[y][s.key]);
      const x=cx+(si-1)*(bw+4)-bw/2;
      const yy=Yp(Math.max(v,0)), h=Math.abs(Yp(v)-Yp(0));
      const r=el('rect',{x,y:yy,width:bw,height:Math.max(h,1.5),fill:s.c,rx:2,class:'mark'});
      svg.appendChild(r);
      const t=el('text',{x:x+bw/2,y:v>=0?yy-6:yy+h+14,class:'dlabel','text-anchor':'middle'});
      t.textContent=f1(v); svg.appendChild(t);
      r.addEventListener('mousemove',e=>showTip(e,`<b>${y} ${s.k}</b><br>${f1(v)}억원`));
      r.addEventListener('mouseleave',hideTip);
    });
    const t=el('text',{x:cx,y:H-10,class:'tick','text-anchor':'middle'}); t.textContent=y; svg.appendChild(t);
  });
})();

/* ── 그림 4: 부문 구성 ── */
(function(){
  const svg=document.getElementById('c4');
  const W=720,H=260,L=46,R=18,T=22,B=34;
  const sg=DATA.segments;
  legend('lg4',[{k:'헤어&스칼프',c:S.s1},{k:'스킨&바디',c:S.s3}]);
  const hi=Math.max(...Y.map(y=>sg[y].total))*1.14;
  const gw=(W-L-R)/Y.length, bw=gw*0.34;
  const Yp=v=>T+(1-v/hi)*(H-T-B);
  [0,20000,40000].forEach(t=>{
    svg.appendChild(el('line',{x1:L,x2:W-R,y1:Yp(t),y2:Yp(t),class:t===0?'axis-line':'grid-line'}));
    const tx=el('text',{x:L-8,y:Yp(t)+4,class:'tick','text-anchor':'end'});
    tx.textContent=(t/1000)+'천'; svg.appendChild(tx);
  });
  Y.forEach((y,i)=>{
    const cx=L+i*gw+gw/2, d=sg[y];
    const hH=(H-T-B)*d.hair/hi, sH=(H-T-B)*d.skin/hi;
    const yTop=Yp(d.total);
    const r1=el('rect',{x:cx-bw/2,y:yTop,width:bw,height:Math.max(sH,1),fill:S.s3,class:'mark'});
    const r2=el('rect',{x:cx-bw/2,y:yTop+sH+2,width:bw,height:Math.max(hH-2,1),fill:S.s1,class:'mark'});
    svg.appendChild(r1); svg.appendChild(r2);
    const pct=el('text',{x:cx,y:yTop+sH+hH/2+4,class:'dlabel inv','text-anchor':'middle'});
    pct.textContent=f1(d.hair/d.total*100)+'%'; svg.appendChild(pct);
    const tot=el('text',{x:cx,y:yTop-8,class:'dlabel','text-anchor':'middle'});
    tot.textContent=d.total.toLocaleString('ko-KR'); svg.appendChild(tot);
    const t=el('text',{x:cx,y:H-10,class:'tick','text-anchor':'middle'}); t.textContent=y; svg.appendChild(t);
    [[r1,'스킨&바디',d.skin],[r2,'헤어&스칼프',d.hair]].forEach(([r,k,v])=>{
      r.addEventListener('mousemove',e=>showTip(e,
        `<b>${y} ${k}</b><br>${v.toLocaleString('ko-KR')}백만원 <i>${f1(v/d.total*100)}%</i>`));
      r.addEventListener('mouseleave',hideTip);
    });
  });
})();

/* ── 부문 x 수출·내수 교차표 ── */
(function(){
  const E=DATA.exportDomestic, e25=E['2025'];
  const g=k=>e25[k+'_증감률'];
  const cell=(v,gr)=>`<td class="${gr<0?'neg':'em'}">${(+v).toLocaleString('ko-KR')}` +
    `<span style="opacity:.72;font-weight:400"> (${gr>0?'+':''}${f1(gr)}%)</span></td>`;
  const tb=document.getElementById('xtb');
  [['헤어&스칼프','헤어&스칼프_수출','헤어&스칼프_내수'],
   ['스킨&바디','스킨&바디_수출','스킨&바디_내수']].forEach(([nm,ke,kd])=>{
    const sub=e25[ke]+e25[kd];
    tb.insertAdjacentHTML('beforeend',
      `<tr><td>${nm}</td>${cell(e25[ke],g(ke))}${cell(e25[kd],g(kd))}` +
      `<td>${sub.toLocaleString('ko-KR')}</td></tr>`);
  });
  tb.insertAdjacentHTML('beforeend',
    `<tr><td><b>합계</b></td>${cell(e25['수출'],g('수출'))}${cell(e25['내수'],g('내수'))}` +
    `<td class="${g('합계')<0?'neg':'em'}"><b>${e25['합계'].toLocaleString('ko-KR')}</b>` +
    `<span style="opacity:.72;font-weight:400"> (${f1(g('합계'))}%)</span></td></tr>`);

  document.getElementById('sec4p').textContent =
    `2025년 매출액은 ${f2(Math.abs(g('합계')))}% 줄었다. 같은 금액을 수출·내수로 나누면 수출은 ` +
    `${g('수출')>0?'+':''}${f2(g('수출'))}%, 내수는 ${f2(g('내수'))}% 변동했다.`;
  const grown=['헤어&스칼프_수출','헤어&스칼프_내수','스킨&바디_수출','스킨&바디_내수'].filter(k=>g(k)>0);
  document.getElementById('xnote').textContent =
    `네 칸 가운데 2025년에 증가한 칸은 ${grown.map(k=>k.replace('_',' ')).join(', ')} ` +
    `${grown.length===1?'하나뿐이다':grown.length+'개다'}. 수출 비중은 ${f1(E['2023']['수출비중'])}%에서 ${f1(e25['수출비중'])}%로 높아졌다. ` +
    `출처: 2025 사업보고서 II-4 매출 및 수주상황.`;
})();

/* ── 제품 표 ── */
(function(){
  const tb=document.getElementById('ptb');
  Object.entries(DATA.products).forEach(([k,v])=>{
    const g=(v['2025']/v['2024']-1)*100;
    tb.insertAdjacentHTML('beforeend',
      `<tr><td>${k}</td><td>${(+v['2023']).toLocaleString('ko-KR')}</td>
       <td>${(+v['2024']).toLocaleString('ko-KR')}</td>
       <td class="em">${(+v['2025']).toLocaleString('ko-KR')}</td>
       <td class="${g<0?'neg':''}">${g>0?'+':''}${f1(g)}%</td></tr>`);
  });
})();

/* ── 서두·리드 문장 (수치는 런타임에 채운다) ── */
(function(){
  const m=DATA.metrics, h=DATA.hero, fc=DATA.financeCost2023;
  document.getElementById('stand').textContent =
    `2023년 ${f1(Math.abs(eok(m['2023'].net_income)))}억 순손실에서 2024년 ${f1(eok(m['2024'].net_income))}억 ` +
    `순이익으로 돌아섰다. 그 변화를 손익계산서 항목별로 갈라보면, 영업이 만든 몫보다 금융원가가 ` +
    `사라져서 생긴 몫이 ${f1(h.fin/h.op)}배 크다.`;
  document.getElementById('heronote').textContent =
    `금융원가는 2023년 ${f1(eok(m['2023'].finance_cost))}억원에서 2024년 ${f1(eok(m['2024'].finance_cost))}억원으로 ` +
    `줄었다. 그중 ${f1(eok(fc.non_cash))}억원(${f1(fc.non_cash/fc.total*100)}%)은 파생상품평가손실과 ` +
    `손상차손으로, 현금이 나가지 않는 항목이다. 두 항목의 잔액은 각각 2024년 말과 2023년 말에 0이 되었다.`;
  document.getElementById('sec2p').textContent =
    `세 지표 모두 매출액으로 나눈 비율이다. 영업이익률이 ` +
    `${f2(m['2025'].operating_margin-m['2023'].operating_margin)}%p 움직이는 동안 당기순이익률은 ` +
    `${f2(m['2025'].net_margin-m['2023'].net_margin)}%p 움직였다. 그 차이를 금융원가율이 메운다.`;
  document.getElementById('sec3p').textContent =
    `당기순이익은 ${f2(m['2025'].ni_growth)}% 늘었는데 영업활동현금흐름은 ` +
    `${f2(Math.abs(m['2025'].ocf_growth))}% 줄었다. 2023년에는 반대로, 순손실인 해에 영업현금이 플러스였다.`;
})();

/* ── 가설 2·3 (수치는 런타임에 채운다) ── */
(function(){
  const e25=DATA.exportDomestic['2025'], m=DATA.metrics;
  const g=k=>e25[k+'_증감률'];
  document.getElementById('hyp2').innerHTML =
    `<b>성장 축의 축소</b> 동력이 헤어&amp;스칼프 수출로 좁아지고 있을 수 있다. 2025년 부문&times;수출·내수 ` +
    `네 칸 중 증가한 칸은 헤어&amp;스칼프 수출(+${f1(g('헤어&스칼프_수출'))}%) 하나이고, 같은 부문의 내수와 ` +
    `스킨&amp;바디의 양 칸은 모두 줄었다.`;
  document.getElementById('hyp3').innerHTML =
    `<b>비용 선행과 운전자본</b> 2025년 판관비는 ${f1(eok(m['2024'].sga))}억에서 ${f1(eok(m['2025'].sga))}억으로 ` +
    `늘었고, 영업에서 창출된 현금은 ${f1(eok(m['2024'].cash_from_operations))}억에서 ` +
    `${f1(eok(m['2025'].cash_from_operations))}억으로 줄었다.`;
})();

/* ── 관찰·출처 ── */
(function(){
  const m=DATA.metrics, fc=DATA.financeCost2023, b=DATA.bridge.find(x=>x.item==='금융원가 감소');
  const o=DATA.bridge.find(x=>x.item==='영업이익');
  document.getElementById('obs').innerHTML = [
    `<b>흑자 전환의 구성</b> 2024년 당기순이익 변화 +${f1(eok(DATA.bridgeTotal))}억원 중 금융원가 감소가 +${f1(eok(b.value))}억원(${f1(b.share)}%), 영업이익 개선이 +${f1(eok(o.value))}억원(${f1(o.share)}%)이다.`,
    `<b>비현금 항목</b> 2023년 금융원가 ${f1(eok(fc.total))}억원 중 ${f1(eok(fc.non_cash))}억원(${f1(fc.non_cash/fc.total*100)}%)이 현금 유출을 수반하지 않는다.`,
    `<b>2025년의 엇갈림</b> 매출액 ${f2(Math.abs(m['2025'].revenue_growth))}%, 영업이익 ${f2(Math.abs(m['2025'].op_growth))}%, 영업활동현금흐름 ${f2(Math.abs(m['2025'].ocf_growth))}%가 줄어든 반면 당기순이익은 ${f2(m['2025'].ni_growth)}% 늘었다.`,
  ].map(t=>`<li>${t}</li>`).join('');

  const v=DATA.verification;
  document.getElementById('vinfo').textContent =
    `DART 원문 내부의 관계식 재계산과 전사 일치 확인으로 ${v.crossChecked}건을 교차검증했고 전 건이 통과했다. ` +
    `여기에 원문에 직접 실려 있지 않아 도출한 값의 재현 기록 ${v.derived}건을 더해 총 ${v.total}건을 남겼다. ` +
    `검증 기록과 계산 코드는 제출 자료에 포함되어 있다.`;
  document.getElementById('srcs').innerHTML = DATA.sources
    .filter((s,i,a)=>a.findIndex(x=>x.rcp===s.rcp)===i)
    .map(s=>`<li><b>${s.report}</b><span>접수번호 ${s.rcp} · ${s.date}</span></li>`).join('');
})();

/* ── 테마 ── */
(function(){
  const btn=document.getElementById('themeBtn');
  const sync=()=>{ const dark=document.documentElement.getAttribute('data-theme')==='dark'
    || (!document.documentElement.hasAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    btn.textContent = dark ? '주간' : '야간'; };
  sync();
  btn.addEventListener('click',()=>{
    const cur=document.documentElement.getAttribute('data-theme');
    const dark = cur ? cur==='dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', dark?'light':'dark');
    sync();
  });
})();
</script>
</body>
</html>
"""

out = HTML.replace("__DATA__", json.dumps(PAYLOAD, ensure_ascii=False))
out = out.replace("__TOTAL__", f"{total/1e8:,.1f}")

path = os.path.join(BASE, "index.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(out)
print(f"저장: index.html ({os.path.getsize(path):,} bytes)")

# ── 아티팩트 버전 ─────────────────────────────────────────
# 게시 시 문서 골격이 자동으로 감싸지므로 doctype/html/head/body를 두지 않는다.
art = out
art = art.split("<title>", 1)[1]
art = "<title>" + art
art = art.replace("</head>\n<body>", "", 1)
art = art.replace("</body>\n</html>\n", "", 1)
art = art.replace('<title>', '<meta name="claude:viewport-fit-sides" content="cover">\n<title>', 1)

apath = os.path.join(BASE, "artifact.html")
with open(apath, "w", encoding="utf-8") as f:
    f.write(art)
print(f"저장: artifact.html ({os.path.getsize(apath):,} bytes)")
