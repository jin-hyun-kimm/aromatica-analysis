# -*- coding: utf-8 -*-
"""
04_build_report.py — 중간보고서 생성

metrics.json / verification_log.csv / data/*.csv 를 읽어 보고서를 만든다.
본문·표의 모든 수치는 스크립트가 계산한 값을 그대로 삽입하므로
본문과 그래프의 숫자가 어긋날 수 없다.

실행:  python3 code/04_build_report.py
출력:  {학번}_{이름}_중간보고서.docx  (표지 정보는 identity.json에서 읽는다)
"""
import csv, json, os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KR = "Noto Sans CJK KR"
INK = RGBColor(0x14, 0x14, 0x14)
GREY = RGBColor(0x63, 0x63, 0x63)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
RED = RGBColor(0xC0, 0x3B, 0x2B)

with open(os.path.join(BASE, "metrics.json"), encoding="utf-8") as f:
    D = json.load(f)
M = D["metrics"]
YEARS = ["2023", "2024", "2025"]


def load(name):
    with open(os.path.join(BASE, "data", name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


seg = {}
for r in load("segment_revenue.csv"):
    seg.setdefault(int(r["year"]), {})[r["segment"]] = int(r["revenue_million_krw"])
ED = {int(k): v for k, v in D["export_domestic"].items()}
chan = load("channel_revenue_2025.csv")
ind = load("industry_market.csv")
prod = {}
for r in load("product_revenue.csv"):
    prod.setdefault(r["product"], {})[int(r["year"])] = int(r["revenue_million_krw"])
cmp23 = {r["item"]: r for r in load("basis_2023_comparison.csv")}
qtr = {r["period"]: r for r in load("quarterly_2026.csv")}
cf = {int(r["year"]): r for r in load("cashflow_annual.csv")}
bal = {int(r["year"]): r for r in load("balance_annual.csv")}
fcd = load("finance_cost_detail.csv")
vlog = list(csv.DictReader(open(os.path.join(BASE, "verification_log.csv"), encoding="utf-8-sig")))
bdet = {(r["period"], r["item"]): int(r["value_krw"]) for r in load("balances_detail.csv")}
tr23 = {r["item"]: int(r["net_income_adj_krw"]) for r in load("transition_2023.csv")}
fin = {int(r["year"]): r for r in load("financials_annual.csv")}
FCD = {(int(r["year"]), r["item"]): int(r["value_krw"]) for r in load("finance_cost_detail.csv")}
N_DATA = len([f for f in os.listdir(os.path.join(BASE, "data")) if f.endswith(".csv")])


def fv(y, key):
    return int(fin[y][key])


def ppt(a, b):
    """퍼센트포인트 차이 — 표시값이 아닌 원수치로 계산한다."""
    return a - b

FC = D["finance_cost_2023"]
BR = {b["item"]: b for b in D["bridge_2024"]}


def eok(v, d=1):
    return f"{v/1e8:,.{d}f}"


def mn(v):
    return f"{v:,}"


# ───────────────────────── 문서 골격 ─────────────────────────
doc = Document()
s = doc.sections[0]
s.top_margin = Cm(1.7); s.bottom_margin = Cm(1.7)
s.left_margin = Cm(2.0); s.right_margin = Cm(2.0)

st = doc.styles["Normal"]
st.font.name = KR; st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), KR)
st.paragraph_format.space_after = Pt(3)
st.paragraph_format.line_spacing = 1.30


def sf(r, size=10, bold=False, color=INK):
    r.font.name = KR; r.font.size = Pt(size)
    r.font.bold = bold; r.font.color.rgb = color
    r._element.rPr.rFonts.set(qn("w:eastAsia"), KR)


def P(t="", size=10, bold=False, color=INK, before=0, after=3.5,
      indent=0, line=1.24, align=None):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after); pf.line_spacing = line
    if indent: pf.left_indent = Cm(indent)
    if align: p.alignment = align
    if t: sf(p.add_run(t), size, bold, color)
    return p


def rich(parts, size=10, before=0, after=3.5, indent=0, line=1.24):
    """[(텍스트, 굵게), ...] 형태로 한 문단 안에서 강조를 섞는다."""
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after); pf.line_spacing = line
    if indent: pf.left_indent = Cm(indent)
    for t, b in parts:
        sf(p.add_run(t), size, b)
    return p


def H1(t):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(5)
    sf(p.add_run(t), 12.5, True, INK)
    bdr = OxmlElement("w:pBdr"); b = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "4"), ("w:color", "C4C4C4")):
        b.set(qn(k), v)
    bdr.append(b); p._p.get_or_add_pPr().append(bdr)
    return p


def H2(t, before=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(3)
    sf(p.add_run(t), 10.5, True, BLUE)
    return p


def bul(t, size=9.6, ind=0.35, after=2.0):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.left_indent = Cm(ind + 0.4); pf.first_line_indent = Cm(-0.4)
    pf.space_after = Pt(after); pf.line_spacing = 1.22
    sf(p.add_run("· " + t), size)
    return p


def shade(c, h):
    tcPr = c._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    for k, v in (("w:val", "clear"), ("w:color", "auto"), ("w:fill", h)):
        sh.set(qn(k), v)
    tcPr.append(sh)


def T(headers, rows, widths=None, fs=8.6, ar=None, note=None, hl=None, after=7, nosplit=False):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    ar = ar or []; hl = hl or []
    hc = t.rows[0].cells
    for i, h in enumerate(headers):
        hc[i].text = ""; p = hc[i].paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0.5); p.paragraph_format.space_before = Pt(0.5)
        sf(p.add_run(h), fs, True); shade(hc[i], "EEF1F4")
    # 표가 쪽 경계에서 나뉘어도 머리글이 반복되도록 한다
    _trPr = t.rows[0]._tr.get_or_add_trPr()
    _th = OxmlElement("w:tblHeader"); _th.set(qn("w:val"), "true"); _trPr.append(_th)
    for ri, r in enumerate(rows):
        _row = t.add_row()
        if nosplit:
            _cs = OxmlElement("w:cantSplit")
            _row._tr.get_or_add_trPr().append(_cs)
        cs = _row.cells
        for i, v in enumerate(r):
            cs[i].text = ""; p = cs[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0.5); p.paragraph_format.space_before = Pt(0.5)
            p.alignment = (WD_ALIGN_PARAGRAPH.RIGHT if i in ar
                           else WD_ALIGN_PARAGRAPH.CENTER if i == 0
                           else WD_ALIGN_PARAGRAPH.LEFT)
            txt = str(v)
            col = RED if (txt.strip().startswith("-") and i in ar) else INK
            sf(p.add_run(txt), fs, False, col)
            if ri in hl: shade(cs[i], "FBF4EC")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    P(note or "", 8, False, GREY, before=2, after=after if note else after, line=1.28)
    return t


def fig(name, caption, width=9.6):
    doc.add_picture(os.path.join(BASE, "figures", name), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6); c.paragraph_format.space_before = Pt(0)
    sf(c.add_run(caption), 8.6, False, GREY)


# ═══════════════════ 표지 영역 ═══════════════════
P("통계컨설팅의 이해 · 중간고사 과제", 9, False, GREY, after=2)
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(3)
sf(p.add_run("아로마티카 현황분석 기초보고서"), 18, True, INK)
P("2023~2025년 이익 개선의 원천 — 영업 성과인가, 재무구조 변화인가", 11.5, False, BLUE, after=9)

# 제출자 성명·학번은 공개 저장소에 두지 않으려고 identity.json으로 분리했다.
# 파일이 없으면 identity.example.json의 자리표시자로 생성된다(제출 ZIP에는 포함되어 있다).
_idp = os.path.join(BASE, "identity.json")
if not os.path.exists(_idp):
    _idp = os.path.join(BASE, "identity.example.json")
    print("  [알림] identity.json이 없어 자리표시자로 표지를 만듭니다.")
with open(_idp, encoding="utf-8") as _f:
    ID = json.load(_f)

info = doc.add_table(rows=0, cols=4); info.style = "Table Grid"
for a, b, c, d in [("학번", ID["학번"], "이름", ID["이름"]),
                   ("조", ID["조"], "대상기업", "아로마티카(주) · 코스닥 상장"),
                   ("제출일", ID["제출일"], "자료 기준일", ID["자료 기준일"])]:
    cs = info.add_row().cells
    for i, (txt, isk) in enumerate([(a, 1), (b, 0), (c, 1), (d, 0)]):
        cs[i].text = ""; pp = cs[i].paragraphs[0]
        pp.paragraph_format.space_after = Pt(0.5); pp.paragraph_format.space_before = Pt(0.5)
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER if isk else WD_ALIGN_PARAGRAPH.LEFT
        sf(pp.add_run(txt), 9, bool(isk))
        if isk: shade(cs[i], "EEF1F4")
for row in info.rows:
    for i, w in enumerate([1.9, 3.6, 2.2, 7.5]):
        row.cells[i].width = Cm(w)
P("", after=2)

