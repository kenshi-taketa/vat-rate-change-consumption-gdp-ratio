"""P6: English tables and Figure 1 for the core sample (proposal; not inserted in the manuscript).
Reads (cloud-relative): results/{episode_results.csv, aggregate_results.json, event_time_paths_ascm.csv}, core_episodes_20261015.csv
Outputs next to this script: table1_core_episodes.{csv,tex}, table2_episode_results.{csv,tex}, table3_aggregate.{csv,tex}, fig1_event_time.png"""
import pandas as pd, json, numpy as np, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=os.environ.get('P6_DATA','.')+'/'; O=os.path.dirname(os.path.abspath(__file__))+'/'
core=pd.read_csv(R+'inputs/core_episodes_20261015.csv',encoding='utf-8-sig').set_index('episode')
e=pd.read_csv(R+'results/episode_results.csv'); e=e[e.tag=='main']
order=['DE2007Q1','GB1979Q2','GB1991Q2','GB2011Q1','HU2012Q1','JP1997Q2','JP2014Q2','LU2015Q1','NL2012Q4','NZ2010Q4','SI2013Q3','FR1977Q1']
name={'DE':'Germany','FR':'France','GB':'United Kingdom','HU':'Hungary','JP':'Japan','LU':'Luxembourg','NL':'Netherlands','NZ':'New Zealand','SI':'Slovenia'}
# motive labels: Gunter et al. (2021) rule (JP2014, SI2013 coded by us), and our original coding fixed before estimation (D7)
gun={'DE2007Q1':'b','GB1979Q2':'a','GB1991Q2':'a','GB2011Q1':'b','HU2012Q1':'b','JP1997Q2':'b','JP2014Q2':'b*','LU2015Q1':'n/a','NL2012Q4':'b','NZ2010Q4':'a','SI2013Q3':'b*','FR1977Q1':'n/a'}
orig={'DE2007Q1':'a/b','GB1979Q2':'a','GB1991Q2':'a','GB2011Q1':'b','HU2012Q1':'b','JP1997Q2':'a','JP2014Q2':'b (prov.)','LU2015Q1':'c','NL2012Q4':'b','NZ2010Q4':'a','SI2013Q3':'b','FR1977Q1':'?'}
def q(ep): return f"{ep[2:6]}Q{ep[-1]}"
rows1=[]
for ep in order:
    c=core.loc[ep]; rows1.append(dict(Country=name[ep[:2]],Quarter=q(ep),Change=f"{c['kind']} {abs(c['change_pp']):.1f}",Donors=int(e[(e.ep==ep)&(e.est=='ascm')].J.iloc[0]),Gunter_rule=gun[ep],Original_coding=orig[ep]))
t1=pd.DataFrame(rows1); t1.to_csv(O+'table1_core_episodes.csv',index=False)
rows2=[]
for ep in order:
    a=e[(e.ep==ep)&(e.est=='ascm')].iloc[0]; s=e[(e.ep==ep)&(e.est=='scm')].iloc[0]
    rows2.append(dict(Country=name[ep[:2]],Quarter=q(ep),Pre_RMSPE=a.pre_rmspe,ASCM_gap=a.mean_gap,ASCM_ratio=a.ratio,ASCM_p=a.p_ratio,SCM_gap=s.mean_gap,SCM_ratio=s.ratio,SCM_p=s.p_ratio))
t2=pd.DataFrame(rows2); t2.to_csv(O+'table2_episode_results.csv',index=False)
agg=json.load(open(R+'results/aggregate_results.json'))
def A(k): d=agg[k]; return d['n'],d['estimate'],d['perm_p_two']
rows3=[]
for lab,ka,ks in [('Tax increases, mean gap (pp)','core_increases|ascm|mean_gap|equal','core_increases|scm|mean_gap|equal'),
                  ('Tax increases, mean slope (pp/yr)','core_increases|ascm|slope|equal','core_increases|scm|slope|equal'),
                  ('Increases and cut, sign-flipped mean gap (pp)','core_pooled_signflip|ascm|mean_gap|equal','core_pooled_signflip|scm|mean_gap|equal')]:
    n,a,pa=A(ka); _,s,ps=A(ks); rows3.append(dict(Panel='A. Aggregate',Row=lab,N=n,ASCM=a,ASCM_p=pa,SCM=s,SCM_p=ps))
mot=[('Core, Gunter et al. rule (3 vs 7)',3,7,-5.25,.038),('Core, Gunter-covered episodes only (3 vs 5)',3,5,-4.71,.085),('Core, original coding (4 vs 5)',4,5,-4.85,.047),
     ('Core+extended, Gunter rule incl. our coding (6 vs 23)',6,23,-3.35,.109),('Core+extended, Gunter-covered only (6 vs 18)',6,18,-2.24,.245)]
