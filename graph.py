from langgraph.graph import END, StateGraph

from nodes import (
    generator_node,
    planner_node,
    quality_critic_node,
    repair_node,
    route_after_quality_critic,
    route_after_schema_verifier,
    schema_verifier_node,
)
from schemas import FlowState


def build_graph():
    graph = StateGraph(FlowState)

    graph.add_node("planner", planner_node)
    graph.add_node("generator", generator_node)
    graph.add_node("schema_verifier", schema_verifier_node)
    graph.add_node("quality_critic", quality_critic_node)
    graph.add_node("repair", repair_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "generator")
    graph.add_edge("generator", "schema_verifier")
    graph.add_conditional_edges(
        "schema_verifier",
        route_after_schema_verifier,
        {
            "repair": "repair",
            "quality_critic": "quality_critic",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "quality_critic",
        route_after_quality_critic,
        {
            "repair": "repair",
            "end": END,
        },
    )
    graph.add_edge("repair", "schema_verifier")

    return graph.compile()
