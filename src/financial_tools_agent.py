"""
Financial Tool-Using Agent
Provides financial calculation tools for agents to use
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ============================================================
# FINANCIAL CALCULATION TOOLS
# ============================================================

def calculate_profit_margin(revenue: float, profit: float) -> Dict[str, Any]:
    """Calculate profit margin percentage"""
    try:
        if revenue == 0:
            return {"error": "Revenue cannot be zero", "value": None}
        margin = (profit / revenue) * 100
        return {
            "calculation": "Profit Margin = (Profit / Revenue) × 100",
            "value": round(margin, 2),
            "unit": "%",
            "interpretation": f"For every $1 of revenue, {round(margin, 2)}¢ is profit"
        }
    except Exception as e:
        logger.error(f"Profit margin calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_roi(investment: float, return_amount: float) -> Dict[str, Any]:
    """Calculate return on investment"""
    try:
        if investment == 0:
            return {"error": "Investment cannot be zero", "value": None}
        roi = ((return_amount - investment) / investment) * 100
        return {
            "calculation": "ROI = ((Return - Investment) / Investment) × 100",
            "value": round(roi, 2),
            "unit": "%",
            "interpretation": f"Investment returned {round(roi, 2)}% profit"
        }
    except Exception as e:
        logger.error(f"ROI calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_debt_to_equity(debt: float, equity: float) -> Dict[str, Any]:
    """Calculate debt-to-equity ratio"""
    try:
        if equity == 0:
            return {"error": "Equity cannot be zero", "value": None}
        ratio = debt / equity
        return {
            "calculation": "Debt-to-Equity = Total Debt / Total Equity",
            "value": round(ratio, 2),
            "unit": "ratio",
            "interpretation": f"For every $1 of equity, company has ${round(ratio, 2)} of debt"
        }
    except Exception as e:
        logger.error(f"Debt-to-equity calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Dict[str, Any]:
    """Calculate current ratio (liquidity measure)"""
    try:
        if current_liabilities == 0:
            return {"error": "Current liabilities cannot be zero", "value": None}
        ratio = current_assets / current_liabilities
        return {
            "calculation": "Current Ratio = Current Assets / Current Liabilities",
            "value": round(ratio, 2),
            "unit": "ratio",
            "interpretation": f"Company has ${round(ratio, 2)} in current assets per $1 of current liabilities"
        }
    except Exception as e:
        logger.error(f"Current ratio calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> Dict[str, Any]:
    """Calculate quick ratio (more conservative liquidity)"""
    try:
        if current_liabilities == 0:
            return {"error": "Current liabilities cannot be zero", "value": None}
        quick_assets = current_assets - inventory
        ratio = quick_assets / current_liabilities
        return {
            "calculation": "Quick Ratio = (Current Assets - Inventory) / Current Liabilities",
            "value": round(ratio, 2),
            "unit": "ratio",
            "interpretation": f"Company has ${round(ratio, 2)} in liquid assets per $1 of current liabilities"
        }
    except Exception as e:
        logger.error(f"Quick ratio calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_growth_rate(current_value: float, previous_value: float, periods: int = 1) -> Dict[str, Any]:
    """Calculate growth rate"""
    try:
        if previous_value == 0:
            return {"error": "Previous value cannot be zero", "value": None}
        growth = ((current_value - previous_value) / previous_value) * 100
        annual_growth = growth / periods if periods > 0 else growth
        return {
            "calculation": f"Growth Rate = ((Current - Previous) / Previous) × 100",
            "value": round(growth, 2),
            "annual_value": round(annual_growth, 2),
            "unit": "%",
            "interpretation": f"Value grew by {round(growth, 2)}% over {periods} period(s)"
        }
    except Exception as e:
        logger.error(f"Growth rate calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_earnings_per_share(net_income: float, shares_outstanding: int) -> Dict[str, Any]:
    """Calculate earnings per share (EPS)"""
    try:
        if shares_outstanding == 0:
            return {"error": "Shares outstanding cannot be zero", "value": None}
        eps = net_income / shares_outstanding
        return {
            "calculation": "EPS = Net Income / Shares Outstanding",
            "value": round(eps, 2),
            "unit": "$ per share",
            "interpretation": f"Each share generates ${round(eps, 2)} in earnings"
        }
    except Exception as e:
        logger.error(f"EPS calculation error: {e}")
        return {"error": str(e), "value": None}


def calculate_price_to_earnings(stock_price: float, eps: float) -> Dict[str, Any]:
    """Calculate price-to-earnings ratio"""
    try:
        if eps == 0:
            return {"error": "EPS cannot be zero", "value": None}
        pe_ratio = stock_price / eps
        return {
            "calculation": "P/E Ratio = Stock Price / EPS",
            "value": round(pe_ratio, 2),
            "unit": "ratio",
            "interpretation": f"Investors pay ${round(pe_ratio, 2)} for every $1 of earnings"
        }
    except Exception as e:
        logger.error(f"P/E ratio calculation error: {e}")
        return {"error": str(e), "value": None}


def analyze_financial_health(
    profit_margin: float,
    debt_to_equity: float,
    current_ratio: float,
    growth_rate: float
) -> Dict[str, Any]:
    """
    Analyze overall financial health based on key metrics
    Returns risk assessment
    """
    try:
        health_score = 0
        risks = []

        # Profit margin check (healthy: > 10%)
        if profit_margin > 15:
            health_score += 25
        elif profit_margin > 10:
            health_score += 20
        elif profit_margin > 5:
            health_score += 10
        else:
            risks.append("Low profit margin (<5%)")

        # Debt-to-equity check (healthy: < 1.5)
        if debt_to_equity < 1:
            health_score += 25
        elif debt_to_equity < 1.5:
            health_score += 15
        else:
            risks.append("High debt-to-equity ratio (>1.5)")

        # Current ratio check (healthy: 1.5-3)
        if 1.5 <= current_ratio <= 3:
            health_score += 25
        elif current_ratio >= 1:
            health_score += 15
        else:
            risks.append("Low current ratio (<1) - liquidity concerns")

        # Growth rate check (healthy: > 5%)
        if growth_rate > 10:
            health_score += 25
        elif growth_rate > 5:
            health_score += 20
        elif growth_rate > 0:
            health_score += 10
        else:
            risks.append("Negative or stagnant growth")

        # Determine overall health
        if health_score >= 80:
            status = "EXCELLENT"
        elif health_score >= 60:
            status = "GOOD"
        elif health_score >= 40:
            status = "FAIR"
        else:
            status = "POOR"

        return {
            "overall_health": status,
            "health_score": health_score,
            "identified_risks": risks if risks else ["No major risks identified"],
            "recommendation": get_recommendation(status, risks)
        }
    except Exception as e:
        logger.error(f"Financial health analysis error: {e}")
        return {"error": str(e)}


def get_recommendation(status: str, risks: list) -> str:
    """Get recommendation based on health status"""
    recommendations = {
        "EXCELLENT": "Strong financial position. Continue current strategy.",
        "GOOD": "Healthy financial position. Monitor identified risks.",
        "FAIR": "Mixed financial signals. Address identified weaknesses.",
        "POOR": "Significant financial concerns. Immediate action needed."
    }
    return recommendations.get(status, "Review financial metrics")


def format_currency(amount: float, currency: str = "$") -> str:
    """Format amount as currency"""
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage"""
    return f"{value:.{decimals}f}%"


