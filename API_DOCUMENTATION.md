# ShieldML API

Base URL (local): `http://127.0.0.1:8000`. Interactive docs: `/docs`. **Live deployed URL: PENDING** (see DEPLOYMENT_AND_GITHUB.md).

| Endpoint | Purpose |
|---|---|
| `GET /health` | 200 when the model is loaded; **503** with a reason when not |
| `POST /predict` | Score one transaction |
| `GET /metrics` | In-memory monitoring stub |

## POST /predict
Request (Kaggle schema; `V1…V28` all required, extra fields rejected). Optional: `merchant_id`, `device_id`,
`customer_id`, `tx_count_1h|24h|7d` (override velocity features), `explain` (default `true`).
```json
{"Time": 406.0, "Amount": 149.62, "V1": -1.36, "V2": -0.07, "V3": 2.54, "V4": 1.38, "V5": -0.34, "V6": 0.46,
 "V7": 0.24, "V8": 0.10, "V9": 0.36, "V10": 0.09, "V11": -0.55, "V12": -0.62, "V13": -0.99, "V14": -0.31,
 "V15": 1.47, "V16": -0.47, "V17": 0.21, "V18": 0.03, "V19": 0.40, "V20": 0.25, "V21": -0.02, "V22": 0.28,
 "V23": -0.11, "V24": 0.07, "V25": 0.13, "V26": -0.19, "V27": 0.13, "V28": -0.02, "explain": true}
```
Response (shape; values come from the loaded model, nothing is hard-coded):
```json
{"prediction": "LEGITIMATE", "fraud_probability": 0.0, "selected_threshold": 0.0,
 "prediction_confidence": 0.0,
 "top_features": [{"feature": "V14", "value": 0.0, "contribution": 0.0, "direction": "decreases fraud score"}],
 "shap_explanation": {"method": "...", "models_used": ["xgboost","lightgbm"], "contributions": {}, "note": "..."},
 "explanation_status": "ok", "model_name": "...", "model_version": "...",
 "latency_ms": 0.0, "prediction_latency_ms": 0.0, "disclaimer": "..."}
```
* `prediction` = `FRAUD` iff `fraud_probability >= selected_threshold`. The threshold maximises **validation F2**, so it
  is usually far below 0.5 — a "FRAUD" label with probability 0.2 is expected and means "send to review".
* `prediction_confidence` = calibrated probability of the *predicted* class.
* `latency_ms` = end-to-end inside the service (incl. SHAP); `prediction_latency_ms` = features + scoring only.
* `explanation_status`: `ok`, `unavailable`, `failed: …` or `not_requested`; prediction is returned regardless.
* SHAP values are relative, non-causal attributions (see MODEL_CARD).

**Validation errors → HTTP 422** (FastAPI standard): missing/typed-wrong/negative/unknown fields. **503** if no model is loaded.
**401** if `API_KEY` is set and the `X-API-Key` header is wrong.

PowerShell:
```powershell
$body = Get-Content example_request.json -Raw
Invoke-RestMethod -Uri http://127.0.0.1:8000/predict -Method Post -ContentType "application/json" -Body $body
Invoke-RestMethod http://127.0.0.1:8000/health
```
curl (Git Bash / WSL): `curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d @example_request.json`

## GET /metrics (stub)
`prediction_count`, `error_count`, `average_latency_ms`, `max_latency_ms`, `recent_p95_latency_ms_last_100`,
`fraud_rate_last_100`, `mean_fraud_probability_last_100`, `uptime_seconds`. **In-memory, per-process, resets on restart**;
not production monitoring (export to Prometheus/OpenTelemetry for that).

## Serving-time features
Behavioural/velocity features are computed from an in-memory history of previously scored requests using the *same*
function as training. A freshly started service has no history (cold start). With the Kaggle data there are no entity
IDs, so velocity features are off by default (see MODEL_CARD).

## Security recommendations
Set `API_KEY` (or put the service behind an API gateway / mTLS), enforce HTTPS, rate-limit, never log payloads
(the service logs only prediction, latency and status), keep transaction data under your PCI/GDPR policy,
and treat scores as advisory.