# ═══════════════════ 1. 경영진 요약 ═══════════════════
H1("1.  경영진 요약")

H2("분석 질문", before=4)
P("아로마티카의 2023~2025년 이익 개선은 영업 성과에서 나온 것인가, 재무구조 변화에서 나온 것인가?",
  10.5, True, INK, after=5)

H2("핵심 발견")
rich([("① 이익 개선의 주된 원천은 영업이 아니다. ", True),
      (f"2024년 당기순이익 변화 +{eok(D['bridge_2024_total'])}억원 가운데 금융원가 감소가 "
       f"+{eok(BR['금융원가 감소']['value'])}억원으로 {BR['금융원가 감소']['share']:.1f}%를 차지한다. "
       f"영업이익 개선의 기여도는 {BR['영업이익']['share']:.1f}%다.", False)], after=3)
rich([("② 2025년에는 손익 항목의 증감 방향이 엇갈린다. ", True),
      (f"매출액이 {abs(M['2025']['revenue_growth']):.2f}%, 영업이익이 {abs(M['2025']['op_growth']):.2f}% "
       f"감소했으나 당기순이익은 {M['2025']['ni_growth']:.2f}% 증가했다.", False)], after=3)
rich([("③ 이익과 현금의 방향도 엇갈린다. ", True),
      (f"2025년 당기순이익은 {M['2025']['ni_growth']:.2f}% 증가했으나 영업활동현금흐름은 "
       f"{abs(M['2025']['ocf_growth']):.2f}% 감소했다.", False)], after=3)
rich([("④ 매출 정체의 내부에서 구성이 바뀌고 있다. ", True),
      (f"2025년 매출액이 {abs(M['2025']['revenue_growth']):.2f}% 감소하는 동안 수출은 "
       f"{ED[2025]['수출_증감률']:+.2f}%, 내수는 {ED[2025]['내수_증감률']:+.2f}% 변동했다. "
       f"사업부문과 수출·내수를 교차한 네 칸 가운데 증가한 칸은 헤어&스칼프 수출"
       f"({ED[2025]['헤어&스칼프_수출_증감률']:+.1f}%) 하나다.", False)], after=5)

H2("문제 후보")
P("외형 성장의 둔화가 재무구조 개선 효과에 가려져 있을 가능성. 2024년 흑자 전환과 2025년 당기순이익 "
  "증가는 지표상 개선으로 보이지만, 그 변화의 상당 부분이 영업 외 항목에서 발생했고 같은 기간 매출액과 "
  "영업활동현금흐름은 감소했다.", 10, after=5)

H2("분석의 한계")
P("2023년은 회계기준 전환으로 두 수치가 모두 공시되어 추세 해석에 제약이 있고, 2026년부터는 연결재무제표가 "
  "작성되어 2023~2025년(별도)과 직접 비교할 수 없다. 관찰된 사실과 가설을 구분하여 기술하였으며 "
  "인과관계를 단정하지 않는다.", 10, after=4)

doc.add_page_break()

# ═══════════════════ 2. 기업 소개와 개인 분석 질문 ═══════════════════
H1("2.  기업 소개와 개인 분석 질문")

H2("2-1. 기업 개요", before=4)
P(f"아로마티카(주)는 에센셜오일 기반 화장품을 제조·판매하는 클린뷰티 브랜드로, 2004년 런칭 이후 약 "
  f"22년간 사업을 영위해 왔다. 사업보고서에 따르면 전 제품에 합성향료와 인체 유해 성분을 배제한 100% "
  f"비건 처방을 적용하며, 원료 선별·수입부터 연구·제조·물류까지 전 과정을 직접 수행한다. 2025년 11월 "
  f"코스닥시장에 상장하였다. 사업부문은 헤어&스칼프와 스킨&바디 둘이며, "
  f"2025년 매출액 {eok(M['2025']['revenue'])}억원은 각각 {mn(seg[2025]['헤어&스칼프'])}백만원, "
  f"{mn(seg[2025]['스킨&바디'])}백만원으로 구성된다.", after=4)
P(f"산업 환경은 수출 주도의 성장 국면이다. 사업보고서는 2025년 국내 화장품 수출액이 전년 대비 12.3% "
  f"증가한 114억 달러로 역대 최대라고 기재하면서, 동시에 국내 시장은 진입장벽이 낮아져 경쟁강도가 "
  f"비교적 높다고 기술하고 있다. 산업의 특성·성장성·경기변동과 인용된 시장 규모 전망은 부록 G에 있다.",
  after=4)

H2("2-2. 분석 질문과 선정 이유")
P("아로마티카의 2023~2025년 이익 개선은 영업 성과에서 나온 것인가, 재무구조 변화에서 나온 것인가?",
  10.5, True, INK, after=4)
P("조별 자료조사에서 당기순이익과 현금흐름 항목을 담당하면서 손익계산서의 윗부분과 아랫부분이 서로 "
  "다른 방향을 가리키는 구간을 확인했다. 2023년은 영업이익이 흑자인데 당기순손실이었고, 2025년은 "
  "매출액과 영업이익이 줄었는데 당기순이익은 늘었다.", after=4)
P("당기순이익만 보면 이 기업은 '적자에서 흑자로 전환한 뒤 증가세를 이어가는 기업'으로 읽힌다. "
  "그 해석이 영업 성과와 얼마나 일치하는지를 지표의 표면이 아니라 구성 요소로 확인하는 것이 "
  "본 보고서의 질문이다.", after=4)

# ═══════════════════ 3. 자료 출처, 지표 정의와 분석 방법 ═══════════════════
H1("3.  자료 출처, 지표 정의와 분석 방법")

H2("3-1. 자료 출처", before=4)
P("모든 수치는 DART 전자공시시스템의 공시서류 원문에서 직접 확인하였고, 언론 보도와 기업정보 "
  "사이트는 사용하지 않았다.", after=4)
T(["공시서류", "접수번호", "접수일", "본 보고서에서 사용한 항목"],
  [["2025 사업보고서", "20260320001362", "2026.03.20",
    "손익·재무상태·현금흐름(III-4), 사업부문별·제품별 매출(II-2), "
    "수출·내수·채널별 매출(II-4), 산업 환경·지적재산권(II-7)"],
   ["2024 감사보고서", "20250331002452", "2025.03.31",
    "금융원가 내역, 회계기준 전환 차이조정(주석 36)"],
   ["2023 감사보고서", "20240401001486", "2024.04.01", "과거회계기준 2023년 손익계산서·재무상태표"],
   ["2026 반기보고서", "20260818000129", "2026.08.18", "2026년 연결 실적, 종속회사 현황"],
   ["증권발행실적보고서", "20251121000203", "2025.11.21", "공모 주식수, 상장 일정"]],
  widths=[3.3, 2.8, 1.9, 8.1], ar=[],
  note="표 1. 사용한 공시서류. 원문 링크는 https://dart.fss.or.kr/dsaf001/main.do?rcpNo={접수번호} 형식이며, "
       "이후 캡션에서 접수번호가 생략된 출처는 이 표에서 찾을 수 있다.",
  after=5)

H2("3-2. 지표 정의와 산식")
T(["지표", "산식", "분모", "단위", "기준 기간", "원자료 출처"],
  [["영업이익률", "영업이익 ÷ 매출액 × 100", "매출액", "%", "2023~2025", "포괄손익계산서"],
   ["당기순이익률", "당기순이익 ÷ 매출액 × 100", "매출액", "%", "2023~2025", "포괄손익계산서"],
   ["금융원가율", "금융원가 ÷ 매출액 × 100", "매출액", "%", "2023~2025", "포괄손익계산서"],
   ["부채비율", "부채총계 ÷ 자본총계 × 100", "자본총계", "%", "2023~2025", "재무상태표"],
   ["OCF 배수", "영업활동현금흐름 ÷ 영업이익(또는 당기순이익)", "영업이익·당기순이익", "배",
    "2023~2025", "현금흐름표·포괄손익계산서"],
   ["증감률", "(당기 값 ÷ 전기 값 − 1) × 100", "전기 값", "%", "2024~2025", "각 지표의 원자료"],
   ["기여도", "항목별 변화분 ÷ 당기순이익 변화 총액 × 100", "당기순이익 변화 총액", "%",
    "2023→2024", "포괄손익계산서"],
   ["비중", "구성 항목 매출 ÷ 해당 연도 매출액 × 100", "해당 연도 매출액", "%", "2023~2025",
    "매출실적·판매경로 표"]],
  widths=[1.9, 4.4, 2.8, 0.9, 1.8, 2.7], fs=8.0,
  note="표 2. 지표 정의. 원문 위치는 표 1·data/sources.csv 참조. 전기 값이 음수여서 증감률 해석이 "
       "성립하지 않는 경우(2024년 당기순이익)는 산출하지 않았다.",
  after=5)

