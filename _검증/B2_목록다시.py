# -*- coding: utf-8 -*-
"""B2: 예전 '쓰지 말 것' 목록 3개를 새 데이터(data\\통합_전체_202611)로 다시 만든다. 값은 고치지 않는다(목록만).
규칙은 data\\DataGuide_추가_202610 의 예전 스크립트를 그대로 옮김(문턱값·조건·순서 같음):
  1. make_merge_unadjusted_list.py → 수정주가_병합미반영.csv
  2. make_tr_anomaly_list.py + make_tr_flat_list.py → 수정주가TR_이상칸.csv
  3. make_code_reuse_list.py → 코드재사용.csv
같은 규칙인지 확인: 같은 함수를 예전 데이터(DataGuide_갱신_202609\\parquet)에 먼저 돌려 예전 csv와 대조한다(파일은 안 씀).
새 데이터에 없는 항목: DataGuide 1개월대비수익률(병합 조건 ③), 주재무 PIT 회계연도(코드재사용 근거 글의 한 부분).
  → 그 조건·글만 빼고 돌리고 '조건 못 씀'이라고 적는다. 다른 값으로 대신 채우지 않는다.
월말: 예전 resample('BME') 대신 '그 달 마지막 영업일' 라벨로 묶음. 2000년 뒤(토요일 거래 없음)는 같고, 예전 데이터로 대조해 확인한다.
  새 데이터 1998년까지는 토요일 거래일이 있어 resample('BME')를 쓰면 월말 토요일이 다음 달로 넘어간다."""
import gc
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트\공통")
import 데이터읽기 as 읽기

ROOT = 읽기.DATA.parent
OLDDIR = ROOT / "DataGuide_추가_202610"
GSP = ROOT / "DataGuide_갱신_202609" / "parquet"
OUT = Path(__file__).parent / "새목록"
OUT.mkdir(exist_ok=True)
END = pd.Timestamp("2026-09-30")
OLDF = {"종가": "종가.parquet", "수정주가": "수정주가.parquet", "TR": "수정주가(현금배당포함).parquet", "상장주식수": "상장주식수.parquet",
        "시가총액": "시가총액.parquet", "업종": "거래소 업종(세부분류).parquet", "정지": "거래정지구분.parquet", "거래량": "거래량.parquet",
        "1개월": "1개월대비수익률.parquet"}
NEWF = {"종가": 읽기.종가, "수정주가": 읽기.수정주가, "TR": 읽기.TR, "상장주식수": 읽기.주식수, "시가총액": 읽기.시총, "업종": 읽기.업종,
        "정지": 읽기.정지구분, "거래량": 읽기.거래량, "시장구분": 읽기.시장구분}  # 1개월대비수익률 없음


def 있는열(f, cols):
    h = set(pq.read_schema(f).names)
    return [c for c in cols if c in h]


def rd(src, key, cols=None):
    if src == "예전":
        f = GSP / OLDF[key]
        return pd.read_parquet(f, columns=None if cols is None else 있는열(f, cols))
    if key not in NEWF:
        return None
    f = 읽기.파일(NEWF[key])
    t = pq.read_table(f, columns=None if cols is None else ["날짜"] + 있는열(f, cols))
    return t.to_pandas(strings_to_categorical=True).rename_axis(None).loc[:읽기.공통끝()]


def 이름표(src):
    if src == "예전":
        return pd.read_csv(ROOT / "6번전략_parquet_202610" / "mapping_table.csv", encoding="cp949").set_index("코드")["코드명"]
    return 읽기.종목정보()["코드명"]


def 월(d):
    """그 달 마지막 영업일 라벨로 묶어 마지막 값(빈칸 아닌 것). resample('BME').last()와 2000년 뒤 같음."""
    lab = pd.DatetimeIndex([pd.offsets.BMonthEnd().rollback(x) for x in d.index.to_period("M").to_timestamp(how="end").normalize().unique()])
    key = d.index.to_period("M")
    g = d.groupby(key).last()
    g.index = lab
    return g


def nn(x):
    return x if pd.notna(x) else None


