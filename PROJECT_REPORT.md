# Internship Project Report — ShieldML

**Project:** Code A Nova Project 4 — Real-Time Financial Fraud Detection System.

## 1. Summary
A reproducible pipeline from raw transactions to a served, explainable fraud score. This report describes the design and
decisions. **Quantitative results are produced by `scripts/train.py` and must be copied from `reports/metrics/*` after
your run** — none were fabricated here (the build environment had no network access to the real dataset).

## 2. Design decisions
| Topic | Decision | Reason |
|---|---|---|
| Split | chronological 70/15/15, duplicates removed first | prevents temporal & duplicate leakage |
| Features | stateless **causal** history features + train-fitted `FeatureBuilder` | past-only counts/statistics (strict `<` timestamp), no labels used |
| Missing entities | features switch off, never invented | dataset has no merchant/device/customer ids |
| Imbalance | baseline vs class weights vs SMOTE vs undersampling vs ADASYN inside `imblearn.Pipeline` | resampling only at fit on training folds |
| CV | `TimeSeriesSplit` scored by PR-AUC | respects time; accuracy is misleading at 0.17 % prevalence |
| Tuning | Optuna (XGB/LGBM), GridSearchCV (RF); nested MLflow runs | brief requirement |
| Calibration | sigmoid, `FrozenEstimator` on last 20 % of train | calibrate on data models never saw; validation reserved for threshold |
| Ensemble | custom soft voting over calibrated member probabilities | works with prefit calibrated members |
| Champion | best validation PR-AUC (threshold-free); ensemble wins ties | honest comparison; ensemble not assumed better |
| Threshold | max validation F2, ties → highest threshold; cost table as context | recall-weighted fraud cost; fixed before test |
| SHAP | TreeExplainer on tree members, rescaled mean | exact TreeExplainer unsupported on calibrated blend; limitation documented |
| Serving | model loaded once; causal features from in-memory history | <50 ms target, same code as training |

## 3. Deviations from the brief
* scikit-learn 1.6.1 (not 1.4) for `FrozenEstimator`; `cv="prefit"` is removed in recent scikit-learn.
* Brief's "stratified time-based folds": implemented as `TimeSeriesSplit` (true stratification is incompatible with ordered folds).
* Velocity / merchant z-score / device frequency depend on columns the Kaggle data lacks; implemented and tested on a
  synthetic fixture with entity columns, off by default for Kaggle.
* Deployed URL and 5-minute demo video: **pending** (need your accounts).

## 4. Results (fill after training)
Copy from `reports/metrics/final_metrics.json`: test ROC-AUC, PR-AUC, precision, recall, F1, F2 at the validation-selected
threshold; `ensemble_vs_members`; latency from `latency_benchmark.json`.
If test ROC-AUC ≤ 0.90, report it as is and investigate (data size, drift between early/late hours, feature choices) —
never tune on the test set.

## 5. What I would do next
Real entity IDs and timestamps, drift monitoring, persistent feature store, cost-sensitive threshold from real losses,
fairness audit, shadow-mode rollout.