H2("3-3. 자료 정리 기준")
bul("재무제표 기준 — 2023~2025년은 별도(개별)재무제표를 사용한다. 아로마티카는 해당 기간에 "
    "연결재무제표를 작성하지 않으며, 2025 사업보고서 「III-2. 연결재무제표」는 '해당사항이 없습니다'로 "
    "기재되어 있다. 종속회사 AROMATICA USA INC.가 2026년 2월 4일 설립되어 2026년부터 연결재무제표가 작성된다.")
bul("회계기준 — 전 기간을 한국채택국제회계기준(K-IFRS)으로 통일한다. 2024 회계연도부터 K-IFRS를 최초 "
    "적용하여 2023년 수치가 두 기준으로 모두 공시되어 있으므로, 2023년은 2025 사업보고서의 제23기 "
    "비교표시 열을 사용하였다. 항목별 대조와 조정 내역(2024 감사보고서 주석 36)은 부록 E에 있다.")
bul("단위 — 본문은 억원(소수 첫째 자리, 1억원 미만만 둘째 자리) 표기다. 매출 관련 표는 원문이 백만원, "
    "주석은 천원 단위이며 각 데이터 파일의 source_unit 열에 밝혔다.")
bul("결측치 — 임의로 생성하지 않는다. 2023년은 전년 대비 증감률을 산출하지 않았고, "
    "자본총계가 음수인 2023년 부채비율과 전년이 순손실인 2024년 당기순이익 증감률은 "
    "해석이 성립하지 않으므로 공란으로 둔다.")
bul("분석 방법 — 지표 계산과 그래프 생성을 스크립트로 수행하여 본문·표·그래프가 동일한 계산 결과를 "
    "참조한다. 관측치가 연간 3개뿐이어서 추론통계 없이 수준·변화·구성의 기술적 분석에 한정하였고, "
    "검증은 원문 수치 간 관계식 재계산으로 수행하였다(부록 A).")

# ═══════════════════ 4. 표·그래프와 핵심 발견 ═══════════════════
H1("4.  표·그래프와 핵심 발견")

H2("4-1. 3개년 추이", before=4)
T(["구분", "2023", "2024", "2025"],
  [["매출액 (억원)"] + [eok(M[y]["revenue"]) for y in YEARS],
   ["영업이익 (억원)"] + [eok(M[y]["operating_income"]) for y in YEARS],
   ["당기순이익 (억원)"] + [eok(M[y]["net_income"]) for y in YEARS],
   ["금융원가 (억원)"] + [eok(M[y]["finance_cost"]) for y in YEARS],
   ["영업활동현금흐름 (억원)"] + [eok(M[y]["ocf"]) for y in YEARS],
   ["영업이익률"] + [f"{M[y]['operating_margin']:.2f}%" for y in YEARS],
   ["당기순이익률"] + [f"{M[y]['net_margin']:.2f}%" for y in YEARS],
   ["금융원가율"] + [f"{M[y]['finance_cost_ratio']:.2f}%" for y in YEARS],
   ["부채비율"] + [("—" if M[y]["debt_ratio"] is None else f"{M[y]['debt_ratio']:.2f}%") for y in YEARS]],
  widths=[5.2, 3.5, 3.5, 3.5], ar=[1, 2, 3], hl=[2, 3],
  note="표 3. 주요 지표 요약 (별도재무제표 · K-IFRS). 2023년 부채비율은 자본잠식으로 산출하지 않았고 "
       "%p 차이는 원수치로 계산한다. 출처: 2025 사업보고서 III-4-1·4-2·4-4.",
  after=5)

fig("fig1_ratios.png", "그림 1.  수익성 지표와 금융원가율 추이 (2023~2025, 단위: %). "
    "출처: 2025 사업보고서 III-4-2.", 9.0)
P(f"변동 폭이 가장 큰 지표는 금융원가율로 매출액의 {M['2023']['finance_cost_ratio']:.2f}%에서 "
  f"{M['2025']['finance_cost_ratio']:.2f}%로 낮아졌다. 같은 기간 영업이익률은 "
  f"{ppt(M['2025']['operating_margin'], M['2023']['operating_margin']):.2f}%p 상승한 반면 당기순이익률은 "
  f"{ppt(M['2025']['net_margin'], M['2023']['net_margin']):.2f}%p 움직였다.", after=4)

H2("4-2. 핵심 발견 ① — 이익 개선의 주된 원천은 영업 외 항목이다")
fig("fig2_bridge.png",
    f"그림 2.  2024년 당기순이익 변화 분해 (2023→2024, 총 {D['bridge_2024_total']/1e8:+,.1f}억원, 단위: 억원). "
    f"출처: 2025 사업보고서 III-4-2.",
    9.8)
P(f"당기순손익은 2023년 {eok(M['2023']['net_income'])}억원에서 2024년 {eok(M['2024']['net_income'])}억원으로 "
  f"+{eok(D['bridge_2024_total'])}억원 변화했다. 그림 2는 이를 항목별로 분해한 것으로(금액은 부록 D 표 D-1), "
  f"비용은 감소가 이익 증가로 작용하므로 부호를 반전했다.", after=4)
rich([("금융원가 감소가 단일 항목으로 ", False),
      (f"{BR['금융원가 감소']['share']:.1f}%", True),
      ("를 차지한다. 영업이익 개선의 기여도 ", False),
      (f"{BR['영업이익']['share']:.1f}%", True),
      ("보다 3배 이상 크다. 이는 각 항목의 산술적 기여도이며, 항목 간 인과관계를 뜻하지는 않는다.", False)],
     after=4)
P(f"2023년 금융원가 {eok(FC['total'])}억원은 이자비용 {eok(FC['cash'])}억원, 파생상품평가손실 "
  f"{eok(FCD[(2023, '파생상품평가손실')])}억원, 손상차손 {eok(FCD[(2023, '손상차손')])}억원으로 구성되며, "
  f"뒤의 두 항목 합계 {eok(FC['non_cash'])}억원({FC['non_cash']/FC['total']*100:.1f}%)은 현금 유출을 "
  f"수반하지 않는다. 그 발생 원천인 파생상품부채·상환전환우선주부채 합계 "
  f"{eok(bdet[('2023-12-31','파생상품부채')] + bdet[('2023-12-31','상환전환우선주부채')])}억원은 2024년 중 "
  f"전액 자본으로 전환되어 2024년 말 잔액이 0이고(주석 19.1·5.3), 상각후원가측정금융자산은 2023년 말 "
  f"장부금액이 이미 0이다(주석 10.1).", after=4)

H2("4-3. 핵심 발견 ② — 2025년 손익 항목의 증감 방향이 엇갈린다")
rich([(f"2025년 매출액은 {abs(M['2025']['revenue_growth']):.2f}%, 영업이익은 "
       f"{abs(M['2025']['op_growth']):.2f}% 감소했다. 그러나 당기순이익은 "
       f"{M['2025']['ni_growth']:.2f}% 증가했다. ", False),
      ("손익계산서의 윗부분과 아랫부분이 반대 방향을 가리킨다.", True)], after=3)
P(f"같은 기간 금융원가 {eok(M['2024']['finance_cost'])}→{eok(M['2025']['finance_cost'])}억원, 기타비용 "
  f"{eok(fv(2024,'other_expense'))}→{eok(fv(2025,'other_expense'))}억원으로 줄었고 기타수익은 "
  f"{eok(fv(2024,'other_income'))}→{eok(fv(2025,'other_income'))}억원으로 늘었다.", after=4)

H2("4-4. 핵심 발견 ③ — 이익과 현금의 방향도 엇갈린다")
fig("fig3_levels.png", "그림 3.  영업이익·당기순이익·영업활동현금흐름 (2023~2025, 단위: 억원). "
    "출처: 2025 사업보고서 III-4-2·III-4-4.", 9.0)
P(f"2023년은 당기순손실 {eok(M['2023']['net_income'])}억원에도 영업활동현금흐름이 "
  f"+{eok(M['2023']['ocf'])}억원이었다. [참고 계산] 순손실에 4-2절의 비현금 금융원가 "
  f"{eok(FC['non_cash'])}억원만 되돌리면 +{eok(M['2023']['net_income']+FC['non_cash'])}억원으로 부호가 "
  f"맞는다. 방향 확인용 약식 계산이며 정식 조정 내역은 현금흐름표 간접법 항목에서 확인해야 한다.",
  after=4)
rich([(f"2025년에는 당기순이익이 {M['2025']['ni_growth']:.2f}% 증가하는 동안 영업활동현금흐름은 "
       f"{eok(M['2024']['ocf'])}억원에서 {eok(M['2025']['ocf'])}억원으로 ", False),
      (f"{abs(M['2025']['ocf_growth']):.2f}% 감소했다", True),
      (f". 영업활동현금흐름 ÷ 영업이익 배수는 {M['2023']['ocf_to_op']:.2f}배 → {M['2024']['ocf_to_op']:.2f}배 → "
       f"{M['2025']['ocf_to_op']:.2f}배로, 당기순이익 대비 배수는 2024년 {M['2024']['ocf_to_ni']:.2f}배에서 "
       f"2025년 {M['2025']['ocf_to_ni']:.2f}배로 낮아졌다(부록 D 표 D-2).", False)], after=4)

