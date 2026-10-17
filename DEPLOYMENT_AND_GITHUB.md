# Deployment & GitHub

## A. Push to GitHub (beginner, Windows)
1. Install Git (git-scm.com) and create a free GitHub account. Create an **empty** repository named `ShieldML`
   (no README/licence/.gitignore) at github.com/new.
2. In PowerShell, inside the project folder:
```powershell
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git init
git add .
git status            # check: no .venv, no data\raw\*.csv, no .env, no *.zip, no models\*.joblib
git commit -m "ShieldML: initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/ShieldML.git
git push -u origin main
```
3. When asked to sign in, use the browser prompt or a Personal Access Token (Settings → Developer settings →
   Tokens) as the password. **Never commit tokens, `.env`, Kaggle keys or the dataset.**
4. The Actions tab will run `.github/workflows/ci.yml` automatically.

## B. Deploy (Render or Railway) — requires YOUR account; no live URL exists yet
The image needs `models/shieldml_bundle.joblib`, which is git-ignored. Options:
* **Git LFS** (recommended if the file is >50 MB): `git lfs install`, `git lfs track "models/*.joblib"`, remove `models/*` from `.gitignore`, commit `.gitattributes` and the bundle.
* Or build the image locally and push it to a registry (Docker Hub / GHCR), then deploy that image.

Render: New → Blueprint → select the repo (uses `render.yaml`) → set `API_KEY` in the dashboard → deploy.
Railway: New Project → Deploy from GitHub → it detects the `Dockerfile` → add variables (`API_KEY`, `SHAP_API_MODELS`) → Generate Domain.
Both inject `PORT`; the container already binds `0.0.0.0:$PORT`. Free tiers have low CPU/RAM and cold starts: re-run
`scripts/benchmark_api.py --url https://<your-service>` against the live URL and report *those* latencies.
Once deployed, put the real URL in README. Until then it stays **PENDING**.

## C. Docker one-liner
`docker run -p 8000:8000 shieldml-api` after `docker build -t shieldml-api .` (requires a trained model in `models/`).
