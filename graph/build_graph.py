"""
Builds and compiles the LangGraph StateGraph.
The conditional edge between validate_pitch and score_match is the
core agentic behaviour — it's what makes this a graph, not a pipeline.
"""

from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import (
    parse_resume_node,
    parse_jobs_node,
    score_match_node,
    validate_pitch_node,
    aggregate_results_node,
)


def should_retry(state: AgentState) -> str:
    """
    Conditional edge function — the decision point of the graph.
    If validation failed and we still have retries left, go back
    to score_match. Otherwise we're done.
    """
    if not state.get("validation_passed", True):
        return "retry"
    return "done"


def build_graph():
    graph = StateGraph(AgentState)

    # register nodes
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("parse_jobs", parse_jobs_node)
    graph.add_node("score_match", score_match_node)
    graph.add_node("validate_pitch", validate_pitch_node)
    graph.add_node("aggregate_results", aggregate_results_node)

    # linear edges
    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "parse_jobs")
    graph.add_edge("parse_jobs", "score_match")
    graph.add_edge("score_match", "validate_pitch")

    # conditional edge — this is the agentic part
    graph.add_conditional_edges(
        "validate_pitch",
        should_retry,
        {
            "retry": "score_match",   # loop back with retry context
            "done": "aggregate_results",              # all pitches valid, finish
        },
    )
    graph.add_edge("aggregate_results", END)

    return graph.compile()