H2("4-5. 핵심 발견 ④ — 매출 정체의 내부에서 구성이 바뀌고 있다")
tot = {y: seg[y]["헤어&스칼프"] + seg[y]["스킨&바디"] for y in (2023, 2024, 2025)}
T(["구분", "2023", "2024", "2025", "2024→2025"],
  [["헤어&스칼프 (백만원)"] + [mn(seg[y]["헤어&스칼프"]) for y in (2023, 2024, 2025)]
   + [f"{seg[2025]['헤어&스칼프']/seg[2024]['헤어&스칼프']*100-100:+.1f}%"],
   ["스킨&바디 (백만원)"] + [mn(seg[y]["스킨&바디"]) for y in (2023, 2024, 2025)]
   + [f"{seg[2025]['스킨&바디']/seg[2024]['스킨&바디']*100-100:+.1f}%"],
   ["수출 (백만원)"] + [mn(ED[y]["수출"]) for y in (2023, 2024, 2025)]
   + [f"{ED[2025]['수출_증감률']:+.1f}%"],
   ["내수 (백만원)"] + [mn(ED[y]["내수"]) for y in (2023, 2024, 2025)]
   + [f"{ED[2025]['내수_증감률']:+.1f}%"],
   ["매출액 (백만원)"] + [mn(tot[y]) for y in (2023, 2024, 2025)]
   + [f"{tot[2025]/tot[2024]*100-100:+.1f}%"]],
  widths=[5.0, 2.6, 2.6, 2.6, 2.9], ar=[1, 2, 3, 4], hl=[2, 3],
  note="표 4. 매출액의 두 가지 구성 (단위: 백만원). 위 두 줄은 사업부문별, 아래 두 줄은 수출·내수별 "
       "구분이며 각각의 합이 매출액이다. 교차 내역·비중·채널별 매출은 부록 H, 제품별은 부록 D 표 D-3. "
       "출처: 2025 사업보고서(20260320001362) II-2, II-4.", after=5)
P(f"같은 매출액을 두 방향으로 나누면 감소분의 소재가 드러난다. 2025년 매출액이 "
  f"{abs(M['2025']['revenue_growth']):.2f}% 감소하는 동안 수출은 {ED[2025]['수출_증감률']:+.2f}%, "
  f"내수는 {ED[2025]['내수_증감률']:+.2f}% 변동했다. 수출 비중은 3년 사이 {ED[2023]['수출비중']:.1f}%에서 "
  f"{ED[2025]['수출비중']:.1f}%로 높아졌고, 헤어&스칼프 비중은 {seg[2023]['헤어&스칼프']/tot[2023]*100:.1f}%에서 "
  f"{seg[2025]['헤어&스칼프']/tot[2025]*100:.1f}%로 높아졌다. 두 구분을 교차한 네 칸 가운데 2025년에 "
  f"증가한 칸은 헤어&스칼프 수출({ED[2025]['헤어&스칼프_수출_증감률']:+.1f}%) 하나이고 나머지 세 칸은 "
  f"모두 감소했다(부록 H 표 H-1). 금액이 공시된 두 품목도 2024→2025년에 로즈마리 루트 인핸서 "
  f"{prod['로즈마리 루트 인핸서'][2025]/prod['로즈마리 루트 인핸서'][2024]*100-100:+.1f}%, 스케일링 샴푸 "
  f"{prod['로즈마리 스칼프 스케일링 샴푸'][2025]/prod['로즈마리 스칼프 스케일링 샴푸'][2024]*100-100:+.1f}%로 "
  f"갈렸다(부록 D 표 D-3).", after=4)

# ═══════════════════ 5. 문제 후보, 한계와 추가 확인 계획 ═══════════════════
H1("5.  문제 후보, 분석의 한계와 추가 확인 계획")

H2("5-1. 문제 후보", before=4)
P("외형 성장의 둔화가 재무구조 개선 효과에 가려져 있을 가능성", 11, True, INK, after=5)

P("관찰된 사실", 10, True, INK, before=3, after=3)
bul(f"2024년 당기순이익 변화 +{eok(D['bridge_2024_total'])}억원 중 금융원가 감소가 "
    f"+{eok(BR['금융원가 감소']['value'])}억원({BR['금융원가 감소']['share']:.1f}%), "
    f"영업이익 개선이 +{eok(BR['영업이익']['value'])}억원({BR['영업이익']['share']:.1f}%)이다.")
bul(f"2023년 금융원가 {eok(FC['total'])}억원 중 {eok(FC['non_cash'])}억원"
    f"({FC['non_cash']/FC['total']*100:.1f}%)이 비현금 항목이며, 두 항목의 잔액은 각각 2024년 말과 "
    f"2023년 말에 0이 되었다(주석 19.1·5.3 / 10.1).")
bul(f"2025년 매출액 {abs(M['2025']['revenue_growth']):.2f}%, 영업이익 {abs(M['2025']['op_growth']):.2f}%, "
    f"영업활동현금흐름 {abs(M['2025']['ocf_growth']):.2f}%가 각각 감소한 반면 당기순이익은 "
    f"{M['2025']['ni_growth']:.2f}% 증가했다. 같은 해 내수 매출은 {abs(ED[2025]['내수_증감률']):.1f}%, "
    f"스킨&바디 매출은 {abs(seg[2025]['스킨&바디']/seg[2024]['스킨&바디']*100-100):.1f}% 감소한 반면 "
    f"수출 매출은 {ED[2025]['수출_증감률']:+.1f}% 증가했다.")

P("가능한 원인 가설 (단정하지 않음)", 10, True, INK, before=5, after=3)
bul("가설 1 — 2024년의 이익 개선은 상환전환우선주의 자본 전환과 금융자산 손상 종료에 따른 일회성 효과일 수 있다. "
    "두 항목의 잔액이 모두 0이므로 같은 항목에서 같은 크기의 개선 요인이 다시 발생할 여지는 없다. "
    "다만 다른 자산의 손상 가능성까지 배제되는 것은 아니다.")
bul(f"가설 2 — 성장 동력이 헤어&스칼프 수출로 좁아지고 있을 수 있다. 2025년 부문×수출·내수 네 칸 중 "
    f"증가한 칸은 헤어&스칼프 수출({ED[2025]['헤어&스칼프_수출_증감률']:+.1f}%) 하나이고, 같은 부문의 "
    f"내수와 스킨&바디의 양 칸은 모두 감소했다. 금액이 공시된 두 품목의 2024→2025년 증감 방향도 "
    f"갈렸다(부록 D 표 D-3).")
bul(f"가설 3 — 2025년의 영업이익·영업활동현금흐름 감소는 비용 선행과 운전자본 변동에서 비롯되었을 수 있다"
    f"(판관비 {eok(fv(2024,'sga'))} → {eok(fv(2025,'sga'))}억원, 영업에서 창출된 현금 "
    f"{eok(int(cf[2024]['cash_from_operations']))} → {eok(int(cf[2025]['cash_from_operations']))}억원).")

P("더 필요한 자료와 확인 방법", 10, True, INK, before=5, after=3)
T(["확인할 것", "필요한 자료", "확인 방법"],
  [["가설 1 — 일회성 여부", "2026년 3분기 분기보고서 및 2026 사업보고서",
    f"금융원가가 2025년 수준({eok(M['2025']['finance_cost'])}억원)에서 유지되는지, "
    f"2026년 누적 추세가 이어지는지 확인"],
   ["가설 2 — 성장 축의 범위", "2024년 채널별 매출 (증권신고서 2025.11 또는 2026 사업보고서)",
    "2025년 채널별 매출은 확보하였으나(부록 H 표 H-2) 전년 수치가 없다. "
    "확보 시 채널별 증감을 부문×수출·내수 증감과 대조"],
   ["가설 3 — 비용·운전자본", "판매비와관리비 주석, 현금흐름표 간접법 조정 내역",
    "계정별 증감을 분리하고 매출채권·재고자산·매입채무 변동액을 OCF 감소분과 대조"],
   ],
  widths=[3.2, 5.0, 6.8], fs=8.0,
  note="현황 설명에 한정하였으며, 가설 검증과 전략은 기말 프로젝트에서 다룬다.", after=4)

H2("5-2. 분석의 한계")
bul("기준의 이중성과 변경 — 2023년은 채택하는 회계기준에 따라 추세 해석이 달라지고, 2026년부터는 "
    "연결재무제표가 작성되어 별도 기준의 2023~2025년과 직접 비교할 수 없다. 2026년 수치를 본문 추세에 "
    "넣지 않고 부록 F에 참고로 분리한 이유다.")
bul("시계열의 길이와 비교 표본 — 2025년 11월 상장으로 분기 정기보고서는 2026년 1분기부터만 존재하고, "
    "연간 3개 관측치로는 추세 검정이 성립하지 않아 추론통계를 쓰지 않았다. 회계기준 전환을 겪은 기업과 "
    "그렇지 않은 기업의 비교는 해석을 왜곡하므로 경쟁사 비교도 하지 않았다.")
