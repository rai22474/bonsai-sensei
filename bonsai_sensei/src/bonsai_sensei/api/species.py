from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Dict, Callable
from bonsai_sensei.domain.species import Species

router = APIRouter()

def get_list_species_svc(request: Request) -> Callable:
    return request.app.state.herbarium_service["list_species"]

def get_create_species_svc(request: Request) -> Callable:
    return request.app.state.herbarium_service["create_species"]

def get_search_species_svc(request: Request) -> Callable:
    return request.app.state.herbarium_service["search_species_by_name"]

def get_update_species_svc(request: Request) -> Callable:
    return request.app.state.herbarium_service["update_species"]

def get_delete_species_svc(request: Request) -> Callable:
    return request.app.state.herbarium_service["delete_species"]


@router.get("/species", response_model=List[Species])
def get_species_list(list_species: Callable = Depends(get_list_species_svc)):
    return list_species()


@router.get("/species/search", response_model=List[Species])
def search_species_by_name(
    name: str, search_species: Callable = Depends(get_search_species_svc)
):
    return search_species(name=name)

@router.post("/species", response_model=Species)
def create_new_species(
    species: Species, 
    create_species_func: Callable = Depends(get_create_species_svc)
):
    # Ensure ID is None so DB assigns it
    species.id = None 
    return create_species_func(species=species)

@router.put("/species/{species_id}", response_model=Species)
def update_existing_species(
    species_id: int, 
    species_data: Dict, 
    update_species_func: Callable = Depends(get_update_species_svc)
):
    result = update_species_func(species_id=species_id, species_data=species_data)
    if not result:
        raise HTTPException(status_code=404, detail="Species not found")
    return result

@router.delete("/species/{species_id}")
def delete_existing_species(
    species_id: int, 
    delete_species_func: Callable = Depends(get_delete_species_svc)
):
    success = delete_species_func(species_id=species_id)
    if not success:
        raise HTTPException(status_code=404, detail="Species not found")
    return {"status": "success", "message": f"Species {species_id} deleted"}

