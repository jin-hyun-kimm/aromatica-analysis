# -*- coding: utf-8 -*-
"""
01_verify.py — 핵심 수치 검증

DART 원문에서 수집한 수치가 내부적으로 일관되는지 재계산으로 확인한다.
외부 자료와의 대조는 사용하지 않으며, 모든 검증은 원문 수치 간 관계식으로만 수행한다.

실행:  python3 code/01_verify.py
출력:  검증 결과 표 (통과/실패) + verification_log.csv
"""
import csv, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(row, key):
    return int(row[key])


fin = {int(r["year"]): r for r in load("financials_annual.csv")}
bal = {int(r["year"]): r for r in load("balance_annual.csv")}
fcd = load("finance_cost_detail.csv")
rmx = load("revenue_mix_note.csv")
cmp23 = {r["item"]: r for r in load("basis_2023_comparison.csv")}
qtr = {r["period"]: r for r in load("quarterly_2026.csv")}
segr = {}
for _r in load("segment_revenue.csv"):
    segr.setdefault(int(_r["year"]), {})[_r["segment"]] = int(_r["revenue_million_krw"])
sed = {}
for _r in load("segment_export_domestic.csv"):
    sed.setdefault(int(_r["year"]), {})[(_r["segment"], _r["channel_type"])] = int(_r["revenue_million_krw"])
chan = load("channel_revenue_2025.csv")

checks = []


def check(no, target, formula, lhs, rhs, tol=0, note="", where="", kind="관계식 재계산"):
    """tol: 허용 오차(원). 단위가 천원·백만원인 주석과 대조할 때만 그 단위만큼 허용한다."""
    diff = lhs - rhs
    ok = abs(diff) <= tol
    checks.append({
        "no": no, "kind": kind, "target": target, "source_location": where,
        "formula": formula, "computed": lhs, "reported": rhs, "diff": diff,
        "tolerance": tol, "result": "통과" if ok else "불일치", "note": note,
    })
    return ok


# 공시서류별 원문 위치 (sources.csv와 동일)
LOC = {
    "pl": "2025 사업보고서(20260320001362) III-4-2 포괄손익계산서",
    "bs": "2025 사업보고서(20260320001362) III-4-1 재무상태표",
    "seg": "2025 사업보고서(20260320001362) II-2 주요 제품 및 서비스",
    "fc": "2024 감사보고서(20250331002452) 주석 - 금융원가",
    "rev": "2024 감사보고서(20250331002452) 주석 - 수익(매출) 구성",
    "n19": "2024 감사보고서(20250331002452) 주석 19.1",
    "n10": "2024 감사보고서(20250331002452) 주석 10.1",
    "n53": "2024 감사보고서(20250331002452) 주석 5.3(2)",
    "n36": "2024 감사보고서(20250331002452) 주석 36.3 / 36.4",
    "k23": "2023 감사보고서(20240401001486) (첨부) 재무제표",
    "h26": "2026 반기보고서(20260818000129) III-2-2 연결 포괄손익계산서",
    "sed": "2025 사업보고서(20260320001362) II-4 매출 및 수주상황 - 가. 매출실적",
    "chn": "2025 사업보고서(20260320001362) II-4 매출 및 수주상황 - 나. 판매경로 및 판매방법",
}


# ── 1. 손익계산서 내부 정합성 ─────────────────────────────
for y in (2023, 2024, 2025):
    r = fin[y]
    check(f"1-{y}a", f"{y} 매출총이익",
          "매출액 - 매출원가",
          num(r, "revenue") - num(r, "cogs"), num(r, "gross_profit"), where=LOC["pl"])
    check(f"1-{y}b", f"{y} 영업이익",
          "매출총이익 - 판매비와관리비",
          num(r, "gross_profit") - num(r, "sga"), num(r, "operating_income"), where=LOC["pl"])
    check(f"1-{y}c", f"{y} 법인세비용차감전순이익",
          "영업이익 + 기타수익 - 기타비용 + 금융수익 - 금융원가",
          (num(r, "operating_income") + num(r, "other_income") - num(r, "other_expense")
           + num(r, "finance_income") - num(r, "finance_cost")),
          num(r, "pretax_income"), where=LOC["pl"])
    check(f"1-{y}d", f"{y} 당기순이익",
          "법인세비용차감전순이익 - 법인세비용",
          num(r, "pretax_income") - num(r, "income_tax"), num(r, "net_income"), where=LOC["pl"])

