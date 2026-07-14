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
import os
import re

from google.adk.runners import Runner
from opentelemetry import trace

logger = logging.getLogger(__name__)

# 1. PII Redaction
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


def redact_pii(text: str) -> str:
    if not text:
        return text
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)
    text = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", text)
    return text


# 2. Structured JSON Logging Formatter
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if isinstance(record.msg, dict):
            log_data.update(record.msg)
            log_data.pop("message", None)
        elif (
            record.msg
            and str(record.msg).startswith("{")
            and str(record.msg).endswith("}")
        ):
            try:
                log_data.update(json.loads(record.msg))
                log_data.pop("message", None)
            except Exception:
                pass
        return json.dumps(log_data)


def configure_json_logging() -> None:
    """Register custom JSON log formatting on the root logging handler."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler.formatter, JSONFormatter):
            return
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)


# 3. Intent & Outcome Classifier
def enrich_telemetry(query: str, response: str):
    query_lower = query.lower()
    intent = "general_financial"
    if any(k in query_lower for k in ["retire", "401k", "nest egg", "nestegg", "ira"]):
        intent = "retirement_planning"
    elif any(
        k in query_lower
        for k in [
            "house",
            "home",
            "piti",
            "afford",
            "mortgage",
            "interest rate",
            "preapprove",
        ]
    ):
        intent = "home_buying"
    elif any(
        k in query_lower
        for k in ["stock", "fund", "invest", "share", "liability", "asset", "cashflow"]
    ):
        intent = "investment"
    elif any(k in query_lower for k in ["budget", "expense", "spend", "saving"]):
        intent = "budgeting"
    elif any(k in query_lower for k in ["debt", "loan", "payoff", "owe"]):
        intent = "debt_management"
    elif any(k in query_lower for k in ["windfall", "inherit", "lottery", "bonus"]):
        intent = "windfall_management"

    response_lower = response.lower()
    outcome = "success"
    if any(
        k in response_lower
        for k in ["cannot answer", "decline", "strictly a financial", "irrelevant"]
    ):
        outcome = "safety_rejection"

    # Set attributes on active OpenTelemetry span
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("agent.intent", intent)
        span.set_attribute("agent.outcome", outcome)

    # Redact PII before logging!
    redacted_query = redact_pii(query)
    redacted_response = redact_pii(response)

    # Emit structured JSON log event
    telemetry_logger = logging.getLogger("agent.telemetry")
    telemetry_logger.info(
        {
            "event_type": "agent_execution",
            "intent": intent,
            "outcome": outcome,
            "query": redacted_query,
            "response": redacted_response,
        }
    )


# 4. Monkey-patch Runner execution
original_run = Runner.run
original_run_async = Runner.run_async


def wrap_run(orig):
    def new_run(self, *args, **kwargs):
        new_message = kwargs.get("new_message")
        if not new_message and len(args) >= 3:
            new_message = args[2]
        query_text = ""
        if new_message and hasattr(new_message, "parts"):
            query_text = "".join(part.text for part in new_message.parts if part.text)

        response_parts = []
        for event in orig(self, *args, **kwargs):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_parts.append(part.text)
            yield event

        response_text = "".join(response_parts)
        try:
            enrich_telemetry(query_text, response_text)
        except Exception:
            pass

    return new_run


def wrap_run_async(orig_async):
    async def new_run_async(self, *args, **kwargs):
        new_message = kwargs.get("new_message")
        if not new_message and len(args) >= 3:
            new_message = args[2]
        query_text = ""
        if new_message and hasattr(new_message, "parts"):
            query_text = "".join(part.text for part in new_message.parts if part.text)

        response_parts = []
        async for event in orig_async(self, *args, **kwargs):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_parts.append(part.text)
            yield event

        response_text = "".join(response_parts)
        try:
            enrich_telemetry(query_text, response_text)
        except Exception:
            pass

    return new_run_async


Runner.run = wrap_run(original_run)
Runner.run_async = wrap_run_async(original_run_async)


def setup_telemetry() -> str | None:
    """Configure GenAI prompt/response logging via OpenTelemetry."""
    configure_json_logging()
    # Keep full prompts/responses out of trace span attributes (use GenAI logging instead).
    os.environ.setdefault("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false")
    os.environ.setdefault("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true")

    bucket = os.environ.get("LOGS_BUCKET_NAME")
    capture_content = os.environ.get(
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false"
    )
    if bucket and capture_content != "false":
        logging.info(
            "Prompt-response logging enabled - mode: NO_CONTENT (metadata only, no prompts/responses)"
        )
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "NO_CONTENT"
        os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT", "jsonl")
        os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK", "upload")
        os.environ.setdefault(
            "OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental"
        )
        commit_sha = os.environ.get("COMMIT_SHA", "dev")
        os.environ.setdefault(
            "OTEL_RESOURCE_ATTRIBUTES",
            f"service.namespace=financial-advisor-agent,service.version={commit_sha}",
        )
        path = os.environ.get("GENAI_TELEMETRY_PATH", "completions")
        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH",
            f"gs://{bucket}/{path}",
        )
    else:
        logging.info(
            "Prompt-response logging disabled (set LOGS_BUCKET_NAME=gs://your-bucket and OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT to enable)"
        )

    return bucket


def setup_agent_engine_telemetry() -> None:
    """Install the Agent Engine tracer provider (traces/logs to the customer project).

    Tags spans with the reasoningEngine resource. The OTel resource is fixed at
    provider creation, so this must run before get_fast_api_app to set the tags.
    No-op unless GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY is set.
    """
    if os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "").lower() not in (
        "true",
        "1",
    ):
        return

    import google.auth
    from vertexai.agent_engines.templates.adk import _default_instrumentor_builder

    try:
        _, project_id = google.auth.default()
        _default_instrumentor_builder(
            project_id, enable_tracing=True, enable_logging=True
        )
    except Exception as e:
        logger.warning(f"Could not initialize telemetry: {e}")
