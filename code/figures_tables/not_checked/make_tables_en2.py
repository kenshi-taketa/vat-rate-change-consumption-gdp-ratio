"""P6: English Table 4 (conformal and CFT) and Tables A1, A2 (extended-sample motives and sensitivities). Proposal; not in the manuscript."""
import pandas as pd, numpy as np, os
R=os.environ.get('P6_DATA','.')+'/'; O=os.path.dirname(os.path.abspath(__file__))+'/'
name={'DE':'Germany','FR':'France','GB':'United Kingdom','HU':'Hungary','JP':'Japan','LU':'Luxembourg','NL':'Netherlands','NZ':'New Zealand','SI':'Slovenia'}
order=['DE2007Q1','GB1979Q2','GB1991Q2','GB2011Q1','HU2012Q1','JP1997Q2','JP2014Q2','LU2015Q1','NL2012Q4','NZ2010Q4','SI2013Q3','FR1977Q1']
def q(ep): return f"{ep[2:6]}Q{ep[-1]}"
c=pd.read_csv(R+'results/conformal_core_v2.csv'); c=c[c.q==1].set_index(['ep','est'])
f=pd.read_csv(R+'results/cft_core.csv').set_index('episode')
def ci(r):
    lo=f"{r.ci95_lo:.1f}"+('†' if r.ci95_lo<=-30 else ''); hi=f"{r.ci95_hi:.1f}"+('†' if r.ci95_hi>=20 else ''); return f"[{lo}, {hi}]"
rows=[]
for ep in order:
    a=c.loc[(ep,'ascm')]; s=c.loc[(ep,'scm')]; g=f.loc[ep]
    sg='−' if g.gaussian_n_neg>0 and g.gaussian_n_pos==0 else ('+' if g.gaussian_n_pos>0 and g.gaussian_n_neg==0 else '')
    rows.append(dict(Country=name[ep[:2]],Quarter=q(ep),ASCM_p0=a.p_zero,ASCM_CI=ci(a),SCM_p0=s.p_zero,SCM_CI=ci(s),CFT_n=f"{int(g.gaussian_n_excl0)}/20 ({sg})" if g.gaussian_n_excl0>0 else '0/20',CFT_mean=f"[{g.gaussian_mean_lo_pp:.1f}, {g.gaussian_mean_hi_pp:.1f}]"))
t4=pd.DataFrame(rows); t4.to_csv(O+'table4_conformal_cft.csv',index=False)
# A1
m=pd.read_csv(R+'s10/P6_ext36_motive_20261015_v4.csv'); e=pd.read_csv(R+'results/episode_results.csv'); e=e[(e.tag=='main')&(e.est=='ascm')].set_index('ep')
gc=pd.read_csv(R+'s10/gunter_concordance_20261015.csv',keep_default_na=False).drop_duplicates('ep').set_index('ep')
word={'pro':'procyclical','ctr':'countercyclical','dbt':'debt-driven','def':'deficit-driven','oth':'other-tax offset','spn':'spending offset','not covered':'not covered'}
m['gunter_class']=m.ep.map(gc.gunter).map(word)
def rule(ep):
    if ep in ('EE2009Q3','IL2013Q2','IS2010Q1'): return 'b*'
    if ep=='DE1983Q3': return 'x*'
    if ep=='GR2016Q2': return '?'
    return gc.g_ab[ep]
m['rule_class']=m.ep.map(rule)
m['Gap']=m.ep.map(e.mean_gap)
m['Country']=m.ep.str[:2]; m['Quarter']=m.ep.map(q)
a1=m[['Country','Quarter','class','gunter_class','rule_class','verif','Gap','source']].rename(columns={'class':'Original_class','gunter_class':'Gunter_class','rule_class':'Rule_class','verif':'Verification','source':'Source'})
a1['Gap']=a1.Gap.round(2); a1=a1.sort_values(['Country','Quarter']); a1.to_csv(O+'tableA1_extended_motives.csv',index=False)
a2=pd.DataFrame([
 ('Original coding (D7, fixed before estimation)','8 / 22','−5.22','.028'),
 ('Original, (a/b) → a','','−5.24','.012'),('Original, (a/b) → b','','−5.14','.034'),
 ('Original, c → b','','−4.83','.013'),('Original, c → a','','−3.92','.040'),
 ('Original, undetermined → b','','−3.03','.082'),('Original, undetermined → a','','−3.92','.013'),
 ('Original, verification "good" only','','−6.01','.009'),('Original, DE2007 and LU2015 → b','','−4.55','.031'),
 ('Gunter et al. (2021) classes only','6 / 18','−2.24','.245'),
 ('Gunter classes where covered, original coding elsewhere','7 / 23','−3.05','.134'),
 ('Original coding, dropping episodes where Gunter et al. disagree','5 / 15','−7.09','.021'),
 ('Gunter rule incl. our coding for uncovered episodes','6 / 23','−3.35','.109'),
 ('Gunter only; DE1993 → b','6 / 19','−2.09','.243'),('Gunter only; FR1982 excluded','5 / 18','−3.16','.116'),
 ('Gunter only; both changes','5 / 19','−3.03','.119'),('Gunter only; DE1993 → b, FR1982 → b','5 / 20','−3.29','.088')],columns=['Classification','n(a) / n(b)','Difference (pp)','p'])
