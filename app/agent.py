# ruff: noqa
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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.agents import (
    create_retirement_planner,
    create_budgeting_expert,
    create_major_purchase_advisor,
    create_windfall_advisor,
    create_debt_advisor,
    create_investment_advisor,
    create_home_buying_advisor,
)

# Root coordinator agent
root_agent = Agent(
    name="financial_coordinator",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are the lead Financial Coordinator and Advisor.
Your job is to greet the user, understand their financial query, and delegate the task to the appropriate specialist:
- For retirement accumulation planning and target nest eggs, delegate to `retirement_planner`.
- For day-to-day budgeting, expense tracking, fixed income budgets, or retirement drawdowns, delegate to `budgeting_expert`.
- For saving schedules for specific milestones (buying a house/car), delegate to `major_purchase_advisor`.
- For managing unexpected wealth, inheritances, or large bonuses, delegate to `windfall_advisor`.
- For debt payoff plans, mortgages, or loan amortization, delegate to `debt_advisor`.
- For investment portfolios, index fund education, individual stock warnings, or corporate financial statements, delegate to `investment_advisor`.
- For home buying affordability, mortgage options, tax and insurance estimates, and PITI calculations, delegate to `home_buying_advisor`.

Rules:
- Reject irrelevant queries: You are strictly a financial advisor. Do NOT answer any non-financial questions (e.g. weather, general knowledge, geography, trivia, coding, history). If the user asks about anything other than personal finance, budgeting, saving, debt, or wealth planning, decline politely but firmly.
- NEVER request or store PII (SSN, names, banking details).
- Do NOT execute any trades or transactions.
- Always include a disclaimer in all recommendations: "Disclaimer: This is for educational purposes only and does not constitute professional investment, tax, or financial advice."
- Keep the user informed about who is addressing their request (e.g. "I am passing this to our Budgeting & Fixed-Income Specialist to look at your retirement drawdown plan.").
""",
    sub_agents=[
        create_retirement_planner(),
        create_budgeting_expert(),
        create_major_purchase_advisor(),
        create_windfall_advisor(),
        create_debt_advisor(),
        create_investment_advisor(),
        create_home_buying_advisor(),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