for lab,na,nb,d,p in mot: rows3.append(dict(Panel='B. Motive: (b) minus (a), era-stratified',Row=lab,N=na+nb,ASCM=d,ASCM_p=p,SCM=np.nan,SCM_p=np.nan))
t3=pd.DataFrame(rows3); t3.to_csv(O+'table3_aggregate.csv',index=False)
def f(x,d=2): return '' if pd.isna(x) else f"{x:.{d}f}"
def tex(df,cols,align,cap,lab,note,fmt):
    L=[r'\begin{table}[htbp]\centering',r'\caption{'+cap+r'}\label{'+lab+'}',r'\begin{tabular}{'+align+'}',r'\toprule',' & '.join(cols)+r' \\',r'\midrule']
    for _,r in df.iterrows(): L.append(' & '.join(fmt(r))+r' \\')
    L+= [r'\bottomrule',r'\end{tabular}',r'\par\smallskip\parbox{0.95\textwidth}{\footnotesize '+note+'}',r'\end{table}']; return '\n'.join(L)
open(O+'table1_core_episodes.tex','w').write(tex(t1,['Country','Quarter','Change (pp)','Donors','Motive: Gunter rule','Motive: original'],'llrrll',
 'Core sample: standard-rate changes','tab:core',r'Notes: Donors = number of countries in the donor pool. Motive (a): increase offsetting a cut in another tax; (b): inherited deficit or debt; n/a: outside the definition or the sample of Gunter et al. (2021). * = coded by the authors with the same rule (outside their sample). Original coding was fixed before estimation; prov. = provisional.',
 lambda r:[r.Country,r.Quarter,r.Change.replace('increase','+').replace('cut','$-$'),str(r.Donors),r.Gunter_rule.replace('*',r'$^*$'),r.Original_coding]))
open(O+'table2_episode_results.tex','w').write(tex(t2,['Country','Quarter','Pre-RMSPE','ASCM gap','Ratio','$p$','SCM gap','Ratio','$p$'],'llrrrrrrr',
 'Episode-level results (outcome: log consumption minus log GDP, in percentage points)','tab:episodes',r'Notes: Gap = mean post-treatment gap over 20 quarters between the treated country and its synthetic control (40 pre-treatment quarters). Ratio = post-/pre-treatment RMSPE. $p$ = rank of the ratio among the treated country and donors divided by their number (permutation).',
 lambda r:[r.Country,r.Quarter,f(r.Pre_RMSPE),f(r.ASCM_gap),f(r.ASCM_ratio),f(r.ASCM_p,3),f(r.SCM_gap),f(r.SCM_ratio),f(r.SCM_p,3)]))
open(O+'table3_aggregate.tex','w').write(tex(t3,['Panel','Row','$N$','ASCM','$p$','SCM','$p$'],'llrrrrr',
 'Aggregation and permutation inference','tab:aggregate',r'Notes: Panel A uses equal weights and permutation inference over donor assignments. Panel B reports the difference in mean gaps between (b) and (a) episodes, weighted within era strata (2010--13 versus other), with a stratified permutation $p$-value (5,000 draws); extended-sample rows are exploratory. The motive definition affects the result; see the text.',
 lambda r:[r.Panel,r.Row,str(int(r.N)),f(r.ASCM),f(r.ASCM_p,3),f(r.SCM),f(r.SCM_p,3)]))
p=pd.read_csv(R+'results/event_time_paths_ascm.csv')
fig,ax=plt.subplots(figsize=(6.4,3.8),dpi=200)
ax.axhline(0,color='#888',lw=.8); ax.axvline(-0.5,color='#888',lw=.8,ls=':')
ax.plot(p.h,p.core_increases,color='#1f4e79',lw=2,marker='o',ms=3,label='Increases (11 episodes)')
ax.plot(p.h,p.core_cuts,color='#c0504d',lw=1.5,ls='--',marker='s',ms=3,label='Cut (1 episode: FR1977)')
ax.set_xlabel('Quarters since the rate change (0 = first quarter in effect)'); ax.set_ylabel('Mean ASCM gap, ln C − ln Y (pp)')
ax.set_xticks(range(0,20,2)); ax.legend(frameon=False,fontsize=8); ax.spines[['top','right']].set_visible(False)
fig.tight_layout(); fig.savefig(O+'fig1_event_time.png'); print(t1.to_string()); print(t2.round(3).to_string()); print(t3.round(3).to_string())
