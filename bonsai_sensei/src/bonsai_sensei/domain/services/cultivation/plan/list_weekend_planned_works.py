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
                    "bonsai_name": bonsai_map.get(work.bonsai_id, f"Bonsái {work.bonsai_id}").capitalize(),
                    "work_type": work.work_type,
                    "scheduled_date": work.scheduled_date.isoformat(),
                    "payload": work.payload,
                }
                for work in works
            ],
        }

    return list_weekend_planned_works
