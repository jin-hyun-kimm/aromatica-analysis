# -*- coding: utf-8 -*-
"""
03_charts.py — 보고서 그림 생성

02_metrics.py가 만든 metrics.json만 읽는다. 그래프의 숫자는 본문·표와
같은 계산 결과에서 나오므로 문서 간 수치가 어긋날 수 없다.

실행:  python3 code/02_metrics.py && python3 code/03_charts.py
출력:  figures/fig1_ratios.png, fig2_bridge.png, fig3_levels.png
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

with open(os.path.join(BASE, "metrics.json"), encoding="utf-8") as f:
    D = json.load(f)
M = D["metrics"]
YEARS = ["2023", "2024", "2025"]

# 검증된 카테고리 팔레트 1~3번 슬롯 (dataviz 기본 테마, light)
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8a85"
GRID, SURFACE = "#e4e4e0", "#ffffff"

plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "axes.unicode_minus": False,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
})


def frame(ax, ylab):
    # 캡션은 보고서 본문에 텍스트로 넣는다(PDF 텍스트 레이어에 남도록).
    # 여기서는 그림 안에 제목을 그리지 않는다.
    ax.set_ylabel(ylab, fontsize=9, color=MUTED, rotation=0,
                  ha="right", va="bottom", labelpad=2)
    ax.yaxis.set_label_coords(-0.012, 1.02)
    ax.grid(axis="y", color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9.5, length=0)


# ══ 그림 1 — 비율 지표 (단위가 % 하나뿐이므로 축이 하나다) ══
om = [M[y]["operating_margin"] for y in YEARS]
nm = [M[y]["net_margin"] for y in YEARS]
fr = [M[y]["finance_cost_ratio"] for y in YEARS]

fig, ax = plt.subplots(figsize=(6.6, 2.75), dpi=200)
ax.axhline(0, color=INK2, lw=0.9, zorder=2)
series = [("영업이익률", om, S1, "o"), ("당기순이익률", nm, S2, "s"),
          ("금융원가율", fr, S3, "^")]
for name, vals, col, mk in series:
    ax.plot(YEARS, vals, color=col, lw=2, marker=mk, ms=8,
            mec=SURFACE, mew=2, label=name, zorder=4)

# 직접 라벨은 양 끝점에만 둔다 (모든 점에 숫자를 붙이지 않는다).
# 중간 연도의 정확한 값은 본문 표 3에서 제공한다.
last = len(YEARS) - 1
for vals, dy_first, dy_last in ((om, 13, 13), (nm, -21, -21), (fr, 13, -19)):
    for i, dy in ((0, dy_first), (last, dy_last)):
        ax.annotate(f"{vals[i]:.1f}%", (i, vals[i]), textcoords="offset points",
                    xytext=(0, dy), ha="center", fontsize=8.6, color=INK2)

ax.set_ylim(-19, 26)
frame(ax, "%")
ax.legend(frameon=False, fontsize=9, loc="upper right", ncol=3,
          handlelength=1.6, columnspacing=1.4)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig1_ratios.png"), bbox_inches="tight")
plt.close()

# ══ 그림 3 — 금액 지표 (단위가 억원 하나뿐이므로 축이 하나다) ══
op = [M[y]["operating_income"] / 1e8 for y in YEARS]
ni = [M[y]["net_income"] / 1e8 for y in YEARS]
oc = [M[y]["ocf"] / 1e8 for y in YEARS]

fig, ax = plt.subplots(figsize=(6.6, 2.85), dpi=200)
x = np.arange(3)
w = 0.26
groups = [("영업이익", op, S1, -w), ("당기순이익", ni, S2, 0.0),
          ("영업활동현금흐름", oc, S3, w)]
for name, vals, col, off in groups:
    bars = ax.bar(x + off, vals, w * 0.92, color=col, label=name, zorder=3)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:,.1f}", (b.get_x() + b.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 4 if v >= 0 else -13),
                    ha="center", fontsize=8.4, color=INK2)

ax.axhline(0, color=INK, lw=1.0, zorder=5)
ax.set_xticks(x)
ax.set_xticklabels(YEARS)
ax.set_ylim(-74, 112)
frame(ax, "억원")
ax.legend(frameon=False, fontsize=9, loc="upper left", ncol=3,
          handlelength=1.4, columnspacing=1.4)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig3_levels.png"), bbox_inches="tight")
plt.close()

# ══ 그림 2 — 2024년 당기순이익 변화 분해 (폭포) ══
start = M["2023"]["net_income"] / 1e8
end = M["2024"]["net_income"] / 1e8
steps = [(b["item"], b["value"] / 1e8, b["share"]) for b in D["bridge_2024"]]

labels = ["2023년\n당기순이익"] + [s[0].replace(" ", "\n") for s in steps] + ["2024년\n당기순이익"]
fig, ax = plt.subplots(figsize=(7.2, 3.15), dpi=200)

cum = start
pos = 0
ax.bar(pos, start, 0.56, color=MUTED, zorder=3)
ax.annotate(f"{start:,.1f}", (pos, 0), textcoords="offset points",
            xytext=(0, 6), ha="center", fontsize=8.6, color=INK2, fontweight="bold")

for name, val, share in steps:
    pos += 1
    bottom = cum if val >= 0 else cum + val
    col = S1 if val >= 0 else S2
    ax.bar(pos, abs(val), 0.56, bottom=bottom, color=col, zorder=3)
    top = max(cum, cum + val)
    ax.annotate(f"{val:+,.1f}\n({share:,.1f}%)", (pos, top),
                textcoords="offset points", xytext=(0, 5), ha="center",
                fontsize=8.2, color=INK2)
    ax.plot([pos - 0.28, pos + 0.28], [cum + val, cum + val],
            color=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=4)
    cum += val

pos += 1
ax.bar(pos, end, 0.56, color=MUTED, zorder=3)
ax.annotate(f"{end:,.1f}", (pos, end), textcoords="offset points",
            xytext=(0, 5), ha="center", fontsize=8.6, color=INK2, fontweight="bold")

ax.axhline(0, color=INK, lw=1.0, zorder=5)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=8.2)
ax.set_ylim(-74, 78)
frame(ax, "억원")
# 증가/감소 식별을 색 하나에만 맡기지 않도록 범례를 둔다
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor=S1, label="이익 증가 요인"),
                   Patch(facecolor=S2, label="이익 감소 요인"),
                   Patch(facecolor=MUTED, label="기말 당기순이익")],
          frameon=False, fontsize=8.8, loc="upper left", ncol=1,
          handlelength=1.3, columnspacing=1.2)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig2_bridge.png"), bbox_inches="tight")
plt.close()

print("생성 완료:")
for n in ("fig1_ratios.png", "fig2_bridge.png", "fig3_levels.png"):
    p = os.path.join(FIG, n)
    print(f"  figures/{n}  ({os.path.getsize(p):,} bytes)")
