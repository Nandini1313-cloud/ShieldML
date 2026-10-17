"""ShieldML FastAPI service. Run: uvicorn app.main:app --host 0.0.0.0 --port 8000"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, HTTPException  # noqa: E402

from app.dependencies import require_api_key  # noqa: E402
from app.schemas import HealthResponse, PredictionResponse, TransactionRequest  # noqa: E402
from app.services.model_service import ModelService, ModelUnavailable  # noqa: E402
from src.monitoring.metrics import PredictionMonitor  # noqa: E402
from src.utils.logging_utils import get_logger  # noqa: E402

log = get_logger("shieldml.api", json_format=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    svc = ModelService()
    svc.load()                       # once, at startup (never per request)
    app.state.service = svc
    app.state.monitor = PredictionMonitor(window=100)
    yield


app = FastAPI(title="ShieldML Fraud Detection API", version="1.0.0", lifespan=lifespan,
              description="Real-time transaction scoring with SHAP explanations. "
                          "Scores are risk estimates, not proof of fraud.")


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health():
    s: ModelService = app.state.service
    body = HealthResponse(status="ok" if s.loaded else "degraded", model_loaded=s.loaded,
                          model_name=s.model_name, model_version=s.model_version, model_source=s.source,
                          explanations_available=s.explainer is not None, synthetic_model=s.synthetic)
    if not s.loaded:
        raise HTTPException(status_code=503, detail={"status": "degraded", "reason": s.load_error})
    return body


@app.post("/predict", response_model=PredictionResponse, tags=["scoring"], dependencies=[Depends(require_api_key)])
def predict(tx: TransactionRequest):
    s: ModelService = app.state.service
    m: PredictionMonitor = app.state.monitor
    try:
        res = s.predict(tx.model_dump(), explain=tx.explain)
    except ModelUnavailable as e:
        m.record_error()
        raise HTTPException(status_code=503, detail=f"model unavailable: {e}")
    except Exception as e:           # never leak transaction contents in logs or errors
        m.record_error()
        log.error("prediction failed: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="internal prediction error")
    m.record(res["prediction"] == "FRAUD", res["latency_ms"], res["fraud_probability"])
    log.info("predict", extra={"fields": {"prediction": res["prediction"], "latency_ms": round(res["latency_ms"], 2),
                                          "explanation": res["explanation_status"]}})
    return res


@app.get("/metrics", tags=["ops"], dependencies=[Depends(require_api_key)])
def metrics():
    return app.state.monitor.snapshot()
