"""Milestone 3: implement three selected validation responsibilities."""

from __future__ import annotations

from .agent_models import ToolCallDecision
from .models import AgentResponse, LabRequest, TraceEvent
from .policy_context import ReservationContext, build_reservation_context


def validate_request_binding(
    decision: ToolCallDecision,
    *,
    request: LabRequest,
) -> list[str]:
    errors: list[str] = []
    arguments = decision.arguments

    if "user_id" in arguments and arguments["user_id"] != request.authenticated_user_id:
        errors.append("user_id_must_match_authenticated_user")

    for field in ("project_id", "resource_id", "start", "end"):
        trusted_value = getattr(request, field)

        if trusted_value is None:
            if decision.tool == "reserve_resource":
                errors.append(f"{field}_unresolved_in_request")
        elif field in arguments and arguments[field] != trusted_value:
            errors.append(f"{field}_does_not_match_request")

    return errors


def validate_reservation_preconditions(context: ReservationContext) -> list[str]:
    """TODO 3.2: Return an error for every required context fact that is false."""
    errors: list[str] = []

    error_codes = {
        "qualification_current": "required_qualification_missing",
        "calibration_current": "calibration_not_current",
    }

    for name, satisfied in context.model_dump().items():
        if not satisfied:
            errors.append(
                error_codes.get(name, f"Reservation precondition failed: {name}")
            )
    return errors


def validate_proposed_tool_call(
    decision: ToolCallDecision,
    *,
    request: LabRequest,
    trace: list[TraceEvent],
) -> list[str]:
    """Supplied wrapper. Do not modify this function."""
    errors = validate_request_binding(decision, request=request)
    if decision.tool == "reserve_resource":
        context = build_reservation_context(decision, trace)
        errors.extend(validate_reservation_preconditions(context))
    return errors


def retrieved_passage_ids(trace: list[TraceEvent]) -> set[str]:
    """Supplied helper. Do not modify this function."""
    identifiers: set[str] = set()
    for event in trace:
        if event.observation.tool != "search_lab_documents" or not event.observation.ok:
            continue
        identifiers.update(
            passage["passage_id"]
            for passage in event.observation.data.get("passages", [])
        )
    return identifiers


def validate_final_response(
    response: AgentResponse, trace: list[TraceEvent]
) -> list[str]:
    """Validate citations, claimed actions, and final status."""
    errors: list[str] = []
    retrieved_ids = retrieved_passage_ids(trace)

    for citation in response.citations:
        if citation not in retrieved_ids:
            errors.append(f"citations_not_retrieved: {citation}.")

    successful_mutations = {
        event.observation.tool
        for event in trace
        if event.mutating and event.observation.ok
    }

    for action in response.completed_actions:
        if action not in successful_mutations:
            errors.append(f"completed_action_not_in_successful_trace")

    if response.status == "completed":
        if not successful_mutations:
            errors.append("completed_without_successful_mutation")
        if not response.completed_actions:
            errors.append("Completed status requires at least one completed action.")
    else:
        if response.completed_actions:
            errors.append("A non-completed response cannot claim completed actions.")
        if successful_mutations:
            errors.append(
                "A non-completed response leaves a successful mutation " "unreported."
            )

    return errors
