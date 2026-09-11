"""
Knowledge Graph Engine API Router (KalaCart V10)
Exposes semantic graph discovery, multi-hop subgraphs, entity relationships,
and cross-entity heritage recommendations.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.knowledge_graph import (
    knowledge_graph_engine,
    NodeLabel,
    EdgeType,
    KnowledgeNode,
)

router = APIRouter(prefix="/api/v1/graph", tags=["Knowledge Graph Engine (V10)"])


class AddNodeRequest(BaseModel):
    node_id: str
    label: str
    name: str
    properties: Dict[str, Any] = {}


class AddEdgeRequest(BaseModel):
    edge_type: str
    source_node_id: str
    target_node_id: str
    weight: float = 1.0
    properties: Dict[str, Any] = {}


@router.get("/summary")
async def get_graph_summary():
    """Retrieve overall graph statistics (total nodes by label, total edges by relationship type)."""
    node_counts: Dict[str, int] = {}
    for n in knowledge_graph_engine.nodes.values():
        lbl = n.label.value
        node_counts[lbl] = node_counts.get(lbl, 0) + 1

    edge_counts: Dict[str, int] = {}
    for e in knowledge_graph_engine.edges.values():
        typ = e.edge_type.value
        edge_counts[typ] = edge_counts.get(typ, 0) + 1

    return {
        "total_nodes": len(knowledge_graph_engine.nodes),
        "total_edges": len(knowledge_graph_engine.edges),
        "node_labels_breakdown": node_counts,
        "edge_types_breakdown": edge_counts,
    }


@router.get("/nodes/{node_id}/subgraph")
async def get_node_subgraph(
    node_id: str,
    depth: int = Query(1, ge=1, le=3, description="Expansion depth (1 to 3 hops)"),
):
    """Expand multi-hop neighborhood for a root node (e.g. all materials, artisans, and GI tags connected to a craft)."""
    res = knowledge_graph_engine.get_node_subgraph(node_id=node_id, depth=depth)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/search/semantic")
async def search_knowledge_graph(
    query: str = Query(..., description="Semantic search query across craft heritage graph"),
):
    """Semantic search across graph nodes, properties, and connected relationships."""
    results = knowledge_graph_engine.semantic_graph_search(query=query)
    return {
        "query": query,
        "matched_count": len(results),
        "results": results,
    }


@router.post("/nodes/create")
async def create_graph_node(req: AddNodeRequest):
    """Add a new entity node into the knowledge graph."""
    try:
        label_enum = NodeLabel(req.label)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid node label '{req.label}'.")

    node = KnowledgeNode(
        node_id=req.node_id,
        label=label_enum,
        name=req.name,
        properties=req.properties,
    )
    saved = knowledge_graph_engine.add_node(node)
    return {
        "status": "success",
        "node": saved.to_dict(),
    }


@router.post("/edges/create")
async def create_graph_edge(req: AddEdgeRequest):
    """Create a relationship edge between two existing nodes."""
    try:
        edge_enum = EdgeType(req.edge_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid edge type '{req.edge_type}'.")

    if req.source_node_id not in knowledge_graph_engine.nodes:
        raise HTTPException(status_code=404, detail=f"Source node '{req.source_node_id}' not found.")
    if req.target_node_id not in knowledge_graph_engine.nodes:
        raise HTTPException(status_code=404, detail=f"Target node '{req.target_node_id}' not found.")

    edge = knowledge_graph_engine.add_edge(
        edge_type=edge_enum,
        source_node_id=req.source_node_id,
        target_node_id=req.target_node_id,
        weight=req.weight,
        properties=req.properties,
    )
    return {
        "status": "success",
        "edge": edge.to_dict(),
    }
