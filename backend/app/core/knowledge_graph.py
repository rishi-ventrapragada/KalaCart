"""
Knowledge Graph Engine (KalaCart V10)
Connects every entity across the platform into an interconnected semantic property graph:
- Nodes: Artisan, Product, Material, Craft, Buyer, Supplier, District, GI, Museum, Organization.
- Edges: creates, uses, located_in, purchased_by, supplied_by, belongs_to, certified_as.
- Multi-hop semantic traversal and relational graph recommendations.
- Cross-entity heritage discovery & research analytics.
"""

import uuid
import math
import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field


class NodeLabel(str, Enum):
    ARTISAN = "Artisan"
    PRODUCT = "Product"
    MATERIAL = "Material"
    CRAFT = "Craft"
    BUYER = "Buyer"
    SUPPLIER = "Supplier"
    DISTRICT = "District"
    GI = "GI"
    MUSEUM = "Museum"
    ORGANIZATION = "Organization"


class EdgeType(str, Enum):
    CREATES = "creates"
    USES = "uses"
    LOCATED_IN = "located_in"
    PURCHASED_BY = "purchased_by"
    SUPPLIED_BY = "supplied_by"
    BELONGS_TO = "belongs_to"
    CERTIFIED_AS = "certified_as"


class KnowledgeNode(BaseModel):
    node_id: str
    label: NodeLabel
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label.value,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at,
        }


class KnowledgeEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    edge_type: EdgeType
    source_node_id: str
    target_node_id: str
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "edge_type": self.edge_type.value,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "weight": self.weight,
            "properties": self.properties,
        }


