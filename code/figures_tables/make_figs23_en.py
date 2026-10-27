"""P6: English Figures 2 and 3 (proposal; not in the manuscript). Inputs: stage4/out/res/*__main.pkl, perm_draws npz, episode_results.csv, s10/gunter rule labels (hard-coded from the concordance, same as table 1)."""
import numpy as np, pandas as pd, pickle, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=os.environ.get('P6_STAGE4_OUT','results')+'/'; O=os.path.dirname(os.path.abspath(__file__))+'/'
order=['DE2007Q1','GB1979Q2','GB1991Q2','GB2011Q1','HU2012Q1','JP1997Q2','JP2014Q2','LU2015Q1','NL2012Q4','NZ2010Q4','SI2013Q3','FR1977Q1']
nm={'DE':'Germany','FR':'France','GB':'UK','HU':'Hungary','JP':'Japan','LU':'Luxembourg','NL':'Netherlands','NZ':'New Zealand','SI':'Slovenia'}
BL='#1f4e79'; GR='#b0b0b0'
fig,axs=plt.subplots(3,4,figsize=(10,6.6),dpi=200,sharex=True)
for ax,ep in zip(axs.ravel(),order):
    r=pickle.load(open(R+f'res/{ep}__main.pkl','rb'))['res']['ascm']
    for k,v in r['placebo'].items(): ax.plot(range(20),v['gap_path'],color=GR,lw=.6,alpha=.8)
    ax.plot(range(20),r['gap_path'],color=BL,lw=2); ax.axhline(0,color='#555',lw=.6)
    ax.set_title(f"{nm[ep[:2]]} {ep[2:6]}Q{ep[-1]}  (p = {r['p_ratio']:.2f})",fontsize=8.5); ax.tick_params(labelsize=7)
    lim=max(np.percentile(np.abs(np.concatenate([v['gap_path'] for v in r['placebo'].values()])),97),np.abs(r['gap_path']).max())*1.08; ax.set_ylim(-lim,lim)
    ax.spines[['top','right']].set_visible(False)
for ax in axs[-1]: ax.set_xlabel('Quarters since change',fontsize=8)
for ax in axs[:,0]: ax.set_ylabel('Gap (pp)',fontsize=8)
fig.suptitle('Treated gap (blue) and placebo gaps for donor countries (grey), ASCM',fontsize=10)
fig.tight_layout(rect=[0,0,1,.96]); fig.savefig(O+'fig2_episode_gaps.png')
# Figure 3
e=pd.read_csv(R+'episode_results.csv'); e=e[(e.tag=='main')&(e.est=='ascm')].set_index('ep')
z=np.load(R+'perm_draws_core_increases_ascm_meangap.npz'); d=z['draws']; obs=float(z['observed'])
gun={'DE2007Q1':'b','GB1979Q2':'a','GB1991Q2':'a','GB2011Q1':'b','HU2012Q1':'b','JP1997Q2':'b','JP2014Q2':'b','NL2012Q4':'b','NZ2010Q4':'a','SI2013Q3':'b'}
fig,(a1,a2)=plt.subplots(1,2,figsize=(10,3.9),dpi=200,gridspec_kw={'width_ratios':[1,1.15]})
a1.hist(d,bins=60,color='#cfd8e3',edgecolor='none'); a1.axvline(obs,color=BL,lw=2); 
lo,hi=np.percentile(d,[2.5,97.5]); a1.axvspan(lo,hi,color='none',ec='#888',ls=':')
a1.set_xlabel('Mean ASCM gap over 11 increases (pp)'); a1.set_ylabel('Permutation draws'); a1.set_title('Aggregate: observed vs permutation distribution',fontsize=9)
a1.text(obs,a1.get_ylim()[1]*.93,f' observed {obs:.2f}',color=BL,fontsize=8); a1.spines[['top','right']].set_visible(False)
era=lambda ep:2010<=int(ep[2:6])<=2013
xs={'a':0,'b':1}
for m in 'ab':
    items=sorted([(e.loc[ep,'mean_gap'],ep) for ep,mm in gun.items() if mm==m])
    for i,(y,ep) in enumerate(items):
        x=xs[m]-.3+.6*i/max(len(items)-1,1)
        a2.scatter(x,y,color='#c0504d' if era(ep) else BL,s=34,zorder=3); a2.annotate(ep[:2]+ep[4:6],(x,y),fontsize=6.5,xytext=(0,7),textcoords='offset points',ha='center')
for m in 'ab':
    v=[e.loc[ep,'mean_gap'] for ep,mm in gun.items() if mm==m]; a2.hlines(np.mean(v),xs[m]-.22,xs[m]+.22,color='k',lw=2)
a2.axhline(0,color='#555',lw=.6); a2.set_xticks([0,1]); a2.set_xticklabels(['(a) offset by another tax\n(n = 3)','(b) inherited deficit/debt\n(n = 7)'],fontsize=8)
a2.set_xlim(-.6,1.6); a2.set_ylabel('Mean ASCM gap (pp)'); a2.set_title('Core episodes by motive (Gunter et al. rule)',fontsize=9)
a2.scatter([],[],color='#c0504d',s=34,label='2010–13'); a2.scatter([],[],color=BL,s=34,label='other years'); a2.legend(frameon=False,fontsize=7.5,loc='upper right'); a2.spines[['top','right']].set_visible(False)
fig.tight_layout(); fig.savefig(O+'fig3_aggregate_motive.png'); print(obs,lo,hi)
