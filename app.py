"""Read-only local presentation of the authoritative HyperSpy/eXSpy EELS results."""
from pathlib import Path
import html
import streamlit as st
from data_access import APP,LABELS,REGIONS,WINDOWS,DataError,source_root,fingerprint,load_results
from charts import spectrum,background,maps,comparison,PLOT_CONFIG

st.set_page_config(page_title='MTT-105 | Experimental EELS',page_icon='🔬',layout='wide',
                   initial_sidebar_state='expanded',menu_items={'About':'MTT-105 · IIT Roorkee. A local presentation of verified experimental EELS results.'})
st.markdown((APP/'style.css').read_text(encoding='utf-8'),unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def cached_results(root,signature):
    return load_results(root)


SECTIONS=['01  Experimental spectrum','02  Background subtraction','03  Elemental mapping','04  Comparative analysis']
with st.sidebar:
    st.markdown('<div class="brand-kicker">IIT ROORKEE</div><div class="brand-title">Microscopy lab</div>'
                '<div class="brand-subtitle">MTT-105 Electron Microscopy</div>',unsafe_allow_html=True)
    st.divider()
    section=st.radio('Explore the results',SECTIONS,key='section')
    if section!=SECTIONS[3]:
        selected=st.selectbox('Experimental particle',list(LABELS),format_func=LABELS.get,key='sample')
    else:
        selected='pristine'
        st.caption('Comparison uses all three particles and their verified projected-interior spectra.')
    if section in SECTIONS[:2]:
        region_label=st.selectbox('Verified spectral region',list(REGIONS),key='region')
        region=REGIONS[region_label]
    else:region='interior'
    st.divider()
    st.markdown('**Instructor**  \nProf. K. S. Suresh')
    with st.expander('Our Group · Third-Year B.Tech'):
        for name in ('Anugra Chahande', 'Sanjosh Kumar', 'Baljot Singh', 'Vivek Parihar'):
            st.markdown(f'**{name}**')
        st.caption('Metallurgical and Materials Engineering')
        st.caption('Indian Institute of Technology Roorkee')
    st.markdown('<div class="sidebar-note">LOCAL SHOWCASE<br>Precomputed experimental results<br>HyperSpy 2.5.0 · eXSpy 0.3.2</div>',unsafe_allow_html=True)

st.markdown('<div class="eyebrow">EXPERIMENTAL CHARACTERIZATION · IIT ROORKEE</div>'
            '<h1>4D Data Analysis Using HyperSpy: EELS</h1>'
            '<p class="hero-subtitle">From measured energy losses to spatial O/Mn signals in spinel oxide nanoparticles.</p>',
            unsafe_allow_html=True)
st.markdown('<div class="status-strip"><span>● Verified experimental inputs</span>'
            '<span>3 untreated nanoparticle fields</span><span>Precomputed · local · reproducible</span></div>',unsafe_allow_html=True)
try:
    source=source_root()
    samples=cached_results(str(source),fingerprint(source))
except DataError as exc:
    st.error('Verified EELS data could not be loaded.')
    st.code(str(exc),language=None)
    st.info('Restore the bundled files from the deployment repository and restart the app.')
    st.stop()
s=samples[selected]


def panel_heading(kicker,title,description):
    st.markdown(f'<div class="section-kicker">{html.escape(kicker)}</div><h2>{html.escape(title)}</h2>'
                f'<p class="section-description">{html.escape(description)}</p>',unsafe_allow_html=True)


def plot(fig,key):
    st.plotly_chart(fig,width='stretch',theme=None,config=PLOT_CONFIG,key=key)


if section==SECTIONS[0]:
    panel_heading('01 / EXPERIMENTAL SPECTRUM','A spectrum at every probe position',
        'Core-electron excitations produce element-related edges. Hover to inspect the actual measured ROI mean.')
    col,detail=st.columns([3,2])
    with col:
        st.markdown(f'**{s.label}** · {"projected interior" if region=="interior" else "projected outer band"} · '
                    f'{s.roi(region)["n"]} accepted pixels')
    with detail:
        view=st.selectbox('Energy view',['Full core-loss','O-K detail','Mn-L₂,₃ detail'],key='energy_view',label_visibility='collapsed')
    plot(spectrum(s,region,view),'spectrum')
    st.caption('PRECOMPUTED · Calibrated experimental mean before project background subtraction. '
               'Shaded regions identify the established O-K and Mn-L₃/L₂ analysis regions, not fitted ionization thresholds. '
               'Recorded units are not calibrated electron counts; acquisition corrections were already present in the supplied data.')
    a,b=st.columns(2)
    with a:
        st.markdown('**Why EELS?**  \nAn electron transfers energy to the specimen. Exciting O 1s or Mn 2p electrons '
                    'produces the O-K or Mn-L₂,₃ edges. Their near-edge structure can respond to local electronic states and bonding.')
    with b:
        st.markdown('**What does “4D” mean here?**  \nThese are EELS spectrum images, **I(x, y, E)**: two scan axes and one energy axis. '
                    'Conventional diffraction 4D-STEM records **I(x, y, kₓ, kᵧ)**. The assigned title is retained with this distinction.')

elif section==SECTIONS[1]:
    panel_heading('02 / BACKGROUND SUBTRACTION','Separate an edge from the falling background',
        'Fit before the target edge, extrapolate beneath it, then subtract. These are stored, verified fits; no optimizer runs in the dashboard.')
    edge=st.radio('Elemental edge',['O','Mn'],format_func=lambda x:'O-K' if x=='O' else 'Mn-L₂,₃',horizontal=True,key='edge')
    w=WINDOWS[edge];q=s.roi(region)
    c1,c2,c3=st.columns(3)
    c1.metric('Verified ROI',f'{q["n"]} pixels')
    c2.metric('Relative fitting RMSE',f'{q[edge+"_fit_relative_rmse"]:.4f}')
    c3.metric('Held-out relative bias',f'{q[edge+"_holdout_bias"]:+.4f}')
    plot(background(s,edge,region),'background')
    st.markdown(f'<div class="window-row"><span class="window-fit">Fit: {w["pre"][0]:g}–{w["pre"][1]:g} eV</span>'
                f'<span class="window-check">Held-out check: {w["hold"][0]:g}–{w["hold"][1]:g} eV</span>'
                f'<span class="window-edge">Integration: {w["band"][0]:g}–{w["band"][1]:g} eV</span></div>',unsafe_allow_html=True)
    st.caption('PRECOMPUTED · B(E) = c(E/E₀)⁻ʳ, equivalent to AE⁻ʳ. Pre-edge bounds select the original rounded-inclusive '
               'HyperSpy channels; integrations and held-out checks are half-open energy intervals. Signed residuals, including negatives, are preserved.')
    st.info('A good pre-edge fit supports this local background estimate; it does not prove an exact continuum beneath the edge. '
            + ('The Mn residual also contains a post-edge continuum and is not a continuum-subtracted white-line spectrum.' if edge=='Mn' else
               'Convergence, independent numerical agreement and empirical residual checks were required in the full analysis.'))

elif section==SECTIONS[2]:
    panel_heading('03 / ELEMENTAL MAPPING','Locate the O and Mn edge signals',
        'Validated signed edge sums reveal projected spatial signals. Hover a pixel to see its value or exclusion reason.')
    c1,c2,c3=st.columns(3)
    c1.metric('O-K accepted map pixels',f'{int(s.accepted("O").sum())} / {s.arrays["bad_core"].size}')
    c2.metric('Mn-L₂,₃ accepted map pixels',f'{int(s.accepted("Mn").sum())} / {s.arrays["bad_core"].size}')
    c3.metric('Spatial sampling',f'{s.step[0]:.4f} nm',delta=None)
    fig,scales=maps(s);plot(fig,'maps')
    st.markdown('<div class="map-legend"><span><i style="background:#00ffff"></i> O · cyan</span>'
                '<span><i style="background:#ff00ff"></i> Mn · magenta</span>'
                '<span><i style="background:#a6a6a6"></i> Artefact / calibration exclusion</span>'
                '<span><i style="background:#bf2b3d"></i> Background-fit rejection</span></div>',unsafe_allow_html=True)
    st.caption('PRECOMPUTED · O-K: 529–560 eV; Mn-L₂,₃: 637–670 eV. Corrected fit masks are preserved. '
               'Excluded pixels are unavailable data, not elemental absence. Scalar maps retain signed negative values; '
               'their upper colour limits use the established 99.5th-percentile display convention. Scale bars: 10 nm; sampling is not measured spatial resolution.')
    st.info('These are qualitative edge-intensity maps, not elemental concentration maps. Projected co-location is consistent with '
            'O/Mn-containing particles; it does not determine O:Mn stoichiometry or Mn oxidation state.')
    with st.expander('Composite display and preserved masks'):
        st.write('The composite maps O to cyan and Mn to magenta. Each channel is independently scaled to its 99th percentile '
                 'among pixels accepted for both edges, with display-only clipping to [0,1]. Original signed arrays remain unchanged. '
                 'Pale/white overlap does not imply equal atomic concentrations.')
        st.write(f'Display upper scales: O {scales["O"]:,.3f}; Mn {scales["Mn"]:,.3f} recorded edge-sum units.')
        st.write('Only explicitly converged, independently validated and empirically accepted fits enter maps. '
                 'Artefact/calibration exclusions take precedence over background-fit exclusions.')

else:
    panel_heading('04 / COMPARATIVE ANALYSIS','Compare O-K near-edge shape, cautiously',
        'Three separately acquired untreated particles. Stored projected-interior spectra are normalized by each signed 529–560 eV O-K edge sum.')
    for col,(key,item) in zip(st.columns(3),samples.items()):
        with col:
            q=item.roi('interior')
            st.metric(item.label,f'{q["oxygen"]["pre_fraction"]:.6f}')
            st.caption(f'O-K pre-feature fraction · {q["n"]} interior pixels')
    plot(comparison(samples),'comparison')
    st.caption('PRECOMPUTED · Pre-feature fraction = signed area in 529–535 eV / signed area in 529–560 eV. '
               'The shaded interval marks the pre-feature window. Values are spectral descriptors, not oxygen concentrations.')
    a,b=st.columns(2)
    with a:
        st.markdown('**Experimental observation**  \nThe pristine interior has a larger O-K pre-feature fraction than the '
                    'discharged and charged interiors under the stated processing. Pristine separation persists across the '
                    'tested background/calibration and ROI choices. Charged/discharged background/calibration ranges overlap.')
    with b:
        st.markdown('**Limits on interpretation**  \nDifferent particles, acquisition geometry/stage tilt, uncertain thickness '
                    'and prior acquisition processing prevent a statistically established cycling-effect claim. '
                    'O-K fine structure is sensitive to electronic states and bonding, without a unique chemical assignment here.')
    st.info('We report observed spectral differences. We do not infer absolute Mn valence, quantitative composition or a causal cycling effect. '
            'Exploratory Mn white-line ratios depend on continuum subtraction; PCA remains supplementary in the full notebook.')

with st.expander('Provenance, validation and course context'):
    st.markdown('This app displays SHA-256 checked spectra, maps, and descriptors exported from the corrected analysis. '
                'Calibration and fitting were performed in the full notebook.')
    st.markdown('**Dataset**  \nTang et al. (2024), *Nanoscale Stacking Fault Engineering and Mapping in Spinel Oxides for '
                'Reversible Multivalent Ion Insertion*, Version 1, Illinois Data Bank. '
                '[DOI 10.13012/B2IDB-8188066_V1](https://doi.org/10.13012/B2IDB-8188066_V1). '
                '[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Full citation in the repository README.')
    st.markdown('**Course**  \nMTT-105 Electron Microscopy, Indian Institute of Technology Roorkee. '
                'Prof. K. S. Suresh’s Lecture 3, Slide 26, motivates the workflow.')
st.markdown('<div class="page-footer">MTT-105 · IIT ROORKEE &nbsp; / &nbsp; Presentation interface for verified HyperSpy/eXSpy results</div>',unsafe_allow_html=True)
