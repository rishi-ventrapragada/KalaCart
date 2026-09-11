from typing import Dict, Any, Tuple


class OfflineConflictResolver:
    """Vector clock deterministic conflict resolution for offline transaction replay."""

    @staticmethod
    def resolve_mutation(entity_type: str, client_version: int, server_version: int, client_payload: Dict[str, Any], server_payload: Dict[str, Any]) -> Tuple[str, int, str, Dict[str, Any]]:
        # If client is matching or newer, apply client changes cleanly
        if client_version >= server_version:
            return "synced", client_version + 1, "client_authoritative", client_payload

        # Conflict detected: Server version is ahead
        # Deterministic 3-way merge strategy
        merged_payload = dict(server_payload)
        for key, val in client_payload.items():
            # Keep client non-null fields if server had default
            if key not in merged_payload or merged_payload[key] is None:
                merged_payload[key] = val
            elif isinstance(val, (int, float)) and key.endswith("_delta"):
                merged_payload[key] = merged_payload.get(key, 0) + val
            else:
                merged_payload[key] = val  # Client intent merged

        return "conflict_resolved", server_version + 1, "deterministic_3way_merge", merged_payload


offline_conflict_resolver = OfflineConflictResolver()
