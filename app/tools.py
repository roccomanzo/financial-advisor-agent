# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)


def get_stock_price(ticker: str) -> dict:
    """Gets the current stock price and key metrics for a given ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'VOO').

    Returns:
        A dictionary containing the current price, symbol, currency, and high/low values.
    """
    ticker = ticker.upper().strip()

    # Try Yahoo Finance API (very stable and unauthenticated)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            chart = data.get("chart", {})
            result = chart.get("result", [])
            if not result:
                return {
                    "status": "error",
                    "message": f"No data found for ticker {ticker}",
                }

            meta = result[0].get("meta", {})
            current_price = meta.get("regularMarketPrice")
            currency = meta.get("currency", "USD")

            # Get latest indicators
            indicators = result[0].get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            high = quote.get("high", [None])[-1]
            low = quote.get("low", [None])[-1]

            return {
                "status": "success",
                "ticker": ticker,
                "current_price": current_price,
                "currency": currency,
                "high_24h": high,
                "low_24h": low,
                "source": "Yahoo Finance",
            }
    except Exception as e:
        logger.error(f"Failed fetching stock price from Yahoo: {e}")
        return {
            "status": "error",
            "message": f"Could not fetch data for ticker {ticker}: {e!s}",
        }


def calculate_compound_interest(
    principal: float,
    annual_rate: float,
    years: int,
    monthly_contribution: float = 0.0,
    compounding_frequency: int = 12,
) -> dict:
    """Calculates compound interest for investment/savings projections.

    Args:
        principal: The starting amount/balance.
        annual_rate: Annual interest rate as a decimal (e.g. 0.07 for 7%).
        years: The number of years to compound.
        monthly_contribution: Additional monthly contribution amount. Defaults to 0.0.
        compounding_frequency: How many times per year interest is compounded. Defaults to 12 (monthly).

    Returns:
        A dictionary with the final balance, total principal contributions, and total interest earned.
    """
    total_contributions = principal + (monthly_contribution * 12 * years)

    n = compounding_frequency
    r = annual_rate
    t = years
    pmt = monthly_contribution

    p_comp = principal * ((1 + r / n) ** (n * t))

    if r == 0:
        pmt_comp = pmt * 12 * t
    else:
        pmt_comp = pmt * (((1 + r / n) ** (n * t) - 1) / (r / n))

    total_balance = p_comp + pmt_comp
    interest_earned = total_balance - total_contributions

    return {
        "starting_principal": principal,
        "total_contributions": round(total_contributions, 2),
        "total_interest_earned": round(interest_earned, 2),
        "final_balance": round(total_balance, 2),
    }


def calculate_loan_amortization(
    loan_amount: float,
    annual_rate: float,
    years: int,
    extra_monthly_payment: float = 0.0,
) -> dict:
    """Calculates loan payment details and amortization metrics for debt payoff analysis.

    Args:
        loan_amount: The starting loan amount / balance.
        annual_rate: Annual interest rate as a decimal (e.g. 0.05 for 5%).
        years: The length of the loan in years.
        extra_monthly_payment: Extra amount paid each month. Defaults to 0.0.

    Returns:
        A dictionary with the standard monthly payment, total interest paid, actual months to pay off, and savings from extra payments.
    """
    r = annual_rate / 12
    n = years * 12
    p = loan_amount

    if r == 0:
        standard_monthly_payment = p / n
    else:
        standard_monthly_payment = p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    balance = p
    total_interest = 0.0
    months_elapsed = 0
    total_paid = 0.0

    while balance > 0 and months_elapsed < 1200:
        months_elapsed += 1
        interest_payment = balance * r
        principal_payment = (
            standard_monthly_payment - interest_payment + extra_monthly_payment
        )

        if balance < principal_payment:
            actual_payment = balance + interest_payment
            principal_payment = balance
            balance = 0.0
        else:
            actual_payment = standard_monthly_payment + extra_monthly_payment
            balance -= principal_payment

        total_interest += interest_payment
        total_paid += actual_payment

    baseline_total_interest = (standard_monthly_payment * n) - p if r > 0 else 0.0
    interest_savings = max(0.0, baseline_total_interest - total_interest)
    months_saved = max(0, n - months_elapsed)

    return {
        "standard_monthly_payment": round(standard_monthly_payment, 2),
        "actual_months_to_pay_off": months_elapsed,
        "total_interest_paid": round(total_interest, 2),
        "total_amount_paid": round(total_paid, 2),
        "interest_savings": round(interest_savings, 2),
        "months_saved": months_saved,
    }


