import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/balance_sheet.csv")


def load_financial_data():
    """
    Load the financial CSV.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Financial CSV not found."
        )

    return pd.read_csv(DATA_PATH)


def get_financial_record(year: int):
    """
    Retrieve a financial record for a given year.
    """

    df = load_financial_data()

    record = df[
        df["Year"].astype(str) == str(year)
    ]

    if record.empty:
        raise ValueError(
            f"No financial data found for year {year}."
        )

    return record.iloc[0].to_dict()