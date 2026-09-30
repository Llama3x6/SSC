import operator
from datetime import datetime
from typing import Annotated, Any, TypedDict

import requests
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from llm import call_llm, call_llm_structured
from models import Order, Product, ReorderNarrative

BASE_URL = "http://localhost:8000"

load_dotenv()


class AgentState(TypedDict):
    reorder: list[Product]  # products that qualify for reorder
    ordered: Annotated[list[Order], operator.add]  # proposed reorders (confirm w/ hitl)
    log: Annotated[list[str], operator.add]


def fetch_products(state: AgentState) -> dict[str, Any]:
    resp = requests.get(f"{BASE_URL}/products")
    products = [Product(**p) for p in resp.json()]
    reorder_products = [p for p in products if p.current_stock <= p.reorder_threshold]

    log_msg = f"Filtered {len(reorder_products)} products below reorder threshold"

    return {"reorder": reorder_products, "log": [log_msg]}


def should_reorder(state: AgentState) -> str:
    if len(state["reorder"]) == 0:
        return "no_reorder"
    return "reorder"


def propose_reorder(state: AgentState) -> dict[str, Any]:
    proposed_orders = []
    log_messages = []

    for product in state["reorder"]:
        resp = requests.get(
            f"{BASE_URL}/supplier-product/supplier_recommendations",
            params={"sku": product.sku},
        )

        if resp.status_code != 200 or not resp.json():
            log_messages.append(f"No suppliers found for '{product.sku}' — skipping")
            continue

        top_supplier = resp.json()[0]
        order_qty = product.reorder_threshold * 5 - product.current_stock

        if order_qty > 0:
            proposed_orders.append(
                Order(
                    product_sku=product.sku,
                    supplier_id=top_supplier["id"],
                    quantity=order_qty,
                )
            )

    log_messages.append(f"Proposed {len(proposed_orders)} orders to replenish stock")

    return {"ordered": proposed_orders, "log": log_messages}


# HITL approval for proposed orders happens
def hitl_reorder_narrative(state: AgentState) -> dict[str, Any]:
    products_summary = "\n".join(
        f"- SKU: {p.sku}, Name: {p.name}, Stock: {p.current_stock}, Threshold: {p.reorder_threshold}"
        for p in state["reorder"]
    )
    orders_summary = "\n".join(
        f"- SKU: {o.product_sku}, Supplier ID: {o.supplier_id}, Quantity: {o.quantity}"
        for o in state["ordered"]
    )
    prompt = f"""You are a supply chain assistant. Analyze the following reorder proposal and provide structured feedback for a human operator.

Products below threshold:
{products_summary}

Proposed orders:
{orders_summary}

Provide:
1. A clear summary of what's happening
2. List of products below threshold with their stock levels
3. List of proposed orders with details
4. Any risk flags (supplier reliability, cost concerns, etc.)
5. A clear recommendation: 'approve', 'review_first', or 'reject_and_reason'
"""
    narrative = call_llm_structured(prompt, ReorderNarrative)

    # Format the structured output for the log
    formatted = f"""REORDER NARRATIVE (STRUCTURED):
Summary: {narrative.summary}
Low Products: {', '.join(narrative.low_products)}
Proposed Orders: {', '.join(narrative.proposed_orders)}
Risk Flags: {', '.join(narrative.risk_flags) if narrative.risk_flags else 'None'}
Recommendation: {narrative.recommendation}
"""
    return {"log": [formatted]}


# post orders to API and update state with confirmed orders
def commit_orders(state: AgentState) -> dict[str, Any]:
    confirmed_orders = []
    for order in state["ordered"]:
        payload = order.model_dump(mode="json")
        resp = requests.post(f"{BASE_URL}/orders", json=payload)
        if resp.status_code == 201:
            confirmed_orders.append(Order(**resp.json()))
        else:
            log_msg = f"Failed to commit order for {order.product_sku}: {resp.text}"
            return {"ordered": confirmed_orders, "log": [log_msg]}

    log_msg = f"Committed {len(confirmed_orders)} orders to the system"

    return {"log": [log_msg]}


def log_run(state: AgentState) -> dict:
    log_msg = f"FINAL MESSAGE => Current state: {len(state['reorder'])} products to reorder, {len(state['ordered'])} orders proposed/committed"
    with open("agent_run.log", "a") as log_file:
        log_file.write("\n".join(state["log"]) + "\n" + log_msg + "\n")
    return {}


# =============================================================================================
#


memory = MemorySaver()

graph = StateGraph(AgentState)

graph.add_node("fetch_products", fetch_products)
graph.add_node("propose_reorder", propose_reorder)
graph.add_node("commit_orders", commit_orders)
graph.add_node("hitl_reorder_narrative", hitl_reorder_narrative)
graph.add_node("log_run", log_run)

graph.add_edge(START, "fetch_products")
graph.add_conditional_edges(
    "fetch_products",
    should_reorder,
    {"reorder": "propose_reorder", "no_reorder": "log_run"},
)
# HITL approval for proposed orders happens here
graph.add_edge("propose_reorder", "hitl_reorder_narrative")
graph.add_edge("hitl_reorder_narrative", "commit_orders")
graph.add_edge("commit_orders", "log_run")
graph.add_edge("log_run", END)

app = graph.compile(checkpointer=memory, interrupt_before=["commit_orders"])


# =============================================================================================
#


def run_agent():
    config = {
        "configurable": {
            "thread_id": f"reorder-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
    }

    initial_state = {"reorder": [], "ordered": [], "log": []}

    # Run until interrupt
    app.invoke(initial_state, config)

    # Graph is now paused before commit_orders
    # Get current state to show human what was proposed
    current_state = app.get_state(config)
    proposed = current_state.values["ordered"]

    if not proposed:
        print("No orders to propose.")
        return

    print("\n--- Reorder Summary ---")
    print(current_state.values["log"][-1])  # narrative is last log entry

    approval = input("\nApprove orders? (yes/no): ").strip().lower()

    if approval == "yes":
        # Resume graph
        app.invoke(None, config)
        print("Orders committed.")
    else:
        print("Orders rejected. Logging and exiting.")
        # Skip commit, jump straight to log
        app.update_state(config, {}, as_node="commit_orders")
        app.invoke(None, config)


if __name__ == "__main__":
    run_agent()
