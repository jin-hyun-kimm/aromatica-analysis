# -*- coding: utf-8 -*-
"""
02_metrics.py — 핵심 지표 계산

보고서 본문·표·그래프·대시보드가 모두 이 스크립트의 출력을 사용한다.
수치를 한 곳에서만 계산하므로 문서 간 숫자가 어긋날 수 없다.

산식
  영업이익률   = 영업이익 ÷ 매출액 × 100
  당기순이익률 = 당기순이익 ÷ 매출액 × 100
  부채비율     = 부채총계 ÷ 자본총계 × 100
  금융원가율   = 금융원가 ÷ 매출액 × 100
  OCF 배수     = 영업활동현금흐름 ÷ (영업이익 또는 당기순이익)

실행:  python3 code/02_metrics.py
출력:  콘솔 표 + metrics.csv
"""
import csv, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
YEARS = (2023, 2024, 2025)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


fin = {int(r["year"]): r for r in load("financials_annual.csv")}
bal = {int(r["year"]): r for r in load("balance_annual.csv")}
cf = {int(r["year"]): r for r in load("cashflow_annual.csv")}
fcd = load("finance_cost_detail.csv")
sed = {}
for r in load("segment_export_domestic.csv"):
    sed.setdefault(int(r["year"]), {})[(r["segment"], r["channel_type"])] = int(r["revenue_million_krw"])

M = {}
for y in YEARS:
    f, b, c = fin[y], bal[y], cf[y]
    rev = int(f["revenue"]); op = int(f["operating_income"])
    ni = int(f["net_income"]); fc = int(f["finance_cost"])
    liab = int(b["total_liabilities"]); eq = int(b["total_equity"])
    ocf = int(c["ocf"])
    M[y] = {
        "year": y,
        "revenue": rev,
        "operating_income": op,
        "net_income": ni,
        "finance_cost": fc,
        "ocf": ocf,
        "total_equity": eq,
        "sga": int(f["sga"]),
        "cash_from_operations": int(c["cash_from_operations"]),
        "operating_margin": op / rev * 100,
        "net_margin": ni / rev * 100,
        "finance_cost_ratio": fc / rev * 100,
        # 자본총계가 음수인 해의 부채비율은 해석이 불가능하므로 None 처리한다.
        "debt_ratio": (liab / eq * 100) if eq > 0 else None,
        "ocf_to_op": ocf / op,
        "ocf_to_ni": (ocf / ni) if ni > 0 else None,
    }

# 전년 대비 증감률
for i, y in enumerate(YEARS):
    if i == 0:
        M[y]["revenue_growth"] = None
        M[y]["op_growth"] = None
        M[y]["ni_growth"] = None
        M[y]["ocf_growth"] = None
        continue
    p = YEARS[i - 1]
    M[y]["revenue_growth"] = (M[y]["revenue"] / M[p]["revenue"] - 1) * 100
    M[y]["op_growth"] = (M[y]["operating_income"] / M[p]["operating_income"] - 1) * 100
    M[y]["ni_growth"] = None  # 전년이 순손실이면 증감률이 의미를 갖지 않는다
    M[y]["ocf_growth"] = (M[y]["ocf"] / M[p]["ocf"] - 1) * 100
M[2025]["ni_growth"] = (M[2025]["net_income"] / M[2024]["net_income"] - 1) * 100

# ── 2024년 당기순이익 변화 분해 ───────────────────────────
# 비용 항목은 감소가 이익 증가로 작용하므로 부호를 반전한다.
a, b_ = fin[2023], fin[2024]
total = int(b_["net_income"]) - int(a["net_income"])
bridge = [
    ("영업이익",        int(b_["operating_income"]) - int(a["operating_income"])),
    ("기타수익",        int(b_["other_income"]) - int(a["other_income"])),
    ("기타비용 감소",    -(int(b_["other_expense"]) - int(a["other_expense"]))),
    ("금융수익",        int(b_["finance_income"]) - int(a["finance_income"])),
    ("금융원가 감소",    -(int(b_["finance_cost"]) - int(a["finance_cost"]))),
    ("법인세비용 증가",  -(int(b_["income_tax"]) - int(a["income_tax"]))),
]
assert sum(v for _, v in bridge) == total, "분해 합계가 당기순이익 변화와 일치하지 않음"

# ── 2023년 금융원가의 현금·비현금 구분 ────────────────────
nc = sum(int(r["value_krw"]) for r in fcd
         if int(r["year"]) == 2023 and r["cash_flow_type"] == "non_cash")
cash = sum(int(r["value_krw"]) for r in fcd
           if int(r["year"]) == 2023 and r["cash_flow_type"] == "cash")

# ── 출력 ──────────────────────────────────────────────────
def pct(v):
    return "-" if v is None else f"{v:,.2f}%"


def mul(v):
    return "-" if v is None else f"{v:,.2f}배"


def eok(v):
    return f"{v/1e8:,.1f}"


