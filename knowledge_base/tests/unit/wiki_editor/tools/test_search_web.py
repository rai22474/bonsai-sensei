from unittest.mock import MagicMock, patch
from hamcrest import assert_that, contains_string, equal_to

from knowledge_base.wiki_editor.tools.search_web import create_web_searcher


def test_should_return_answer_and_sources():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "answer": "Trichoderma es un hongo beneficioso.",
        "results": [
            {"title": "Guía Trichoderma", "url": "https://example.com/tricho", "content": "Detalle sobre Trichoderma."},
        ],
    }

    with patch("knowledge_base.wiki_editor.tools.search_web.TavilyClient", return_value=mock_client):
        search = create_web_searcher("fake-key")
        result = search("Trichoderma bonsai")

    assert_that(result, contains_string("Trichoderma es un hongo beneficioso."), "Should include answer summary")
    assert_that(result, contains_string("Guía Trichoderma"), "Should include source title")
    assert_that(result, contains_string("https://example.com/tricho"), "Should include source URL")


def test_should_return_no_results_message_when_empty():
    mock_client = MagicMock()
    mock_client.search.return_value = {"answer": "", "results": []}

    with patch("knowledge_base.wiki_editor.tools.search_web.TavilyClient", return_value=mock_client):
        search = create_web_searcher("fake-key")
        result = search("query sin resultados")

    assert_that(result, equal_to("No se encontraron resultados."), "Should report no results")


def test_should_call_tavily_with_correct_parameters():
    mock_client = MagicMock()
    mock_client.search.return_value = {"answer": "ok", "results": []}

    with patch("knowledge_base.wiki_editor.tools.search_web.TavilyClient", return_value=mock_client):
        search = create_web_searcher("fake-key")
        search("Biogold fertilizante bonsai")

    mock_client.search.assert_called_once_with(
        query="Biogold fertilizante bonsai",
        max_results=5,
        include_answer=True,
        include_raw_content=False,
    )


def test_should_include_multiple_sources():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "answer": "",
        "results": [
            {"title": "Fuente A", "url": "https://a.com", "content": "Contenido A."},
            {"title": "Fuente B", "url": "https://b.com", "content": "Contenido B."},
        ],
    }

    with patch("knowledge_base.wiki_editor.tools.search_web.TavilyClient", return_value=mock_client):
        search = create_web_searcher("fake-key")
        result = search("query")

    assert_that(result, contains_string("Fuente A"), "Should include first source")
    assert_that(result, contains_string("Fuente B"), "Should include second source")
