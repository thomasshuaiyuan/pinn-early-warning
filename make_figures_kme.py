"""Figs 1, 2 and 4 redrawn for Kimberly Edwards's comments of November 2026.

Run: python3 make_figures_kme.py <data_dir> <out_dir>

Same data and same calculations as generate_figures.py (flux_data.csv,
chp_respiratory_cleaned.csv, epiestim_admissions_results.csv; CHP 4.94% and the
data-derived RSV 1.87%). Only the drawing changes:

  Fig 1  one positivity scale and one R(t) scale across the three panels
  Fig 2  bars added for all-ages, 0-5 and 65+ admissions
  Fig 4  standard error in place of standard deviation; age groups in age
         order; ILI rates in their own panel
  all    no title inside the figure (PLOS), panels lettered

Writes PNG and PLOS-specification TIFF (RGB, LZW, 300 dpi, at most 19.05 cm wide)
and fig_values_check.csv holding every plotted number.
"""
import sys, os, csv
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates
from scipy.stats import gamma as gamma_dist
from PIL import Image

DATA, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8.5,'axes.titlesize':9,
 'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7,'savefig.dpi':300,
 'savefig.bbox':'tight','axes.spines.top':False,'axes.spines.right':False})
FLU='#2166AC'; RSV='#D6604D'; GRAY='#999999'; THR='#E31A1C'
FLU_TH=0.0494; RSV_TH=1.87
W=7.4   # inches; 18.8 cm, inside the 19.05 cm page box

df=pd.read_csv(os.path.join(DATA,"flux_data.csv"))
df["From"]=pd.to_datetime(df["From"],format="%d/%m/%Y"); df["To"]=pd.to_datetime(df["To"],format="%d/%m/%Y")
df["MidDate"]=df["From"]+(df["To"]-df["From"])/2
rsv=pd.read_csv(os.path.join(DATA,"chp_respiratory_cleaned.csv"))
for c in ("From","To"): rsv[c]=pd.to_datetime(rsv[c])
rsv["MidDate"]=rsv["From"]+(rsv["To"]-rsv["From"])/2

FLU_WIN={"2014/15 winter":("2014-10-01","2015-06-01"),"2015/16 winter":("2015-10-01","2016-06-01"),
 "2016/17 winter":("2016-09-15","2017-06-01"),"2017/18 summer":("2017-04-01","2018-04-01"),
 "2018/19 winter":("2018-09-15","2019-06-01"),"2023 summer":("2023-01-15","2023-10-01"),
 "2023/24 winter":("2023-07-15","2024-04-01"),"2024/25 winter":("2024-08-01","2025-04-01")}
