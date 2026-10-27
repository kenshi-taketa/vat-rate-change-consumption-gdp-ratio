"""P6: English Table 5 (own-history and pooled kink) and Table 7 (independent re-estimation in Stata and R). Proposal; not in the manuscript.
Inputs: stage4/kink/out2/own_kink_core_B2000_s20261015.csv, pooled_kink_B2000_s20261015.json; and the compare_*.csv files of stage6_20261015\\p6_stata_check\\output
(set CMP below to that folder; in the cloud they were staged to /mnt/user-data/uploads/...)."""
import pandas as pd, numpy as np, json, os, glob
R=os.environ.get('P6_DATA','.')+'/'; O=os.path.dirname(os.path.abspath(__file__))+'/'
CMP=os.environ.get('P6_STATA_OUT','results')+'/'
name={'DE':'Germany','FR':'France','GB':'United Kingdom','HU':'Hungary','JP':'Japan','LU':'Luxembourg','NL':'Netherlands','NZ':'New Zealand','SI':'Slovenia'}
order=['DE2007Q1','GB1979Q2','GB1991Q2','GB2011Q1','HU2012Q1','JP1997Q2','JP2014Q2','LU2015Q1','NL2012Q4','NZ2010Q4','SI2013Q3','FR1977Q1']
k=pd.read_csv(R+'stage4/kink/out2/own_kink_core_B2000_s20261015.csv').set_index('ep')
rows=[]
for ep in order:
    r=k.loc[ep]; rows.append(dict(Country=name[ep[:2]],Quarter=f"{ep[2:6]}Q{ep[-1]}",N=int(r.n),Controls=int(r.n_ctrl),Slope_change=r.gamma400,SE_slope=r.se400,p_slope=r.p_gamma,Level_step=r.delta100,SE_step=r.se_delta100,p_step=r.p_delta))
t5=pd.DataFrame(rows); t5.to_csv(O+'table5A_own_kink.csv',index=False)
pj=json.load(open(R+'stage4/kink/out2/pooled_kink_B2000_s20261015.json'))
pl={'increases_all':'All 11 increases','increases_ex_JP2014':'Excluding JP2014','increases_ex_euro_crisis':'Excluding euro-crisis episodes (HU, NL, SI)'}
t5b=pd.DataFrame([dict(Sample=pl[s],Episodes=v['n_ep'],Slope_change=v['gamma400'],SE_slope=v['se400'],Level_step=v['delta100'],SE_step=v['se_d100']) for s,v in pj.items()]); t5b.to_csv(O+'table5B_pooled_kink.csv',index=False)
def f(x,d=2): return f"{x:.{d}f}".replace('-','$-$')
L=[r'\begin{table}[htbp]\centering\small',r'\caption{Own-history kink regressions (OECD series, no crisis dummies)}\label{tab:kink}',r'\begin{tabular}{llrrrrrr}',r'\toprule',r'Country & Quarter & Slope change (pp/yr) & SE & $p$ & Level step (pp) & SE & $p$ \\',r'\midrule',r'\multicolumn{8}{l}{\emph{A. Episode by episode}} \\']
for _,r in t5.iterrows(): L.append(' & '.join([r.Country,r.Quarter,f(r.Slope_change),f(r.SE_slope),f(r.p_slope,3),f(r.Level_step),f(r.SE_step),f(r.p_step,3)])+r' \\')
L+=[r'\midrule',r'\multicolumn{8}{l}{\emph{B. Pooled (episode fixed effects and own trends; clustered by episode)}} \\']
for _,r in t5b.iterrows(): L.append(' & '.join([r.Sample,f"{int(r.Episodes)} ep.",f(r.Slope_change),f(r.SE_slope),'',f(r.Level_step),f(r.SE_step),''])+r' \\')
L+=[r'\bottomrule',r'\end{tabular}',r'\par\smallskip\parbox{0.95\textwidth}{\footnotesize Notes: OLS with Newey--West (4 lags) standard errors; control break dates from a Bai--Perron search with a block bootstrap (B = 2,000). The estimates are not comparable with the kink estimates in our Japan and UK papers, which use other data and crisis dummies.}',r'\end{table}']
open(O+'table5_kink.tex','w').write('\n'.join(L))
# Table 7
kk=pd.read_csv(CMP+'compare_kink_own.csv'); kp=pd.read_csv(CMP+'compare_kink_pooled.csv'); sa=pd.read_csv(CMP+'compare_scm_ascm.csv'); cf=pd.read_csv(CMP+'compare_conformal.csv'); ct=pd.read_csv(CMP+'compare_cft.csv')
def cnt(d,col='ok'): return int((d[col]==1).sum()),len(d)
rows7=[('Own-history kink (slope, SE, level step)','Stata',*cnt(kk),'0.002 / 0.002 / 0.005'),('Pooled kink (three samples)','Stata',*cnt(kp),'same'),
 ('SCM and ridge ASCM: fit, ratio, mean gap, permutation p, $\\lambda$','Stata (own solver)',*cnt(sa),'ratio 0.5%; gap 0.01 pp; p exact'),
 ('Conformal $p(0)$ and 95% set ($q=1,2$)','Stata',*cnt(cf),'p exact; bounds within one grid step')]
for m in ('gaussian','ls','qreg'):
    d=ct[ct.method==m]; rows7.append((f'CFT prediction intervals, {m}','R (scpi)',int((d.verdict=='MATCH').sum()),len(d),'$\\pm$2 quarters; $\\pm$0.5 pp'))
t7=pd.DataFrame(rows7,columns=['Object','Tool','Matches','Compared','Tolerance']); t7.to_csv(O+'table7_replication.csv',index=False)
L=[r'\begin{table}[htbp]\centering\small',r'\caption{Independent re-estimation of the core-sample results}\label{tab:replic}',r'\begin{tabular}{llrrl}',r'\toprule',r'Object & Tool & Matches & Compared & Tolerance \\',r'\midrule']
for _,r in t7.iterrows(): L.append(' & '.join([r.Object,r.Tool,str(r.Matches),str(r.Compared),r.Tolerance])+r' \\')
L+=[r'\bottomrule',r'\end{tabular}',r'\par\smallskip\parbox{0.95\textwidth}{\footnotesize Notes: The Python estimates are compared with Stata (own active-set solver) and R (scpi). The CFT differences arise from random-number streams and, for quantile regression, from different estimators in the R and Python implementations of scpi (the quantile-regression bounds depend on the implementation); the main specification is Gaussian. Not independently re-done: Bai--Perron break dates, the stage-5 robustness checks, permutation aggregation.}',r'\end{table}']
open(O+'table7_replication.tex','w').write('\n'.join(L)); print(t5.round(3).to_string()); print(t5b.round(3).to_string()); print(t7.to_string())
