from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator

class AgentState(TypedDict, total=False):
    """
    The state of the agent in the LangGraph workflow.
    All fields are optional to allow partial state updates.
    """
    # Chat history
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # The user's original question
    user_question: str
    
    # The generated SQL query
    generated_sql: Optional[str]
    
    # The raw result from the database (list of dicts)
    query_result: Optional[List[Dict[str, Any]]]
    
    # The final answer to present to the user
    final_answer: Optional[str]
    
    # Error tracking for resilience loop
    error: Optional[str]
    retry_count: int
    
    # Context retrieved from "Golden Knowledge"
    golden_examples: Optional[str]