# ---------------- 3. 코드 재사용 (TR 가격고정 판정이 이걸 씀 → 먼저) ----------------
def 코드재사용(src):
    names = 이름표(src)
    P, C, SH, SEC, HALT = rd(src, "수정주가"), rd(src, "종가"), rd(src, "상장주식수"), rd(src, "업종"), rd(src, "정지")
    FY = pd.read_parquet(OLDDIR / "parquet" / "PIT_일별_M000903001_자본총계_천원_회계연도.parquet") if src == "예전" else None

    def at(df, c, d):
        return df.at[d, c] if c in df.columns and d in df.index else np.nan

    rows = []
    for c in P.columns:
        v = np.where(P[c].notna().to_numpy())[0]
        if len(v) < 2:
            continue
        gaps = np.diff(v) - 1
        for k in np.where(gaps > 250)[0]:
            a, b = P.index[v[k]], P.index[v[k + 1]]
            pa, pb = P.at[a, c], P.at[b, c]
            sa, sb = at(SH, c, a), at(SH, c, b)
            ha = HALT.loc[(HALT.index > a) & (HALT.index < b), c].astype(object).value_counts(dropna=False).to_dict() if c in HALT.columns else {}
            cgap = int(C.loc[(C.index > a) & (C.index < b), c].notna().sum()) if c in C.columns else 0
            if src == "예전":
                assert cgap == 0, (c, "종가는 공백 안에 값이 있음")
            cg = "종가도 공백" if cgap == 0 else f"종가는 공백 안에 값 {cgap}칸"
            if FY is not None:
                fa, fb = at(FY, c, a), at(FY, c, b)
                fy = f"주재무 PIT 회계연도 {fa}→{fb}" + ("(새 회사 첫날에 이전 회사 재무가 보임)" if pd.notna(fa) and pd.notna(fb) and fb <= fa + 1 and (b - a).days > 730 else "")
            else:
                fy = "주재무 PIT 회계연도 확인 못 함(새 데이터에 없음)"
            ev = (f"수정주가 {gaps[k]}거래일 공백({cg}), 건너뛴 수익률 {pb / pa - 1:+.1%}; "
                  f"상장주식수 {sa:,.0f}→{sb:,.0f}; 업종 {nn(at(SEC, c, a))}→{nn(at(SEC, c, b))}; 종가 {at(C, c, a):,.0f}→{at(C, c, b):,.0f}; "
                  f"공백 중 거래정지구분 {ha}; " + fy)
            rows.append(dict(코드=c, 이름=names.get(c), 이전회사_마지막날짜=a.date(), 새회사_첫날짜=b.date(), 공백거래일=int(gaps[k]), 근거=ev))
    out = pd.DataFrame(rows).sort_values("코드").reset_index(drop=True)
    if src == "예전":
        assert len(out) == 16 and out["코드"].is_unique, out
    return out


# ---------------- 1. 수정주가 병합 미반영 ----------------
def 병합(src, use_gap=True):
    names = 이름표(src)
    cl = rd(src, "종가").loc[:END]
    cols = cl.columns
    ad = rd(src, "수정주가").loc[:END].reindex(columns=cols)
    r1 = rd(src, "1개월")
    if r1 is None:
        use_gap = False  # 조건 ③ 못 씀
    else:
        r1 = r1.loc[:END].reindex(columns=cols) / 100
    sh, cap = rd(src, "상장주식수").loc[:END].reindex(columns=cols), rd(src, "시가총액").loc[:END].reindex(columns=cols)
    adm, clm, shm, capm = 월(ad), 월(cl), 월(sh), 월(cap)
    r1m = 월(r1) if use_gap else None
    a1 = adm.pct_change(fill_method=None)
    c1 = clm.pct_change(fill_method=None)
    shr = shm / shm.shift(1)
    capr = capm / capm.shift(1) - 1
    fac = adm / clm
    facchg = (fac / fac.shift(1) - 1).abs()
    m = ((shr > 1.5) | (shr < 1 / 1.5)) & (facchg < 0.005)
    if use_gap:
        m &= (a1 - r1m).abs() > 1.0
    s = m.stack()
    hits = s[s].index
    sec = rd(src, "업종", cols=sorted({c for _, c in hits}))
    rows = []
    for d, c in hits:
        x = 월(sec[[c]].astype(object))[c].ffill(limit=1).get(d) if c in sec.columns else None
        rows.append(dict(코드=c, 이름=names.get(c), 날짜=d.date(), 시장=str(x)[:3] if pd.notna(x) else "업종없음", 상장주식수_변화배율=round(shr.at[d, c], 4),
                         수정주가_월수익률=round(a1.at[d, c], 4), DataGuide_1개월대비수익률=round(r1m.at[d, c], 4) if use_gap else np.nan,
                         종가_월수익률=round(c1.at[d, c], 4), 시가총액_월변화=round(capr.at[d, c], 4),
                         수정계수_전월=round(fac.shift(1).at[d, c], 5), 수정계수=round(fac.at[d, c], 5)))
    full = pd.DataFrame(rows, columns=["코드", "이름", "날짜", "시장", "상장주식수_변화배율", "수정주가_월수익률", "DataGuide_1개월대비수익률", "종가_월수익률",
                                       "시가총액_월변화", "수정계수_전월", "수정계수"]).sort_values(["날짜", "코드"])
    if use_gap:
        dg = lambda r: f"DataGuide 1개월대비 {r.DataGuide_1개월대비수익률:+.1%} → 수정주가 수익률 {r.수정주가_월수익률:+.1%}는 병합·감자 미반영. 재감사 1번 r15_scan"
    else:
        dg = lambda r: (f"DataGuide 1개월대비 조건(③ 괴리>100%p) 못 씀(새 데이터에 1개월대비수익률 없음) → 수정주가 수익률 {r.수정주가_월수익률:+.1%}. "
                        f"시장 {r.시장}. B2_목록다시(조건 ①②만)")
    out = pd.DataFrame({
        "코드": full["코드"], "날짜(월말)": full["날짜"], "상장주식수 변화배율": full["상장주식수_변화배율"], "수정주가 월수익률": full["수정주가_월수익률"],
        "DataGuide 1개월대비수익률": full["DataGuide_1개월대비수익률"],
        "근거": [f"{r.이름}; 상장주식수 ×{r.상장주식수_변화배율:g}인데 수정계수(수정주가/종가) {r.수정계수_전월:g}→{r.수정계수:g} 그대로; "
               f"종가 월수익률 {r.종가_월수익률:+.1%}, 시가총액 월변화 {r.시가총액_월변화:+.1%}, " + dg(r) for r in full.itertuples()]})
    return out, full


