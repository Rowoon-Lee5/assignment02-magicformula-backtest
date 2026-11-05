import sys, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
cd = pd.read_excel(r"D:\26-2_데이터기반투자전략\과제02\data\교수제공\08.[액셀실습]TSMom(K200).xlsx", sheet_name="TS모멘텀_m", header=None)
print(cd.iloc[:6, :6])
c = cd.iloc[5:, [1, 3]].dropna(); c.index = pd.to_datetime(c.iloc[:, 0]).values
c = pd.to_numeric(c.iloc[:, 1], errors="coerce")
print(c.loc["2021-10-01":].to_string())
c.loc["2023-01-01":].to_csv(r"D:\26-2_데이터기반투자전략\과제02\과제02_백테스트\_검증\1106\CD1m_RF\CD1m_2023이후.csv", encoding="utf-8-sig")
