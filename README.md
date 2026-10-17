# ShieldML — Real-Time Financial Fraud Detection

End-to-end fraud detection pipeline (Code A Nova, Project 4): time-safe feature engineering, imbalance
handling (SMOTE / class weights / undersampling / ADASYN), tuned Random Forest + XGBoost + LightGBM,
calibrated soft-voting ensemble, **validation-selected F2 threshold**, SHAP `TreeExplainer`
explanations, MLflow tracking + registry, and a FastAPI scoring service (target < 50 ms).

> **Read first:** [`docs/VERIFICATION_STATUS.md`](docs/VERIFICATION_STATUS.md) lists exactly what was
> executed during the build and what you must still run on your own machine. No metric in this repo
> is pre-computed: train it yourself and read `reports/metrics/final_metrics.json`.

## 1. Setup (Windows, PowerShell, VS Code)

```powershell
# Python 3.12 from python.org (tick "Add to PATH"). Then, inside the project folder:
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Get the data

Real dataset: Kaggle *Credit Card Fraud Detection* (ULB, 284,807 tx, 492 frauds, columns `Time, V1–V28, Amount, Class`).

```powershell
pip install kaggle                    # (already in requirements)
python scripts/download_data.py       # needs Kaggle credentials; otherwise prints manual steps
python scripts/validate_data.py       # writes reports/metrics/data_quality.json
python scripts/run_eda.py             # plots -> reports/figures, tables -> reports/metrics
```
Manual: download `creditcard.csv` from kaggle.com/datasets/mlg-ulb/creditcardfraud into `data\raw\`.
No credentials? `python scripts/train.py --synthetic ...` uses a **synthetic test fixture only** (never real performance).

## 3. Train (everything logged to MLflow)

```powershell
# Terminal A - tracking UI (leave running)
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000      # open http://127.0.0.1:5000

# Terminal B
python scripts/train.py --quick --n-trials 5     # laptop-friendly first run
python scripts/train.py                          # full run (15 Optuna trials per boosting model)
python scripts/evaluate.py                       # re-scores the held-out test split with the stored threshold
python scripts/register_model.py                 # registers ShieldML-Champion, alias "champion", verifies load
```
Outputs: `reports/figures/` (ROC, PR, confusion matrix, threshold plot), `reports/metrics/` (all tables/JSON),
`reports/shap/` (global bar, summary, 3 waterfalls), `models/shieldml_bundle.joblib`.

Time-based design (why numbers may differ from tutorials): data is split **chronologically** 70/15/15, and
`Time` is *relative seconds* (≈2 days) — there are no real timestamps, merchant, device or customer IDs in this
dataset, so those features switch on **only if** such columns exist (see `docs/MODEL_CARD.md`).

## 4. Run the API

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
# registry mode instead of the local file:
$env:MLFLOW_TRACKING_URI="sqlite:///mlflow.db"; $env:MLFLOW_MODEL_URI="models:/ShieldML-Champion@champion"
```
Docs UI: http://127.0.0.1:8000/docs. Health / predict / metrics examples: [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).

## 5. Test and benchmark

```powershell
python -m pytest                      # unit + API tests
python scripts/benchmark_api.py       # writes reports/metrics/latency_benchmark.json (with & without SHAP)
```

## 6. Docker

```powershell
python scripts/train.py --quick       # the image bundles models/shieldml_bundle.joblib
docker build -t shieldml-api .
docker run -p 8000:8000 shieldml-api
docker compose up --build             # API + MLflow server
```
Env vars: see `.env.example`. Never bake secrets into the image; pass `-e API_KEY=...` at run time.

## 7. Layout
`app/` FastAPI · `src/` data, features, models, evaluation, explainability, monitoring · `scripts/` CLI steps ·
`tests/` · `docs/` model card, API docs, architecture, report, deployment & GitHub guide · `reports/` generated outputs.

Deployment and GitHub steps: [`docs/DEPLOYMENT_AND_GITHUB.md`](docs/DEPLOYMENT_AND_GITHUB.md).