# ---------------- 2. TR 이상칸 (배당효과 기준 + TR변동_가격고정) ----------------
def TR이상(src, reuse):
    names = 이름표(src)
    T = rd(src, "TR")
    T = T.loc[:, T.notna().any()]  # ponytail: 값 없는 열은 결과에 영향 없음, 메모리만 줄임
    ix, cx = T.index, T.columns
    P = rd(src, "수정주가").reindex(index=ix, columns=cx)
    C = rd(src, "종가").reindex(index=ix, columns=cx)
    S = rd(src, "상장주식수").reindex(index=ix, columns=cx)
    V = T.notna() & P.notna()
    Tv, Pv, Cv = T.where(V), P.where(V), C.where(V)
    Tp, Pp, Cp = Tv.ffill().shift(1), Pv.ffill().shift(1), Cv.ffill().shift(1)
    Dp = pd.DataFrame(np.repeat(ix.values[:, None], len(cx), axis=1), index=ix, columns=cx).where(V).ffill().shift(1)
    Sv = S.ffill()
    shr = Sv.where(V) / Sv.where(V).ffill().shift(1)
    del S, Sv
    rT, rP = Tv / Tp - 1, Pv / Pp - 1
    J = (1 + rT) / (1 + rP) - 1
    tol = 0.5 / Tv + 0.5 / Tp + 0.5 / Pv + 0.5 / Pp
    fch = (Pv / Cv) / (Pp / Cp) - 1
    del Cp
    gc.collect()
    neg = (J < -0.02) & (J < -tol)
    pos = J > 0.20
    flag = (neg | pos).to_numpy()
    r_, c_ = np.nonzero(flag)
    take = lambda F, r, c: F.to_numpy()[r, c]
    cols = {"앞_날짜": Dp, "수정주가_앞": Pp, "수정주가": Pv, "TR_앞": Tp, "TR": Tv, "가격수익률": rP, "TR수익률": rT,
            "배당효과": J, "반올림허용": tol, "수정계수변화": fch, "상장주식수배율": shr}

    def rows_at(r, c):
        o = pd.DataFrame({"날짜": ix[r], "코드": cx[c]})
        for k, F in cols.items():
            o[k] = take(F, r, c)
        o.insert(1, "이름", o["코드"].map(names))
        o["앞_날짜"] = pd.to_datetime(o["앞_날짜"])
        return o

    out = rows_at(r_, c_)
    fc = out["수정계수변화"].abs() > 0.005
    dbl = fc & (((1 + out["배당효과"]) / (1 + out["수정계수변화"]) - 1).abs().lt(0.05) |
                ((1 + out["배당효과"]) * (1 + out["수정계수변화"]) - 1).abs().lt(0.05))
    out["분류"] = np.where(out["배당효과"] > 0.20, "큰 양의 배당효과(>20%)", "음의 배당효과(<-2%)")
    out["분류"] = out["분류"] + np.where(dbl, "; 이중수정 의심", np.where(fc, "; 수정계수 변화일", ""))
    out["과제기간_안(≤2026-09-30)"] = out["날짜"] <= END
    old = out.sort_values(["코드", "날짜"]).reset_index(drop=True)  # = 예전 '수정주가TR_이상칸_D38전.csv'

    # ---- make_tr_flat_list.py ----
    H = (rd(src, "정지") == "거래정지").reindex(index=ix, columns=cx, fill_value=False).astype(bool)
    VOL = rd(src, "거래량").reindex(index=ix, columns=cx)
    notrade = H | (VOL.fillna(0) <= 0)
    flat = (rP.abs() < 1e-12) | notrade
    cand = V & Tp.notna() & flat & (J.abs() > tol)
    traded = (V & ~notrade).to_numpy()
    R = (Tv / Pv).to_numpy()
    Vn, Hn, Nn = V.to_numpy(), H.to_numpy(), notrade.to_numpy()
    rr, cc = np.nonzero(cand.to_numpy())
    o = np.lexsort((cc, rr))  # stack() 순서(날짜 → 코드)
    rr, cc = rr[o], cc[o]
    pos_ = {d: i for i, d in enumerate(ix)}
    Jn, Tpn, Ppn, VOLn = J.to_numpy(), Tp.to_numpy(), Pp.to_numpy(), VOL.to_numpy()
    rows = []
    for i, ci in zip(rr, cc):
        c = cx[ci]
        vi = np.flatnonzero(Vn[:, ci])
        k = np.searchsorted(vi, i)
        j_ = float(Jn[i, ci])
        r_prev = float(Tpn[i, ci] / Ppn[i, ci])
        nxt = vi[k + 1:k + 21]
        rev = False
        if len(nxt):
            q = R[nxt, ci] / r_prev - 1
            rev = bool((q < j_ / 2).any()) if j_ > 0 else bool((q > j_ / 2).any())
        after = vi[k + 1:]
        gaps = np.flatnonzero(np.diff(np.r_[i, after]) > 20)
        seg_end = after[gaps[0] - 1] if len(gaps) and gaps[0] > 0 else (i if len(gaps) else (after[-1] if len(after) else i))
        for _, x in reuse[reuse["코드"] == c].iterrows():
            e = pos_.get(pd.Timestamp(x.iloc[2]))
            if e is not None and i <= e < seg_end:
                seg_end = e
        tr_after = traded[i + 1:seg_end + 1, ci].any()
        at_data_end = seg_end == vi[-1] and vi[-1] == len(ix) - 1
        nt = bool(Nn[i, ci])
        if j_ < 0:
            judge = "깨짐-음수"
        elif rev:
            judge = "깨짐-반전"
        elif nt and not tr_after and not at_data_end:
            judge = "깨짐-거래없이끝남"
        elif nt and not tr_after and at_data_end:
            judge = "보류-끝까지정지"
        else:
            judge = "배당으로 봄(정지 중)" if bool(Hn[i, ci]) else ("배당으로 봄(거래량 0)" if nt else "배당으로 봄")
        rows.append({"날짜": ix[i], "코드": c, "판정": judge, "배당효과": j_, "거래정지": bool(Hn[i, ci]), "거래량": VOLn[i, ci],
                     "구간끝": ix[seg_end], "그뒤거래": bool(tr_after), "반전": rev, "_r": i, "_c": ci})
    A = pd.DataFrame(rows)
    key_old = set(zip(old["코드"], old["날짜"]))
    A["기존 목록"] = [(c, d) in key_old for c, d in zip(A["코드"], A["날짜"])]
    B = A[A["판정"].str.startswith("깨짐") & ~A["기존 목록"]]
    F_ = Pv / C.where(V)
    Fp_ = F_.ffill().shift(1)
    cols["수정계수변화"] = F_ / Fp_ - 1  # make_tr_flat_list.py 정의(앞 날 계수 = 계수의 ffill)
    add = rows_at(B["_r"].to_numpy(), B["_c"].to_numpy())
    add["분류"] = "TR변동_가격고정; " + B["판정"].values
    add["과제기간_안(≤2026-09-30)"] = add["날짜"] <= END
    add["유형"] = "TR변동_가격고정"
    old["유형"] = "배당효과_기준(-2%/+20%)"
    new = pd.concat([old, add[old.columns]], ignore_index=True).sort_values(["코드", "날짜"]).reset_index(drop=True)
    assert not new.duplicated(["코드", "날짜"]).any() and len(new) == len(old) + len(add)
    assert (new["앞_날짜"] < new["날짜"]).all()
    for _, r in add.iterrows():  # 원자료 값 그대로인지
        assert T.at[r["날짜"], r["코드"]] == r["TR"] and T.at[r["앞_날짜"], r["코드"]] == r["TR_앞"]
        assert P.at[r["날짜"], r["코드"]] == r["수정주가"] and P.at[r["앞_날짜"], r["코드"]] == r["수정주가_앞"]
    A = A.drop(columns=["_r", "_c"])
    A.insert(2, "이름", A["코드"].map(names))
    info = dict(기간=f"{ix[0].date()}~{ix[-1].date()}", 크기=T.shape, 하루배당효과칸=int(J.notna().to_numpy().sum()),
                음수=int(neg.to_numpy().sum()), 큰양=int(pos.to_numpy().sum()), 후보=len(A))
    return new, old.drop(columns="유형"), A, info


