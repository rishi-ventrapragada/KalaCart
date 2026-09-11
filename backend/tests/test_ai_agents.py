"""
Test Suite for Universal AI Agent Platform (KalaCart V10)
Verifies:
- Tool registry retrieval across specialized agents
- Agent task delegation and execution (Catalog, Pricing, Negotiation, Support)
- Multi-agent collaboration across an end-to-end product onboarding pipeline
- Shared blackboard memory layer persistence
- Human-in-the-loop approval workflow
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_agent_tools():
    response = client.get("/api/v1/agents/tools")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "tools" in data
    assert data["count"] >= 4
    tool_names = [t["tool_name"] for t in data["tools"]]
    assert "verify_gi_registry" in tool_names
    assert "calculate_fair_wage" in tool_names
    assert "generate_customs_manifest" in tool_names


def test_delegate_single_agent_tasks():
    # 1. Delegate task to Catalog Agent
    cat_res = client.post(
        "/api/v1/agents/delegate",
        json={
            "delegator": "supervisor_orchestrator",
            "assignee": "catalog_agent",
            "goal": "Verify GI origin and generate catalog tags",
            "input_context": {
                "craft_name": "Kullu Handloom Shawl",
                "region": "Himachal Pradesh",
                "material": "Pure Merino & Angora Wool",
            },
            "requires_human_approval": False,
        },
    )
    assert cat_res.status_code == 200
    task_cat = cat_res.json()["task"]
    assert task_cat["status"] == "completed"
    assert task_cat["output_result"]["gi_tag_verified"] is True
    assert "Himachal Pradesh" in task_cat["output_result"]["title"]

    # 2. Delegate task to Negotiation Agent
    neg_res = client.post(
        "/api/v1/agents/delegate",
        json={
            "delegator": "supervisor_orchestrator",
            "assignee": "negotiation_agent",
            "goal": "Evaluate wholesale bulk offer",
            "input_context": {
                "buyer_bid_inr": 3500.0,
                "min_negotiation_floor_inr": 3200.0,
                "recommended_mrp_inr": 4800.0,
                "quantity": 15,
            },
            "requires_human_approval": False,
        },
    )
    assert neg_res.status_code == 200
    task_neg = neg_res.json()["task"]
    assert task_neg["status"] == "completed"
    assert task_neg["output_result"]["decision"] == "ACCEPT"


def test_full_multi_agent_onboarding_pipeline():
    # Execute full cooperating pipeline: Catalog -> Pricing -> Marketing -> Export -> Inventory
    payload = {
        "craft_name": "Bidriware Silver Inlay Hookah Base",
        "region": "Bidar, Karnataka",
        "material": "Zinc Copper Alloy & Pure Silver Inlay",
        "material_cost": 2200.0,
        "hours_worked": 18.0,
        "initial_stock": 40,
        "destination_country": "US",
    }
    response = client.post("/api/v1/agents/workflow/onboard-craft", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "collaborating_agents" in data
    assert len(data["collaborating_agents"]) == 5

    # Verify Catalog Agent output
    assert "Bidriware" in data["catalog_metadata"]["title"]
    assert data["catalog_metadata"]["gi_tag_verified"] is True

    # Verify Pricing Agent output: 2200 material + (18 * 250 wage = 4500) = 6700 base cost -> MRP 9045
    pricing = data["pricing_breakdown"]
    assert pricing["fair_artisan_wage_inr"] == 4500.0
    assert pricing["base_cost_inr"] == 6700.0
    assert pricing["recommended_mrp_inr"] == 9045.0

    # Verify Marketing Agent output
    assert "instagram_caption" in data["marketing_narrative"]

    # Verify Export Agent output
    assert data["export_customs"]["hs_code"] == "7419.80.00"

    # Verify Inventory Agent output
    assert data["inventory_status"]["initial_stock"] == 40

    # Verify Shared Memory Layer
    mem_res = client.get("/api/v1/agents/memory")
    assert mem_res.status_code == 200
    assert len(mem_res.json()["memory_snapshot"]) > 0


def test_human_in_the_loop_approval_workflow():
    # 1. Delegate a sensitive high-discount pricing task requiring human approval
    task_res = client.post(
        "/api/v1/agents/delegate",
        json={
            "delegator": "negotiation_agent",
            "assignee": "pricing_agent",
            "goal": "Authorize deep 50% discount for institutional government tender",
            "input_context": {
                "material_cost": 1000.0,
                "hours_worked": 10.0,
            },
            "requires_human_approval": True,
        },
    )
    assert task_res.status_code == 200
    task_data = task_res.json()["task"]
    task_id = task_data["id"]
    assert task_data["status"] == "awaiting_human_approval"
    assert task_data["human_approval_required"] is True

    # 2. Human Admin Approves Task
    approval_res = client.post(
        "/api/v1/agents/human-approval",
        json={
            "task_id": task_id,
            "approved": True,
            "reviewer_name": "Senior Artisan Guild Master (Ramesh)",
        },
    )
    assert approval_res.status_code == 200
    approved_task = approval_res.json()["task"]
    assert approved_task["status"] == "completed"
    assert approved_task["approval_status"] == "approved"
    assert approved_task["approved_by"] == "Senior Artisan Guild Master (Ramesh)"
    assert "recommended_mrp_inr" in approved_task["output_result"]
