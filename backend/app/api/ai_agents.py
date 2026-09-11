"""
Universal AI Agent Platform API Router (KalaCart V10)
Exposes agent task delegation, multi-agent collaborative workflows, shared memory inspection,
tool registry, and human-in-the-loop approvals.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.ai_agents import (
    universal_agent_manager,
    AgentType,
    TaskStatus,
)

router = APIRouter(prefix="/api/v1/agents", tags=["Universal AI Agent Platform (V10)"])


class DelegateTaskRequest(BaseModel):
    delegator: str = "supervisor_orchestrator"
    assignee: str = "catalog_agent"
    goal: str
    input_context: Dict[str, Any] = {}
    requires_human_approval: bool = False


class HumanApprovalRequest(BaseModel):
    task_id: str
    approved: bool
    reviewer_name: str


class OnboardProductWorkflowRequest(BaseModel):
    craft_name: str
    region: str
    material: str
    material_cost: float
    hours_worked: float
    initial_stock: int = 50
    destination_country: str = "US"


class StartConversationRequest(BaseModel):
    session_id: str
    prompt: str
    initiator: str = "artisan"


@router.get("/tools")
async def list_registered_tools():
    """Retrieve all executable domain tools registered across specialized agents."""
    return {
        "count": len(universal_agent_manager.tool_registry.get_tools_list()),
        "tools": universal_agent_manager.tool_registry.get_tools_list(),
    }


@router.get("/memory")
async def get_shared_memory():
    """Retrieve global shared blackboard memory across collaborating agents."""
    return {
        "memory_snapshot": universal_agent_manager.memory.get_all(),
    }


@router.post("/conversation/start")
async def start_agent_conversation(req: StartConversationRequest):
    """Start an agentic session with conversation history tracking."""
    history = universal_agent_manager.start_conversation(
        session_id=req.session_id,
        initial_prompt=req.prompt,
        initiator=req.initiator,
    )
    return {
        "session_id": req.session_id,
        "history": [m.model_dump() for m in history],
    }


@router.post("/delegate")
async def delegate_agent_task(req: DelegateTaskRequest):
    """Delegate a discrete specialized task to a targeted AI agent."""
    try:
        del_type = AgentType(req.delegator)
        ass_type = AgentType(req.assignee)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid delegator or assignee agent type.")

    task = universal_agent_manager.delegate_task(
        delegator=del_type,
        assignee=ass_type,
        goal=req.goal,
        input_context=req.input_context,
        requires_human_approval=req.requires_human_approval,
    )
    return {
        "status": "success",
        "task": task.model_dump(),
    }


@router.post("/workflow/onboard-craft")
async def execute_onboarding_workflow(req: OnboardProductWorkflowRequest):
    """Execute end-to-end multi-agent collaboration (Catalog -> Pricing -> Marketing -> Export -> Inventory)."""
    result = universal_agent_manager.execute_full_product_onboarding_pipeline(
        craft_name=req.craft_name,
        region=req.region,
        material=req.material,
        material_cost=req.material_cost,
        hours_worked=req.hours_worked,
        initial_stock=req.initial_stock,
        destination_country=req.destination_country,
    )
    return result


@router.post("/human-approval")
async def review_human_approval(req: HumanApprovalRequest):
    """Approve or reject a sensitive agent action requiring human verification."""
    task = universal_agent_manager.review_human_approval(
        task_id=req.task_id,
        approved=req.approved,
        reviewer_name=req.reviewer_name,
    )
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{req.task_id}' not found.")
    return {
        "status": "success",
        "task": task.model_dump(),
    }