# ---------------- 대조 도구 ----------------
def csv_back(df, **kw):
    b = io.StringIO()
    df.to_csv(b, index=False, date_format="%Y-%m-%d", **kw)
    b.seek(0)
    return pd.read_csv(b)


def same_table(mine, path):
    """내가 만든 표(csv로 썼다 읽은 것)와 예전 csv를 칸마다 대조. 숫자는 상대 1e-12, 글은 그대로."""
    a, b = csv_back(mine), pd.read_csv(path, encoding="utf-8-sig")
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return f"다름: 열 {list(a.columns) == list(b.columns)}, 줄 {len(a)} vs {len(b)}"
    bad = []
    for k in a.columns:
        x, y = a[k], b[k]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            ok = np.isclose(x.astype(float), y.astype(float), rtol=1e-12, atol=0, equal_nan=True)
        else:
            ok = (x.astype(str) == y.astype(str)).to_numpy()
        if not ok.all():
            bad.append(f"{k} {int((~ok).sum())}칸")
    return "같음(열·줄 순서·모든 칸)" if not bad else "다름: " + ", ".join(bad)


# ---------------- 차이표 ----------------
PRE = {}  # (src, 항목) → 차이 난 종목들 열만 한 번에 읽은 표


def 준비(codes):
    codes = sorted(codes)
    for src in ("예전", "새"):
        for key in ("수정주가", "종가", "상장주식수", "1개월", "TR", "거래량", "정지", "시장구분"):
            if src == "예전" and key == "시장구분":
                continue
            PRE[(src, key)] = rd(src, key, cols=codes)
        w = PRE[(src, "수정주가")].columns
        pm, km, sm = (월(PRE[(src, k)].loc[:END].reindex(columns=w)) for k in ("수정주가", "종가", "상장주식수"))
        f = pm / km
        PRE[(src, "월")] = dict(배율=sm / sm.shift(1), 계수_전=f.shift(1), 계수=f, 수정주가월=pm.pct_change(fill_method=None))
        if PRE.get((src, "1개월")) is not None:
            PRE[(src, "월")]["DG1개월"] = 월(PRE[(src, "1개월")].loc[:END].reindex(columns=w) / 100)


