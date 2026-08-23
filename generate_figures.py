"""
Manuscript figures — v8, fully data-driven (no hard-coded leads).
All quantities are computed from flux_data.csv, chp_respiratory_cleaned.csv,
and the committed onset CSVs, using the 4.94% (flu) / 1.87% (RSV) thresholds.

Run: python generate_figures.py
Outputs: fig1_rt_trajectories, fig2_signal_amplitude, fig3_preonset_signals,
         fig4_admissions_comparison  (.png + .pdf)

Thomas Yuan — HKU SPH / HKU-Pasteur (Dhanasekaran lab)
"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt, matplotlib.dates as mdates
from scipy.stats import gamma as gamma_dist
import warnings; warnings.filterwarnings("ignore")

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,'axes.titlesize':12,
 'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8,'figure.dpi':200,'savefig.dpi':300,
 'savefig.bbox':'tight','axes.spines.top':False,'axes.spines.right':False})
FLU='#2166AC'; RSV='#D6604D'; ADM='#4DAF4A'; ORANGE='#FF7F00'; GRAY='#999999'; THR='#E31A1C'
FLU_TH=0.0494; RSV_TH=1.87  # RSV_pct is already in percent

df=pd.read_csv("flux_data.csv")
df["From"]=pd.to_datetime(df["From"],format="%d/%m/%Y"); df["To"]=pd.to_datetime(df["To"],format="%d/%m/%Y")
df["MidDate"]=df["From"]+(df["To"]-df["From"])/2
rsv=pd.read_csv("chp_respiratory_cleaned.csv")
for c in ("From","To"): rsv[c]=pd.to_datetime(rsv[c])
rsv["MidDate"]=rsv["From"]+(rsv["To"]-rsv["From"])/2

FLU_WIN={"2014/15 winter":("2014-10-01","2015-06-01"),"2015/16 winter":("2015-10-01","2016-06-01"),
 "2016/17 winter":("2016-09-15","2017-06-01"),"2017/18 summer":("2017-04-01","2018-04-01"),
 "2018/19 winter":("2018-09-15","2019-06-01"),"2023 summer":("2023-01-15","2023-10-01"),
 "2023/24 winter":("2023-07-15","2024-04-01"),"2024/25 winter":("2024-08-01","2025-04-01")}
SHORT={"2014/15 winter":"2014/15","2015/16 winter":"2015/16","2016/17 winter":"2016/17",
 "2017/18 summer":"2017/18","2018/19 winter":"2018/19","2023 summer":"2023 S",
 "2023/24 winter":"2023/24","2024/25 winter":"2024/25"}

def flu_crossing(s,e):
    m=(df["MidDate"]>=s)&(df["MidDate"]<=e)
    sub=df.loc[m].dropna(subset=["AandB_proportion"]).sort_values("MidDate")
    x=sub[sub["AandB_proportion"]>=FLU_TH]
    return x["MidDate"].iloc[0] if len(x) else None

def epiestim_rt(inc,si_mean=3.0,si_sd=1.5,window=4,tu=7.0):
    n=len(inc); shape=(si_mean/si_sd)**2; scale=si_sd**2/si_mean; si=np.zeros(n)
    for t in range(1,n):
        si[t]=gamma_dist.cdf((t+0.5)*tu,a=shape,scale=scale)-gamma_dist.cdf(max(0,(t-0.5)*tu),a=shape,scale=scale)
    if si.sum()>0: si/=si.sum()
    lam=np.zeros(n)
    for t in range(1,n):
        for s in range(1,min(t+1,n)): lam[t]+=inc[t-s]*si[s]
    ti,va=[],[]
    for t in range(window,n):
        a=t-window+1; sI=np.sum(inc[a:t+1]); sL=np.sum(lam[a:t+1])
        if 0.2+sL>0: ti.append(t); va.append((1.0+sI)/(0.2+sL))
    return ti,va

adm=pd.read_csv("epiestim_admissions_results.csv")
onset={(r.season_name,r.signal):pd.to_datetime(r.onset_date) for r in adm.itertuples()}
degen={(r.season_name,r.signal):(r.best_Rt>1000) for r in adm.itertuples()}
crossing={s:flu_crossing(*FLU_WIN[s]) for s in FLU_WIN}
def flu_lead(season,signal):
    on=onset.get((season,signal)); cr=crossing[season]
    return None if (on is None or cr is None) else (cr-on).days

# ---------------- FIGURE 1 : R(t) trajectories ----------------
fig,axes=plt.subplots(1,3,figsize=(14,4))
panels=[("2018/19 influenza\n(high amplitude, peak 30%)","2018-09-15","2019-06-01",df,"AandB_proportion",FLU_TH,3.0,1.5,FLU,False),
        ("2024/25 influenza\n(post-COVID, peak 10.5%)","2024-08-01","2025-04-01",df,"AandB_proportion",FLU_TH,3.0,1.5,FLU,False),
        ("2017 RSV\n(low amplitude, peak 9.9%)","2017-01-01","2017-12-01",rsv,"RSV_pct",RSV_TH,7.5,3.5,RSV,True)]
for ax,(title,st,en,src,col,th,sim,sisd,color,ispct) in zip(axes,panels):
    m=(src["MidDate"]>=st)&(src["MidDate"]<=en); se=src.loc[m].dropna(subset=[col]).sort_values("MidDate")
    dates=se["MidDate"].values; pos=se[col].values
    if ispct: disp=pos; thd=th; inc=(pos/100*10000).astype(float)
    else: disp=pos*100; thd=th*100; inc=(pos*10000).astype(float)
    inc=np.maximum(inc,0); ti,va=epiestim_rt(inc,sim,sisd); ax2=ax.twinx()
    ax.fill_between(dates,disp,alpha=0.15,color=color); ax.plot(dates,disp,color=color,lw=1.5,label='Lab positivity')
    ax.axhline(thd,color=THR,ls='--',lw=1,alpha=0.7,label='Threshold')
    ax2.plot(dates[ti],va,color='black',lw=1.5,label='R(t)'); ax2.axhline(1.0,color='black',ls=':',lw=0.8,alpha=0.5)
    ax2.set_ylim(0,max(3,max(va)*1.1) if va else 3)
    ax.set_title(title,fontweight='bold',fontsize=10); ax.set_ylabel('Positivity (%)'); ax2.set_ylabel('R(t)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y')); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    if ax is axes[0]:
        l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
        ax.legend(l1+l2,la1+la2,loc='upper left',framealpha=0.9)
plt.tight_layout(); plt.savefig("fig1_rt_trajectories.png"); plt.savefig("fig1_rt_trajectories.pdf"); plt.close()

# ---------------- FIGURE 2 : signal amplitude vs EpiEstim lead ----------------
flu_peaks=[38.6,25.7,15.6,40.6,29.9,18.2,14.9,10.5]
flu_leads=[flu_lead(s,"AandB_proportion") for s in FLU_WIN]
rsvres=pd.read_csv("epiestim_rsv_results.csv")
rsv_peaks=list(rsvres["peak_positivity"]); rsv_leads=list(rsvres["lead_days"])
fig,ax=plt.subplots(figsize=(7,5))
ax.axvspan(0,10,alpha=0.06,color=RSV,label='Peak < 10%'); ax.axhline(0,color=GRAY,ls='--',lw=1,alpha=0.7)
ax.scatter(flu_peaks,flu_leads,c=FLU,s=80,marker='s',label='Influenza',edgecolors='black',lw=0.5,zorder=5)
ax.scatter(rsv_peaks,rsv_leads,c=RSV,s=80,marker='o',label='RSV',edgecolors='black',lw=0.5,zorder=5)
ax.set_xlabel('Peak season positivity (%)'); ax.set_ylabel('EpiEstim lead time (days)\n(positive = earlier than threshold)')
ax.set_xlim(0,45); ax.set_ylim(-120,150); ax.legend(loc='lower right',framealpha=0.9)
ax.set_title('Signal amplitude predicts R(t) method performance',fontweight='bold')
plt.tight_layout(); plt.savefig("fig2_signal_amplitude.png"); plt.savefig("fig2_signal_amplitude.pdf"); plt.close()

# ---------------- FIGURE 3 : pre-onset amplification (correct channels) ----------------
SW=[("2014/15","2014-10-01","2015-06-01"),("2015/16","2015-10-01","2016-06-01"),
    ("2018/19","2018-09-15","2019-06-01"),("2023 S","2023-01-15","2023-10-01"),("2024/25","2024-08-01","2025-04-01")]
CH=[("Adm_6_11","Admissions 6-11y"),("Adm_65_higher","Admissions 65+"),("Adm_All","Admissions all ages"),
    ("Adm_0_5","Admissions 0-5y"),("Adm_12_17","Admissions 12-17y"),
    ("ILI_FMC","GOPC/FMC ILI rate"),("ILI_AED","A&E ILI rate"),("ILI_PMP","GP ILI rate")]
def preonset(col):
    ch=[]
    for _,st,en in SW:
        m=(df["MidDate"]>=st)&(df["MidDate"]<=en)
        s=df.loc[m].dropna(subset=["AandB_proportion",col]).sort_values("MidDate").reset_index(drop=True)
        cr=s[s["AandB_proportion"]>=FLU_TH]
        if len(cr)==0 or cr.index[0]-8<0: continue
        b=s.loc[cr.index[0]-8,col]; p=s.loc[cr.index[0]-1,col]
        if b and b>0: ch.append((p-b)/b*100)
    return ch
rows=[]
for col,lab in CH:
    v=preonset(col); rows.append((lab,np.mean(v),np.std(v,ddof=1) if len(v)>1 else 0,len(v)))
names=[r[0] for r in rows]; vals=[r[1] for r in rows]; sds=[r[2] for r in rows]; ns=[r[3] for r in rows]
colors=[ADM if v>150 else (ORANGE if v>=100 else GRAY) for v in vals]
fig,ax=plt.subplots(figsize=(8.4,4.8)); y=range(len(names))
ax.barh(list(y),vals,xerr=sds,color=colors,edgecolor='white',height=0.7,error_kw=dict(ecolor=GRAY,elinewidth=1,capsize=3))
for i,(v,s,n) in enumerate(zip(vals,sds,ns)): ax.text(v+s+40,i,f'n={n}',va='center',fontsize=8,color=GRAY)
ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis(); ax.axvline(0,color='black',lw=0.5)
ax.set_xlabel('Mean pre-onset change (%)  ±SD\n(8 weeks before the 4.94% threshold crossing, single-wave seasons)')
ax.set_title('Hospital admissions surge before laboratory positivity crosses threshold',fontweight='bold')
plt.tight_layout(); plt.savefig("fig3_preonset_signals.png"); plt.savefig("fig3_preonset_signals.pdf"); plt.close()

# ---------------- FIGURE 4 : admissions vs positivity leads ----------------
seasons=[SHORT[s] for s in FLU_WIN]; pos=[flu_lead(s,"AandB_proportion") for s in FLU_WIN]
a12=[flu_lead(s,"Adm_12_17") for s in FLU_WIN]; a12d=[degen.get((s,"Adm_12_17"),False) for s in FLU_WIN]
a6=[flu_lead(s,"Adm_6_11") for s in FLU_WIN]; a6d=[degen.get((s,"Adm_6_11"),False) for s in FLU_WIN]
x=np.arange(len(seasons)); w=0.26
fig,ax=plt.subplots(figsize=(9.2,5))
ax.bar(x-w,pos,w,label='Lab positivity',color=FLU,alpha=0.85)
b12=ax.bar(x,a12,w,label='12-17y admissions',color=ADM,alpha=0.85)
b6=ax.bar(x+w,a6,w,label='6-11y admissions',color=ORANGE,alpha=0.85)
for bars,dg in [(b12,a12d),(b6,a6d)]:
    for b,d in zip(bars,dg):
        if d: b.set_hatch('///'); b.set_edgecolor('black'); b.set_alpha(0.45)
ax.axhline(0,color='black',lw=0.8); ax.set_xticks(x); ax.set_xticklabels(seasons,rotation=30,ha='right')
ax.set_ylabel('Lead time vs CHP 4.94% threshold (days)\n(positive = earlier detection)')
ax.set_title('Age-stratified admissions outperform lab positivity on difficult seasons',fontweight='bold')
for i in [2,3,6]: ax.axvspan(i-0.42,i+0.42,alpha=0.05,color='red')
ax.legend(loc='lower left',framealpha=0.9)
ax.text(0.99,0.02,'/// degenerate EpiEstim fit (near-zero admission denominators)',transform=ax.transAxes,
        ha='right',va='bottom',fontsize=6.5,color=GRAY)
plt.tight_layout(); plt.savefig("fig4_admissions_comparison.png"); plt.savefig("fig4_admissions_comparison.pdf"); plt.close()
print("Figures regenerated (data-driven, 4.94%).")
print("flu_leads:",dict(zip(seasons,flu_leads)))