bul("자료의 범위 — 채널별 매출은 2025년만 기재되어 증감을 산출하지 못했고(부록 H), 마케팅비 세부 "
    "내역은 정기보고서에 없다. 부록 G의 시장 전망치는 회사가 인용한 외부 자료여서 판단 근거로 쓰지 않았다.")



# ═══════════════════ 부록 ═══════════════════
_h = _h = H1("부록 A.  핵심 수치 검증 기록")
_h.paragraph_format.page_break_before = True
_h.paragraph_format.space_before = Pt(0)
_kinds = {}
for _c in vlog:
    _kinds[_c["kind"]] = _kinds.get(_c["kind"], 0) + 1
P(f"총 {len(vlog)}건을 기록하였고 전 건이 통과하였다. 외부 자료와의 대조는 사용하지 않고, "
  f"DART 원문 내부의 관계식 재계산({_kinds.get('관계식 재계산', 0)}건)과 같은 수치의 전사 일치 확인"
  f"({_kinds.get('전사 일치 확인', 0)}건)으로만 수행하였다. 나머지 {_kinds.get('도출값 재현', 0)}건은 "
  f"2026년 1분기처럼 원문에 직접 실려 있지 않아 도출한 값이 도출식과 일치하는지 남긴 기록으로, "
  f"구조상 실패할 수 없으므로 검증 건수와 구분하였다(원문 수치 간 교차검증은 "
  f"{len(vlog) - _kinds.get('도출값 재현', 0)}건). 이 구분은 verification_log.csv의 kind 열에 "
  "'도출값 재현'으로 표시되어 있고, code/01_verify.py를 실행하면 같은 결과를 재현할 수 있다. "
  "아래는 그중 핵심 6건이다.", after=5)

pick = ["1-2025d", "3-2023", "4b-2025", "8-3", "8-4", "9-4"]
labels = {
    "1-2025d": "2025년 당기순이익",
    "3-2023": "2023년 금융원가",
    "4b-2025": "2025년 사업부문 매출 합계",
    "8-3": "2023년 손상차손",
    "8-4": "2023년 말 상환전환우선주 관련 부채",
    "9-4": "2025년 수출액 (서로 다른 두 표 대조)",
}
rows = []
for i, no in enumerate(pick, 1):
    c = next(x for x in vlog if x["no"] == no)
    rows.append([str(i), labels[no], c["source_location"], c["formula"],
                 f"{int(c['computed']):,}", c["result"]])
T(["번호", "검증 대상", "원문 위치", "계산식", "계산값", "결과"], rows,
  widths=[1.0, 2.8, 4.2, 4.4, 2.6, 1.1], ar=[4], fs=7.6,
  note="2번은 주석 단위가 천원, 3·6번은 사업부문·판매경로 표 단위가 백만원이어서 각 단위만큼의 허용 "
       "오차를 두었다. 따라서 '통과'는 차이가 0이라는 뜻이 아니라 단위에서 오는 반올림 범위 안이라는 "
       "뜻이며, 허용치와 실제 차이는 verification_log.csv의 tolerance·diff 열에 건별로 기록되어 있다. "
       "6번은 판매경로표의 해외 채널 합계가 매출실적표의 수출 합계와 일치하는지를 확인한 것으로, "
       "같은 사업보고서 안의 서로 다른 두 표를 맞대본 검증이다.", after=5)
P("검증 과정에서 수정한 내용", 10, True, INK, before=2, after=3)
bul("사전 조사 단계에서 일부 기업정보 사이트의 2023년 매출액이 47,014백만원으로 표기되어 있었다. "
    "원문 대조 결과 이는 과거회계기준 수치였고 K-IFRS 기준으로는 44,554백만원이다. "
    "두 기준의 차이를 확인한 뒤 본문 전체를 K-IFRS로 통일하고 비교표를 부록 E에 추가하였다.")
bul("초안에서 '파생금융부채와 손상 대상 금융자산의 기말 잔액이 2024년에 각각 0이 되었다'고 기술했으나, "
    "주석 10.1을 대조한 결과 상각후원가측정금융자산의 장부금액은 2023년 말에 이미 0이었다. "
    "해당 서술을 항목별로 분리하고 주석 번호를 병기하는 것으로 수정하였다.")
bul("초안에서 '채널별 매출은 정기보고서에 기재되지 않아 확인하지 못했다'고 기술하고 이를 추가 확인 "
    "과제로 분류했으나, 사업보고서 「II-4. 매출 및 수주상황」에 2025년 채널별 매출과 3개년 수출·내수 "
    "분해가 기재되어 있음을 확인하였다. 해당 자료를 부록 H로 수록하고 본문 4-5절과 표 4를 수출·내수 "
    "구분까지 포함하도록 다시 작성하였으며, 한계 서술은 '2025년만 기재되어 채널별 전년 대비 증감을 "
    "산출할 수 없다'로 범위를 좁혔다.")
bul("부록 G 초안에서 산업 특성을 '다품종 소량생산 구조', 경쟁 상황을 '제조 위탁이 보편화되어 진입장벽이 "
    "낮다'로 기술했으나, 원문을 문장 단위로 다시 대조한 결과 두 표현 모두 사업보고서에 없는 서술이었다. "
    "원문 기재('소비 트렌드 변화에 민감한 소비재 산업', '진입장벽이 낮아져 경쟁강도가 비교적 높음')대로 "
    "고치고 본문 2-1절의 같은 표현도 함께 수정하였다. 같은 대조에서 지적재산권 36건의 출처가 "
    "「II-7-라」가 아니라 「II-7-나」임을 확인하여 출처 표기를 분리하였다.")

H1("부록 B.  AI 활용 기록")
P("본 과제는 분석·시각화·문서 작성에 AI를 활용하였다. 아래는 대표 프롬프트와, "
  "AI 출력에서 확인한 문제 및 수정한 내용이다.", after=5)
T(["번호", "입력한 프롬프트 (요지)", "AI 출력에서 확인한 문제", "검토·수정한 내용"],
  [["1", "매출 500~2000억 구간의 중소·중견기업 중 시장 변화로 매출이 둔화된 기업을 찾아 달라",
    "후보 기업의 매출 규모가 연결·별도 기준에 따라 범위를 벗어났고, 일부는 2차 자료의 수치였다",
    "연결·별도 기준을 명시하도록 요구하고 DART 원문으로 규모를 재확인한 뒤 대상 기업을 아로마티카로 확정"],
   ["2", "출처나 판단이 다 확실한 것인가",
    "2026년 분기 실적이 언론 기사 기준으로 들어가 있었고, 원인에 대한 단정적 서술이 사실과 섞여 있었다",
    "반기보고서 원문으로 전면 교체(1분기 영업이익 13.0억 → 13.4억 등). 기여도 서술을 단일 수치 대신 "
    "전 항목 분해표로 바꾸어 검증 가능하게 수정"],
   ["3", "DART 공시에서 나온 것 말고는 쓰지 말자. 추론 부분도 빼자",
    "종목코드·상장일·공모주식수가 위키백과와 기사 출처였고 공모주식수는 249만주로 잘못 기재되어 있었다. "
    "또 매출액과 영업이익률을 하나의 그래프에 이중축으로 그려 단위가 다른 두 계열이 같은 평면에서 비교되었다",
    "증권발행실적보고서(20251121000203)로 대체하여 3,000,000주 확인. 원문에서 확인되지 않는 항목은 삭제. "
    "관찰·계산과 추론을 분리하고 추론은 본문에서 제외. 그래프는 단위가 같은 계열끼리 분리하여 "
    "비율(그림 1)과 금액(그림 3)으로 나누고, 자본잠식으로 음수인 2023년 부채비율은 그래프에서 제외"],
   ["4", "과제 요건을 다시 정확히 대조하고 빠진 것을 채워 달라",
    "산업 환경에 대한 서술이 거의 없었고, 2026년 수치가 본문에서 빠진 뒤 어디에도 남아 있지 않았다. "
    "또 '채널별 매출은 정기보고서에 기재되지 않는다'는 서술이 사실과 달랐다",
    "사업보고서 II-7-라에서 산업 환경을 정리해 부록 G로, 2026 반기 실적을 부록 F로 수록. "
    "II-4에서 수출·내수 분해와 채널별 매출을 확보하여 부록 H로 수록하고 본문 4-5절을 다시 작성. "
    "잘못된 서술과 그에 근거한 확인 계획 항목을 수정하고 그 사실을 부록 A에 기록. 검증은 36건 → 62건"]],
  widths=[1.1, 3.9, 5.0, 5.9], fs=8.0,
  note="AI가 생성한 사실과 수치는 모두 DART 원문 또는 재계산으로 확인하였다. "
       "확인되지 않은 항목은 보고서에 포함하지 않았다.", after=5)

