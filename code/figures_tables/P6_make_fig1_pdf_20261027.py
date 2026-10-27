import os
import pandas as pd
import matplotlib; matplotlib.use('Agg'); matplotlib.rcParams['pdf.fonttype']=42
import matplotlib.pyplot as plt
p=pd.read_csv(os.path.join(os.environ.get('P6_DATA','.'),'results','event_time_paths_ascm.csv'))
fig,ax=plt.subplots(figsize=(6.4,3.8),dpi=200)
ax.axhline(0,color='#888',lw=.8); ax.axvline(-0.5,color='#888',lw=.8,ls=':')
ax.plot(p.h,p.core_increases,color='#1f4e79',lw=2,marker='o',ms=3,label='Increases (11 episodes)')
ax.plot(p.h,p.core_cuts,color='#c0504d',lw=1.5,ls='--',marker='s',ms=3,label='Cut (1 episode: FR1977)')
ax.set_xlabel('Quarters since the rate change (0 = first quarter in effect)'); ax.set_ylabel('Mean ASCM gap, ln C − ln Y (pp)')
ax.set_xticks(range(0,20,2)); ax.legend(frameon=False,fontsize=8); ax.spines[['top','right']].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(os.environ.get('P6_OUT','.'),'fig1_event_time.pdf')); fig.savefig(os.path.join(os.environ.get('P6_OUT','.'),'fig1_event_time.png'),dpi=300)
print(p.core_increases.round(2).tolist()[:6], p.core_cuts.round(2).tolist()[-3:])
