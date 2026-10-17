# Model Card — ShieldML Champion

*Numbers are intentionally not hard-coded here. After training, copy them from
`reports/metrics/final_metrics.json`, `model_comparison.csv`, `imbalance_comparison.csv`.*

## Overview
Binary classifier estimating P(fraud) for a card transaction. Champion = best validation PR-AUC among
{Random Forest, XGBoost, LightGBM, calibrated soft-voting ensemble}; ties go to the ensemble. The ensemble is **not
assumed** to win — `final_metrics.json → ensemble_vs_members` records whether it actually improved on validation and test.

## Intended use
Decision *support*: rank/flag transactions for human review or step-up authentication. **Not** for automated
account closure, denial of service to customers, legal or credit decisions without human review.

## Data
Kaggle "Credit Card Fraud Detection" (ULB MLG): 284,807 European card transactions over ~2 days, 492 frauds (0.172 %);
`V1–V28` are PCA components (original features hidden), `Time` = seconds since first transaction, `Amount`, `Class`.
Licence: DbCL v1.0 (verify on Kaggle). Exact duplicates are dropped before splitting. Split is chronological 70/15/15.

## Features
Log amount and amount z-score, `V1–V28`, fractional hour-of-day sin/cos (of *relative* time), missing indicators.
Velocity (1h/24h/7d), entity amount-z (merchant/customer), device frequency are **built only when the needed columns exist**.
The Kaggle file has no merchant/device/customer IDs and no wall-clock timestamps, so by default these are *disabled, not faked*.
`--global-velocity` enables system-wide traffic counts, which describe stream volume rather than a cardholder and
cause train/serve skew in a low-traffic demo API — use with care.

## Training procedure
Imbalance strategies compared on validation (no resampling, class weights, SMOTE, undersampling, ADASYN); resampling
runs only inside training folds. Tuning: Optuna (XGBoost, LightGBM) and GridSearchCV (RF) with `TimeSeriesSplit`, scored by PR-AUC,
every trial a nested MLflow run. Final models are fit on the first 80 % of train, calibrated (sigmoid) on the last 20 %,
averaged. Threshold = argmax validation F2 (ties → highest threshold). Test split evaluated once after selection.

## Metrics reported
Precision, recall, F1, F2, ROC-AUC, PR-AUC, confusion matrix at the selected threshold (accuracy is logged but is
uninformative at ~0.17 % prevalence: predicting "legitimate" always scores ≈99.8 %). Brief target: test ROC-AUC > 0.90
(a target, not a guarantee; actual value in `final_metrics.json`).

## Explainability
SHAP `TreeExplainer` on the constituent tree models; combined by rescaled averaging (an approximation, documented in
`src/explainability/shap_explainer.py`). Values are *relative associations used by the model*, not causes, and not proof of fraud.

## Limitations & known failure modes
* Only ~2 days of data and 492 frauds: high variance; small shifts change precision/recall noticeably.
* **Concept drift**: fraud patterns change; performance will decay without monitoring and retraining.
* **Anonymised PCA features**: cannot be audited for individual meaning; PCA was fitted by the data owner on all rows (mild leakage outside our control).
* Relative `Time`: hour-of-day is a proxy, not real time-of-day; weekly seasonality is untestable.
* Cold-start: new cards/merchants have no history; entity features fall back to global statistics.
* Adversarial adaptation, low-amount "card testing" and novel attack types are likely misses.
* Calibration may degrade out of time; calibration slice has few positives (sigmoid chosen for stability).
* In-memory history/monitoring in the demo API is per-process and non-persistent.
* Threshold favours recall (F2), so expect many false positives; review capacity must be sized accordingly.
* Costs used in `cost_analysis` (FN=100, FP=5) are **assumptions**, not measured business costs.

## Bias, fairness and privacy
The dataset contains no demographic or geographic attributes, so group fairness cannot be measured here; that is a
gap, not evidence of fairness. In a real deployment, audit false-positive rates across customer segments and
geographies, document legal basis for automated profiling (e.g. GDPR Art. 22), minimise retained data, and provide
appeal paths. Do not log raw transactions.

## Consequences of errors
False negative = undetected fraud loss and chargebacks. False positive = blocked legitimate customer, friction, lost revenue.
A high probability is a risk estimate, never definitive proof of fraud.
