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
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# --- Tool Output Schemas ---


class StockPriceOutput(BaseModel):
    status: str = Field(description="Execution status, e.g., 'success' or 'error'.")
    symbol: str = Field(description="The stock ticker symbol.")
    price: float = Field(description="Current stock price.")
    currency: str = Field(description="Currency of the price.")
    high: float = Field(description="Daily high price.")
    low: float = Field(description="Daily low price.")
    error: str = Field(default="", description="Error details if execution failed.")


class CompoundInterestOutput(BaseModel):
    status: str = Field(description="Execution status.")
    total_balance: float = Field(description="Total balance at the end of the term.")
    total_contributions: float = Field(description="Total contributions made.")
    interest_earned: float = Field(description="Total interest earned.")
    error: str = Field(default="", description="Error details if execution failed.")


class LoanAmortizationOutput(BaseModel):
    status: str = Field(description="Execution status.")
    monthly_payment: float = Field(description="Calculated monthly P&I payment.")
    total_payments: float = Field(description="Total amount paid over the term.")
    total_interest: float = Field(description="Total interest paid over the term.")
    error: str = Field(default="", description="Error details if execution failed.")


class MortgageRateOutput(BaseModel):
    status: str = Field(description="Execution status.")
    credit_score: int = Field(description="The input credit score.")
    credit_tier: str = Field(description="Credit score tier description.")
    estimated_rate: float = Field(description="Estimated annual interest rate as a decimal.")
    formatted_rate: str = Field(description="Estimated rate formatted as a percentage string.")
    error: str = Field(default="", description="Error details if execution failed.")


class LocalRatesOutput(BaseModel):
    status: str = Field(description="Execution status.")
    state: str = Field(description="Cleaned state name.")
    property_tax_rate: float = Field(description="State property tax rate as a decimal.")
    formatted_property_tax_rate: str = Field(
        description="Property tax rate formatted as a percentage."
    )
    avg_annual_insurance: float = Field(
        description="Average annual home insurance premium."
    )
    error: str = Field(default="", description="Error details if execution failed.")


class AffordabilityRiskOutput(BaseModel):
    status: str = Field(description="Safety status, either 'safe' or 'warning'.")
    message: str = Field(description="Affordability risk warning or safety message.")