H1("부록 C.  개인 수행 범위와 동료 피드백")
H2("개인 수행 범위", before=3)
T(["구분", "내용"],
  [["공동 수행 (3조)", "분석 대상 기업 선정, 분야별 자료조사 분담 및 공유"],
   ["본인 담당 자료조사", "4. 당기순이익 및 보조 자료 — 3개년 당기순이익, 영업활동현금흐름, "
    "연도별 출처·단위, 최근 사업 변화 및 공식 발표 자료"],
   ["본인 단독 수행", "분석 질문 설정, 지표 정의와 산식 확정, 데이터셋 구축, 검증 스크립트 작성, "
    "지표 계산 및 그래프 생성, 본 보고서 작성"],
   ["공유 자료의 출처", "조원이 공유한 매출액·영업이익·부채비율 자료는 참고하였으나, "
    "본 보고서에 수록한 수치는 전부 본인이 DART 원문에서 다시 확인한 값이다"]],
  widths=[3.4, 11.7], fs=8.6, after=5)

H2("동료 피드백 및 반영 내용")
T(["번호", "피드백 내용", "반영 결과"],
  [["1", "2023년 회계기준 수립 필요 — 아로마티카는 2024 회계연도부터 K-IFRS를 최초 적용했고 "
    "그 이전은 일반기업회계기준으로 작성되어 2023년 수치가 두 가지로 공시되어 있다. "
    "2024·2025년과 기준을 맞추기 위해 K-IFRS로 통일하되, 2023 감사보고서가 아닌 "
    "2024 감사보고서에 비교표시된 2023년 수치를 사용하자",
    "조 공통기준으로 채택. 다만 K-IFRS 재작성 수치는 2024 감사보고서와 2025 사업보고서가 동일하게 비교표시하고 있어, 본 보고서는 더 최근 보고서인 2025 사업보고서의 제23기 비교표시 열을 사용하였다. 3-3절에 기준으로 명시하고 두 기준의 차이는 부록 E 표 E-1로 제시"],
   ["2", "별도재무제표와 연결재무제표 중 무엇을 쓸 것인가 — 해외법인이 2026년에 설립된 것으로 파악되므로 "
    "2023~2025년은 별도, 2026년은 연결을 쓰는 것이 좋겠다. 2023~2025년은 연결재무제표가 아예 없는 것으로 보인다",
    "조 공통기준으로 채택. 2025 사업보고서 「III-2. 연결재무제표」가 '해당사항이 없습니다'로 기재된 것을 "
    "원문에서 확인하여 3-3절에 근거로 기재"],
   ],
  widths=[1.1, 7.0, 7.0], fs=8.0,
  note="두 건 모두 본인이 조 자료조사 단계에서 제기한 쟁점에 대해 조원이 검토·동의하여 조 공통기준으로 확정된 것이다. "
       "조원이 추가로 제공한 종속회사 관련 정보는 2026 반기보고서 「IX-1. 연결대상 종속회사 현황」과 대조하여 "
       "기재 범위를 확인한 뒤 반영하였다.", after=5)

H1("부록 D.  본문 표의 상세 수치")
P("본문에서 그림으로 제시한 내용의 항목별 금액이다.", after=4)
P("표 D-1. 2024년 당기순이익 변화 분해 (단위: 억원)", 9.6, True, INK, before=2, after=3)
T(["항목", "2023", "2024", "변화", "기여도"],
  [["영업이익", eok(fv(2023, "operating_income")), eok(fv(2024, "operating_income")),
    f"{BR['영업이익']['value']/1e8:+,.1f}", f"{BR['영업이익']['share']:.1f}%"],
   ["기타수익", eok(fv(2023, "other_income")), eok(fv(2024, "other_income")),
    f"{BR['기타수익']['value']/1e8:+,.1f}", f"{BR['기타수익']['share']:.1f}%"],
   ["기타비용 (감소)", eok(fv(2023, "other_expense")), eok(fv(2024, "other_expense")),
    f"{BR['기타비용 감소']['value']/1e8:+,.1f}", f"{BR['기타비용 감소']['share']:.1f}%"],
   ["금융수익", eok(fv(2023, "finance_income")), eok(fv(2024, "finance_income")),
    f"{BR['금융수익']['value']/1e8:+,.1f}", f"{BR['금융수익']['share']:.1f}%"],
   ["금융원가 (감소)", eok(fv(2023, "finance_cost")), eok(fv(2024, "finance_cost")),
    f"{BR['금융원가 감소']['value']/1e8:+,.1f}", f"{BR['금융원가 감소']['share']:.1f}%"],
   ["법인세비용 (증가)", eok(fv(2023, "income_tax")), eok(fv(2024, "income_tax")),
    f"{BR['법인세비용 증가']['value']/1e8:+,.1f}", f"{BR['법인세비용 증가']['share']:.1f}%"],
   ["당기순이익 변화", eok(M["2023"]["net_income"]), eok(M["2024"]["net_income"]),
    f"{D['bridge_2024_total']/1e8:+,.1f}", "100.0%"]],
  widths=[4.0, 2.7, 2.7, 2.7, 2.6], ar=[1, 2, 3, 4], hl=[4, 6],
  note="비용 항목은 감소가 이익 증가로 작용하므로 부호를 반전하여 표기하였다. "
       "기여도 = 항목별 변화분 ÷ 당기순이익 변화 총액. 반올림으로 합계가 소수점 이하에서 차이날 수 있다. "
       "출처: 2025 사업보고서(20260320001362) III-4-2 포괄손익계산서.", after=5)
P("표 D-2. 이익과 영업활동현금흐름 대조", 9.6, True, INK, before=4, after=3)
T(["구분", "2023", "2024", "2025"],
  [["영업이익 (억원)"] + [eok(M[y]["operating_income"]) for y in YEARS],
   ["당기순이익 (억원)"] + [eok(M[y]["net_income"]) for y in YEARS],
   ["영업활동현금흐름 (억원)"] + [eok(M[y]["ocf"]) for y in YEARS],
   ["OCF ÷ 영업이익"] + [f"{M[y]['ocf_to_op']:.2f}배" for y in YEARS],
   ["OCF ÷ 당기순이익", "—"] + [f"{M[y]['ocf_to_ni']:.2f}배" for y in ("2024", "2025")]],
  widths=[5.2, 3.5, 3.5, 3.5], ar=[1, 2, 3],
  note="2023년 OCF ÷ 당기순이익은 분모가 순손실이므로 산출하지 않았다. "
       "출처: 2025 사업보고서(20260320001362) III-4-2 포괄손익계산서(영업이익·당기순이익) 및 "
       "III-4-4 현금흐름표(영업활동현금흐름).", after=5)

P("표 D-3. 헤어&스칼프 부문 주요 제품별 매출 (단위: 백만원)", 9.6, True, INK, before=4, after=3)
T(["제품", "2023", "2024", "2025", "2024→2025"],
  [["로즈마리 루트 인핸서"] + [mn(prod["로즈마리 루트 인핸서"][y]) for y in (2023, 2024, 2025)]
   + [f"{prod['로즈마리 루트 인핸서'][2025]/prod['로즈마리 루트 인핸서'][2024]*100-100:+.1f}%"],
   ["로즈마리 스칼프 스케일링 샴푸"] + [mn(prod["로즈마리 스칼프 스케일링 샴푸"][y]) for y in (2023, 2024, 2025)]
   + [f"{prod['로즈마리 스칼프 스케일링 샴푸'][2025]/prod['로즈마리 스칼프 스케일링 샴푸'][2024]*100-100:+.1f}%"]],
  widths=[5.0, 2.6, 2.6, 2.6, 2.9], ar=[1, 2, 3, 4], fs=8.6, nosplit=True,
  note="사업보고서가 금액을 공시한 품목은 이 둘뿐이며 모두 헤어&스칼프 부문이다. 2023→2025년 구간에서는 "
       "두 품목 모두 증가했고(각 +147.7%, +6.7%), 방향이 갈리는 것은 2024→2025년 구간이다. "
       "출처: 2025 사업보고서(20260320001362) II-2.", after=5)

H1("부록 E.  2023년 회계기준 전환 대조")
P("2023년은 과거회계기준과 K-IFRS 재작성 수치가 모두 공시되어 있다. 두 기준의 차이는 "
  "당기순손익의 부호와 자본잠식 여부까지 바꾸므로, 3개년 추세를 읽을 때 기준을 혼용하면 해석이 달라진다.", after=4)