a2.to_csv(O+'tableA2_motive_sensitivity.csv',index=False)
def tex(df,cols,align,cap,lab,note,fmt,small=False):
    L=[r'\begin{table}[htbp]\centering'+(r'\small' if small else ''),r'\caption{'+cap+r'}\label{'+lab+'}',r'\begin{tabular}{'+align+'}',r'\toprule',' & '.join(cols)+r' \\',r'\midrule']
    for _,r in df.iterrows(): L.append(' & '.join(fmt(r))+r' \\')
    L+=[r'\bottomrule',r'\end{tabular}',r'\par\smallskip\parbox{0.95\textwidth}{\footnotesize '+note+'}',r'\end{table}']; return '\n'.join(L)
def fx(x): return str(x).replace('−','$-$').replace('→',r'$\to$').replace('&',r'\&')
open(O+'table4_conformal_cft.tex','w').write(tex(t4,['Country','Quarter','ASCM $p(0)$','ASCM 95\\% set','SCM $p(0)$','SCM 95\\% set','CFT quarters excl. 0','CFT mean-gap interval'],'llrcrccc',
 'Conformal and prediction intervals (percentage points)','tab:intervals',r'Notes: Conformal sets use the $q=1$ statistic on a grid from $-30$ to $+20$ pp; $\dagger$ = the set reaches the grid edge, so it is not informative. CFT = scpi prediction intervals (Gaussian, one-sided 2.5\%): number of the 20 post-treatment quarters whose interval excludes zero (sign in parentheses) and the interval for the mean gap.',
 lambda r:[r.Country,r.Quarter,f"{r.ASCM_p0:.2f}",fx(r.ASCM_CI),f"{r.SCM_p0:.2f}",fx(r.SCM_CI),fx(r.CFT_n),fx(r.CFT_mean)],True))
open(O+'tableA2_motive_sensitivity.tex','w').write(tex(a2,['Classification','$n_a$ / $n_b$','Diff. (pp)','$p$'],'lrrr','Motive comparison: sensitivity to the definition (appendix)','tab:motive_sens',r'Notes: Difference in mean ASCM gaps between (b) and (a) episodes, weighted within era strata (2010--13 versus other); stratified permutation $p$-value, 5,000 draws. Rows are exploratory. Counts for the original-coding rows other than the first are not shown here.',
 lambda r:[fx(r['Classification']),fx(r['n(a) / n(b)']),fx(r['Difference (pp)']),fx(r['p'])]))
open(O+'tableA1_extended_motives.tex','w').write(tex(a1.drop(columns=['Source']),['Country','Quarter','Original','Gunter class','Rule','Verif.','Gap (pp)'],'llllllr','Extended sample: motive classes of VAT increases (appendix)','tab:motive_ext',r'Notes: Original = our coding fixed before estimation (a: paired with a cut in another tax; b: stand-alone consolidation; c: other; a\_b: mixed; ?: undetermined). Gunter class = classification in Gunter et al. (2021, Table 1) where the episode is covered. Rule = class under the Gunter rule (x = excluded; * = coded by us under the same rule for episodes outside their sample, DE1983 following Riera-Crichton et al. (2016); ? = undetermined). Verif. = verification level of our sources. Sources are listed in the replication files.',
 lambda r:[r.Country,r.Quarter,fx(r.Original_class),fx(r.Gunter_class),fx(r.Rule_class),r.Verification,f"{r.Gap:.2f}"],True))
print(t4.to_string()); print(a1.drop(columns='Source').to_string()); print(len(a1), a1.Rule_class.value_counts(dropna=False).to_dict())
