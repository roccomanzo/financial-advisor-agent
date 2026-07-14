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
import json
import os

from dotenv import load_dotenv

# Load agent's dotenv
load_dotenv(dotenv_path="/Users/roccomanzo/Desktop/financial-advisor-agent/.env")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


async def run_case(case_dict, agent_name):
    # Initialize fresh session service
    session_service = InMemorySessionService()
    session_id = "eval_" + case_dict["eval_case_id"]
    user_id = "eval_user"

    # Create the session
    session = await session_service.create_session(
        app_name="app", user_id=user_id, session_id=session_id
    )

    # Build Runner
    runner = Runner(agent=root_agent, app_name="app", session_service=session_service)

    # Get user prompt
    prompt_text = case_dict["prompt"]["parts"][0]["text"]
    new_message = types.Content(
        role="user", parts=[types.Part.from_text(text=prompt_text)]
    )

    # Execute the agent and record all events
    async for _event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        pass

    # Re-fetch session to get full history (including tool events)
    session = await session_service.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )

    # Structure the turns for the trace JSON
    turn_events = []

    # Add user event first
    user_event_dict = {
        "author": "user",
        "content": {"role": "user", "parts": [{"text": prompt_text}]},
    }
    turn_events.append(user_event_dict)

    # Add all model and tool events from the session
    final_response = None
    for event in session.events:
        if event.author == "user":
            continue

        # Format the content part
        content_dict = None
        if event.content:
            parts = []
            for part in event.content.parts or []:
                part_dict = {}
                if part.text:
                    part_dict["text"] = part.text
                if part.function_call:
                    part_dict["function_call"] = {
                        "name": part.function_call.name,
                        "args": part.function_call.args,
                    }
                if part.function_call and hasattr(part.function_call, "id"):
                    part_dict["function_call"]["id"] = part.function_call.id
                if part.function_response:
                    part_dict["function_response"] = {
                        "name": part.function_response.name,
                        "response": part.function_response.response,
                    }
                parts.append(part_dict)
            content_dict = {"role": event.content.role or "model", "parts": parts}

            # Keep track of the final text response
            texts = [p.get("text") for p in parts if p.get("text")]
            if texts:
                final_response = {"role": "model", "parts": [{"text": "".join(texts)}]}

        turn_events.append({"author": event.author, "content": content_dict})

    # Get the sub-agent details (names, descriptions, instructions)
    agents_map = {}

    def register_agent(ag):
        sub_agent_ids = [sub.name for sub in getattr(ag, "sub_agents", []) or []]
        agent_type = ag.__class__.__name__
        agents_map[ag.name] = {
            "agent_id": ag.name,
            "agent_type": agent_type,
            "description": getattr(ag, "description", "") or "",
            "instruction": getattr(ag, "instruction", "") or "",
            "sub_agents": sub_agent_ids,
        }
        for sub in getattr(ag, "sub_agents", []) or []:
            register_agent(sub)

    register_agent(root_agent)

    # Construct the final trace case dictionary
    trace_case = {
        "eval_case_id": case_dict["eval_case_id"],
        "agent_data": {
            "agents": agents_map,
            "turns": [{"turn_index": 0, "events": turn_events}],
        },
    }

    if final_response:
        trace_case["responses"] = [{"response": final_response}]

    return trace_case


async def main():
    dataset_path = "/Users/roccomanzo/Desktop/financial-advisor-agent/tests/eval/datasets/financial-advisor-dataset.json"
    output_path = "/Users/roccomanzo/Desktop/financial-advisor-agent/artifacts/traces/financial-advisor-dataset-traces.json"

    print(f"Loading dataset from: {dataset_path}")
    with open(dataset_path) as f:
        data = json.load(f)

    eval_cases = data.get("eval_cases", [])
    print(f"Loaded {len(eval_cases)} cases.")

    traces = []
    for i, case in enumerate(eval_cases):
        print(
            f"Running inference for case {i + 1}/{len(eval_cases)}: {case['eval_case_id']}"
        )
        try:
            trace = await run_case(case, root_agent.name)
            traces.append(trace)
            print(f"Case {case['eval_case_id']} finished successfully.")
        except Exception as e:
            print(f"Case {case['eval_case_id']} failed: {e}")
            import traceback

            traceback.print_exc()

    # Write to output traces file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"eval_cases": traces}, f, indent=2)

    print(f"Wrote traces to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