T(["2023년 (제23기)", "과거회계기준", "K-IFRS 재작성", "차이"],
  [["매출액 (억원)", eok(int(cmp23["revenue"]["kgaap_2023"])), eok(int(cmp23["revenue"]["kifrs_2023"])),
    eok(int(cmp23["revenue"]["kifrs_2023"]) - int(cmp23["revenue"]["kgaap_2023"]))],
   ["영업이익 (억원)", eok(int(cmp23["operating_income"]["kgaap_2023"])),
    eok(int(cmp23["operating_income"]["kifrs_2023"])),
    eok(int(cmp23["operating_income"]["kifrs_2023"]) - int(cmp23["operating_income"]["kgaap_2023"]))],
   ["당기순손익 (억원)", eok(int(cmp23["net_income"]["kgaap_2023"])), eok(int(cmp23["net_income"]["kifrs_2023"])),
    eok(int(cmp23["net_income"]["kifrs_2023"]) - int(cmp23["net_income"]["kgaap_2023"]))],
   ["자본총계 (억원)", eok(int(cmp23["total_equity"]["kgaap_2023"])), eok(int(cmp23["total_equity"]["kifrs_2023"])),
    eok(int(cmp23["total_equity"]["kifrs_2023"]) - int(cmp23["total_equity"]["kgaap_2023"]))],
   ["부채비율",
    f"{int(cmp23['total_liabilities']['kgaap_2023'])/int(cmp23['total_equity']['kgaap_2023'])*100:.2f}%",
    "— (자본잠식)", "—"]],
  widths=[4.2, 3.4, 3.6, 3.0], ar=[1, 2, 3], hl=[2, 3],
  note="표 E-1. 2023년 두 회계기준 대조. 과거회계기준 열의 출처는 2023 감사보고서(20240401001486), "
       "K-IFRS 재작성 열의 출처는 2025 사업보고서(20260320001362) 제23기 비교표시이며, "
       "아래 조정 내역은 2024 감사보고서(20250331002452) 주석 36.4에서 확인하였다. "
       "두 기준의 수치 모두 외부감사를 받은 정식 공시 수치다.", after=5)
_adj = [(k, v) for k, v in tr23.items() if k != "과거회계기준 당기순이익"]
_adj.sort(key=lambda x: x[1])
_tot = sum(v for _, v in _adj)
P(f"2024 감사보고서 주석 36.4에 따르면 당기순손익 조정액 {_tot/1e8:,.1f}억원의 내역은 "
  + ", ".join(f"{k} {v/1e8:+,.1f}억원" for k, v in _adj)
  + "이다. 본 보고서는 2024·2025년과 기준을 맞추기 위해 K-IFRS 열을 사용하였다.", after=4)

# ─── 부록 F. 2026년 실적 참고 ───
H1("부록 F.  2026년 실적 참고 (본문 추세에서 제외)")
P("2026년부터 연결재무제표가 작성되어 2023~2025년(별도)과 기준이 다르다. 본문 3~5절의 추세에는 "
  "포함하지 않았으나, 가설 1(금융원가 감소의 일회성 여부)의 확인 방향을 가늠할 수 있어 참고로 수록한다. "
  "아래 수치는 2026 반기보고서 원문의 연결 포괄손익계산서이며, 1분기 값은 반기 누적에서 2분기 3개월을 "
  "차감하여 도출하고 검증 기록에 남겼다(verification_log.csv의 검증번호 7-* · 7g-*).", after=4)
_PER = ("2026Q1", "2026Q2", "2026H1")


def _qr(lbl, k):
    return [lbl] + [eok(int(qtr[p][k])) for p in _PER] + [eok(int(qtr["2025H1"][k]))] + [
        f"{int(qtr['2026H1'][k])/int(qtr['2025H1'][k])*100-100:+.1f}%"]


_qrows = [_qr("매출액 (억원)", "revenue"), _qr("매출총이익 (억원)", "gross_profit"),
          _qr("영업이익 (억원)", "operating_income"), _qr("금융수익 (억원)", "finance_income"),
          _qr("금융원가 (억원)", "finance_cost"), _qr("당기순이익 (억원)", "net_income")]
for _lbl, _n, _d in (("영업이익률", "operating_income", "revenue"),
                     ("당기순이익률", "net_income", "revenue"),
                     ("금융원가율", "finance_cost", "revenue")):
    _qrows.append([_lbl] + [f"{int(qtr[p][_n])/int(qtr[p][_d])*100:.2f}%" for p in _PER]
                  + [f"{int(qtr['2025H1'][_n])/int(qtr['2025H1'][_d])*100:.2f}%", "—"])
T(["구분", "2026 1분기", "2026 2분기", "2026 상반기", "2025 상반기", "상반기 증감"], _qrows,
  widths=[3.6, 2.3, 2.3, 2.5, 2.5, 2.2], ar=[1, 2, 3, 4, 5], hl=[4],
  note="표 F-1. 2026년 실적과 전년 동기 (단위: 억원). 2026년 열은 연결, 2025년 상반기 열은 별도 기준이며 "
       "두 기준의 범위가 다르므로 증감률은 참고치다. 1분기는 반기 누적에서 2분기를 차감하여 도출하였다. "
       "출처: 2026 반기보고서(20260818000129) III-2-2. 연결 포괄손익계산서.", after=4)
P(f"가설 1과 관련하여 — 2026년 상반기 금융원가는 {eok(int(qtr['2026H1']['finance_cost']),2)}억원으로 "
  f"전년 동기 {eok(int(qtr['2025H1']['finance_cost']),2)}억원보다 줄었고, 금융원가율은 "
  f"{int(qtr['2025H1']['finance_cost'])/int(qtr['2025H1']['revenue'])*100:.2f}%에서 "
  f"{int(qtr['2026H1']['finance_cost'])/int(qtr['2026H1']['revenue'])*100:.2f}%로 낮아졌다. "
  f"2023년 금융원가율 {M['2023']['finance_cost_ratio']:.2f}%와 비교하면 그 수준으로 되돌아간 "
  f"징후는 아직 관찰되지 않는다. 다만 이는 반기 수치이고 기준도 연결로 바뀌었으므로 가설 1의 확인은 "
  f"2026 사업보고서가 공시된 뒤에 수행해야 한다. 또한 금융수익이 "
  f"{eok(int(qtr['2025H1']['finance_income']),2)}→{eok(int(qtr['2026H1']['finance_income']),2)}억원으로 "
  f"늘었는데, 2025년 11월 공모자금의 운용과 관련될 수 있으나 주석을 확인하지 않았으므로 단정하지 않는다.",
  after=4)

# ─── 부록 G. 산업 환경과 시장 여건 ───
H1("부록 G.  산업 환경과 시장 여건")
P("아래는 2025 사업보고서 「II-7. 기타 참고사항 — 라. 사업부문의 시장여건 및 영업의 개황」에 기재된 "
  "내용을 요약한 것이다(마지막 항목만 같은 장의 「나. 지적재산권 현황」). 회사가 자사 경쟁력에 관해 "
  "서술한 부분은 그 사실을 밝혀 적었고, 시장 규모 전망치는 회사가 외부 조사기관을 인용한 것으로 "
  "본 보고서가 원자료를 직접 확인하지 못했으므로 본문의 판단 근거로 사용하지 않았다.", after=4)
bul("산업의 특성 — 화장품 산업은 소비 트렌드 변화에 민감하게 반응하는 소비재 산업으로, 지속적인 제품 "
    "혁신과 브랜드 경쟁력이 중요하다고 기재되어 있다. 식품의약품안전처 집계로 2025년 국내 화장품 "
    "수출액은 전년 대비 12.3% 증가한 114억 달러로 역대 최대이며, 수출 대상국은 전년보다 30개국 늘어 "
    "202개국이다. 국가별로는 미국이 약 22억 달러로 중국(약 20억 달러)을 제치고 1위를 기록했고 일본이 "
    "약 11억 달러로 뒤를 이었다.")
bul("경기변동과 계절성 — 화장품은 2000년대 이후 사치성 소비재가 아닌 필수소비재로 자리잡아 경기 변동에 "
    "비탄력적이라고 기재되어 있다. 계절에 따른 수요 변동은 전통적으로 컸으나 계절별 기능성 제품이 "
    "다양해지면서 점차 축소되는 추세다. 제품 라이프사이클은 업계 전반에서 짧아지고 있으나, 회사 제품은 "
    "유행을 빠르게 타는 색조가 아닌 일상 케어 제품군 위주여서 상대적으로 긴 편이라고 기재되어 있다.")
bul("시장 여건과 경쟁 — 주 고객층은 환경과 건강한 라이프스타일에 관심을 가진 20~30대 여성이며, "
    "국내 시장과 함께 일본·동남아·미국으로 수출을 확대하고 있다. 국내 화장품 시장은 K-뷰티 수출 증가와 "
    "유통채널 다변화로 급격히 성장했으나 진입장벽이 낮아져 경쟁강도가 비교적 높고, 그만큼 브랜드력이 "
    "유통 업체·OEM 업체에 대한 협상력의 원천으로 더욱 중요해졌다고 기재되어 있다.")
bul("회사가 제시한 경쟁우위 — 성분에 대한 고유한 연구로 자체 제품 개발 능력을 갖추고 있고, 국내 인디 "
    "브랜드 중 드물게 회사 소유의 생산시설을 보유하여 연구개발한 제품을 직접 생산한다는 점, 핵심 원료인 "
    "천연 에센셜 오일을 127년 전통의 글로벌 원료사와 직거래로 조달한다는 점을 들고 있다.")