# ── 2. 재무상태표 항등식 ──────────────────────────────────
for y in (2023, 2024, 2025):
    r = bal[y]
    check(f"2-{y}", f"{y} 재무상태표 항등식",
          "부채총계 + 자본총계 = 자산총계",
          num(r, "total_liabilities") + num(r, "total_equity"),
          num(r, "total_assets"), where=LOC["bs"])

# ── 3. 금융원가 세부 내역 합계 (천원 단위 주석 대조) ──────
for y in (2023, 2024):
    s = sum(int(r["value_krw"]) for r in fcd if int(r["year"]) == y)
    check(f"3-{y}", f"{y} 금융원가",
          "주석 내역 합계 = 포괄손익계산서 금융원가",
          s, num(fin[y], "finance_cost"), tol=999, where=LOC["fc"],
          note="주석 단위가 천원이므로 1,000원 미만 오차 허용")

# ── 4. 매출 구성 주석 합계 (천원 단위 주석 대조) ──────────
for y in (2023, 2024):
    s = sum(int(r["value_krw"]) for r in rmx if int(r["year"]) == y)
    check(f"4-{y}", f"{y} 매출액",
          "주석 매출 구성 합계 = 포괄손익계산서 매출액",
          s, num(fin[y], "revenue"), tol=999, where=LOC["rev"],
          note="주석 단위가 천원이므로 1,000원 미만 오차 허용")

# ── 4b. 사업부문별 매출 합계 = 매출액 (백만원 단위 공시) ──
seg = load("segment_revenue.csv")
for y in (2023, 2024, 2025):
    s_mn = sum(int(r["revenue_million_krw"]) for r in seg if int(r["year"]) == y)
    check(f"4b-{y}", f"{y} 사업부문 매출 합계",
          "헤어&스칼프 + 스킨&바디 = 매출액",
          s_mn * 1_000_000, num(fin[y], "revenue"), tol=999_999, where=LOC["seg"],
          note="사업부문 표 단위가 백만원이므로 100만원 미만 오차 허용")

# ── 5. 2023년 과거회계기준 손익 정합성 ────────────────────
check("5-1", "2023 영업이익 (과거회계기준)",
      "매출총이익 - 판매비와관리비",
      int(cmp23["gross_profit"]["kgaap_2023"]) - int(cmp23["sga"]["kgaap_2023"]),
      int(cmp23["operating_income"]["kgaap_2023"]), where=LOC["k23"])
check("5-2", "2023 당기순이익 (과거회계기준)",
      "법인세차감전순이익 - 법인세비용",
      int(cmp23["pretax_income"]["kgaap_2023"]) - int(cmp23["income_tax"]["kgaap_2023"]),
      int(cmp23["net_income"]["kgaap_2023"]), where=LOC["k23"])
check("5-3", "2023 재무상태표 항등식 (과거회계기준)",
      "부채총계 + 자본총계 = 자산총계",
      int(cmp23["total_liabilities"]["kgaap_2023"]) + int(cmp23["total_equity"]["kgaap_2023"]),
      int(cmp23["total_assets"]["kgaap_2023"]), where=LOC["k23"])

# ── 6. 2023년 두 기준의 K-IFRS 열이 본 데이터셋과 동일한지 ─
for item, key in (("revenue", "revenue"), ("operating_income", "operating_income"),
                  ("net_income", "net_income")):
    check(f"6-{item}", f"2023 {item} (K-IFRS 열 일치)",
          "basis_2023_comparison.kifrs_2023 = financials_annual(2023)",
          int(cmp23[item]["kifrs_2023"]), num(fin[2023], key), where=LOC["pl"],
          kind="전사 일치 확인")

