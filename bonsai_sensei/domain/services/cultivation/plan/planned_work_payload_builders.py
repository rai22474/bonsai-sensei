def build_fertilizer_payload(fertilizer_id: int, fertilizer_name: str, amount: str) -> dict:
    return {"fertilizer_id": fertilizer_id, "fertilizer_name": fertilizer_name, "amount": amount}


def build_phytosanitary_payload(phytosanitary_id: int, phytosanitary_name: str, amount: str) -> dict:
    return {"phytosanitary_id": phytosanitary_id, "phytosanitary_name": phytosanitary_name, "amount": amount}


def build_transplant_payload(pot_size: str, pot_type: str, substrate: str) -> dict:
    return {
        key: value
        for key, value in {"pot_size": pot_size, "pot_type": pot_type, "substrate": substrate}.items()
        if value
    }