bul("지적재산권 — 사업보고서 제출일 현재 상표권·디자인권·특허권 총 36건(국내 16건, 해외 20건)을 "
    "출원·등록하였다. 이 항목의 출처는 같은 장의 「II-7-나. 지적재산권 현황」이다.")
T(["시장", "기준연도 규모", "전망연도 규모", "성장률", "구분", "보고서가 인용한 출처"],
  [[r["market"],
    f"{r['base_year']}년 {r['base_value']}{r['base_unit']}",
    (f"{r['target_year']}년 {r['target_value']}{r['base_unit']}" if r["target_value"] else "—"),
    f"{r['growth_pct']}%", r["growth_kind"],
    r["source_in_report"]] for r in ind],
  widths=[4.3, 2.6, 2.6, 1.3, 1.4, 3.1], fs=8.0, ar=[],
  note="표 G-1. 사업보고서에 인용된 산업 규모와 성장률. 첫 행은 식품의약품안전처 집계 실적치이고 나머지 "
       "네 행은 외부 조사기관의 전망치이며, 성장률의 '약'과 범위 표기도 원문 그대로다. 사업보고서가 "
       "기재한 수치만 옮겼고 기준연도 금액을 역산하거나 단위를 환산하지 않았다. 그 결과 기준·전망 금액으로 "
       "역산한 연평균 성장률이 원문에 기재된 성장률과 일치하지 않는 행이 있으나(아로마테라피만 정합), "
       "원문 기재값을 그대로 두었다. 출처: 2025 사업보고서(20260320001362) II-7-라.", after=4)
P("본 보고서의 관찰과의 관계 — 산업 전체가 수출 주도로 성장하는 국면이라는 기재는, 4-5절에서 확인한 "
  "'수출 증가·내수 감소' 구성 변화와 방향이 일치한다. 다만 산업 통계와 회사 수치는 집계 범위와 기간이 "
  "달라 둘을 인과로 연결하지 않았고, 경쟁 심화에 대한 기재 역시 회사 자신의 서술이므로 "
  "경쟁사 수치로 대조하지 않았다(5-2절 참조).", after=4)

# ─── 부록 H. 수출·내수 및 채널별 매출 ───
H1("부록 H.  수출·내수 및 채널별 매출")
P("본문 표 4는 매출액을 사업부문별과 수출·내수별로 각각 나눈 것이다. 아래 표 H-1은 두 구분을 "
  "교차한 네 칸을 보여준다.", after=4)
_SG = ("헤어&스칼프", "스킨&바디")
_hrows = []
for _sg in _SG:
    for _ct in ("수출", "내수"):
        _k = f"{_sg}_{_ct}"
        _hrows.append([f"{_sg} · {_ct}"] + [mn(ED[y][_k]) for y in (2023, 2024, 2025)]
                      + [f"{ED[2024][_k + '_증감률']:+.1f}%", f"{ED[2025][_k + '_증감률']:+.1f}%"])
    _hrows.append([f"  {_sg} 소계"] + [mn(seg[y][_sg]) for y in (2023, 2024, 2025)]
                  + [f"{seg[2024][_sg]/seg[2023][_sg]*100-100:+.1f}%",
                     f"{seg[2025][_sg]/seg[2024][_sg]*100-100:+.1f}%"])
for _ct in ("수출", "내수"):
    _hrows.append([f"{_ct} 합계"] + [mn(ED[y][_ct]) for y in (2023, 2024, 2025)]
                  + [f"{ED[2024][_ct + '_증감률']:+.1f}%", f"{ED[2025][_ct + '_증감률']:+.1f}%"])
_hrows.append(["매출액"] + [mn(ED[y]["합계"]) for y in (2023, 2024, 2025)]
              + [f"{ED[2024]['합계_증감률']:+.1f}%", f"{ED[2025]['합계_증감률']:+.1f}%"])
_hrows.append(["수출 비중"] + [f"{ED[y]['수출비중']:.1f}%" for y in (2023, 2024, 2025)] + ["—", "—"])
_hl = [i for i, r in enumerate(_hrows) if r[-1].startswith("+")]
T(["구분 (백만원)", "2023", "2024", "2025", "2023→2024", "2024→2025"], _hrows,
  widths=[4.0, 2.2, 2.2, 2.2, 2.4, 2.4], ar=[1, 2, 3, 4, 5], fs=8.0, hl=_hl,
  note=f"표 H-1. 사업부문 × 수출·내수 교차 매출 (단위: 백만원). 음영은 2024→2025년에 증가한 {len(_hl)}개 줄이다. "
       "소계·합계는 모두 원문 매출실적표에 인쇄된 값이며, 원문이 셀별로 백만원 단위에서 반올림되어 "
       "합계가 구성 항목의 산술합과 1백만원 어긋나는 칸이 있다(2024년 헤어&스칼프 소계, 수출 합계). "
       "출처: 2025 사업보고서(20260320001362) II-4-가. 매출실적.", after=5)
P("표 H-2는 2025년 매출액을 판매채널별로 나눈 것이다. 전년 수치는 기재되지 않아 채널별 증감은 "
  "산출할 수 없다(5-1절 확인 계획 참조).", after=4)
_order = ["미주", "일본", "유럽", "아시아", "중동", "글로벌 B2B", "글로벌", "기타", "한국"]
_crows = []
for _rg in _order:
    _items = [r for r in chan if r["region"] == _rg]
    for _r in _items:
        _crows.append([_rg, _r["channel_type"], _r["channel_name"],
                       mn(int(_r["revenue_million_krw"])), f"{float(_r['share_pct']):.1f}%"])
_glob = sum(int(r["revenue_million_krw"]) for r in chan if r["region"] != "한국")
_dom = sum(int(r["revenue_million_krw"]) for r in chan if r["region"] == "한국")
_crows.append(["해외 합계 (= 수출)", "", "", mn(_glob), f"{_glob/ED[2025]['합계']*100:.1f}%"])
_crows.append(["국내 합계 (= 내수)", "", "", mn(_dom), f"{_dom/ED[2025]['합계']*100:.1f}%"])
_crows.append(["매출액", "", "", mn(_glob + _dom), "100.0%"])
T(["지역", "유형", "주요 채널", "2025 매출", "비중"], _crows,
  widths=[2.6, 1.9, 6.0, 2.3, 1.8], ar=[3, 4], fs=7.8,
  hl=[len(_crows) - 3, len(_crows) - 2, len(_crows) - 1],
  note="표 H-2. 2025년 판매채널별 매출 (단위: 백만원). 해외·국내 합계가 표 H-1의 수출·내수 합계와 "
       "일치하는지 검증하였다(verification_log.csv의 검증번호 9-4·9-5). 행별 비중은 원문이 소수 첫째 "
       "자리로 반올림해 기재한 값이어서 행별 합(해외 30.7%, 국내 69.3%)이 합계 행과 0.1%p 다르다. "
       "출처: 2025 사업보고서(20260320001362) II-4-나. 판매경로 및 판매방법.", after=4)


H1("부록 I.  제출 자료 구성")
P(f"제출 ZIP({ID['학번']}_{ID['이름']}_분석자료.zip)의 구성은 다음과 같다. "
  "code 디렉터리의 스크립트를 순서대로 실행하면 본 보고서의 모든 수치와 그래프가 재생성된다.", after=4)
T(["경로", "내용"],
  [[f"data/ ({N_DATA}개 파일)", "DART 원문에서 수집한 재무·사업부문·주석 데이터, 출처 매핑표(sources.csv)"],
   ["code/01_verify.py", f"핵심 수치 검증 {len(vlog)}건"],
   ["code/02_metrics.py", "지표 계산 — 본문·표·그래프가 참조하는 단일 계산 결과 생성"],
   ["code/03_charts.py", "그림 1~3 생성"],
   ["code/04_build_report.py", "본 보고서 생성"],
   ["code/05_build_dashboard.py", "대시보드 생성 — 보고서와 같은 metrics.json을 읽는다"],
   ["figures/ (3개 파일)", "그림 1 fig1_ratios · 그림 2 fig2_bridge · 그림 3 fig3_levels"],
   ["index.html", "대시보드 (HTML·CSS·JS 한 파일. 웹폰트만 Google Fonts에서 불러온다)"],
   ["verification_log.csv", "검증 기록 전체"],
   ["metrics.csv / metrics.json", "계산된 지표"],
   ["README.md / GITHUB_PAGES.md", "실행 방법·재계산 절차·출처·공동 작업 범위 / 대시보드 배포 방법"],
   ["identity.json", "표지의 학번·이름·조·일자. 공개 저장소에는 올리지 않는다"]],
  widths=[4.6, 10.5], fs=8.6,
  note="실행: python3 code/01_verify.py → 02_metrics.py → 03_charts.py → 04_build_report.py → "
       "05_build_dashboard.py. 대시보드 공개 주소는 제출 메일에 함께 적었다.", after=4)

out = os.path.join(BASE, f"{ID['학번']}_{ID['이름']}_중간보고서.docx")
doc.save(out)
print(f"저장: {os.path.basename(out)}")
