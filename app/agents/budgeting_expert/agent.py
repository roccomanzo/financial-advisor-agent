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

from pathlib import Path

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types


def get_instruction():
    path = Path(__file__).parent / "instruction.md"
    return path.read_text(encoding="utf-8")


def create_agent():
    return Agent(
        name="budgeting_expert",
        model=Gemini(
            model="gemini-3.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description="Specialist for day-to-day budgeting, expense tracking, and living on a fixed income or retirement drawdowns.",
        instruction=get_instruction(),
    )