def get_mortgage_rate_by_credit_score(credit_score: int) -> dict:
    """Estimates the current average 30-year fixed mortgage interest rate based on a user's credit score.

    Args:
        credit_score: The user's credit score (FICO score between 300 and 850).

    Returns:
        A dictionary containing the estimated interest rate and the credit tier name.
    """
    if credit_score < 300 or credit_score > 850:
        return {
            "status": "error",
            "message": "Credit score must be between 300 and 850.",
        }

    # Baseline prime 30-year fixed rate (Freddie Mac national average)
    baseline_rate = 0.065

    if credit_score >= 760:
        rate = baseline_rate
        tier = "Excellent (760-850)"
    elif credit_score >= 700:
        rate = baseline_rate + 0.0022
        tier = "Good (700-759)"
    elif credit_score >= 680:
        rate = baseline_rate + 0.0040
        tier = "Fair (680-699)"
    elif credit_score >= 660:
        rate = baseline_rate + 0.0061
        tier = "Fair (660-679)"
    elif credit_score >= 640:
        rate = baseline_rate + 0.0104
        tier = "Passable (640-659)"
    elif credit_score >= 620:
        rate = baseline_rate + 0.0159
        tier = "Poor (620-639)"
    else:
        rate = baseline_rate + 0.0200
        tier = "Subprime (<620)"

    return {
        "status": "success",
        "credit_score": credit_score,
        "credit_tier": tier,
        "estimated_annual_rate": round(rate, 4),
        "formatted_rate": f"{round(rate * 100, 2)}%",
    }


def get_local_tax_and_insurance_rates(state: str) -> dict:
    """Returns typical average property tax rates and homeowners insurance averages for a US state.

    Args:
        state: The two-letter state abbreviation or full name (e.g. 'TX', 'Texas', 'CA', 'California').

    Returns:
        A dictionary with typical property tax rate (percent of home value) and average annual insurance premium.
    """
    state_clean = state.strip().upper()

    # State average database (typical ranges)
    database = {
        "TX": {
            "property_tax_rate": 0.0160,
            "avg_annual_insurance": 2500.0,
            "state_name": "Texas",
        },
        "TEXAS": {
            "property_tax_rate": 0.0160,
            "avg_annual_insurance": 2500.0,
            "state_name": "Texas",
        },
        "CA": {
            "property_tax_rate": 0.0075,
            "avg_annual_insurance": 1400.0,
            "state_name": "California",
        },
        "CALIFORNIA": {
            "property_tax_rate": 0.0075,
            "avg_annual_insurance": 1400.0,
            "state_name": "California",
        },
        "FL": {
            "property_tax_rate": 0.0090,
            "avg_annual_insurance": 4200.0,
            "state_name": "Florida",
        },
        "FLORIDA": {
            "property_tax_rate": 0.0090,
            "avg_annual_insurance": 4200.0,
            "state_name": "Florida",
        },
        "NY": {
            "property_tax_rate": 0.0140,
            "avg_annual_insurance": 1800.0,
            "state_name": "New York",
        },
        "NEW YORK": {
            "property_tax_rate": 0.0140,
            "avg_annual_insurance": 1800.0,
            "state_name": "New York",
        },
        "NJ": {
            "property_tax_rate": 0.0220,
            "avg_annual_insurance": 1500.0,
            "state_name": "New Jersey",
        },
        "NEW JERSEY": {
            "property_tax_rate": 0.0220,
            "avg_annual_insurance": 1500.0,
            "state_name": "New Jersey",
        },
        "IL": {
            "property_tax_rate": 0.0200,
            "avg_annual_insurance": 1600.0,
            "state_name": "Illinois",
        },
        "ILLINOIS": {
            "property_tax_rate": 0.0200,
            "avg_annual_insurance": 1600.0,
            "state_name": "Illinois",
        },
    }

    # Fallback to national averages
    result = database.get(
        state_clean,
        {
            "property_tax_rate": 0.0110,
            "avg_annual_insurance": 1800.0,
            "state_name": state,
        },
    )

    return {
        "status": "success",
        "state": result["state_name"],
        "property_tax_rate": result["property_tax_rate"],
        "formatted_property_tax_rate": f"{round(result['property_tax_rate'] * 100, 2)}%",
        "avg_annual_insurance": result["avg_annual_insurance"],
    }
