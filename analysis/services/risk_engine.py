from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

HIGH_VALUE_THRESHOLD = Decimal("5000")
VERY_HIGH_VALUE_THRESHOLD = Decimal("10000")
WATCHLIST_COUNTRIES = {"RU", "IR", "KP"}
SENSITIVE_CATEGORIES = {"consulting", "gifts", "cash", "crypto"}


@dataclass
class RiskEvaluation:
    score: int
    level: str
    reasons: list[str]


def evaluate_record(*, amount: Decimal, country: str, approved_by: str, category: str, record_date: date) -> RiskEvaluation:
    """Valuta un record con regole deterministiche e spiegabili."""
    score = 0
    reasons: list[str] = []
    normalized_country = country.strip().upper()
    normalized_category = category.strip().lower()

    if amount > HIGH_VALUE_THRESHOLD:
        score += 35
        reasons.append("Importo superiore alla soglia di 5.000 €")
    if amount > VERY_HIGH_VALUE_THRESHOLD:
        score += 20
        reasons.append("Importo molto elevato, superiore a 10.000 €")
    if normalized_country in WATCHLIST_COUNTRIES:
        score += 25
        reasons.append("Paese presente nella watchlist demo")
    if not approved_by.strip() or approved_by.strip().lower() in {"n/a", "pending", "non approvato"}:
        score += 20
        reasons.append("Approvazione assente o non conclusa")
    if normalized_category in SENSITIVE_CATEGORIES:
        score += 15
        reasons.append("Categoria considerata sensibile nel prototipo")
    if record_date.weekday() >= 5:
        score += 10
        reasons.append("Operazione registrata nel fine settimana")

    score = min(score, 100)
    if score >= 60:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"
    return RiskEvaluation(score=score, level=level, reasons=reasons)
