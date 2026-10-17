# Verification status (honest build log)

Build sandbox: Python 3.12.3, pandas 3.0.2, numpy 2.4.4, scikit-learn 1.8.0, matplotlib. **No network, no Docker,
1 CPU / 4 GB RAM.** Not installable there: xgboost, lightgbm, imbalanced-learn, shap, mlflow, optuna, fastapi, uvicorn,
pydantic, httpx, pytest. Kaggle data could not be downloaded.

## EXECUTED and observed
| Check | Result |
|---|---|
| `compileall` on src/app/scripts/tests | OK |
| Core module imports (config, data, features, models, evaluation, monitoring, services) | OK |
| Test suite via a minimal pytest-compatible shim (real pytest unavailable) | **28 passed, 0 failed, 5 skipped** |
| Data validation, cleaning, chronological split, no-overlap, tie handling | passed |
| Velocity counts vs brute-force; future-data leakage; row-order independence; label independence | passed |
| Fit-on-train-only; unseen entities; missing timestamps/values; cyclical encoding | passed |
| Train/serve parity: `HistoryStore` + `ModelService` equals batch features/predictions (with entities and global velocity) | passed |
| F2 threshold vs brute force, tie rule; metrics/confusion consistency; soft-voting = member mean; model serialise/reload | passed |
| Monitor rolling-window logic | passed |
| `train.py` smoke run, **Random-Forest only, synthetic fixture, no MLflow, no SHAP** (baseline vs class-weight comparison, grid tuning, calibration, threshold, single test eval, bundle save) | ran end to end; `evaluate.py` reproduced identical test metrics. Metrics are synthetic and meaningless as fraud performance |
| `ModelService` load + predict + graceful "explanations unavailable" | worked |
| `run_eda.py --synthetic` | ran |

Two real defects were found and fixed by these tests (integer-hour cyclical encoding; a test-data bug).

## NOT EXECUTED (code written, **unverified**) — run these yourself
| Item | Why | How to verify |
|---|---|---|
| XGBoost / LightGBM training, Optuna tuning | libs not installable | `python scripts/train.py --quick --n-trials 5` |
| SMOTE / undersampling / ADASYN comparison | imbalanced-learn missing (fallback path only covers baseline/class-weight) | same command; see `imbalance_comparison.csv` |
| SHAP TreeExplainer plots, 3 waterfalls, API explanations | shap missing | same; `reports/shap/` |
| MLflow logging, child runs, registry, alias, load check | mlflow missing | `train.py` then `register_model.py` |
| FastAPI endpoints, 422 handling, pytest API tests | fastapi/pydantic/httpx missing | `python -m pytest` |
| Latency benchmark (<50 ms) | no server stack; 1-core sandbox not representative | `python scripts/benchmark_api.py` |
| Docker build/run, compose | Docker absent | see README §6 |
| Real-dataset results, ROC-AUC > 0.90 target | no data/network | train on `creditcard.csv` |
| Live deployment URL, demo video | needs your accounts | docs/DEPLOYMENT_AND_GITHUB.md — **PENDING** |

The pins in `requirements.txt` were chosen for compatibility but never installed here; if pip reports a conflict, adjust and note it.

## Deliverable checklist
| # | Deliverable | Status | Evidence / reason |
|---|---|---|---|
| 1 | Modular source | COMPLETED | file tree; compile + import OK |
| 2 | Ingestion/validation scripts | COMPLETED (tested on synthetic; real data PENDING) | tests, scripts |
| 3 | EDA reports/plots | PARTIAL | script ran on synthetic only; run on real data |
| 4 | Feature pipeline | COMPLETED | 12+ tests incl. leakage/parity |
| 5 | Imbalance experiments | PARTIAL | baseline/class-weight ran; SMOTE/under/ADASYN unrun |
| 6 | RF, XGB, LGBM trained | PARTIAL | only RF smoke-trained (synthetic) |
| 7 | Ensemble + calibration | PARTIAL | logic tested; 3-model ensemble unrun |
| 8 | Validation F2 threshold | COMPLETED (logic) | brute-force test; real value after training |
| 9 | Held-out test report | NOT COMPLETED | needs real-data run |
| 10 | ROC/PR curves | PARTIAL | plotting code ran in smoke run; real plots pending |
| 11 | Confusion matrix/metrics | PARTIAL | same |
| 12–13 | SHAP global + 3 waterfalls | NOT COMPLETED (unverified code) | shap missing |
| 14 | MLflow runs + registry | NOT COMPLETED (unverified code) | mlflow missing |
| 15–16 | FastAPI endpoints | PARTIAL | service logic verified; HTTP layer unrun |
| 17 | Latency benchmark | NOT COMPLETED | script written, never run |
| 18 | Docker | NOT COMPLETED | files written, not built |
| 19–23 | Model card, diagram, README, API docs, report | COMPLETED | docs/ (results sections intentionally unfilled) |
| 24 | pytest suite | PARTIAL | 28 pass via shim; 5 skipped; real pytest unrun |
| 25 | .gitignore / .env.example | COMPLETED | secret scan clean |
| 26 | GitHub instructions | COMPLETED | docs |
| 27 | Deployment instructions / live URL | PARTIAL / PENDING | no URL exists |
| 28 | ZIP archive | COMPLETED | see final message |
