def create_list_fertilizers_tool(list_fertilizers_func):
    def list_fertilizers_for_planning() -> dict:
        """List all fertilizers registered in the catalog, available for planning fertilizations.

        Returns:
            A dict with "status" and "fertilizers" list.
            Output JSON: {"status": "success", "fertilizers": [{"id": int, "name": str, "recommended_amount": str}]}.
        """
        fertilizers = list_fertilizers_func()
        return {
            "status": "success",
            "fertilizers": [
                {
                    "id": fertilizer.id,
                    "name": fertilizer.name,
                    "recommended_amount": fertilizer.recommended_amount,
                }
                for fertilizer in fertilizers
            ],
        }

    return list_fertilizers_for_planning


def create_list_phytosanitary_tool(list_phytosanitary_func):
    def list_phytosanitary_for_planning() -> dict:
        """List all phytosanitary products registered in the catalog, available for planning treatments.

        Returns:
            A dict with "status" and "products" list.
            Output JSON: {"status": "success", "products": [{"id": int, "name": str, "recommended_amount": str}]}.
        """
        products = list_phytosanitary_func()
        return {
            "status": "success",
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "recommended_amount": product.recommended_amount,
                }
                for product in products
            ],
        }

    return list_phytosanitary_for_planning


def create_list_bonsai_events_tool(get_bonsai_by_name_func, list_bonsai_events_func):
    def list_bonsai_events_for_cultivation(bonsai_name: str) -> dict:
        """List all recorded care events for a bonsai to consult its history before planning.

        Args:
            bonsai_name: Name of the bonsai whose event history to retrieve.

        Returns:
            A dict with "status" and "events" list, or an error dict.
            Output JSON (success): {"status": "success", "events": [{"event_type": str, "payload": dict, "occurred_at": str}]}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_not_found".
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        events = list_bonsai_events_func(bonsai_id=bonsai.id)
        return {"status": "success", "events": events}

    return list_bonsai_events_for_cultivation


def create_list_planned_works_tool(get_bonsai_by_name_func, list_planned_works_func):
    def list_planned_works_for_bonsai(bonsai_name: str) -> dict:
        """List all planned works for a bonsai by its name, sorted by scheduled date.

        Args:
            bonsai_name: Name of the bonsai whose planned works to list.

        Returns:
            A dict with "status" and "planned_works" list, or an error dict.
            Output JSON (success): {"status": "success", "planned_works": [...]}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_not_found".
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        planned_works = list_planned_works_func(bonsai_id=bonsai.id)
        return {
            "status": "success",
            "planned_works": [
                {
                    "id": work.id,
                    "work_type": work.work_type,
                    "scheduled_date": str(work.scheduled_date),
                    "payload": work.payload,
                    "notes": work.notes,
                }
                for work in planned_works
            ],
        }

    return list_planned_works_for_bonsai