# ── 7. 2026년 분기 수치 도출과 내부 정합성 ─────────────────
# 2026Q1 행은 derived=yes, 즉 '반기 누적 - 2분기'로 만들어 저장한 값이다.
# 따라서 아래 7-* 7건과 7g-2026Q1 1건은 원문 간 교차검증이 아니라 도출 과정의
# 재현 기록이다. 실패할 수 없는 항목이므로 kind를 달리하여 검증 건수와 분리한다.
DERIVED = "도출값 재현"
for key in ("revenue", "cogs", "gross_profit", "operating_income",
            "finance_income", "finance_cost", "net_income"):
    check(f"7-{key}", f"2026 1분기 {key}",
          "반기 누적 - 2분기 3개월 (도출식 재현)",
          int(qtr["2026H1"][key]) - int(qtr["2026Q2"][key]),
          int(qtr["2026Q1"][key]), where=LOC["h26"], kind=DERIVED,
          note="2026Q1은 이 식으로 생성한 값이므로 항상 일치한다. 도출 과정의 기록용")

for p in ("2025H1", "2026Q1", "2026Q2", "2026H1"):
    _d = (p == "2026Q1")
    check(f"7g-{p}", f"{p} 매출총이익",
          "매출액 - 매출원가",
          int(qtr[p]["revenue"]) - int(qtr[p]["cogs"]),
          int(qtr[p]["gross_profit"]), where=LOC["h26"],
          kind=DERIVED if _d else "관계식 재계산",
          note="2026Q1의 세 항목은 모두 도출값이므로 항등식이 자동으로 성립한다" if _d else "")

# ── 8. 주석 간 교차 검증 (잔액·변동·전환 조정) ──────────
bd = {(r["period"], r["item"]): int(r["value_krw"]) for r in load("balances_detail.csv")}
dr = {(int(r["year"]), r["item"]): int(r["value_krw"]) for r in load("derivative_rollforward.csv")}
tr = {r["item"]: int(r["net_income_adj_krw"]) for r in load("transition_2023.csv")}

check("8-1", "2023년 말 파생금융부채 잔액",
      "기초 + 당기손익인식액 = 기말 (주석 5.3 변동표 ↔ 주석 19.1 잔액)",
      dr[(2023, "기초금액")] + dr[(2023, "당기손익인식액")],
      bd[("2023-12-31", "파생상품부채")], where=LOC["n53"] + " / " + LOC["n19"])

check("8-2", "2024년 말 파생금융부채 잔액",
      "기초 + 전환 = 기말 (2024년 중 전액 자본 전환)",
      dr[(2024, "기초금액")] + dr[(2024, "전환")],
      bd[("2024-12-31", "파생상품부채")], where=LOC["n53"] + " / " + LOC["n19"])

check("8-3", "2023년 손상차손",
      "손실충당금 증가분 = 금융원가 내 손상차손",
      bd[("2023-12-31", "상각후원가측정금융자산_손실충당금")]
      - bd[("2023-01-01", "상각후원가측정금융자산_손실충당금")],
      next(int(r["value_krw"]) for r in fcd
           if int(r["year"]) == 2023 and r["item"] == "손상차손"),
      where=LOC["n10"] + " / " + LOC["fc"])

check("8-4", "2023년 말 상환전환우선주 관련 부채 합계",
      "파생상품부채 + 상환전환우선주부채 = 주석 36.3 상환전환우선주 조정액",
      bd[("2023-12-31", "파생상품부채")] + bd[("2023-12-31", "상환전환우선주부채")],
      29894564000, where=LOC["n19"] + " / " + LOC["n36"],
      note="주석 36.3의 2023년 말 상환전환우선주 조정액 29,894,564천원과 대조")

check("8-5", "2023년 K-IFRS 당기순손실",
      "과거회계기준 당기순이익 + 주석 36.4 조정액 합계",
      sum(tr.values()), int(cmp23["net_income"]["kifrs_2023"]), tol=999,
      where=LOC["n36"], note="주석 단위가 천원이므로 1,000원 미만 오차 허용")

# ── 9. 수출·내수 및 채널별 매출 정합성 ────────────────────
# 원문 단위가 백만원이므로 백만원 미만 오차를 허용한다.
for y in (2023, 2024, 2025):
    for sg in ("헤어&스칼프", "스킨&바디"):
        check(f"9-1{y}{'h' if sg.startswith('헤어') else 's'}", f"{y} {sg} 부문 소계",
              "수출 + 내수", sed[y][(sg, "수출")] + sed[y][(sg, "내수")], segr[y][sg], tol=1,
              where=LOC["sed"],
              note="단위 백만원. II-2 주요 제품 및 서비스의 부문 매출과 대조. "
                   "원문이 셀별로 백만원 단위에서 반올림되어 1백만원 차이가 날 수 있어 그만큼 허용")

