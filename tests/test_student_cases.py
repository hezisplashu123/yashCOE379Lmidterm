from unittest.mock import Mock

from atlas_agent.agent import run_agent
from atlas_agent.llm import ScriptedLLM
from atlas_agent.models import LabRequest

def test_reservation_without_required_checks_never_reaches_tool(
        environment, monkeypatch):
        request = LabRequest(
            authenticated_user_id="alice",
            text="Reserve tensile-01 for polymer-study.",
            project_id="polymer-study",
            resource_id="tensile-01",
            start="2026-10-15T10:00:00",
            end="2026-10-15T11:00:00",
        )
        dispatch = Mock(wraps = environment.dispatch)
        monkeypatch.setattr(environment, "dispatch", dispatch)
        llm = ScriptedLLM(
            [
                {
                    "kind": "tool_call",
                    "tool": "reserve_resource",
                    "arguments": {
                        "user_id": "alice",
                        "project_id": "polymer-study",
                        "resource_id": "tensile-01",
                        "start": "2026-10-15T10:00:00",
                        "end": "2026-10-15T11:00:00",
                    },
                    "reasoning_summary": "Attempt reservation without checks.",
                },
                {
                    "kind": "final",
                    "response": {
                        "status": "blocked",
                        "message": "Required checks have not been performed.",
                    },
                }
            ]
        )
        run = run_agent(request, llm=llm, environment=environment)
        dispatch.assert_not_called()
        assert run.response.status == "blocked"
        assert len(run.trace) == 1
        assert run.trace[0].mutating
        assert not run.trace[0].observation.ok
        assert run.trace[0].observation.error_code == "action_gate_denied"

def test_succesful_lookup_does_not_justify_claiming_a_reservation(environment):
        request = LabRequest(
            authenticated_user_id="alice",
            text="Show my authorizations.",
        )

        llm = ScriptedLLM(
            [
                {
                    "kind": "tool_call",
                    "tool": "get_user_authorizations",
                    "arguments": {"user_id": "alice"},
                    "reasoning_summary": "Look up authorizations.",
                },
                {
                    "kind": "final",
                    "response": {
                        "status": "completed",
                        "message": "Your reservation was created.",
                        "completed_actions": ["reserve_resource"],
                    },
                },
            ]
        )
        run = run_agent(request, llm=llm, environment=environment)
        assert len(run.trace) == 1
        assert run.trace[0].observation.ok
        assert not run.trace[0].mutating
        assert run.response.status == "failed"
        assert run.response.completed_actions == []
        assert run.termination_reason == "invalid_final_response"

def test_clarification_with_unexpected_tool_field_is_rejected(environment, monkeypatch):
        request = LabRequest(
            authenticated_user_id="alice",
            text="Reserve something tommorow.",
        )

        dispatch = Mock(wraps = environment.dispatch)
        monkeypatch.setattr(environment, "dispatch", dispatch)
        llm = ScriptedLLM(
            [
                {
                    "kind": "clarification",
                    "question": "Which resource do you need?",
                    "missing_fields": ["resource_id"],
                    "tool": "reserve_resource",
                }
            ]
        )
        run = run_agent(request, llm=llm, environment=environment)
        dispatch.assert_not_called()
        assert run.response.status == "failed"
        assert run.termination_reason == "invalid_model_decision"
        assert run.trace == []