def 열(src, key, c):
    """한 종목 한 항목 일간(없으면 None)."""
    d = PRE.get((src, key))
    return d[c] if d is not None and c in d.columns else None


def 월값(src, c):
    if 열(src, "수정주가", c) is None:
        return None
    return pd.DataFrame({k: v[c] for k, v in PRE[(src, "월")].items()})


def 하루(src, c, d):
    """그날 TR·수정주가와 '둘 다 있는 직전 날' 값, 배당효과 J, 거래량·정지."""
    t, p = 열(src, "TR", c), 열(src, "수정주가", c)
    if t is None or p is None or d not in t.index:
        return None
    v = t.notna() & p.reindex(t.index).notna()
    pv = v.loc[:d].iloc[:-1]
    if not v.get(d, False) or not pv.any():
        return dict(값="그날 TR·수정주가 둘 다 있지 않음", TR=nn(t.get(d)), P=nn(p.get(d)))
    a = pv[pv].index[-1]
    J = (t[d] / t[a]) / (p[d] / p[a]) - 1
    vol, h = 열(src, "거래량", c), 열(src, "정지", c)
    return dict(앞=a.date(), TR_앞=t[a], TR=t[d], P_앞=p[a], P=p[d], J=round(J, 6),
                거래량=nn(vol.get(d)) if vol is not None else None, 정지=nn(h.get(d)) if h is not None else None)