def get_stock_price(ticker: str) -> StockPriceOutput:
    """Gets the current stock price and key metrics for a given ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'VOO').

    Returns:
        A StockPriceOutput containing status, price, high, low, and currency.
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
                return StockPriceOutput(
                    status="error",
                    symbol=ticker,
                    price=0.0,
                    currency="USD",
                    high=0.0,
                    low=0.0,
                    error=f"No data found for ticker {ticker}",
                )

            meta = result[0].get("meta", {})
            current_price = meta.get("regularMarketPrice") or 0.0
            currency = meta.get("currency", "USD")

            # Get latest indicators
            indicators = result[0].get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            high = quote.get("high", [0.0])[-1] or 0.0
            low = quote.get("low", [0.0])[-1] or 0.0

            return StockPriceOutput(
                status="success",
                symbol=ticker,
                price=current_price,
                currency=currency,
                high=high,
                low=low,
            )
    except Exception as e:
        logger.error(f"Failed fetching stock price from Yahoo: {e}")
        return StockPriceOutput(
            status="error",
            symbol=ticker,
            price=0.0,
            currency="USD",
            high=0.0,
            low=0.0,
            error=f"Could not fetch data for ticker {ticker}: {e!s}",
        )


def calculate_compound_interest(
    principal: float,
    annual_rate: float,
    years: int,
    monthly_contribution: float = 0.0,
    compounding_frequency: int = 12,
) -> CompoundInterestOutput:
    """Calculates compound interest for investment/savings projections.

    Args:
        principal: The starting amount/balance.
        annual_rate: Annual interest rate as a decimal (e.g. 0.07 for 7%).
        years: The number of years to compound.
        monthly_contribution: Additional monthly contribution amount. Defaults to 0.0.
        compounding_frequency: How many times per year interest is compounded. Defaults to 12 (monthly).

    Returns:
        A CompoundInterestOutput with final balance, total contributions, and interest earned.
    """
    try:
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

        return CompoundInterestOutput(
            status="success",
            total_balance=round(total_balance, 2),
            total_contributions=round(total_contributions, 2),
            interest_earned=round(interest_earned, 2),
        )
    except Exception as e:
        return CompoundInterestOutput(
            status="error",
            total_balance=0.0,
            total_contributions=0.0,
            interest_earned=0.0,
            error=str(e),
        )


def calculate_loan_amortization(
    loan_amount: float,
    annual_rate: float,
    years: int,
    extra_monthly_payment: float = 0.0,
) -> LoanAmortizationOutput:
    """Calculates loan payment details and amortization metrics for debt payoff analysis.

    Args:
        loan_amount: The starting loan amount / balance.
        annual_rate: Annual interest rate as a decimal (e.g. 0.05 for 5%).
        years: The length of the loan in years.
        extra_monthly_payment: Extra amount paid each month. Defaults to 0.0.

    Returns:
        A LoanAmortizationOutput with monthly payment, total payments, and interest paid.
    """
    try:
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

        return LoanAmortizationOutput(
            status="success",
            monthly_payment=round(standard_monthly_payment, 2),
            total_payments=round(total_paid, 2),
            total_interest=round(total_interest, 2),
        )
    except Exception as e:
        return LoanAmortizationOutput(
            status="error",
            monthly_payment=0.0,
            total_payments=0.0,
            total_interest=0.0,
            error=str(e),
        )


def get_mortgage_rate_by_credit_score(credit_score: int) -> MortgageRateOutput:
    """Estimates the current average 30-year fixed mortgage interest rate based on a user's credit score.

    Args:
        credit_score: The user's credit score (FICO score between 300 and 850).

    Returns:
        A MortgageRateOutput containing status, credit score, tier, and rate.
    """
    if credit_score < 300 or credit_score > 850:
        return MortgageRateOutput(
            status="error",
            credit_score=credit_score,
            credit_tier="",
            estimated_rate=0.0,
            formatted_rate="",
            error="Credit score must be between 300 and 850.",
        )

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

    return MortgageRateOutput(
        status="success",
        credit_score=credit_score,
        credit_tier=tier,
        estimated_rate=round(rate, 4),
        formatted_rate=f"{round(rate * 100, 2)}%",
    )


def get_local_tax_and_insurance_rates(state: str) -> LocalRatesOutput:
    """Returns typical average property tax rates and homeowners insurance averages for a US state.

    Args:
        state: The two-letter state abbreviation or full name (e.g. 'TX', 'Texas', 'CA', 'California').

    Returns:
        A LocalRatesOutput with typical tax rate, insurance, and formatted values.
    """
    try:
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

        return LocalRatesOutput(
            status="success",
            state=result["state_name"],
            property_tax_rate=result["property_tax_rate"],
            formatted_property_tax_rate=f"{round(result['property_tax_rate'] * 100, 2)}%",
            avg_annual_insurance=result["avg_annual_insurance"],
        )
    except Exception as e:
        return LocalRatesOutput(
            status="error",
            state=state,
            property_tax_rate=0.0,
            formatted_property_tax_rate="",
            avg_annual_insurance=0.0,
            error=str(e),
        )


def verify_affordability_risk(piti_percentage: float) -> AffordabilityRiskOutput:
    """Validates the housing affordability risk level.

    Args:
        piti_percentage: The monthly PITI housing cost as a percentage of gross income (0 to 100).

    Returns:
        An AffordabilityRiskOutput with safety status and message.
    """
    if piti_percentage > 40:
        return AffordabilityRiskOutput(
            status="warning",
            message=f"CRITICAL RISK: Projected housing cost consumes {piti_percentage:.1f}% of gross income, which exceeds the high-risk limit of 40%.",
        )
    return AffordabilityRiskOutput(
        status="safe",
        message=f"Housing cost consumes {piti_percentage:.1f}% of gross income.",
    )


def check_housing_risk_requires_confirmation(piti_percentage: float, **kwargs) -> bool:
    # Require explicit human approval / confirmation if the PITI ratio exceeds 40%
    return piti_percentage > 40