class KnowledgeGraphEngine:
    """
    In-memory graph database & semantic discovery engine.
    Supports Cypher-like graph traversals, 1-hop / 2-hop neighborhood expansion,
    and cross-entity semantic search.
    """

    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}  # edge_id -> edge
        self.adjacency_out: Dict[str, List[KnowledgeEdge]] = {}  # source -> list of edges
        self.adjacency_in: Dict[str, List[KnowledgeEdge]] = {}   # target -> list of edges
        self._seed_heritage_knowledge_graph()

    def _seed_heritage_knowledge_graph(self):
        # 1. Nodes
        nodes_data = [
            # Artisans
            KnowledgeNode(node_id="artisan:ramesh-01", label=NodeLabel.ARTISAN, name="Master Artisan Ramesh Kumar", properties={"state": "Karnataka", "awards": ["National Award 2018"]}),
            KnowledgeNode(node_id="artisan:sitara-02", label=NodeLabel.ARTISAN, name="Sitara Devi", properties={"state": "Uttar Pradesh", "experience_years": 28}),
            # Crafts
            KnowledgeNode(node_id="craft:channapatna-toys", label=NodeLabel.CRAFT, name="Channapatna Lacquerware Craft", properties={"origin_era": "18th Century Tipu Sultan", "heritage_status": "National Heritage"}),
            KnowledgeNode(node_id="craft:banarasi-silk", label=NodeLabel.CRAFT, name="Banaras Handloom Brocade Weaving", properties={"origin_era": "Mughal & Vedic Heritage"}),
            # Products
            KnowledgeNode(node_id="product:channapatna-doll-01", label=NodeLabel.PRODUCT, name="Royal Raja-Rani Lacquer Doll Pair", properties={"price_inr": 1850.0}),
            KnowledgeNode(node_id="product:banarasi-saree-01", label=NodeLabel.PRODUCT, name="Katan Silk Pure Gold Zari Bridal Saree", properties={"price_inr": 35000.0}),
            # Materials
            KnowledgeNode(node_id="material:ivory-wood", label=NodeLabel.MATERIAL, name="Wrightia Tinctoria (Ivory Wood)", properties={"sustainable": True, "eco_certified": True}),
            KnowledgeNode(node_id="material:vegetable-lac-dye", label=NodeLabel.MATERIAL, name="Non-Toxic Vegetable Lacquer Dyes", properties={"organic": True, "child_safe": True}),
            KnowledgeNode(node_id="material:pure-silver-zari", label=NodeLabel.MATERIAL, name="Electroplated Silver & Gold Zari Thread", properties={"purity_pct": 98.5}),
            # Districts
            KnowledgeNode(node_id="district:ramanagara", label=NodeLabel.DISTRICT, name="Ramanagara District", properties={"state": "Karnataka"}),
            KnowledgeNode(node_id="district:varanasi", label=NodeLabel.DISTRICT, name="Varanasi District", properties={"state": "Uttar Pradesh"}),
            # GI Certifications
            KnowledgeNode(node_id="gi:channapatna-toys-19", label=NodeLabel.GI, name="Channapatna Toys & Dolls (GI-19)", properties={"registry_year": 2006, "status": "Registered"}),
            KnowledgeNode(node_id="gi:banaras-brocades-99", label=NodeLabel.GI, name="Banaras Brocades and Sarees (GI-99)", properties={"registry_year": 2009, "status": "Registered"}),
            # Museum
            KnowledgeNode(node_id="museum:national-craft-museum", label=NodeLabel.MUSEUM, name="National Handicrafts Museum New Delhi", properties={"established": 1956}),
            # Organizations
            KnowledgeNode(node_id="org:trifed", label=NodeLabel.ORGANIZATION, name="TRIFED (Tribes India)", properties={"type": "cooperative_federation"}),
            KnowledgeNode(node_id="org:up-odop", label=NodeLabel.ORGANIZATION, name="UP ODOP Directorate", properties={"type": "government"}),
            # Buyers
            KnowledgeNode(node_id="buyer:heritage-curator-delhi", label=NodeLabel.BUYER, name="Delhi Art Gallery & Curators", properties={"tier": "B2B_Institutional"}),
        ]

        for n in nodes_data:
            self.add_node(n)

        # 2. Relationships (Edges)
        edges_data = [
            # Artisan relationships
            (EdgeType.LOCATED_IN, "artisan:ramesh-01", "district:ramanagara"),
            (EdgeType.BELONGS_TO, "artisan:ramesh-01", "craft:channapatna-toys"),
            (EdgeType.CREATES, "artisan:ramesh-01", "product:channapatna-doll-01"),
            (EdgeType.CERTIFIED_AS, "artisan:ramesh-01", "gi:channapatna-toys-19"),

            (EdgeType.LOCATED_IN, "artisan:sitara-02", "district:varanasi"),
            (EdgeType.BELONGS_TO, "artisan:sitara-02", "craft:banarasi-silk"),
            (EdgeType.CREATES, "artisan:sitara-02", "product:banarasi-saree-01"),
            (EdgeType.CERTIFIED_AS, "artisan:sitara-02", "gi:banaras-brocades-99"),

            # Product & Material relationships
            (EdgeType.USES, "product:channapatna-doll-01", "material:ivory-wood"),
            (EdgeType.USES, "product:channapatna-doll-01", "material:vegetable-lac-dye"),
            (EdgeType.BELONGS_TO, "product:channapatna-doll-01", "craft:channapatna-toys"),

            (EdgeType.USES, "product:banarasi-saree-01", "material:pure-silver-zari"),
            (EdgeType.BELONGS_TO, "product:banarasi-saree-01", "craft:banarasi-silk"),

            # Museum & Exhibition relationships
            (EdgeType.USES, "museum:national-craft-museum", "craft:channapatna-toys"),
            (EdgeType.USES, "museum:national-craft-museum", "craft:banarasi-silk"),

            # Buyer Purchases
            (EdgeType.PURCHASED_BY, "product:banarasi-saree-01", "buyer:heritage-curator-delhi"),
        ]

        for e_type, src, tgt in edges_data:
            self.add_edge(edge_type=e_type, source_node_id=src, target_node_id=tgt)

    def add_node(self, node: KnowledgeNode) -> KnowledgeNode:
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency_out:
            self.adjacency_out[node.node_id] = []
        if node.node_id not in self.adjacency_in:
            self.adjacency_in[node.node_id] = []
        return node

    def add_edge(self, edge_type: EdgeType, source_node_id: str, target_node_id: str, weight: float = 1.0, properties: Optional[Dict[str, Any]] = None) -> KnowledgeEdge:
        edge = KnowledgeEdge(
            edge_type=edge_type,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            weight=weight,
            properties=properties or {},
        )
        self.edges[edge.id] = edge
        self.adjacency_out.setdefault(source_node_id, []).append(edge)
        self.adjacency_in.setdefault(target_node_id, []).append(edge)
        return edge

    def get_node_subgraph(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Expands the multi-hop neighborhood for a given node, returning connected
        nodes, edge types, and relationship weights.
        """
        if node_id not in self.nodes:
            return {"error": f"Node '{node_id}' not found."}

        visited_nodes: Set[str] = {node_id}
        collected_edges: List[Dict[str, Any]] = []

        current_frontier = {node_id}
        for _ in range(depth):
            next_frontier = set()
            for curr in current_frontier:
                # Outgoing edges
                for out_edge in self.adjacency_out.get(curr, []):
                    collected_edges.append(out_edge.to_dict())
                    if out_edge.target_node_id not in visited_nodes:
                        visited_nodes.add(out_edge.target_node_id)
                        next_frontier.add(out_edge.target_node_id)
                # Incoming edges
                for in_edge in self.adjacency_in.get(curr, []):
                    collected_edges.append(in_edge.to_dict())
                    if in_edge.source_node_id not in visited_nodes:
                        visited_nodes.add(in_edge.source_node_id)
                        next_frontier.add(in_edge.source_node_id)
            current_frontier = next_frontier

        subgraph_nodes = [self.nodes[n_id].to_dict() for n_id in visited_nodes if n_id in self.nodes]
        return {
            "root_node_id": node_id,
            "depth": depth,
            "nodes_count": len(subgraph_nodes),
            "edges_count": len(collected_edges),
            "nodes": subgraph_nodes,
            "edges": collected_edges,
        }

    def semantic_graph_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches across nodes and their connected relationships.
        Matches node names, properties, and connected entities (e.g. query "Channapatna"
        finds the Craft, Artisan, District, Material, and Products).
        """
        query_lower = query.strip().lower()
        matched_results = []

        for node_id, node in self.nodes.items():
            score = 0.0
            reasons = []

            # 1. Direct Name & Label Match
            if query_lower in node.name.lower():
                score += 10.0
                reasons.append(f"Name matched '{node.name}'")
            if query_lower in node.label.value.lower():
                score += 4.0
                reasons.append(f"Label matched '{node.label.value}'")

            # 2. Properties Match
            for prop_k, prop_v in node.properties.items():
                if query_lower in str(prop_v).lower():
                    score += 5.0
                    reasons.append(f"Property '{prop_k}' matched '{prop_v}'")

            # 3. 1-Hop Connected Neighbor Relationship Matches
            for out_e in self.adjacency_out.get(node_id, []):
                tgt_node = self.nodes.get(out_e.target_node_id)
                if tgt_node and query_lower in tgt_node.name.lower():
                    score += 6.0
                    reasons.append(f"Connected via [{out_e.edge_type.value}] -> {tgt_node.name}")

            for in_e in self.adjacency_in.get(node_id, []):
                src_node = self.nodes.get(in_e.source_node_id)
                if src_node and query_lower in src_node.name.lower():
                    score += 6.0
                    reasons.append(f"Referenced via [{in_e.edge_type.value}] <- {src_node.name}")

            if score > 0.0:
                matched_results.append({
                    "node": node.to_dict(),
                    "relevance_score": score,
                    "match_reasons": reasons,
                })

        return sorted(matched_results, key=lambda x: x["relevance_score"], reverse=True)


# Global Singleton Knowledge Graph Instance
knowledge_graph_engine = KnowledgeGraphEngine()
