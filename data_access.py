"""Read-only access to pinned, convergence-corrected experimental products.

No fitting, calibration, denoising, ROI construction or scientific pipeline imports.
"""
from pathlib import Path
from dataclasses import dataclass
import hashlib
import json
import numpy as np

APP = Path(__file__).resolve().parent
LABELS = {'pristine': 'Pristine U-NP', 'discharged': 'Discharged U-NP', 'charged': 'Charged U-NP'}
REGIONS = {'Projected interior': 'interior', 'Projected outer band': 'rim'}
WINDOWS = {'O': {'pre': (508.,520.), 'hold': (521.,525.), 'band': (529.,560.), 'view': (506.,565.)},
           'Mn': {'pre': (600.,625.), 'hold': (626.,633.), 'band': (637.,670.), 'view': (595.,700.)}}


class DataError(Exception):
    """An actionable missing, changed or invalid verified input."""


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_root():
    return APP


def manifest():
    try: return json.loads((APP/'source_manifest.json').read_text(encoding='utf-8'))['inputs']
    except (OSError, ValueError, KeyError) as exc:
        raise DataError('Dashboard source_manifest.json is missing or unreadable. Restore the dashboard files.') from exc


def fingerprint(root):
    """Check existence on every rerun; changed files invalidate Streamlit's cache."""
    records=[]
    for name in manifest():
        path=Path(root)/name
        if not path.is_file():
            raise DataError(f'Missing verified input: {path}\nRestore it from the convergence-corrected project. '
                            'No simulated or older-result fallback is used. See README.md.')
        stat=path.stat();records.append((name, stat.st_size, stat.st_mtime_ns))
    return tuple(records)


@dataclass(frozen=True)
class Sample:
    key: str
    arrays: dict
    metrics: dict

    @property
    def label(self): return LABELS[self.key]

    @property
    def energy(self): return self.arrays['energy_eV']

    @property
    def step(self): return self.metrics['quality']['step_x_nm'],self.metrics['quality']['step_y_nm']

    def accepted(self, edge):
        return self.arrays[edge+'_valid'] & ~self.arrays['bad_core']

    def roi(self, region): return self.metrics['white_lines'][region]


def load_results(root):
    root=Path(root)
    fingerprint(root)
    for name,digest in manifest().items():
        if sha(root/name)!=digest:
            raise DataError(f'Verified input changed: {root/name}\nThe dashboard refuses unverified results. '
                            'Restore the authoritative file; do not edit the expected checksum to bypass this check.')
    samples={}
    for key in LABELS:
        try:
            with np.load(root/f'results/data/{key}_final.npz',allow_pickle=False) as z:
                arrays={name:z[name].copy() for name in z.files}
            metrics=json.loads((root/f'results/data/{key}_metrics.json').read_text(encoding='utf-8'))
            sample=Sample(key,arrays,metrics)
            validate_sample(sample)
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            raise DataError(f'Invalid verified result for {LABELS[key]}: {exc}') from exc
        for a in arrays.values(): a.setflags(write=False)
        samples[key]=sample
    return samples


def validate_sample(s):
    a=s.arrays;e=s.energy
    assert e.ndim==1 and np.isfinite(e).all() and np.all(np.diff(e)>0), 'Invalid calibrated energy axis.'
    assert np.isclose(np.median(np.diff(e)),.1,rtol=1e-5), 'Unexpected energy dispersion.'
    assert all(np.isfinite(step) and step>0 for step in s.step), 'Invalid spatial sampling.'
    for edge in ['O','Mn']:
        valid=s.accepted(edge)
        assert valid.shape==a['bad_core'].shape and valid.any(), 'Invalid map mask.'
        assert np.all(a[edge+'_converged'][valid]&a[edge+'_numerically_validated'][valid]), 'Unvalidated accepted fit.'
        assert np.all(a[edge+'_empirical_valid'][valid]), 'Rejected fit in accepted map.'
        assert np.isfinite(a[edge+'_intensity'][valid]).all(), 'Nonfinite accepted map intensity.'
        assert int(valid.sum())==s.metrics['optimizer_counts'][edge]['map_accepted'], 'Map count changed.'
    for region in ['interior','rim']:
        roi=a['roi_'+region]
        assert int(roi.sum())==s.roi(region)['n'], 'ROI size changed.'
        assert not np.any(roi&~(s.accepted('O')&s.accepted('Mn'))), 'Excluded ROI pixel.'
        np.testing.assert_array_equal(a[region+'_O_mean'],a[region+'_Mn_mean'])
        for edge in ['O','Mn']:
            mean=a[f'{region}_{edge}_mean'];bg=a[f'{region}_{edge}_bg'];res=a[f'{region}_{edge}_residual']
            assert mean.shape==bg.shape==res.shape==e.shape
            np.testing.assert_allclose(mean-bg,res,rtol=1e-12,atol=1e-8)
        res=a[region+'_O_residual']
        fraction=res[(e>=529)&(e<535)].sum()/res[(e>=529)&(e<560)].sum()
        np.testing.assert_allclose(fraction,s.roi(region)['oxygen']['pre_fraction'],rtol=1e-12)


def composite(s):
    """The existing cyan/magenta 99th-percentile DISPLAY transform; signed inputs unchanged."""
    a=s.arrays;valid=s.accepted('O')&s.accepted('Mn')
    scales={el:float(np.quantile(a[el+'_intensity'][valid],.99)) for el in ['O','Mn']}
    o=np.clip(a['O_intensity']/scales['O'],0,1)
    mn=np.clip(a['Mn_intensity']/scales['Mn'],0,1)
    rgb=np.stack([mn,o,np.maximum(o,mn)],axis=-1)
    # Presentation overlays match the original figures; excluded values are never displayed as measurements.
    rgb[~valid&~a['bad_core']]=[.75,.17,.24]
    rgb[a['bad_core']]=[.65,.65,.65]
    return np.round(rgb*255).astype(np.uint8),scales,valid
