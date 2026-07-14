# ruff: noqa: E402
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

import asyncio

from dotenv import load_dotenv

# Load agent's dotenv
load_dotenv(dotenv_path="/Users/roccomanzo/Desktop/financial-advisor-agent/.env")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


async def run_turn(runner, user_id, session_id, message_text):
    print(f"\n[User]: {message_text}")
    print("[Agent]: ", end="", flush=True)

    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=message_text)]
    )

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        # Print text events as they stream or finish
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
                elif part.function_call:
                    print(
                        f"\n   [Tool Call]: {part.function_call.name}({part.function_call.args})",
                        end="",
                        flush=True,
                    )
                elif part.function_response:
                    print(
                        f"\n   [Tool Response]: {part.function_response.name} -> {part.function_response.response}\n   [Agent]: ",
                        end="",
                        flush=True,
                    )
    print()


async def main():
    session_service = InMemorySessionService()
    session_id = "simulation_budget_conversation"
    user_id = "simulated_user"

    # Create session
    await session_service.create_session(
        app_name="app", user_id=user_id, session_id=session_id
    )

    # Build Runner
    runner = Runner(agent=root_agent, app_name="app", session_service=session_service)

    print("======================================================================")
    print("Starting Multi-Turn Budgeting & Debt Payoff Simulation")
    print("======================================================================")

    # Turn 1: Initial query
    await run_turn(
        runner,
        user_id,
        session_id,
        "Hi, I need help setting up a budget for my family.",
    )

    # Turn 2: Providing financial details (routes to budgeting_expert)
    await run_turn(
        runner,
        user_id,
        session_id,
        "Our monthly income is $6,000. Rent is $2,200. We spend about $600 on groceries, $500 on utilities/transport, and we have $1,000 in credit card debt we want to pay off.",
    )

    # Turn 3: Asking about debt payoff math (routes to debt_advisor)
    await run_turn(
        runner,
        user_id,
        session_id,
        "That sounds good. How long will it take us to pay off the $1,000 credit card debt if we pay $200 a month at an 18% APR?",
    )

    print("\n======================================================================")
    print("Simulation Complete")
    print("======================================================================")


if __name__ == "__main__":
    asyncio.run(main())