print("=" * 86)
print("핵심 지표 (별도재무제표 · K-IFRS · 단위: 억원)")
print("=" * 86)
rows = [
    ("매출액",                 [eok(M[y]["revenue"]) for y in YEARS]),
    ("영업이익",               [eok(M[y]["operating_income"]) for y in YEARS]),
    ("당기순이익",             [eok(M[y]["net_income"]) for y in YEARS]),
    ("금융원가",               [eok(M[y]["finance_cost"]) for y in YEARS]),
    ("영업활동현금흐름",        [eok(M[y]["ocf"]) for y in YEARS]),
    ("자본총계",               [eok(M[y]["total_equity"]) for y in YEARS]),
    ("", []),
    ("영업이익률",             [pct(M[y]["operating_margin"]) for y in YEARS]),
    ("당기순이익률",           [pct(M[y]["net_margin"]) for y in YEARS]),
    ("금융원가율",             [pct(M[y]["finance_cost_ratio"]) for y in YEARS]),
    ("부채비율",               [pct(M[y]["debt_ratio"]) for y in YEARS]),
    ("", []),
    ("OCF ÷ 영업이익",         [mul(M[y]["ocf_to_op"]) for y in YEARS]),
    ("OCF ÷ 당기순이익",       [mul(M[y]["ocf_to_ni"]) for y in YEARS]),
    ("", []),
    ("매출액 증감률",          [pct(M[y]["revenue_growth"]) for y in YEARS]),
    ("영업이익 증감률",        [pct(M[y]["op_growth"]) for y in YEARS]),
    ("당기순이익 증감률",      [pct(M[y]["ni_growth"]) for y in YEARS]),
    ("영업활동현금흐름 증감률", [pct(M[y]["ocf_growth"]) for y in YEARS]),
]
print(f"{'':22}" + "".join(str(y).rjust(16) for y in YEARS))
print("-" * 86)
for label, vals in rows:
    if not label:
        print()
        continue
    print(f"{label:22}" + "".join(v.rjust(16) for v in vals))

print()
print("=" * 86)
print(f"2024년 당기순이익 변화 분해 (총 {total/1e8:,.1f}억원)")
print("=" * 86)
for name, v in bridge:
    print(f"  {name:18}{v/1e8:>10,.1f}억원   기여도 {v/total*100:>7,.1f}%")
print(f"  {'합계':18}{sum(v for _, v in bridge)/1e8:>10,.1f}억원   {'100.0':>14}%")

print()
print("=" * 86)
print("2023년 금융원가의 현금·비현금 구분")
print("=" * 86)
print(f"  현금 유출 (이자비용)        {cash/1e8:>8,.1f}억원   {cash/(cash+nc)*100:>5,.1f}%")
print(f"  비현금 (평가손실·손상차손)   {nc/1e8:>8,.1f}억원   {nc/(cash+nc)*100:>5,.1f}%")
print(f"  합계                        {(cash+nc)/1e8:>8,.1f}억원")
print(f"  [참고] 당기순손실 + 비현금 금융원가 = {(M[2023]['net_income']+nc)/1e8:,.1f}억원")

# ── 수출·내수 분해 (단위: 백만원) ──────────────────────────
SEGS = ("헤어&스칼프", "스킨&바디")
ED = {}
for y in YEARS:
    d = {}
    for ct in ("수출", "내수"):
        for sg in SEGS:
            d[f"{sg}_{ct}"] = sed[y][(sg, ct)]
        # 합계는 부문 합이 아니라 원문 매출실적표의 합계행을 쓴다.
        # 원문이 셀별로 백만원에서 반올림되어 부문 합과 1백만원 어긋나는 해가 있다(2024년 수출).
        d[ct] = sed[y][("합계", ct)]
    d["합계"] = d["수출"] + d["내수"]
    d["수출비중"] = d["수출"] / d["합계"] * 100
    ED[y] = d


def g(y, key):
    """전년 대비 증감률(%). 전년이 없으면 None."""
    if y == YEARS[0]:
        return None
    return ED[y][key] / ED[y - 1][key] * 100 - 100


for y in YEARS:
    for key in ("수출", "내수", "합계") + tuple(f"{s}_{c}" for s in SEGS for c in ("수출", "내수")):
        ED[y][f"{key}_증감률"] = g(y, key)

print()
print("=" * 86)
print("수출·내수 분해 (단위: 백만원)")
print("=" * 86)
print(f"{'':14}" + "".join(str(y).rjust(14) for y in YEARS))
for key in ("수출", "내수", "합계"):
    print(f"{key:14}" + "".join(f"{ED[y][key]:,}".rjust(14) for y in YEARS))
print(f"{'수출비중':14}" + "".join(f"{ED[y]['수출비중']:.1f}%".rjust(14) for y in YEARS))
print()
for key in ("수출", "내수") + tuple(f"{s}_{c}" for s in SEGS for c in ("수출", "내수")):
    vals = "".join((f"{ED[y][key + '_증감률']:+.1f}%" if ED[y][key + "_증감률"] is not None else "—").rjust(14)
                   for y in YEARS)
    print(f"{key:14}" + vals)

# ── 저장 ──────────────────────────────────────────────────
with open(os.path.join(BASE, "metrics.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(M[2023].keys()))
    w.writeheader()
    for y in YEARS:
        w.writerow(M[y])

with open(os.path.join(BASE, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump({
        "metrics": {str(y): M[y] for y in YEARS},
        "bridge_2024": [{"item": n, "value": v, "share": v / total * 100} for n, v in bridge],
        "bridge_2024_total": total,
        "finance_cost_2023": {"cash": cash, "non_cash": nc, "total": cash + nc},
        "export_domestic": {str(y): ED[y] for y in YEARS},
    }, f, ensure_ascii=False, indent=2)

print("\n저장: metrics.csv, metrics.json")
