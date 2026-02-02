from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.sql_generator import sql_generator_node
from src.nodes.sql_executor import sql_executor_node
from src.nodes.pii_scrubber import pii_scrubber_node
from src.nodes.response_synthesizer import response_synthesizer_node

def should_retry(state: AgentState):
    """
    Conditional edge logic: Determine if we should retry SQL generation.
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    
    if error and retry_count < 3:
        print(f"DEBUG: SQL failed. Retrying... (Attempt {retry_count + 1})")
        return "retry"
    elif error:
        return "error"
    else:
        return "success"

def create_graph():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("sql_executor", sql_executor_node)
    workflow.add_node("pii_scrubber", pii_scrubber_node)
    workflow.add_node("response_synthesizer", response_synthesizer_node)
    
    # Set Entry Point
    workflow.set_entry_point("sql_generator")
    
    # Add Edges
    workflow.add_edge("sql_generator", "sql_executor")
    
    # Conditional Edge from Executor
    workflow.add_conditional_edges(
        "sql_executor",
        should_retry,
        {
            "retry": "sql_generator",
            "error": "response_synthesizer", # Skip PII, go to error reporting
            "success": "pii_scrubber"
        }
    )
    
    workflow.add_edge("pii_scrubber", "response_synthesizer")
    workflow.add_edge("response_synthesizer", END)
    
    return workflow.compile()
