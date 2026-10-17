from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, create_model

_v_fields = {f"V{i}": (float, Field(..., description=f"Anonymised PCA component V{i}")) for i in range(1, 29)}

_TransactionBase = create_model(
    "_TransactionBase", __config__=ConfigDict(extra="forbid"),
    Time=(float, Field(..., ge=0, description="Seconds since the first transaction in the stream")),
    Amount=(float, Field(..., ge=0, description="Transaction amount")),
    **_v_fields,
)


class TransactionRequest(_TransactionBase):  # type: ignore[valid-type,misc]
    """Raw transaction. Optional entity ids enable behavioural features when the model was trained with them."""
    merchant_id: Optional[str] = Field(None, max_length=64)
    device_id: Optional[str] = Field(None, max_length=64)
    customer_id: Optional[str] = Field(None, max_length=64)
    tx_count_1h: Optional[float] = Field(None, ge=0, description="Optional override of velocity feature")
    tx_count_24h: Optional[float] = Field(None, ge=0)
    tx_count_7d: Optional[float] = Field(None, ge=0)
    explain: bool = Field(True, description="Include SHAP explanation (adds latency)")


class TopFeature(BaseModel):
    feature: str
    value: float
    contribution: float
    direction: str


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    prediction: Literal["FRAUD", "LEGITIMATE"]
    fraud_probability: float
    selected_threshold: float
    prediction_confidence: float = Field(description="Calibrated probability of the PREDICTED class")
    top_features: list[TopFeature] = []
    shap_explanation: Optional[dict] = None
    explanation_status: str = "ok"
    model_name: str
    model_version: str
    latency_ms: float = Field(description="End-to-end time inside the service, incl. explanation")
    prediction_latency_ms: float = Field(description="Features + model scoring only")
    disclaimer: str = "A score is a risk estimate, not proof of fraud. Route to human review."


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: str
    model_loaded: bool
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    model_source: Optional[str] = None
    explanations_available: bool = False
    synthetic_model: bool = False