SHORT={"2014/15 winter":"2014/15","2015/16 winter":"2015/16","2016/17 winter":"2016/17",
 "2017/18 summer":"2017/18","2018/19 winter":"2018/19","2023 summer":"2023 sum",
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

adm=pd.read_csv(os.path.join(DATA,"epiestim_admissions_results.csv"))
onset={(r.season_name,r.signal):pd.to_datetime(r.onset_date) for r in adm.itertuples()}
degen={(r.season_name,r.signal):(r.best_Rt>1000) for r in adm.itertuples()}
crossing={s:flu_crossing(*FLU_WIN[s]) for s in FLU_WIN}
def flu_lead(season,signal):
    on=onset.get((season,signal)); cr=crossing[season]
    return None if (on is None or cr is None) else (cr-on).days

check=[]
def save(fig,name):
    png=os.path.join(OUT,name+".png"); fig.savefig(png); plt.close(fig)
    im=Image.open(png).convert("RGB")
    im.save(os.path.join(OUT,name+".tif"),format="TIFF",compression="tiff_lzw",dpi=(300,300))
    w,h=im.size; print(f"{name}: {w}x{h} px, {w/300*2.54:.2f} x {h/300*2.54:.2f} cm, "
                      f"{os.path.getsize(os.path.join(OUT,name+'.tif'))/1e6:.2f} MB")
    assert w/300*2.54<=19.05 and h/300*2.54<=22.23

# ---------------- Fig 1 ----------------
fig,axes=plt.subplots(1,3,figsize=(W,2.6))
panels=[("A  Influenza 2018/19","2018-09-15","2019-06-01",df,"AandB_proportion",FLU_TH,3.0,1.5,FLU,False),
        ("B  Influenza 2024/25","2024-08-01","2025-04-01",df,"AandB_proportion",FLU_TH,3.0,1.5,FLU,False),
        ("C  RSV 2017","2017-01-01","2017-12-01",rsv,"RSV_pct",RSV_TH,7.5,3.5,RSV,True)]
for k,(ax,(title,st,en,src,col,th,sim,sisd,color,ispct)) in enumerate(zip(axes,panels)):
    m=(src["MidDate"]>=st)&(src["MidDate"]<=en); se=src.loc[m].dropna(subset=[col]).sort_values("MidDate")
    dates=se["MidDate"].values; pos=se[col].values
    if ispct: disp=pos; thd=th; inc=(pos/100*10000).astype(float)
    else: disp=pos*100; thd=th*100; inc=(pos*10000).astype(float)
    inc=np.maximum(inc,0); ti,va=epiestim_rt(inc,sim,sisd); ax2=ax.twinx()
    ax2.spines['right'].set_visible(True)
    ax.fill_between(dates,disp,alpha=0.15,color=color); ax.plot(dates,disp,color=color,lw=1.2,label='Positivity')
    ax.axhline(thd,color=THR,ls='--',lw=0.9,alpha=0.8,label='Threshold')
    ax2.plot(dates[ti],va,color='black',lw=1.2,label='R(t)'); ax2.axhline(1.0,color='black',ls=':',lw=0.7,alpha=0.6)
    ax.set_ylim(0,32); ax2.set_ylim(0,2.0)          # one scale on each axis, all panels
    ax.set_title(title,fontweight='bold',loc='left')
    if k==0: ax.set_ylabel('Positivity (%)')
    else: ax.set_yticklabels([])
    if k==2: ax2.set_ylabel('R(t)')
    else: ax2.set_yticklabels([])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y')); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    if k==0:
        l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
        ax.legend(l1+l2,la1+la2,loc='upper right',framealpha=0.9,borderaxespad=0.2)
    check.append(("Fig1",title,"peak positivity %",round(float(np.max(disp)),2)))
    check.append(("Fig1",title,"max R(t)",round(float(np.max(va)),3)))
    assert np.max(disp)<32 and np.max(va)<2.0
fig.tight_layout(); save(fig,"Fig1")

# ---------------- Fig 2 ----------------
SIG=[("AandB_proportion","Laboratory positivity",'#2166AC'),("Adm_All","Admissions, all ages",'#555555'),
     ("Adm_0_5","Admissions, 0-5 y",'#A6D96A'),("Adm_6_11","Admissions, 6-11 y",'#FF7F00'),
     ("Adm_12_17","Admissions, 12-17 y",'#1A9641'),("Adm_65_higher","Admissions, 65+ y",'#7B3294')]
seasons=list(FLU_WIN); x=np.arange(len(seasons)); w=0.14
fig,ax=plt.subplots(figsize=(W,3.9))
for i in [2,3,6]: ax.axvspan(i-0.47,i+0.47,alpha=0.06,color='red',lw=0)
for j,(sig,lab,colr) in enumerate(SIG):
    vals=[flu_lead(s,sig) for s in seasons]
    bars=ax.bar(x+(j-2.5)*w,vals,w,label=lab,color=colr,alpha=0.9)
    for b,s,v in zip(bars,seasons,vals):
        d=degen.get((s,sig),False)
        if d: b.set_hatch('////'); b.set_edgecolor('black'); b.set_alpha(0.45); b.set_linewidth(0.5)
        check.append(("Fig2",SHORT[s],lab+(" [not estimable]" if d else ""),v))
ax.axhline(0,color='black',lw=0.7); ax.set_xticks(x); ax.set_xticklabels([SHORT[s] for s in seasons])
ax.set_ylabel('EpiEstim lead time against the 4.94% threshold (days)\n(positive = earlier)')
from matplotlib.patches import Patch
h,l=ax.get_legend_handles_labels()
h.append(Patch(facecolor='white',edgecolor='black',hatch='////',lw=0.5)); l.append('R(t) not estimable (no admissions before onset)')
ax.legend(h,l,loc='upper center',bbox_to_anchor=(0.5,-0.09),frameon=False,ncol=3)
fig.tight_layout(); save(fig,"Fig2")

# ---------------- Fig 4 ----------------
SW=[("2014/15","2014-10-01","2015-06-01"),("2015/16","2015-10-01","2016-06-01"),
    ("2018/19","2018-09-15","2019-06-01"),("2023 S","2023-01-15","2023-10-01"),("2024/25","2024-08-01","2025-04-01")]
ADMCH=[("Adm_0_5","0-5 y"),("Adm_6_11","6-11 y"),("Adm_12_17","12-17 y"),("Adm_65_higher","65+ y"),("Adm_All","All ages")]
ILICH=[("ILI_PMP","Private practitioners (GP)"),("ILI_FMC","Public clinics (GOPC/FMC)"),("ILI_AED","A&E departments")]
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
fig,(axa,axb)=plt.subplots(1,2,figsize=(W,2.9),gridspec_kw=dict(width_ratios=[1.25,1],wspace=0.75))
for ax,CH,colr,ttl,pad in [(axa,ADMCH,'#4DAF4A','A  Hospital admissions',25),(axb,ILICH,GRAY,'B  Influenza-like illness rates',1.5)]:
    for i,(col,lab) in enumerate(CH):
        v=preonset(col); n=len(v); mu=float(np.mean(v)); sd=float(np.std(v,ddof=1)) if n>1 else float('nan')
        se=sd/np.sqrt(n) if n>1 else float('nan')
        ax.barh(i,mu,color=colr,height=0.65,xerr=None if n==1 else se,error_kw=dict(ecolor='#333333',elinewidth=0.9,capsize=2.5))
        ax.text(mu+(0 if n==1 else se)+pad,i,f'n = {n}',va='center',fontsize=7,color='#555555')
        check.append(("Fig4",lab,"mean % change",round(mu,1))); check.append(("Fig4",lab,"SD",round(sd,1)))
        check.append(("Fig4",lab,"SE",round(se,1))); check.append(("Fig4",lab,"n seasons",n))
    ax.set_yticks(range(len(CH))); ax.set_yticklabels([c[1] for c in CH]); ax.invert_yaxis()
    ax.axvline(0,color='black',lw=0.5); ax.set_title(ttl,fontweight='bold',loc='left')
    ax.set_xlabel('Mean change over the eight weeks\nbefore the threshold crossing (%)')
axa.set_xlim(0,900); axb.set_xlim(0,60)
save(fig,"Fig4")

with open(os.path.join(OUT,"fig_values_check.csv"),"w",newline="") as fh:
    wr=csv.writer(fh); wr.writerow(["figure","item","quantity","value"]); wr.writerows(check)
