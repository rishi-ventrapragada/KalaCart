"""
Test Suite for Knowledge Graph Engine (KalaCart V10)
Verifies:
- Entity nodes and relationship edge schema retrieval
- Multi-hop subgraph neighborhood expansions
- Semantic search matching entities across interconnected relationships
- Dynamic node and edge creation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_graph_summary():
    response = client.get("/api/v1/graph/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] >= 10
    assert data["total_edges"] >= 10
    assert "Artisan" in data["node_labels_breakdown"]
    assert "Product" in data["node_labels_breakdown"]
    assert "creates" in data["edge_types_breakdown"]
    assert "uses" in data["edge_types_breakdown"]


def test_get_node_subgraph():
    # Fetch 1-hop subgraph for Channapatna Lacquer Craft
    response = client.get("/api/v1/graph/nodes/craft:channapatna-toys/subgraph?depth=1")
    assert response.status_code == 200
    data = response.json()
    assert data["root_node_id"] == "craft:channapatna-toys"
    assert data["nodes_count"] >= 3
    node_ids = [n["node_id"] for n in data["nodes"]]
    assert "artisan:ramesh-01" in node_ids
    assert "product:channapatna-doll-01" in node_ids


def test_semantic_graph_search_across_relationships():
    # Query for "Ivory Wood" -> should find the Material node AND the Product/Craft connected to it
    response = client.get("/api/v1/graph/search/semantic?query=Ivory%20Wood")
    assert response.status_code == 200
    data = response.json()
    assert data["matched_count"] >= 1
    top_result = data["results"][0]
    assert "Ivory Wood" in top_result["node"]["name"] or any("Ivory Wood" in r for r in top_result["match_reasons"])


def test_create_node_and_edge():
    # 1. Create a new Supplier Node
    node_payload = {
        "node_id": "supplier:natural-indigo-coop",
        "label": "Supplier",
        "name": "Natural Indigo Farmer Collective",
        "properties": {"state": "Andhra Pradesh", "organic_certified": True},
    }
    node_res = client.post("/api/v1/graph/nodes/create", json=node_payload)
    assert node_res.status_code == 200
    assert node_res.json()["node"]["node_id"] == "supplier:natural-indigo-coop"

    # 2. Connect Supplier to Material
    edge_payload = {
        "edge_type": "supplied_by",
        "source_node_id": "material:vegetable-lac-dye",
        "target_node_id": "supplier:natural-indigo-coop",
        "weight": 1.0,
    }
    edge_res = client.post("/api/v1/graph/edges/create", json=edge_payload)
    assert edge_res.status_code == 200
    assert edge_res.json()["edge"]["edge_type"] == "supplied_by"
