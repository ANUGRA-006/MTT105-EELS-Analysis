"""Interactive views of existing arrays; no new scientific processing."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_access import WINDOWS,composite

INK='#18394e';TEAL='#007f8b';PLUM='#b12e79';ORANGE='#b76822'
COLOURS={'pristine':TEAL,'discharged':'#bd5a20','charged':'#8c3986'}
PLOT_CONFIG={'displaylogo':False,'scrollZoom':False,'responsive':True,
             'toImageButtonOptions':{'format':'png','scale':2},
             'modeBarButtonsToRemove':['lasso2d','select2d']}


def style(fig,height=430):
    fig.update_layout(template='plotly_white',height=height,
        font=dict(family='Arial, sans-serif',size=13,color=INK),
        margin=dict(l=60,r=30,t=42,b=55),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='white',
        hovermode='x unified',hoverlabel=dict(bgcolor='white',font_size=12),
        legend=dict(orientation='h',y=-.19,x=0),uirevision='keep-view')
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor='#d7e1e6',ticks='outside')
    fig.update_yaxes(gridcolor='#edf1f3',zerolinecolor='#a8b6c0',linecolor='#d7e1e6')
    return fig


def spectrum(s,region='interior',view='Full core-loss'):
    e=s.energy;y=s.arrays[f'{region}_O_mean']/1000
    ranges={'Full core-loss':(505,700),'O-K detail':(525,565),'Mn-L₂,₃ detail':(633,682)}
    fig=go.Figure(go.Scatter(x=e,y=y,mode='lines',line=dict(color=INK,width=2),
        name='Measured ROI mean',hovertemplate='%{y:.4f} ×10³ units/channel<extra></extra>'))
    for lo,hi,label,colour in [(529,560,'O-K',TEAL),(638,651,'Mn-L₃',PLUM),(651,665,'Mn-L₂',PLUM)]:
        fig.add_vrect(x0=lo,x1=hi,fillcolor=colour,opacity=.07,line_width=0)
        if ranges[view][0]<=lo<=ranges[view][1]:
            fig.add_annotation(x=(lo+hi)/2,y=1.02,xref='x',yref='paper',text=label,showarrow=False,
                               font=dict(color=colour,size=13))
    mask=(e>=ranges[view][0])&(e<ranges[view][1]);lo=float(y[mask].min());hi=float(y[mask].max())
    fig.update_xaxes(title='Calibrated energy loss (eV)',range=ranges[view])
    fig.update_yaxes(title='Mean intensity (10³ recorded units/channel)',range=[max(0,lo-(hi-lo)*.12),hi+(hi-lo)*.17])
    return style(fig)


def background(s,edge,region):
    a=s.arrays;e=s.energy;w=WINDOWS[edge]
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.12,
        subplot_titles=('Measured spectrum and stored power-law fit','Signed background-subtracted signal'))
    for values,label,col,dash,row in [
        (a[f'{region}_{edge}_mean'],'Experimental mean',INK,'solid',1),
        (a[f'{region}_{edge}_bg'],'Verified power law',ORANGE,'dash',1),
        (a[f'{region}_{edge}_residual'],'Measured − background',TEAL if edge=='O' else PLUM,'solid',2)]:
        fig.add_trace(go.Scatter(x=e,y=values/1000,mode='lines',name=label,
            line=dict(color=col,width=1.8,dash=dash),hovertemplate='%{y:.4f} ×10³ units/channel<extra>%{fullData.name}</extra>'),row=row,col=1)
    for row in [1,2]:
        for band,colour in [(w['pre'],'#74ad96'),(w['hold'],'#e7bb5a')]:
            fig.add_vrect(x0=band[0],x1=band[1],fillcolor=colour,opacity=.22,line_width=0,row=row,col=1)
    fig.add_vrect(x0=w['band'][0],x1=w['band'][1],fillcolor=TEAL if edge=='O' else PLUM,opacity=.10,line_width=0,row=2,col=1)
    mask=(e>=w['view'][0])&(e<w['view'][1])
    for row in [1,2]:
        values=a[f'{region}_{edge}_residual'][mask]/1000 if row==2 else np.r_[a[f'{region}_{edge}_mean'][mask],a[f'{region}_{edge}_bg'][mask]]/1000
        low=float(values.min());high=float(values.max());pad=(high-low)*.12
        fig.update_yaxes(range=[low-pad,high+pad],title='10³ units/channel',row=row,col=1)
    fig.update_xaxes(range=w['view']);fig.update_xaxes(title='Calibrated energy loss (eV)',row=2,col=1)
    style(fig,535);fig.update_layout(legend=dict(y=-.14))
    return fig


def maps(s):
    a=s.arrays;ny,nx=a['bad_core'].shape;sx,sy=s.step
    x=np.arange(nx)*sx;y=np.arange(ny)*sy
    fig=make_subplots(rows=1,cols=3,horizontal_spacing=.11,
        subplot_titles=('O-K signed edge sum','Mn-L₂,₃ signed edge sum','O / Mn display composite'))
    for col,edge,cmap,cbar in [(1,'O','Viridis',.274),(2,'Mn','Magma',.646)]:
        valid=s.accepted(edge);z=np.where(valid,a[edge+'_intensity']/1000,np.nan)
        fig.add_trace(go.Heatmap(x=x,y=y,z=z,zsmooth=False,connectgaps=False,hoverongaps=False,
            colorscale=cmap,zmin=min(0,float(np.nanmin(z))),zmax=float(np.nanquantile(z,.995)),
            colorbar=dict(x=cbar,len=.80,thickness=9,title=dict(text='10³ units',side='top'),tickfont=dict(size=10)),
            hovertemplate=f'{edge}: %{{z:.3f}} ×10³ units<br>x=%{{x:.2f}} nm; y=%{{y:.2f}} nm<extra></extra>'),row=1,col=col)
        bad=a['bad_core'];excluded=~valid
        statuses=np.where(bad,1.,np.where(excluded,2.,np.nan))
        labels=np.where(bad,'Artefact / calibration exclusion','Background-fit rejection')
        fig.add_trace(go.Heatmap(x=x,y=y,z=statuses,zmin=1,zmax=2,zsmooth=False,hoverongaps=False,
            colorscale=[[0,'#a6a6a6'],[.49,'#a6a6a6'],[.5,'#bf2b3d'],[1,'#bf2b3d']],showscale=False,
            text=labels,hovertemplate='%{text}<br>x=%{x:.2f} nm; y=%{y:.2f} nm<extra></extra>'),row=1,col=col)
    rgb,scales,both=composite(s)
    status=np.where(a['bad_core'],'Artefact / calibration exclusion',np.where(both,'Both edge fits accepted','Background-fit rejection'))
    fig.add_trace(go.Image(z=rgb,x0=0,y0=0,dx=sx,dy=sy,
        text=status,hovertemplate='%{text}<br>x=%{x:.2f} nm; y=%{y:.2f} nm<extra></extra>'),row=1,col=3)
    for col in [1,2,3]:
        anchor='x' if col==1 else 'x'+str(col)
        fig.update_xaxes(title='x (nm)',range=[-.5*sx,(nx-.5)*sx],showgrid=False,row=1,col=col)
        fig.update_yaxes(title='y (nm)',range=[(ny-.5)*sy,-.5*sy],scaleanchor=anchor,
                         scaleratio=1,showgrid=False,row=1,col=col)
        x0=nx*sx*.06;y0=ny*sy*.91
        fig.add_shape(type='line',x0=x0,x1=x0+10,y0=y0,y1=y0,line=dict(color='#18394e',width=7),row=1,col=col)
        fig.add_shape(type='line',x0=x0,x1=x0+10,y0=y0,y1=y0,line=dict(color='white',width=4),row=1,col=col)
        fig.add_annotation(x=x0+5,y=y0-2.8,text='10 nm',showarrow=False,font=dict(color='white',size=10),
                           bgcolor='rgba(0,0,0,.5)',borderpad=2,row=1,col=col)
    style(fig,430);fig.update_layout(hovermode='closest',margin=dict(l=45,r=10,t=45,b=48),showlegend=False)
    return fig,scales


def comparison(samples):
    fig=go.Figure();visible=[]
    fig.add_vrect(x0=529,x1=535,line_width=0,fillcolor=TEAL,opacity=.07)
    for key,s in samples.items():
        e=s.energy;y=s.arrays['interior_O_residual']
        y=y/y[(e>=529)&(e<560)].sum()  # Existing verified band-normalization convention.
        visible.extend(y[(e>=527)&(e<563)])
        dash={'pristine':'solid','discharged':'dash','charged':'dashdot'}[key]
        fig.add_trace(go.Scatter(x=e,y=y,mode='lines',name=s.label,
            line=dict(color=COLOURS[key],width=2.2,dash=dash),
            hovertemplate='%{y:.6f} a.u.<extra>%{fullData.name}</extra>'))
    hi=max(visible);lo=min(0,min(visible));pad=(hi-lo)*.10
    fig.update_xaxes(title='Calibrated energy loss (eV)',range=[527,563])
    fig.update_yaxes(title='Band-normalized signed intensity (a.u.)',range=[lo-pad,hi+pad])
    fig.add_annotation(x=532,y=1.02,xref='x',yref='paper',text='O-K pre-feature · 529–535 eV',showarrow=False,
                       font=dict(size=12,color=TEAL))
    return style(fig,410)
