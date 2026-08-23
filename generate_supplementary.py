"""Regenerate supplementary files reproducibly from flux_data.csv + chp_respiratory_cleaned.csv.
Outputs: data_dictionary_flu_express.csv, supplementary_table_S1_seasons.csv,
         supplementary_table_S2_preonset.csv"""
import pandas as pd, numpy as np
from scipy.signal import find_peaks

df=pd.read_csv("flux_data.csv"); df["From"]=pd.to_datetime(df["From"],format="%d/%m/%Y"); df["To"]=pd.to_datetime(df["To"],format="%d/%m/%Y")
df["MidDate"]=df["From"]+(df["To"]-df["From"])/2
rsv=pd.read_csv("chp_respiratory_cleaned.csv"); rsv["From"]=pd.to_datetime(rsv["From"]); rsv["MidDate"]=rsv["From"]
FLU_TH=0.0494

# ---------- 1. DATA DICTIONARY (coverage recomputed from data) ----------
dd=pd.read_csv("data_dictionary_flu_express.csv")
nn=[int(df[v].notna().sum()) if v in df.columns else 0 for v in dd["variable"]]
dd["n_non_null"]=nn; dd["n_total"]=len(df); dd["coverage_pct"]=[round(100*x/len(df),1) for x in nn]
dd=dd[["variable","description","unit","source","coverage_pct","n_non_null","n_total","notes"]]
dd.to_csv("data_dictionary_flu_express.csv",index=False)

# ---------- 2. TABLE S1 (n_weeks, peak, classification recomputed) ----------
s1=pd.read_csv("supplementary_table_S1_seasons.csv")
def peaks_flu(a,b):
    m=(df["MidDate"]>=a)&(df["MidDate"]<=b)
    v=df.loc[m].sort_values("MidDate")["AandB_proportion"].dropna().rolling(3,center=True,min_periods=1).mean().values
    return len(find_peaks(v,prominence=0.02,distance=8)[0])
rows=[]
for r in s1.itertuples():
    a=pd.to_datetime(r.start_date); b=pd.to_datetime(r.end_date)
    if r.pathogen=="Influenza":
        m=(df["MidDate"]>=a)&(df["MidDate"]<=b); sub=df.loc[m].dropna(subset=["AandB_proportion"]).sort_values("MidDate")
        nwk=len(sub); pk=sub.loc[sub["AandB_proportion"].idxmax()]; peakpct=round(pk["AandB_proportion"]*100,1); peakdt=pk["From"].date()
        npk=peaks_flu(a,b)
        if r.season.startswith("2016/17"):
            cls="Multi-wave (admissions-based)"; meth="1 positivity peak (find_peaks, prom=0.02, dist=8); multi-wave in age-stratified admissions"
        elif npk>=2:
            cls="Multi-wave"+(" (post-COVID)" if "2023/24" in r.season else ""); meth=f"{npk} positivity peaks (find_peaks, prom=0.02, dist=8)"
        else:
            cls="Single-wave"+(" (post-COVID)" if "2024/25" in r.season else ""); meth=f"{npk} positivity peak (find_peaks, prom=0.02, dist=8)"
    else:
        m=(rsv["MidDate"]>=a)&(rsv["MidDate"]<=b); sub=rsv.loc[m].dropna(subset=["RSV_pct"]).sort_values("MidDate")
        nwk=len(sub); pk=sub.loc[sub["RSV_pct"].idxmax()]; peakpct=round(pk["RSV_pct"],1); peakdt=pk["From"].date()
        cls=r.classification; meth="Visual inspection of RSV_pct time series"
    rows.append((r.season,r.pathogen,r.start_date,r.end_date,nwk,peakpct,peakdt,r.dominant_subtype,cls,meth,
                 r.included_in_pinn,r.included_in_admissions,r.included_in_epiestim))
pd.DataFrame(rows,columns=["season","pathogen","start_date","end_date","n_weeks","peak_positivity_pct","peak_date",
    "dominant_subtype","classification","classification_method","included_in_pinn","included_in_admissions",
    "included_in_epiestim"]).to_csv("supplementary_table_S1_seasons.csv",index=False)

# ---------- 3. TABLE S2 pre-onset amplification per channel ----------
SW=[("2014/15","2014-10-01","2015-06-01"),("2015/16","2015-10-01","2016-06-01"),
    ("2018/19","2018-09-15","2019-06-01"),("2023 S","2023-01-15","2023-10-01"),("2024/25","2024-08-01","2025-04-01")]
CH=[("Adm_6_11","Admissions 6-11y"),("Adm_65_higher","Admissions 65+"),("Adm_All","Admissions all ages"),
    ("Adm_0_5","Admissions 0-5y"),("Adm_12_17","Admissions 12-17y"),("ILI_AED","A&E ILI rate (ILI_AED)"),
    ("ILI_PMP","GP ILI rate (ILI_PMP)"),("ILI_FMC","GOPC/FMC ILI rate (ILI_FMC)")]
def preonset(col):
    out=[]
    for sn,st,en in SW:
        m=(df["MidDate"]>=st)&(df["MidDate"]<=en)
        s=df.loc[m].dropna(subset=["AandB_proportion",col]).sort_values("MidDate").reset_index(drop=True)
        cr=s[s["AandB_proportion"]>=FLU_TH]
        if len(cr)==0 or cr.index[0]-8<0: continue
        base=s.loc[cr.index[0]-8,col]; pre=s.loc[cr.index[0]-1,col]
        if base and base>0: out.append((sn,(pre-base)/base*100))
    return out
s2=[]
for col,lab in CH:
    v=preonset(col); vals=[x[1] for x in v]
    s2.append((lab,col,len(vals),round(np.mean(vals),1),round(np.std(vals,ddof=1),1) if len(vals)>1 else "",
               round(min(vals),0) if vals else "",round(max(vals),0) if vals else "",
               "; ".join(f"{s}:{p:.0f}%" for s,p in v)))
pd.DataFrame(s2,columns=["channel","variable","n_seasons","mean_pct_change","sd_pct_change","min_pct","max_pct","per_season"]
    ).to_csv("supplementary_table_S2_preonset.csv",index=False)
print("Supplementary files regenerated.")
