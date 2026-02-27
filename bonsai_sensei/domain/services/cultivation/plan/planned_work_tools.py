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


def create_list_weekend_planned_works_tool(list_planned_works_in_date_range_func, list_bonsai_func):
    def list_weekend_planned_works() -> dict:
        """List all planned works scheduled for the upcoming weekend (Saturday and Sunday).

        Computes the next Saturday and Sunday automatically and returns all planned works
        across all bonsais within that date range.

        Returns:
            A dict with "status", "saturday", "sunday", and "planned_works" list.
            Output JSON: {
                "status": "success",
                "saturday": "YYYY-MM-DD",
                "sunday": "YYYY-MM-DD",
                "planned_works": [{"bonsai_name": str, "work_type": str, "scheduled_date": str, "payload": dict}]
            }.
        """
        from datetime import date, timedelta
        today = date.today()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = today + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)

        works = list_planned_works_in_date_range_func(start_date=saturday, end_date=sunday)
        bonsai_map = {bonsai.id: bonsai.name for bonsai in list_bonsai_func()}
        return {
            "status": "success",
            "saturday": saturday.isoformat(),
            "sunday": sunday.isoformat(),
            "planned_works": [
                {
                    "bonsai_name": bonsai_map.get(work.bonsai_id, f"Bonsái {work.bonsai_id}"),
                    "work_type": work.work_type,
                    "scheduled_date": work.scheduled_date.isoformat(),
                    "payload": work.payload,
                }
                for work in works
            ],
        }

    return list_weekend_planned_works


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
