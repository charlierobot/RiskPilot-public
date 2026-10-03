from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pandas as pd

REQUIRED_COLUMNS = [
    "transaction_id",
    "date",
    "amount",
    "vendor",
    "country",
    "approved_by",
    "category",
]
MAX_FILE_SIZE = 5 * 1024 * 1024


@dataclass
class ValidationResult:
    valid: bool
    dataframe: pd.DataFrame | None
    errors: list[str]
    warnings: list[str]


def validate_csv(uploaded_file) -> ValidationResult:
    """Legge e valida un CSV senza modificare il file originale."""
    errors: list[str] = []
    warnings: list[str] = []
    filename = getattr(uploaded_file, "name", "dataset.csv")

    if not filename.lower().endswith(".csv"):
        errors.append("Il file deve avere estensione .csv.")

    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_FILE_SIZE:
        errors.append("Il file supera il limite di 5 MB.")

    if errors:
        return ValidationResult(False, None, errors, warnings)

    try:
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        dataframe = pd.read_csv(BytesIO(raw), encoding="utf-8-sig")
    except UnicodeDecodeError:
        return ValidationResult(False, None, ["Il file non è codificato in UTF-8. Salva il CSV con codifica UTF-8."], warnings)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        return ValidationResult(False, None, [f"Il CSV non è leggibile: {exc}"], warnings)
    except Exception as exc:
        return ValidationResult(False, None, [f"Impossibile leggere il file: {exc}"], warnings)

    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing:
        errors.append("Mancano le colonne obbligatorie: " + ", ".join(missing) + ".")
        return ValidationResult(False, dataframe, errors, warnings)

    if dataframe.empty:
        errors.append("Il CSV non contiene righe di dati.")
        return ValidationResult(False, dataframe, errors, warnings)

    _validate_required_values(dataframe, errors, warnings)
    return ValidationResult(not errors, dataframe, errors, warnings)


def _validate_required_values(dataframe: pd.DataFrame, errors: list[str], warnings: list[str]) -> None:
    if dataframe["transaction_id"].isna().any() or (dataframe["transaction_id"].astype(str).str.strip() == "").any():
        errors.append("Ogni record deve avere un transaction_id valorizzato.")

    duplicate_count = dataframe["transaction_id"].astype(str).duplicated().sum()
    if duplicate_count:
        errors.append(f"Sono presenti {duplicate_count} transaction_id duplicati.")

    parsed_dates = pd.to_datetime(dataframe["date"], errors="coerce")
    if parsed_dates.isna().any():
        errors.append("La colonna date contiene valori non validi: usare il formato YYYY-MM-DD.")

    numeric_amounts = pd.to_numeric(dataframe["amount"], errors="coerce")
    if numeric_amounts.isna().any():
        errors.append("La colonna amount deve contenere soltanto numeri.")
    elif (numeric_amounts < 0).any():
        errors.append("La colonna amount non può contenere valori negativi.")

    for column, label in [("vendor", "vendor"), ("approved_by", "approved_by"), ("category", "category")]:
        if dataframe[column].isna().any() or (dataframe[column].astype(str).str.strip() == "").any():
            errors.append(f"La colonna {label} non può contenere valori vuoti.")

    countries = dataframe["country"].astype(str).str.strip()
    if (~countries.str.match(r"^[A-Za-z]{2}$", na=False)).any():
        errors.append("La colonna country deve contenere codici di due lettere, ad esempio IT o DE.")

    extra_columns = [column for column in dataframe.columns if column not in REQUIRED_COLUMNS]
    if extra_columns:
        warnings.append("Colonne aggiuntive ignorate: " + ", ".join(extra_columns) + ".")
