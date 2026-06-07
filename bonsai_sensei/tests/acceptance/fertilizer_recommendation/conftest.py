import uuid

import pytest
from pytest_bdd import given, parsers

from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages
from manage_fertilizers.fertilizer_api import create_fertilizer, delete_fertilizer_by_name
from manage_species.species_api import delete_species_by_name, create_species


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-fertilizer-rec-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "fertilizers_registered": [],
        "bonsai_ids": {},
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for bonsai_name in context["bonsai_created"]:
        delete_bonsai_wiki_pages(bonsai_name, user_id=context["user_id"])
        delete_bonsai_by_name(get, delete, bonsai_name, user_id=context["user_id"])
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)
    for name in context["fertilizers_registered"]:
        delete_fertilizer_by_name(delete, name, user_id=context["user_id"])


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"][name] = species.get("id")


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = context["species_ids"][species_name]
    bonsai = create_bonsai(post, bonsai_name, species_id, user_id=context["user_id"])
    context["bonsai_created"].append(bonsai_name)
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('fertilizer "{name}" is registered in the catalog'))
def ensure_fertilizer_registered(context, name):
    create_fertilizer(post, name, user_id=context["user_id"])
    context["fertilizers_registered"].append(name)
