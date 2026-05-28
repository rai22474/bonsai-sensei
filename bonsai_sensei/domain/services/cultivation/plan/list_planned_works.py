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
