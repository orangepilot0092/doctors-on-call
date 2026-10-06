"""
Multi-Agent Supervisor using LangGraph.
Orchestrates the shift-filling process by delegating tasks to specialized agents.
"""
from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class ShiftState(TypedDict):
    shift_id: int
    shift_details: dict
    matched_doctors: List[dict]
    messages: Annotated[List[str], operator.add]
    is_notified: bool  # 🆕 Memory flag to prevent infinite loops
    next_step: str

# 🧠 Node 1: The Supervisor (Routes tasks based on state memory)
def supervisor_node(state: ShiftState) -> dict:
    print("🧠 Supervisor: Analyzing shift requirements...")
    
    # 1. Check if the job is already done
    if state.get("is_notified"):
        return {"next_step": "FINISH", "messages": ["Supervisor: Shift filling complete. Terminating workflow."]}
        
    # 2. If no doctors found yet, route to Matching Agent
    if not state.get("matched_doctors"):
        return {"next_step": "match", "messages": ["Supervisor: Routing to Matching Agent."]}
        
    # 3. If doctors are found but not notified, route to Notification Agent
    return {"next_step": "notify", "messages": ["Supervisor: Routing to Notification Agent."]}

# 🔍 Node 2: Matching Agent (Uses pgvector + Transit Logic)
def matching_agent_node(state: ShiftState) -> dict:
    print("🔍 Matching Agent: Finding best doctors via pgvector and transit logic...")
    mock_matches = [
        {"doctor_id": 1, "name": "Dr. Rohan Sharma", "score": 200},
        {"doctor_id": 2, "name": "Dr. Anita Desai", "score": 150}
    ]
    return {
        "matched_doctors": mock_matches,
        "messages": [f"Matching Agent: Found {len(mock_matches)} verified candidates."]
    }

# 📱 Node 3: Notification Agent (Uses WhatsApp Gateway)
def notification_agent_node(state: ShiftState) -> dict:
    print("📱 Notification Agent: Broadcasting to WhatsApp...")
    doctors = state["matched_doctors"]
    return {
        "messages": [f"Notification Agent: Sent WhatsApp alerts to {len(doctors)} doctors."],
        "is_notified": True  # 🆕 Set memory flag so Supervisor knows to END
    }

# 🕸️ Build the Cyclic Graph
def build_supervisor_graph():
    workflow = StateGraph(ShiftState)
    
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("match", matching_agent_node)
    workflow.add_node("notify", notification_agent_node)
    
    workflow.set_entry_point("supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_step"],
        {"match": "match", "notify": "notify", "FINISH": END}
    )
    
    workflow.add_edge("match", "supervisor") 
    workflow.add_edge("notify", "supervisor") 
    
    return workflow.compile()

shift_graph = build_supervisor_graph()
