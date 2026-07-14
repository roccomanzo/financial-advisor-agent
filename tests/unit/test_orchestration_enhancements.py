from unittest.mock import MagicMock

import pytest
from google.genai import types as genai_types

from app.app_utils.telemetry import GuardrailPlugin
from app.tools import (
    check_housing_risk_requires_confirmation,
    verify_affordability_risk,
)


def test_verify_affordability_risk():
    # Safe PITI percentage
    res_safe = verify_affordability_risk(25.0)
    assert res_safe["status"] == "safe"
    assert "Housing cost consumes" in res_safe["message"]

    # Risky PITI percentage
    res_risky = verify_affordability_risk(45.0)
    assert res_risky["status"] == "warning"
    assert "CRITICAL RISK" in res_risky["message"]


def test_check_housing_risk_requires_confirmation():
    # Safe ratio -> No confirmation
    assert check_housing_risk_requires_confirmation(25.0) is False

    # Risky ratio -> Requires human confirmation
    assert check_housing_risk_requires_confirmation(45.0) is True


@pytest.mark.asyncio
async def test_guardrail_plugin_pii_redaction():
    plugin = GuardrailPlugin(name="guardrail")

    # Mock callback context with a response that leaks an email
    mock_event = MagicMock()
    mock_event.content.parts = [
        genai_types.Part.from_text(
            text="Please email me at support@example.com for more."
        )
    ]
    mock_event.content.role = "model"

    mock_context = MagicMock()
    mock_context.session.events = [mock_event]

    res = await plugin.after_agent_callback(callback_context=mock_context)

    assert res is not None
    assert "[REDACTED_EMAIL]" in res.parts[0].text
    assert "support@example.com" not in res.parts[0].text


@pytest.mark.asyncio
async def test_guardrail_plugin_disclaimer_enforcement():
    plugin = GuardrailPlugin(name="guardrail")

    # Long financial message missing disclaimer
    long_response = (
        "Based on your gross monthly income of $10,000, we recommend budgeting "
        "approximately $2,500 towards your fixed mortgage payments, which includes "
        "your principal, interest, local property taxes, and home insurance premium estimations."
    )

    mock_event = MagicMock()
    mock_event.content.parts = [genai_types.Part.from_text(text=long_response)]
    mock_event.content.role = "model"

    mock_context = MagicMock()
    mock_context.session.events = [mock_event]

    res = await plugin.after_agent_callback(callback_context=mock_context)

    assert res is not None
    assert "Disclaimer:" in res.parts[0].text
