"""P6: English Table 6 (robustness, core increases, mean gap in pp). Proposal; not in the manuscript. Inputs: stage4/out/spec_curve_core_increases.csv, spec_extra_core_increases.csv, stage4/s5/stage5_summary.csv"""
import pandas as pd, numpy as np, os
R=os.environ.get('P6_STAGE4','results')+'/'; O=os.path.dirname(os.path.abspath(__file__))+'/'
s5=pd.read_csv(R+'s5/stage5_summary.csv'); s5=s5[(s5.outcome.isin(['mean_gap','donut2']))]
lab={'main':'Baseline (40 pre / 20 post quarters)','donut(drop first 2 post quarters)':'Donut: drop first two post quarters','lead1(tax date 1q earlier; mean over t0..t0+19)':'Anticipation: treatment date one quarter earlier',
 'lead2(tax date 2q earlier; mean over t0..t0+19)':'Anticipation: treatment date two quarters earlier','HK+TW added to donors':'Hong Kong and Taiwan added to donors','IFE (two-way FE + r factors, gsynth-type)':'Interactive fixed effects (own implementation)',
 'Eurostat 2026-vintage series for 23 EU/EEA countries':'Eurostat 2026 vintage for 23 EU/EEA countries'}
rows=[]
for k,l in lab.items():
    r={'Panel':'A. Checks (two-sided permutation p)','Check':l}
    for est in ('ascm','scm'):
        for st,nm in (('core_increases','All'),('core_inc_ex_JP2014','exJP'),('core_inc_ex_euro','exEuro')):
            x=s5[(s5.check==k)&(s5.est==('ife' if k.startswith('IFE') and est=='ascm' else est))&(s5.set==st)]
            r[f'{est}_{nm}']=f"{x.estimate.iloc[0]:.2f} ({x.perm_p_two.iloc[0]:.2f})" if len(x) else ''
    rows.append(r)
t6a=pd.DataFrame(rows)
sc=pd.read_csv(R+'out/spec_curve_core_increases.csv',encoding='utf-8-sig')
slab={'main':'Baseline','nobreakrule':'No break rule for donors','pre60':'60 pre-treatment quarters','pre80':'80 pre-treatment quarters (7 episodes)','prefull':'Full pre-treatment history','restricted':'Donors restricted to the pre-window (10 episodes)'}
rb=[]
for k,l in slab.items():
    a=sc[(sc.tag==k)&(sc.est=='ascm')].iloc[0]; s=sc[(sc.tag==k)&(sc.est=='scm')].iloc[0]
    rb.append({'Panel':'B. Specification (one-sided p, H1: gap<0)','Check':l,'n':int(a.n),'ASCM':f"{a.estimate:.2f} ({a.perm_p:.2f})",'SCM':f"{s.estimate:.2f} ({s.perm_p:.2f})"})
t6b=pd.DataFrame(rb)
ex=pd.read_csv(R+'out/spec_extra_core_increases.csv',encoding='utf-8-sig')
elab={'all 11':'All 11 increases','drop euro-crisis HU/NL/SI':'Drop euro-crisis episodes (HU, NL, SI)','drop JP2014':'Drop JP2014','drop JP2014+euro':'Drop JP2014 and euro-crisis episodes','GB1979Q3 in place of Q2':'GB1979 dated 1979Q3 instead of Q2'}
rc=[]
for k,l in elab.items():
    a=ex[(ex.cell==k)&(ex.est=='ascm')].iloc[0]; s=ex[(ex.cell==k)&(ex.est=='scm')].iloc[0]
    rc.append({'Panel':'C. Sample (two-sided permutation p)','Check':l,'n':int(a.n),'ASCM':f"{a.estimate:.2f} ({a.perm_p_two:.2f})",'SCM':f"{s.estimate:.2f} ({s.perm_p_two:.2f})"})
t6c=pd.DataFrame(rc)
t6a.to_csv(O+'table6A_checks.csv',index=False); t6b.to_csv(O+'table6B_specs.csv',index=False); t6c.to_csv(O+'table6C_samples.csv',index=False)
L=[r'\begin{table}[htbp]\centering\small',r'\caption{Robustness of the average effect of tax increases (11 core episodes; mean gap in pp)}\label{tab:robust}']
L+=[r'\begin{tabular}{lcccccc}',r'\toprule',r' & \multicolumn{3}{c}{ASCM} & \multicolumn{3}{c}{SCM} \\',r'\cmidrule(lr){2-4}\cmidrule(lr){5-7}',r'Check & All 11 & Excl.\ JP2014 & Excl.\ euro crisis & All 11 & Excl.\ JP2014 & Excl.\ euro crisis \\',r'\midrule',r'\multicolumn{7}{l}{\emph{A. Checks (two-sided permutation $p$ in parentheses)}} \\']
for _,r in t6a.iterrows():
    L.append(' & '.join([r.Check]+[str(r[c]).replace('-','$-$') if r[c]!='' else '--' for c in ['ascm_All','ascm_exJP','ascm_exEuro','scm_All','scm_exJP','scm_exEuro']])+r' \\')
L+=[r'\midrule',r'\multicolumn{7}{l}{\emph{B. Specification (one-sided $p$ for gap $<0$ in parentheses)}} \\']
for _,r in t6b.iterrows(): L.append(f"{r.Check} ($n$={r.n}) & \\multicolumn{{3}}{{c}}{{{r.ASCM.replace('-','$-$')}}} & \\multicolumn{{3}}{{c}}{{{r.SCM.replace('-','$-$')}}} \\\\")
L+=[r'\midrule',r'\multicolumn{7}{l}{\emph{C. Sample (two-sided permutation $p$ in parentheses)}} \\']
for _,r in t6c.iterrows(): L.append(f"{r.Check} ($n$={r.n}) & \\multicolumn{{3}}{{c}}{{{r.ASCM.replace('-','$-$')}}} & \\multicolumn{{3}}{{c}}{{{r.SCM.replace('-','$-$')}}} \\\\")
L+=[r'\bottomrule',r'\end{tabular}',r'\par\smallskip\parbox{0.95\textwidth}{\footnotesize Notes: Equal-weight mean of episode gaps; permutation reference sets as in the baseline. Panel B reports one-sided $p$-values and is therefore not comparable with panels A and C. IFE and Eurostat rows are ASCM only. The IFE estimator is our own implementation, not gsynth or fect. Individual-episode estimates move by 1--2 pp with the data vintage (Eurostat row).}',r'\end{table}']
open(O+'table6_robustness.tex','w').write('\n'.join(L))
print(t6a.to_string()); print(t6b.to_string()); print(t6c.to_string())