# ============================================================
# TOOL REGISTRY
# ============================================================

FINANCIAL_TOOLS = {
    "profit_margin": {
        "function": calculate_profit_margin,
        "description": "Calculate profit margin from revenue and profit",
        "params": ["revenue", "profit"]
    },
    "roi": {
        "function": calculate_roi,
        "description": "Calculate return on investment",
        "params": ["investment", "return_amount"]
    },
    "debt_to_equity": {
        "function": calculate_debt_to_equity,
        "description": "Calculate debt-to-equity ratio",
        "params": ["debt", "equity"]
    },
    "current_ratio": {
        "function": calculate_current_ratio,
        "description": "Calculate current ratio (liquidity)",
        "params": ["current_assets", "current_liabilities"]
    },
    "quick_ratio": {
        "function": calculate_quick_ratio,
        "description": "Calculate quick ratio (conservative liquidity)",
        "params": ["current_assets", "inventory", "current_liabilities"]
    },
    "growth_rate": {
        "function": calculate_growth_rate,
        "description": "Calculate growth rate over periods",
        "params": ["current_value", "previous_value", "periods"]
    },
    "earnings_per_share": {
        "function": calculate_earnings_per_share,
        "description": "Calculate EPS (earnings per share)",
        "params": ["net_income", "shares_outstanding"]
    },
    "price_to_earnings": {
        "function": calculate_price_to_earnings,
        "description": "Calculate P/E ratio",
        "params": ["stock_price", "eps"]
    },
    "financial_health": {
        "function": analyze_financial_health,
        "description": "Analyze overall financial health and risks",
        "params": ["profit_margin", "debt_to_equity", "current_ratio", "growth_rate"]
    }
}


def get_available_tools() -> Dict[str, str]:
    """Return list of available financial tools"""
    return {
        name: tool["description"]
        for name, tool in FINANCIAL_TOOLS.items()
    }
