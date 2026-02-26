from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from tavily import TavilyClient
import os

# 1. Defining the State (what data moves through the graph)
class AgentState(TypedDict):
    event_data: dict
    verifications: List[str]
    is_verified: bool
    iterations: int

tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

# 2. Node: Verification Logic
def verify_event_node(state: AgentState):
    event = state['event_data']
    query = f"Berlin event {event['eventName']} at {event['venueName']} date verification"
    
    # Automatic search
    search_results = tavily.search(query=query, search_depth="basic")
    
    # If search finds matches, mark as verified
    state['is_verified'] = len(search_results) > 0
    state['iterations'] += 1
    return state

# 3. Create the Graph
workflow = StateGraph(AgentState)
workflow.add_node("verifier", verify_event_node)
workflow.set_entry_point("verifier")

# Conditional Edge: If not verified, we could route back to Mastra
workflow.add_edge("verifier", END)

app_graph = workflow.compile()