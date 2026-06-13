from datetime import date

from pytest_bdd import parsers, scenario, when, then

from cultivation_plan.planned_works_api import list_planned_works
from http_client import advise, choose_selection, get, upload_photo
from manage_bonsai.wiki_api import get_wiki_page

_MINIMAL_WEBP = (
    b'RIFF$\x00\x00\x00WEBPVP8 '
    b'\x18\x00\x00\x000\x01\x00\x9d\x01*'
    b'\x01\x00\x01\x00\x02\x00'
    b'4%\xa4\x00\x03p\x00\xfe'
    b'\xfb\x94\x00\x00'
)


@scenario("../features/work_refinement.feature", "Pre-work analysis session saves wiki under the plan directory")
def test_pre_work_analysis():
    return None


@scenario("../features/work_refinement.feature", "Post-work result session saves wiki under the plan directory")
def test_post_work_result():
    return None


@scenario("../features/work_refinement.feature", "Photos sent during session are analyzed contextually and not added to bonsai gallery")
def test_photos_isolated_and_analyzed():
    return None


@when(parsers.parse('I start a pre-work session for "{bonsai_name}" via advice'))
def start_pre_work_session(context, bonsai_name):
    response = advise(
        text=f"Quiero analizar cómo ejecutar un trabajo planificado del {bonsai_name}.",
        user_id=context["user_id"],
    )
    context["last_response"] = response
    context["pending_selections"] = response.get("pending_selections", [])


@when(parsers.parse('I start a post-work session for "{bonsai_name}" via advice'))
def start_post_work_session(context, bonsai_name):
    response = advise(
        text=f"He terminado un trabajo en el {bonsai_name} y quiero documentar el resultado.",
        user_id=context["user_id"],
    )
    context["last_response"] = response
    context["pending_selections"] = response.get("pending_selections", [])


@when("I select the only planned work")
def select_the_only_work(context):
    selections = context.get("pending_selections", [])
    if not selections:
        response = context.get("last_response", {})
        selections = response.get("pending_selections", [])
    for selection in selections:
        options = selection.get("options", [])
        option = options[0] if options else context["work_type_slug"]
        response = choose_selection(context["user_id"], selection["id"], option)
        context["last_response"] = response
        context["pending_selections"] = response.get("pending_selections", [])


@when(parsers.parse('I discuss the work with "{message}"'))
def discuss_work(context, message):
    response = advise(text=message, user_id=context["user_id"])
    context["last_response"] = response


@when("I send a photo during the session")
def send_session_photo(context):
    response = upload_photo(_MINIMAL_WEBP, context["user_id"], filename="work_photo.webp")
    context["last_response"] = response
    context["sent_session_photo"] = True


@when("I close the kiroku session")
def close_kiroku_session(context):
    response = advise(text="Ya está, guarda las notas.", user_id=context["user_id"])
    context["last_response"] = response


@then(parsers.parse('a refinement wiki page should exist for "{bonsai_name}" under the plan directory'))
def assert_refinement_wiki_exists(context, bonsai_name):
    wiki_path = _get_wiki_path(context, bonsai_name, "refinements")
    _assert_wiki_page_exists(context, wiki_path)


@then(parsers.parse('a result wiki page should exist for "{bonsai_name}" under the plan directory'))
def assert_result_wiki_exists(context, bonsai_name):
    wiki_path = _get_wiki_path(context, bonsai_name, "results")
    _assert_wiki_page_exists(context, wiki_path)


@then(parsers.parse('the "{work_type}" planned work for "{bonsai_name}" should have its refinement_wiki_path set'))
def assert_refinement_wiki_path_on_work(context, work_type, bonsai_name):
    _assert_work_field_set(context, bonsai_name, work_type, "refinement_wiki_path")


@then(parsers.parse('the "{work_type}" planned work for "{bonsai_name}" should have its result_wiki_path set'))
def assert_result_wiki_path_on_work(context, work_type, bonsai_name):
    _assert_work_field_set(context, bonsai_name, work_type, "result_wiki_path")


@then("the result wiki page should contain photo analysis")
def assert_wiki_contains_photo_analysis(context):
    wiki_path = next(
        (p for p in context.get("refinement_wiki_paths", []) if "/results/" in p),
        None,
    )
    assert wiki_path, "No result wiki path in context"
    page = get_wiki_page(wiki_path)
    assert page and page.get("content"), f"Result wiki at '{wiki_path}' has no content"
    keywords = ["foto", "photo", "imagen", "análisis", "analysis", "visual"]
    content = page["content"].lower()
    assert any(k in content for k in keywords), (
        f"Expected photo analysis content in wiki page, found none. Content: {page['content'][:300]}"
    )


@then(parsers.parse('the bonsai gallery for "{bonsai_name}" should not contain the session photo'))
def assert_gallery_not_contaminated(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    gallery_count_before = context.get("gallery_photo_count_before", 0)
    photos = get(f"/api/bonsai/{bonsai_id}/photos") or []
    assert len(photos) == gallery_count_before, (
        f"Expected gallery to have {gallery_count_before} photos (unchanged), "
        f"but found {len(photos)} — session photo was incorrectly added to gallery"
    )


def _get_wiki_path(context, bonsai_name, wiki_subdir):
    today = date.today().isoformat()
    plan_dir = context["plan_wiki_path"].removesuffix(".md")
    work_slug = context["work_type_slug"]
    wiki_path = f"{plan_dir}/{wiki_subdir}/{work_slug}-{today}.md"
    context["refinement_wiki_paths"].append(wiki_path)
    return wiki_path


def _assert_wiki_page_exists(context, wiki_path):
    page = get_wiki_page(wiki_path)
    assert page is not None, (
        f"Expected wiki page at '{wiki_path}'. Last response: {context.get('last_response', {})}"
    )
    assert page.get("content"), f"Wiki page at '{wiki_path}' is empty"


def _assert_work_field_set(context, bonsai_name, work_type, field_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    works = list_planned_works(get, bonsai_id)
    matching = [w for w in works if work_type.lower() in w.get("work_type", "").lower()]
    assert matching, f"No '{work_type}' work found for '{bonsai_name}'"
    assert matching[0].get(field_name), (
        f"Expected PlannedWork.{field_name} to be set for '{work_type}' — got: {matching[0].get(field_name)!r}"
    )
