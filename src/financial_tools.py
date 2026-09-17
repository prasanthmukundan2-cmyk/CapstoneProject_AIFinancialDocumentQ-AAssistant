from typing import Optional


def calculate_growth(
    old_value: float,
    new_value: float,
) -> float:
    """
    Calculate percentage growth.
    """

    if old_value == 0:
        raise ValueError(
            "Cannot calculate growth from a zero base value."
        )

    return ((new_value - old_value) / old_value) * 100


def calculate_profit_margin(
    revenue: float,
    net_income: float,
) -> float:
    """
    Calculate profit margin percentage.
    """

    if revenue == 0:
        raise ValueError(
            "Revenue cannot be zero."
        )

    return (net_income / revenue) * 100


def calculate_net_worth(
    assets: float,
    liabilities: float,
) -> float:
    """
    Calculate net worth.
    """

    return assets - liabilities