for y in (2023, 2024, 2025):
    _tot = sed[y][("합계", "수출")] + sed[y][("합계", "내수")]
    check(f"9-2{y}", f"{y} 매출액 (수출·내수 합계행)",
          "원문 합계행의 수출 + 내수", _tot * 10 ** 6, int(fin[y]["revenue"]), tol=10 ** 6,
          where=LOC["sed"], note="원문 단위가 백만원이므로 백만원 미만 오차 허용")

for y in (2023, 2024, 2025):
    for ct in ("수출", "내수"):
        check(f"9-6{y}{'e' if ct == '수출' else 'd'}", f"{y} {ct} 합계행",
              "두 부문의 수출(또는 내수) 합", sum(sed[y][(sg, ct)] for sg in ("헤어&스칼프", "스킨&바디")),
              sed[y][("합계", ct)], tol=1, where=LOC["sed"],
              note="원문이 셀별로 백만원 단위에서 반올림되어 1백만원 차이가 날 수 있어 그만큼 허용")

_ch_tot = sum(int(r["revenue_million_krw"]) for r in chan)
check("9-3", "2025 매출액 (채널별 합계)", "16개 판매채널 매출 합계",
      _ch_tot * 10 ** 6, int(fin[2025]["revenue"]), tol=10 ** 6,
      where=LOC["chn"], note="원문 단위가 백만원이므로 백만원 미만 오차 허용")

_glob = sum(int(r["revenue_million_krw"]) for r in chan if r["region"] != "한국")
check("9-4", "2025 수출액 (채널별 집계)", "한국 외 지역 채널 매출 합계",
      _glob, sed[2025][("합계", "수출")],
      where=LOC["chn"], note="판매경로표의 해외 채널 합계 = 매출실적표의 수출 합계행")

_dom = sum(int(r["revenue_million_krw"]) for r in chan if r["region"] == "한국")
check("9-5", "2025 내수액 (채널별 집계)", "한국 지역 채널 매출 합계",
      _dom, sed[2025][("합계", "내수")],
      where=LOC["chn"], note="판매경로표의 국내 채널 합계 = 매출실적표의 내수 합계행")

# ── 출력 ──────────────────────────────────────────────────
W = (8, 32, 44, 17, 17, 11, 8)
hdr = ("번호", "검증 대상", "계산식", "계산값", "보고값", "차이", "결과")
line = "-" * (sum(W) + len(W) * 2)
print(line)
print("  ".join(h.ljust(w) for h, w in zip(hdr, W)))
print(line)
for c in checks:
    print("  ".join([
        str(c["no"]).ljust(W[0]),
        c["target"][:W[1]].ljust(W[1]),
        c["formula"][:W[2]].ljust(W[2]),
        f"{c['computed']:,}".rjust(W[3]),
        f"{c['reported']:,}".rjust(W[4]),
        f"{c['diff']:,}".rjust(W[5]),
        c["result"].ljust(W[6]),
    ]))
print(line)
passed = sum(1 for c in checks if c["result"] == "통과")
kinds = {}
for c in checks:
    kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
print(f"총 {len(checks)}건 중 통과 {passed}건, 불일치 {len(checks) - passed}건")
print("  유형별: " + ", ".join(f"{k} {v}건" for k, v in kinds.items()))
_d = kinds.get("도출값 재현", 0)
print(f"  이 중 {_d}건은 저장된 도출값이 도출식과 일치하는지 확인한 기록이며, "
      f"원문 수치 간 교차검증은 {len(checks) - _d}건이다.")

out = os.path.join(BASE, "verification_log.csv")
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(checks[0].keys()))
    w.writeheader()
    w.writerows(checks)
print(f"검증 기록 저장: {os.path.relpath(out, BASE)}")

sys.exit(0 if passed == len(checks) else 1)