def 표(df):
    if len(df) == 0:
        return "(없음)\n"
    return "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n" + \
        "".join("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in r) + " |\n" for r in df.itertuples(index=False))


def 차이표(res):
    o, n = res["예전"], res["새"]
    old7 = pd.read_csv(OLDDIR / "수정주가_병합미반영_7칸.csv", encoding="utf-8-sig")
    oldtr = pd.read_csv(OLDDIR / "수정주가TR_이상칸.csv", encoding="utf-8-sig")
    old16 = pd.read_csv(OLDDIR / "코드재사용_16종목.csv", encoding="utf-8-sig")
    준비(set(old7["코드"]) | set(n["m"]["코드"]) | set(oldtr["코드"]) | set(n["tr"]["코드"]) | set(old16["코드"]) | set(n["reuse"]["코드"]))
    L = ["# B2 목록 다시 만들기: 예전 목록 vs 새 데이터 목록\n",
         "만든 스크립트: `_검증/B2_목록다시.py`. 실행 출력: `_검증/B2_목록다시_결과.txt`. 값은 원본 그대로, 목록만 새로.\n",
         "예전 = `data/DataGuide_추가_202610`의 csv(예전 데이터 `DataGuide_갱신_202609/parquet`, 1999-12-28~2026-10-22, 4,129종목). "
         "새 = `data/통합_전체_202611` 일간(1988-01-04~2026-09-30).\n",
         "\n## 같은 규칙인지 확인(새 스크립트를 예전 데이터에 돌림)\n"]
    L += [f"- {k}: {v}\n" for k, v in res["chk"].items()]
    L.append(f"- 예전 데이터에서 병합 조건 ③(DataGuide 1개월대비수익률 괴리>100%p)을 빼면: {len(o['m_no3'])}줄(③ 있으면 {len(o['m'])}줄).\n")
    nm = 이름표("새")

    # ---- 1. 병합 ----
    old = pd.read_csv(OLDDIR / "수정주가_병합미반영_7칸.csv", encoding="utf-8-sig")
    new = n["m"].astype({"날짜(월말)": str})
    ko, kn = set(zip(old["코드"], old["날짜(월말)"])), set(zip(new["코드"], new["날짜(월말)"]))
    k3 = set(zip(o["m_no3"]["코드"], o["m_no3"]["날짜(월말)"].astype(str)))
    L += ["\n## 1. 수정주가_병합미반영\n",
          "**못 쓴 조건: ③ |수정주가 월수익률 − DataGuide 1개월대비수익률| > 100%p.** 새 데이터에 1개월대비수익률이 없다. "
          "새 목록은 ①(상장주식수 배율 >1.5 또는 <1/1.5) ②(수정계수 변화 <0.5%)만으로 만든 것이다. 'DataGuide 1개월대비수익률' 열은 빈칸.\n",
          f"- 예전 {len(ko)}줄, 새 {len(kn)}줄, 둘 다 {len(ko & kn)}, 예전에만 {len(ko - kn)}, 새에만 {len(kn - ko)}\n",
          f"- 참고: 예전 데이터에 ①②만 쓰면 {len(k3)}줄 → 새 목록과 둘 다 {len(k3 & kn)}, 예전(①②)에만 {len(k3 - kn)}, 새에만 {len(kn - k3)}. "
          "(③을 못 쓴 효과와 데이터 차이를 나눠 보려는 숫자)\n"]

    def 같은값(old, new, keys, cols):
        """둘 다 있는 줄의 값 대조(숫자 상대 1e-9)."""
        m = old.astype({k: str for k in keys}).merge(new.astype({k: str for k in keys}), on=keys, suffixes=("_예전", "_새"))
        bad = {}
        for k in cols:
            x, y = m[k + "_예전"], m[k + "_새"]
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                ok = np.isclose(x.astype(float), y.astype(float), rtol=1e-9, equal_nan=True)
            else:
                ok = (x.astype(str) == y.astype(str)).to_numpy()
            if not ok.all():
                bad[k] = m.loc[~ok, keys + [k + "_예전", k + "_새"]].astype(str).values.tolist()
        return f"둘 다 있는 {len(m)}줄 값 대조({', '.join(cols)}): " + ("모두 같음" if not bad else f"다름 {bad}")
    L.append("- " + 같은값(old, new, ["코드", "날짜(월말)"], ["상장주식수 변화배율", "수정주가 월수익률"]) + "\n")
    rows = []
    for c, d in sorted(ko | kn, key=lambda x: (x[1], x[0])):
        if (c, d) in ko and (c, d) in kn:
            continue
        D = pd.Timestamp(d)
        w = {s: 월값(s, c) for s in ("예전", "새")}
        def g(s, k):
            if w[s] is None:
                return "종목없음"
            if k not in w[s].columns:
                return "항목없음"
            return round(float(w[s].at[D, k]), 5) if D in w[s].index and pd.notna(w[s].at[D, k]) else "없음"
        if (c, d) in kn:
            why = ("예전 데이터 기간 밖(2000-01 전)" if D < pd.Timestamp("2000-01-31") else
                   "예전 데이터에 종목 없음" if w["예전"] is None else
                   "예전 데이터도 ①② 걸림, ③에서 빠짐(③ 못 써서 새로 들어옴)" if (c, d) in k3 else "예전 데이터 값과 다름(아래 값)")
        else:
            why = "새 데이터 ①② 안 걸림(아래 값)"
        rows.append(dict(목록=("새에만" if (c, d) in kn else "예전에만"), 코드=c, 이름=nm.get(c), 날짜=d,
                         **{f"{s}_{k}": g(s, k) for s in ("예전", "새") for k in ("배율", "계수_전", "계수", "수정주가월")},
                         예전_DG1개월=g("예전", "DG1개월"), 까닭=why))
    R = pd.DataFrame(rows)
    if len(R):
        L.append("- 까닭별: " + str(R.groupby(["목록", "까닭"]).size().to_dict()) + "\n")
        L.append("- 새에만 줄의 시장(업종 앞 3글자): " + str(n["mtab"]["시장"].value_counts().to_dict()) + "\n\n")
    L.append(표(R))

    # ---- 2. TR ----
    old = pd.read_csv(OLDDIR / "수정주가TR_이상칸.csv", encoding="utf-8-sig")
    new = csv_back(n["tr"])
    key = lambda t: {(c, d): r for c, d, r in zip(t["코드"], t["날짜"], t.to_dict("records"))}
    ko, kn = key(old), key(new)
    L += ["\n## 2. 수정주가TR_이상칸 (유형 2개)\n", "못 쓴 조건: 없음(TR·수정주가·종가·상장주식수·거래량·거래정지구분 모두 새 데이터에 있음).\n"]
    for t in ["배당효과_기준(-2%/+20%)", "TR변동_가격고정"]:
        a = {k for k, r in ko.items() if r["유형"] == t}
        b = {k for k, r in kn.items() if r["유형"] == t}
        L.append(f"- {t}: 예전 {len(a)}, 새 {len(b)}, 둘 다 {len(a & b)}, 예전에만 {len(a - b)}, 새에만 {len(b - a)}\n")
    both = set(ko) & set(kn)
    L.append(f"- 합계: 예전 {len(ko)}줄, 새 {len(kn)}줄, 둘 다 (코드,날짜) {len(both)}, 예전에만 {len(set(ko) - set(kn))}, 새에만 {len(set(kn) - set(ko))}\n")
    L.append("- " + 같은값(old, new, ["코드", "날짜"], ["앞_날짜", "수정주가_앞", "수정주가", "TR_앞", "TR", "배당효과", "수정계수변화", "상장주식수배율", "분류", "유형"]) + "\n")
    chg = [(k, [f for f in ("앞_날짜", "유형", "분류") if str(ko[k][f]) != str(kn[k][f])]) for k in sorted(both)]
    chg = [(k, f) for k, f in chg if f]
    L.append(f"- 둘 다 있는데 앞_날짜·유형·분류가 다른 줄: {len(chg)}" + ("".join(f"\n  - {k}: " + ", ".join(f"{x} {ko[k][x]} → {kn[k][x]}" for x in f) for k in chg)) + "\n")
    vd = {s: {(c, str(pd.Timestamp(d).date())): j for c, d, j in zip(res[s]["A"]["코드"], res[s]["A"]["날짜"], res[s]["A"]["판정"])} for s in ("예전", "새")}
    rows = []
    for k in sorted(set(ko) ^ set(kn), key=lambda x: (x[1], x[0])):
        c, d = k
        D = pd.Timestamp(d)
        side = "새에만" if k in kn else "예전에만"
        r = kn.get(k) or ko.get(k)
        h = {s: 하루(s, c, D) for s in ("예전", "새")}
        oth = "예전" if side == "새에만" else "새"
        ho, hm = h[oth], h["새" if oth == "예전" else "예전"]
        if ho is None:
            why = ("예전 데이터 기간 밖(1999-12-28 전)" if oth == "예전" and D < pd.Timestamp("1999-12-28") else
                   f"{oth} 데이터에 종목 없음" if 열(oth, "TR", c) is None else f"{oth} 데이터에 그 날 없음")
        elif "값" in ho:
            why = f"{oth} 데이터: {ho['값']}"
        else:
            same = hm is not None and "값" not in hm and all(ho[x] == hm[x] for x in ("앞", "TR_앞", "TR", "P_앞", "P"))
            why = (f"값 같음(앞날·TR·수정주가), {oth} 판정 {vd[oth].get((c, d), '가격고정 후보 아님')}" if same else
                   f"값 다름: {oth} 앞 {ho['앞']} TR {ho['TR_앞']}→{ho['TR']} P {ho['P_앞']}→{ho['P']} J {ho['J']:+.4f}, 판정 {vd[oth].get((c, d), '가격고정 후보 아님')}")
            if same and vd[oth].get((c, d)) is None:
                why += f"; {oth} J {ho['J']:+.4f}, 거래량 {ho['거래량']}, 정지 {ho['정지']}"
        sm = 열("새", "시장구분", c)
        rows.append(dict(목록=side, 코드=c, 이름=r["이름"], 날짜=d, 앞_날짜=r["앞_날짜"], 유형=r["유형"], 분류=r["분류"],
                         TR=f"{r['TR_앞']}→{r['TR']}", 수정주가=f"{r['수정주가_앞']}→{r['수정주가']}", 배당효과=round(r["배당효과"], 4),
                         새_시장구분=nn(sm.get(D)) if sm is not None else None, 까닭=why))
    R = pd.DataFrame(rows)
    if len(R):
        kind = R["까닭"].str.split(r"[:(,]").str[0]
        L.append("- 까닭별(앞부분): " + str(pd.crosstab([R["목록"], R["유형"]], kind).stack().loc[lambda x: x > 0].to_dict()) + "\n")
        L.append("- 새에만 줄의 그날 시장구분: " + str(R.loc[R["목록"] == "새에만", "새_시장구분"].value_counts(dropna=False).to_dict()) + "\n\n")
    L.append(표(R))

    # ---- 3. 코드재사용 ----
    old = pd.read_csv(OLDDIR / "코드재사용_16종목.csv", encoding="utf-8-sig")
    new = csv_back(n["reuse"])
    k_ = lambda t: set(zip(t["코드"], t["이전회사_마지막날짜"], t["새회사_첫날짜"]))
    ko, kn = k_(old), k_(new)
    L += ["\n## 3. 코드재사용\n",
          "못 쓴 것: 조건은 다 씀(수정주가 빈 구간 >250거래일). 근거 글의 '주재무 PIT 회계연도'는 새 데이터에 없어 '확인 못 함'으로 적음. "
          "예전 스크립트의 '공백 중 종가도 빈칸' assert는 새 데이터에서 멈추지 않고 근거 글에 칸 수를 적음.\n",
          f"- 예전 {len(ko)}줄, 새 {len(kn)}줄, 둘 다 {len(ko & kn)}, 예전에만 {len(ko - kn)}, 새에만 {len(kn - ko)}\n",
          f"- 새 목록 코드 수 {new['코드'].nunique()}(한 코드에 공백 2번 이상이면 줄 2개)\n"]
    cut = lambda t: t.assign(근거=t["근거"].str.split("; 주재무").str[0])
    L.append("- " + 같은값(cut(old), cut(new), ["코드", "이전회사_마지막날짜", "새회사_첫날짜"], ["공백거래일", "이름", "근거"])
             + " (근거는 '주재무 PIT' 앞부분만 대조, 이름은 예전 mapping_table vs 새 X03)\n")

    def 공백(src, c):
        p = 열(src, "수정주가", c)
        if p is None:
            return "종목 없음"
        v = np.where(p.notna().to_numpy())[0]
        if len(v) < 2:
            return f"값 {len(v)}개"
        g = np.diff(v) - 1
        i = int(np.argmax(g))
        return (f"첫 {p.index[v[0]].date()} 끝 {p.index[v[-1]].date()}; 250거래일 넘는 공백 {int((g > 250).sum())}개; "
                f"가장 긴 공백 {p.index[v[i]].date()}~{p.index[v[i + 1]].date()} {int(g[i])}거래일")
    rows = []
    for c, a, b in sorted(ko ^ kn):
        side = "새에만" if (c, a, b) in kn else "예전에만"
        r = (new if side == "새에만" else old).set_index(["코드", "이전회사_마지막날짜", "새회사_첫날짜"]).loc[(c, a, b)]
        rows.append(dict(목록=side, 코드=c, 이름=r["이름"], 이전회사_마지막날짜=a, 새회사_첫날짜=b, 공백거래일=r["공백거래일"],
                         예전데이터=공백("예전", c), 새데이터=공백("새", c), 근거=r["근거"],
                         까닭=("예전 데이터에 종목 없음" if 열("예전", "수정주가", c) is None else
                             "예전 데이터 기간 밖(공백이 1999-12-28 전에 시작)" if pd.Timestamp(a) < pd.Timestamp("1999-12-28") else "예전 데이터 값과 다름(예전데이터 칸)")))
    R = pd.DataFrame(rows)
    if len(R):
        L.append("- 까닭별: " + str(R.groupby(["목록", "까닭"]).size().to_dict()) + "\n\n")
    L.append(표(R))
    (OUT / "차이표.md").write_text("".join(L), encoding="utf-8")
    print("\n==================== 차이표 요약(줄 전부는 새목록/차이표.md) ====================")
    print("\n".join(x for x in "".join(L).splitlines() if not x.startswith("|")))


if __name__ == "__main__":
    res = {}
    for src in ["예전", "새"]:
        print(f"\n==================== {src} 데이터 ====================")
        reuse = 코드재사용(src)
        print(f"[코드재사용] {len(reuse)}줄")
        print(reuse.drop(columns="근거").to_string(index=False))
        gc.collect()
        m_full, m_tab = 병합(src)
        m_no3, m_no3tab = 병합(src, use_gap=False) if src == "예전" else (m_full, m_tab)
        print(f"[병합미반영] 조건 ①②③: {len(m_full) if src == '예전' else '③ 못 씀'}줄 / ③ 빼고(①②만): {len(m_no3)}줄, 시장별 {m_no3tab['시장'].value_counts().to_dict()}, "
              f"연도별 {pd.to_datetime(m_no3tab['날짜']).dt.year.value_counts().sort_index().to_dict()}")
        gc.collect()
        tr, tr56, A, info = TR이상(src, reuse)
        print(f"[TR 이상칸] {info}")
        print(f"  배당효과 기준 {len(tr56)}칸, 분류별 {tr56['분류'].value_counts().to_dict()}")
        print(f"  가격고정 후보 판정별 {A['판정'].value_counts().to_dict()}, 덧붙인 칸 {len(tr) - len(tr56)} → 합계 {len(tr)}줄")
        res[src] = dict(reuse=reuse, m=m_full, m_no3=m_no3, mtab=m_no3tab, tr=tr, tr56=tr56, A=A, info=info)
        gc.collect()

    o = res["예전"]
    print("\n==================== 같은 규칙 확인: 예전 데이터로 다시 만든 것 vs 예전 csv ====================")
    chk = {
        "수정주가_병합미반영_7칸.csv": same_table(o["m"], OLDDIR / "수정주가_병합미반영_7칸.csv"),
        "수정주가TR_이상칸_D38전.csv": same_table(o["tr56"], OLDDIR / "수정주가TR_이상칸_D38전.csv"),
        "수정주가TR_이상칸.csv": same_table(o["tr"], OLDDIR / "수정주가TR_이상칸.csv"),
        "코드재사용_16종목.csv": same_table(o["reuse"], OLDDIR / "코드재사용_16종목.csv"),
        "수정주가TR_가격고정후보_판정전수.csv": same_table(o["A"], OLDDIR / "수정주가TR_가격고정후보_판정전수.csv"),
    }
    for k, v in chk.items():
        print(f"  {k}: {v}")
    print(f"  예전 데이터에서 병합 조건 ③을 뺀(①②만) 줄 수: {len(o['m_no3'])} (③ 있으면 {len(o['m'])})")

    n = res["새"]
    n["m"].to_csv(OUT / "수정주가_병합미반영.csv", index=False, encoding="utf-8-sig")
    n["tr"].to_csv(OUT / "수정주가TR_이상칸.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    n["reuse"].to_csv(OUT / "코드재사용.csv", index=False, encoding="utf-8-sig")
    print(f"\n새 목록 저장: {OUT}")
    차이표(res | {"chk": chk})
