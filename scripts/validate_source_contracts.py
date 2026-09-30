import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "data_contracts.json"


def _validate_series(series: pd.Series, declared_type: str) -> list[str]:
    errors: list[str] = []
    nullable = declared_type.endswith("_nullable")
    base_type = declared_type.removesuffix("_nullable")
    values = series.dropna() if nullable else series

    if not nullable and series.isna().any():
        errors.append("contains null values")

    try:
        if base_type == "date":
            pd.to_datetime(values, format="%Y-%m-%d", errors="raise")
        elif base_type == "timestamp":
            pd.to_datetime(values, errors="raise")
        elif base_type == "numeric":
            pd.to_numeric(values, errors="raise")
        elif base_type == "string":
            if values.astype(str).str.strip().eq("").any():
                errors.append("contains blank string values")
        else:
            errors.append(f"unknown declared type: {declared_type}")
    except (ValueError, TypeError) as exc:
        errors.append(f"contains values incompatible with {declared_type}: {exc}")

    return errors


def validate_dataset(name: str, contract: dict) -> list[str]:
    path = ROOT / contract["file"]
    if not path.exists():
        return [f"{name}: source file does not exist: {path}"]

    df = pd.read_csv(path)
    required = contract["required_columns"]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        return [f"{name}: missing required columns: {', '.join(missing)}"]

    errors: list[str] = []
    extras = sorted(set(df.columns) - set(required))
    if extras:
        print(f"WARN {name}: non-breaking additional columns: {', '.join(extras)}")

    for column, declared_type in required.items():
        for detail in _validate_series(df[column], declared_type):
            errors.append(f"{name}.{column}: {detail}")

    for column, allowed in contract.get("allowed_values", {}).items():
        unexpected = sorted(set(df[column].dropna().astype(str)) - set(allowed))
        if unexpected:
            errors.append(
                f"{name}.{column}: unexpected values: {', '.join(unexpected)}; "
                f"allowed: {', '.join(allowed)}"
            )

    return errors


def main() -> None:
    contracts = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    for name, contract in contracts.items():
        dataset_errors = validate_dataset(name, contract)
        if dataset_errors:
            errors.extend(dataset_errors)
        else:
            print(f"PASS {name}: source contract satisfied")

    if errors:
        print("\nBREAKING SOURCE CONTRACT VIOLATION")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
