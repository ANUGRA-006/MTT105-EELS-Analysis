# 4D Data Analysis Using HyperSpy: EELS

MTT-105 Electron Microscopy · Indian Institute of Technology Roorkee  
Department of Metallurgical and Materials Engineering · Prof. K. S. Suresh

The four dashboard sections display measured EELS spectra, corrected backgrounds, qualitative O/Mn edge-intensity maps, and a comparison of three untreated nanoparticle fields. Every bundled number comes from the convergence-corrected analysis. The app uses a small subset of the saved arrays and metrics with the original signed values, masks, energy axes, and spatial calibration. Display normalization and composite colors use the same conventions as the local dashboard. Enrollment numbers belong in the private academic materials.

## Run locally

Use Python 3.12. From the root of this directory:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the localhost address printed by Streamlit. After dependencies are installed, the application serves its data and plots locally. If a bundled file is missing or changed, restore it and restart the app. `source_manifest.json` records SHA-256 hashes for the bundled files and the authoritative source files used to make them.

## Publish manually on GitHub and Streamlit Community Cloud

1. Review this folder with the group and decide the repository and app visibility. Create a GitHub repository containing **this folder's contents only**, with `app.py` and `requirements.txt` at the repository root. Include `.streamlit/config.toml`, `.gitignore`, the other Python modules, `style.css`, `source_manifest.json`, and `results/data/`.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and authorize access to that repository. Choose **Create app**, select the repository and branch, and enter `app.py` as the entrypoint.
3. In **Advanced settings**, select Python **3.12**. The app needs no secrets. Choose **Deploy**, wait for installation, then open the resulting URL.
4. Smoke-test all four sections, including the particle and ROI selectors, and verify that the group panel displays names only before sharing the URL.

For a command-line upload in step 1, create an empty repository on GitHub first. Open a terminal in this folder, replace the example URL with the repository's HTTPS URL, and run these commands yourself:

```sh
git init -b main
git add .
git status --short
git commit -m "Prepare MTT-105 EELS dashboard"
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

Review the staged file list before committing. It should contain the application, configuration, README, requirements, and the six files under `results/data/`.

[Streamlit deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [Dependency requirements](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

## Experimental data attribution

Tang, Zhichu, Chen, Wenxiang, Yin, Kaijun, Busch, Robert, Hou, Hanyu, Lin, Oliver, Lyu, Zhiheng, Zhang, Cheng, Yang, Hong, Zuo, Jian-Min, and Chen, Qian (2024). *Nanoscale Stacking Fault Engineering and Mapping in Spinel Oxides for Reversible Multivalent Ion Insertion*. Version 1, Illinois Data Bank, University of Illinois Urbana-Champaign. [DOI 10.13012/B2IDB-8188066_V1](https://doi.org/10.13012/B2IDB-8188066_V1) · [Dataset record](https://databank.illinois.edu/datasets/IDB-8188066) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The bundled arrays are processed products of the dataset's EELS subset. The project aligned energies, subtracted fitted backgrounds, selected accepted pixels and ROIs, and formed edge sums and descriptors. The package contains these derived display values. The source DM4 files and course lecture materials are held in the academic project.
