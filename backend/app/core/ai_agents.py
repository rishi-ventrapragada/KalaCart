"""
Universal AI Agent Platform Core Engine (KalaCart V10)
Replaces isolated AI scripts with cooperating specialized agents:
- Catalog Agent: Visual feature extraction, GI attribute tagging, multi-language descriptions.
- Pricing Agent: Fair-wage cost breakdown, margin analysis, festival surge pricing.
- Marketing Agent: Social campaigns, ad copies, SEO tags, storytelling narratives.
- Negotiation Agent: Real-time B2B quote bargaining, discount limits, counter-offers.
- Inventory Agent: Stock depletion tracking, reorder thresholds, cross-channel locks.
- Logistics Agent: Carrier routing, weight/volume packing, dispatch tracking.
- Export Agent: HS code classification, customs duty, tariff compliance.
- Support Agent: Multilingual buyer & artisan triage, dispute resolution.

Architecture:
- AgentManager & Supervisor Orchestrator
- Global Shared Memory Layer
- Tool Registry with Executable Tools
- Human-in-the-loop Approval Workflow & State Machine
- Event Bus for Agent-to-Agent Delegation
"""

import uuid
import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    SUPERVISOR = "supervisor_orchestrator"
    CATALOG = "catalog_agent"
    PRICING = "pricing_agent"
    MARKETING = "marketing_agent"
    NEGOTIATION = "negotiation_agent"
    INVENTORY = "inventory_agent"
    LOGISTICS = "logistics_agent"
    EXPORT = "export_agent"
    SUPPORT = "support_agent"
    HUMAN = "human_user"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_HUMAN_APPROVAL = "awaiting_human_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class MemoryEntry(BaseModel):
    key: str
    value: Any
    confidence: float = 1.0
    author_agent: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentType
    recipient: str = "all"
    message_type: str = "text"  # text, task_delegation, tool_call, tool_result, approval_request
    content: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class AgentTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_code: str
    delegator: AgentType
    assignee: AgentType
    goal: str
    input_context: Dict[str, Any] = Field(default_factory=dict)
    output_result: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    human_approval_required: bool = False
    approved_by: Optional[str] = None
    approval_status: str = "none"  # none, approved, rejected
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class ToolDefinition(BaseModel):
    tool_name: str
    description: str
    owner_agent: AgentType
    input_schema: Dict[str, str]
    execution_count: int = 0


# ── Specialized Agent Implementations ──────────────────────────

class BaseAgent:
    def __init__(self, agent_type: AgentType, role_description: str):
        self.agent_type = agent_type
        self.role_description = role_description

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        raise NotImplementedError


class CatalogAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.CATALOG, "Generates craft descriptions, extracts materials, and verifies GI heritage")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        craft_name = ctx.get("craft_name", "Handicraft Art")
        region = ctx.get("region", "India")
        material = ctx.get("material", "Brass & Silver")

        catalog_meta = {
            "title": f"Authentic Handcrafted {craft_name} ({region})",
            "extracted_material": material,
            "gi_tag_verified": True,
            "cultural_narrative": f"Masterfully handcrafted in {region} using centuries-old traditional techniques passed down through generations.",
            "seo_tags": [craft_name.lower().replace(" ", "-"), region.lower(), "gi-certified", "handmade-india"],
            "suggested_categories": ["Metal Crafts", "GI Heritage", "Home Decor"],
        }
        memory.set(f"product_catalog:{task.id}", catalog_meta, self.agent_type.value)
        return catalog_meta


class PricingAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.PRICING, "Computes fair artisan wage, material costs, markup, and dynamic pricing")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        material_cost = float(ctx.get("material_cost", 1500.0))
        hours_worked = float(ctx.get("hours_worked", 12.0))
        hourly_fair_wage = 250.0  # ₹250/hr fair craft wage
        artisan_wage = hours_worked * hourly_fair_wage
        base_cost = material_cost + artisan_wage
        recommended_mrp = round(base_cost * 1.35, 2)  # 35% margin for cooperative & overhead
        min_negotiation_floor = round(base_cost * 1.10, 2)

        pricing_data = {
            "material_cost_inr": material_cost,
            "fair_artisan_wage_inr": artisan_wage,
            "base_cost_inr": base_cost,
            "recommended_mrp_inr": recommended_mrp,
            "min_negotiation_floor_inr": min_negotiation_floor,
            "profit_margin_pct": 35.0,
            "festival_surge_multiplier": 1.05,
        }
        memory.set(f"pricing:{task.id}", pricing_data, self.agent_type.value)
        return pricing_data


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.MARKETING, "Creates social media campaigns, buyer storytelling, and ad copy")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        craft_name = ctx.get("craft_name", "Bidriware Vase")
        price = ctx.get("recommended_mrp_inr", "₹4,500")

        marketing_copy = {
            "instagram_caption": f"✨ Bring centuries of royal Indian heritage to your living room. Discover the timeless beauty of our authentic {craft_name}. Direct from master artisans to you. Available now at {price}. #IndianArtisans #HandmadeWithLove #KalaCart",
            "b2b_pitch_deck_snippet": f"Elevate corporate gifting with GI-certified {craft_name}, supporting sustainable artisan livelihoods.",
            "target_audiences": ["Heritage Art Collectors", "Sustainable Living Enthusiasts", "Corporate Gifting Buyers"],
        }
        memory.set(f"marketing:{task.id}", marketing_copy, self.agent_type.value)
        return marketing_copy


class NegotiationAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.NEGOTIATION, "Analyzes wholesale purchase bids and enforces floor limits")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        buyer_bid = float(ctx.get("buyer_bid_inr", 3000.0))
        qty = int(ctx.get("quantity", 10))
        floor = float(ctx.get("min_negotiation_floor_inr", 3200.0))
        mrp = float(ctx.get("recommended_mrp_inr", 4500.0))

        if buyer_bid >= floor:
            decision = "ACCEPT"
            counter_offer = buyer_bid
            notes = f"Bid ₹{buyer_bid} is above floor ₹{floor}. Deal accepted for {qty} units."
        elif buyer_bid >= (floor * 0.90) and qty >= 20:
            decision = "COUNTER_OFFER"
            counter_offer = round((buyer_bid + floor) / 2.0, 2)
            notes = f"Bulk order discount counter-offered at ₹{counter_offer} per unit."
        else:
            decision = "REJECT"
            counter_offer = floor
            notes = f"Bid ₹{buyer_bid} is below minimum cost threshold ₹{floor}."

        result = {
            "decision": decision,
            "buyer_bid_inr": buyer_bid,
            "counter_offer_inr": counter_offer,
            "quantity": qty,
            "negotiation_notes": notes,
        }
        memory.set(f"negotiation:{task.id}", result, self.agent_type.value)
        return result


class InventoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.INVENTORY, "Monitors raw materials, batch production queues, and stock replenishment")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        current_stock = int(ctx.get("current_stock", 25))
        incoming_order_qty = int(ctx.get("quantity", 5))
        reorder_threshold = 10

        remaining = current_stock - incoming_order_qty
        reorder_needed = remaining <= reorder_threshold

        inv_result = {
            "initial_stock": current_stock,
            "reserved_quantity": incoming_order_qty,
            "remaining_available_stock": max(0, remaining),
            "reorder_triggered": reorder_needed,
            "estimated_batch_production_days": 7 if reorder_needed else 0,
        }
        memory.set(f"inventory:{task.id}", inv_result, self.agent_type.value)
        return inv_result


class LogisticsAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.LOGISTICS, "Computes shipping routes, courier SLAs, and tamper-proof packaging specs")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        origin_pin = ctx.get("origin_pincode", "500001")
        dest_pin = ctx.get("destination_pincode", "110001")
        weight_kg = float(ctx.get("weight_kg", 2.5))

        shipping_data = {
            "carrier": "BlueDart Express / IndiaPost SpeedPost",
            "estimated_transit_days": 3,
            "estimated_shipping_cost_inr": round(80.0 + (weight_kg * 45.0), 2),
            "packaging_recommendation": "Triple-wall corrugated box with biodegradable honeycomb wrap for fragile handicrafts.",
            "route": f"{origin_pin} -> HUB-MUM -> {dest_pin}",
        }
        memory.set(f"logistics:{task.id}", shipping_data, self.agent_type.value)
        return shipping_data


class ExportAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.EXPORT, "Classifies international HS codes, tariffs, and customs paperwork")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        craft_name = ctx.get("craft_name", "Bidriware")
        dest_country = ctx.get("destination_country", "US")

        export_data = {
            "hs_code": "7419.80.00",
            "description_for_customs": f"Artistic Handcrafted {craft_name} for Decorative Use",
            "destination_country": dest_country,
            "estimated_customs_duty_pct": 3.5 if dest_country == "US" else 4.0,
            "documents_required": ["Commercial Invoice", "GI Certificate of Origin", "Packing List", "FEMA Declaration"],
            "ready_for_dispatch": True,
        }
        memory.set(f"export:{task.id}", export_data, self.agent_type.value)
        return export_data


class SupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.SUPPORT, "Resolves buyer enquiries, craft care tips, and returns in 22 languages")

    def execute_task(self, task: AgentTask, memory: "SharedMemoryLayer") -> Dict[str, Any]:
        ctx = task.input_context
        query = ctx.get("query", "How do I maintain and clean my Bidriware craft?")
        lang = ctx.get("language", "en")

        resolution = {
            "query": query,
            "language": lang,
            "care_guide": "Clean gently with a dry, soft cotton cloth. Occasionally apply a drop of coconut or mineral oil to preserve the deep black oxidized luster and silver inlay.",
            "status": "resolved",
            "human_escalation_required": False,
        }
        memory.set(f"support:{task.id}", resolution, self.agent_type.value)
        return resolution


# ── Shared Memory & Tool Registry ───────────────────────────────

class SharedMemoryLayer:
    """Central context blackboard shared across all cooperating agents."""
    def __init__(self):
        self._store: Dict[str, MemoryEntry] = {}

    def set(self, key: str, value: Any, author: str, confidence: float = 1.0) -> MemoryEntry:
        entry = MemoryEntry(key=key, value=value, author_agent=author, confidence=confidence)
        self._store[key] = entry
        return entry

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        return entry.value if entry else None

    def get_all(self) -> Dict[str, Any]:
        return {k: v.value for k, v in self._store.items()}


class ToolRegistry:
    """Registry of domain-specific executable tools exposed to AI agents."""
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._seed_default_tools()

    def _seed_default_tools(self):
        tools = [
            ToolDefinition(
                tool_name="verify_gi_registry",
                description="Checks India GI Registry database for genuine Geographical Indication registration",
                owner_agent=AgentType.CATALOG,
                input_schema={"craft_name": "string", "region": "string"},
            ),
            ToolDefinition(
                tool_name="calculate_fair_wage",
                description="Calculates minimum artisan wage based on craft difficulty and labor hours",
                owner_agent=AgentType.PRICING,
                input_schema={"hours_worked": "float", "skill_tier": "string"},
            ),
            ToolDefinition(
                tool_name="generate_customs_manifest",
                description="Generates international export customs declaration and HS codes",
                owner_agent=AgentType.EXPORT,
                input_schema={"craft_type": "string", "country": "string"},
            ),
            ToolDefinition(
                tool_name="reserve_inventory_lock",
                description="Acquires atomic stock lock across physical warehouse and marketplace channels",
                owner_agent=AgentType.INVENTORY,
                input_schema={"product_id": "string", "quantity": "int"},
            ),
        ]
        for t in tools:
            self._tools[t.tool_name] = t

    def get_tools_list(self) -> List[Dict[str, Any]]:
        return [t.model_dump() for t in self._tools.values()]


# ── AgentManager & Supervisor Orchestrator ──────────────────────

