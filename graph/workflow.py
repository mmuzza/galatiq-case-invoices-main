
import os
import json
from typing import TypedDict, Optional, Any
from typing_extensions import Annotated
 
from langgraph.graph import StateGraph, END

from agents.normalization_agent import normalize_invoice
from agents.validation_agent import validate_invoice
from agents.approval_agent import approval_agent
from agents.payment_agent import payment
from utils.parser import load_invoice_file, load_json_invoice
from utils.helpers import load_inventory_canonical, apply_canonical_to_invoice
from utils.logger import section, setup_logger, pretty_log_dict
 
 
logger = setup_logger()
 
 
# 1. Shared state that flows through every node 
class WorkflowState(TypedDict):
    
    client: Any
    file_path: str
    db_path: str
 

    invoice_obj: Optional[dict]
    inventory_canon: Optional[dict]
    errors: Optional[dict]
    vp_review: Optional[dict]
    payment_status: Optional[dict]
 
 
# 2. Node definitions (one per pipeline stage)
 
def node_load_db(state: WorkflowState) -> dict:
    
    db_path = state["db_path"]
    if not os.path.exists(db_path):
        import services.inventory_service
 
    inventory_canon = load_inventory_canonical(db_path)
    return {"inventory_canon": inventory_canon}
 
 
def node_normalize(state: WorkflowState) -> dict:

    file_path = state["file_path"]
    client = state["client"]
    inventory_canon = state["inventory_canon"]
 
    if file_path.endswith(".json"):
        invoice_obj = load_json_invoice(file_path)
    else:
        raw_text = load_invoice_file(file_path)
        invoice_obj = normalize_invoice(raw_text, client)
 
    apply_canonical_to_invoice(invoice_obj, inventory_canon)
 
    section("NORMALIZATION AGENT")
    pretty_log_dict(invoice_obj)
 
    return {"invoice_obj": invoice_obj}
 
 
def node_validate(state: WorkflowState) -> dict:

    errors = validate_invoice(state["invoice_obj"], state["db_path"])
 
    section("VALIDATION AGENT")
    pretty_log_dict(errors)
 
    return {"errors": errors}
 
 
def node_approval(state: WorkflowState) -> dict:

    vp_review = approval_agent(state["errors"], state["invoice_obj"], state["client"])
 
    section("APPROVAL AGENT")
    pretty_log_dict(vp_review)
 
    return {"vp_review": vp_review}
 
 
def node_payment(state: WorkflowState) -> dict:


    payment_status = payment(
        state["invoice_obj"],
        state["errors"],
        state["vp_review"],
    )
 
    section("PAYMENT AGENT")
    pretty_log_dict(payment_status)
 
    return {"payment_status": payment_status}
 
 
# 3. Building the graph using all the nodes/agent
 
def build_workflow() -> StateGraph:
    graph = StateGraph(WorkflowState)
 
    # Registering nodes
    graph.add_node("load_db",   node_load_db)
    graph.add_node("normalize", node_normalize)
    graph.add_node("validate",  node_validate)
    graph.add_node("approval",  node_approval)
    graph.add_node("payment",   node_payment)
 
    # Connecting the edges/flow
    graph.set_entry_point("load_db")
    graph.add_edge("load_db",   "normalize")
    graph.add_edge("normalize", "validate")
    graph.add_edge("validate",  "approval")
    graph.add_edge("approval",  "payment")
    graph.add_edge("payment",   END)
 
    return graph.compile()
 
 
# 4. Public entry-point
_app = build_workflow()
 
 
def run_workflow(client, file_path: str, db_path: str) -> dict:


    initial_state: WorkflowState = {
        "client": client,
        "file_path": file_path,
        "db_path": db_path,
        "invoice_obj": None,
        "inventory_canon": None,
        "errors": None,
        "vp_review": None,
        "payment_status": None,
    }
 
    final_state = _app.invoke(initial_state)
    return final_state