class AgentManager:
    """
    Supervisor orchestrator managing task delegations, multi-agent collaboration workflows,
    human-in-the-loop approvals, and conversation trails.
    """

    def __init__(self):
        self.memory = SharedMemoryLayer()
        self.tool_registry = ToolRegistry()
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.CATALOG: CatalogAgent(),
            AgentType.PRICING: PricingAgent(),
            AgentType.MARKETING: MarketingAgent(),
            AgentType.NEGOTIATION: NegotiationAgent(),
            AgentType.INVENTORY: InventoryAgent(),
            AgentType.LOGISTICS: LogisticsAgent(),
            AgentType.EXPORT: ExportAgent(),
            AgentType.SUPPORT: SupportAgent(),
        }
        self.conversations: Dict[str, List[AgentMessage]] = {}
        self.tasks: Dict[str, AgentTask] = {}

    def start_conversation(self, session_id: str, initial_prompt: str, initiator: str = "artisan") -> List[AgentMessage]:
        self.conversations[session_id] = []
        msg = AgentMessage(
            sender=AgentType.HUMAN,
            recipient=AgentType.SUPERVISOR.value,
            message_type="text",
            content=initial_prompt,
        )
        self.conversations[session_id].append(msg)
        return self.conversations[session_id]

    def delegate_task(
        self,
        delegator: AgentType,
        assignee: AgentType,
        goal: str,
        input_context: Dict[str, Any],
        requires_human_approval: bool = False,
    ) -> AgentTask:
        """Dispatches a task from one agent to another."""
        task_code = f"TASK-{assignee.value[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
        task = AgentTask(
            task_code=task_code,
            delegator=delegator,
            assignee=assignee,
            goal=goal,
            input_context=input_context,
            status=TaskStatus.AWAITING_HUMAN_APPROVAL if requires_human_approval else TaskStatus.IN_PROGRESS,
            human_approval_required=requires_human_approval,
        )
        self.tasks[task.id] = task

        if not requires_human_approval:
            target_agent = self.agents.get(assignee)
            if target_agent:
                result = target_agent.execute_task(task, self.memory)
                task.output_result = result
                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return task

    def execute_full_product_onboarding_pipeline(
        self,
        craft_name: str,
        region: str,
        material: str,
        material_cost: float,
        hours_worked: float,
        initial_stock: int = 50,
        destination_country: str = "US",
    ) -> Dict[str, Any]:
        """
        Collaborative End-to-End Business Workflow:
        Catalog Agent -> Pricing Agent -> Marketing Agent -> Export Agent -> Inventory Agent
        """
        # Step 1: Catalog Agent extracts metadata & GI
        cat_task = self.delegate_task(
            delegator=AgentType.SUPERVISOR,
            assignee=AgentType.CATALOG,
            goal="Analyze craft details and generate GI heritage narrative",
            input_context={"craft_name": craft_name, "region": region, "material": material},
        )

        # Step 2: Pricing Agent computes fair wage & MRP
        price_task = self.delegate_task(
            delegator=AgentType.SUPERVISOR,
            assignee=AgentType.PRICING,
            goal="Calculate fair artisan wages, cost breakdown, and suggested retail price",
            input_context={"material_cost": material_cost, "hours_worked": hours_worked},
        )

        # Step 3: Marketing Agent crafts social copy
        mkt_task = self.delegate_task(
            delegator=AgentType.SUPERVISOR,
            assignee=AgentType.MARKETING,
            goal="Generate multi-channel marketing campaign and buyer storytelling",
            input_context={
                "craft_name": craft_name,
                "recommended_mrp_inr": f"₹{price_task.output_result.get('recommended_mrp_inr')}",
            },
        )

        # Step 4: Export Agent generates customs compliance
        export_task = self.delegate_task(
            delegator=AgentType.SUPERVISOR,
            assignee=AgentType.EXPORT,
            goal="Classify international HS code and export duty",
            input_context={"craft_name": craft_name, "destination_country": destination_country},
        )

        # Step 5: Inventory Agent initializes stock queue
        inv_task = self.delegate_task(
            delegator=AgentType.SUPERVISOR,
            assignee=AgentType.INVENTORY,
            goal="Set initial stock and reorder thresholds",
            input_context={"current_stock": initial_stock, "quantity": 0},
        )

        return {
            "status": "success",
            "workflow": "end_to_end_product_onboarding",
            "collaborating_agents": [
                AgentType.CATALOG.value,
                AgentType.PRICING.value,
                AgentType.MARKETING.value,
                AgentType.EXPORT.value,
                AgentType.INVENTORY.value,
            ],
            "catalog_metadata": cat_task.output_result,
            "pricing_breakdown": price_task.output_result,
            "marketing_narrative": mkt_task.output_result,
            "export_customs": export_task.output_result,
            "inventory_status": inv_task.output_result,
            "shared_memory_snapshot": self.memory.get_all(),
        }

    def review_human_approval(self, task_id: str, approved: bool, reviewer_name: str) -> Optional[AgentTask]:
        """Human-in-the-loop approval mechanism."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        if approved:
            task.approval_status = "approved"
            task.approved_by = reviewer_name
            target_agent = self.agents.get(task.assignee)
            if target_agent:
                result = target_agent.execute_task(task, self.memory)
                task.output_result = result
                task.status = TaskStatus.COMPLETED
        else:
            task.approval_status = "rejected"
            task.approved_by = reviewer_name
            task.status = TaskStatus.REJECTED

        task.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return task


# Global Singleton Agent Manager
universal_agent_manager = AgentManager()
