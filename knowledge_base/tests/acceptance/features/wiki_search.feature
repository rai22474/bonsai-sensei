Feature: Wiki semantic search — returns relevant pages for a query

  Scenario: Search returns a page whose content matches the query
    Given a wiki page "test-search/biogold-test.md" exists with content "# Biogold\n\nFertilizante orgánico sólido japonés para bonsái. Alto contenido en nitrógeno."
    And the wiki index is rebuilt
    When the wiki is searched for "fertilizante organico japones"
    Then the search results contain a page with path "test-search/biogold-test.md"

  Scenario: Search returns multiple results ordered by relevance
    Given a wiki page "test-search/pino-test.md" exists with content "# Pino negro\n\nEspecie de pino japonés. Requiere mekiri en primavera."
    And a wiki page "test-search/azalea-test.md" exists with content "# Azalea\n\nEspecie de flor. Requiere suelo ácido."
    And the wiki index is rebuilt
    When the wiki is searched for "pino japones mekiri"
    Then the first search result has path "test-search/pino-test.md"

  Scenario: Search returns results with a relevance score
    Given a wiki page "test-search/score-test.md" exists with content "# Trichoderma\n\nHongo beneficioso para el sistema radicular del bonsái."
    And the wiki index is rebuilt
    When the wiki is searched for "hongo beneficioso raices"
    Then the search results contain a page with path "test-search/score-test.md"
    And the first search result has a relevance score above 0.5

  Scenario: Search with user_id returns global pages and that user's pages
    Given a wiki page "test-search/global-user-test.md" exists with content "# Keto\n\nSustrato orgánico tradicional japonés para bonsái de exterior."
    And a user wiki page "users/search-user-bdd/bonsai/mi-ficus/index.md" exists with content "# Mi Ficus\n\nFicus retusa con hojas amarillas en el ápice. Sustrato keto."
    And the wiki index is rebuilt
    When the wiki is searched for "keto sustrato japones" with user_id "search-user-bdd"
    Then the search results contain a page with path "test-search/global-user-test.md"
    And the search results contain a page with path "users/search-user-bdd/bonsai/mi-ficus/index.md"

  Scenario: Search without user_id returns only global pages
    Given a wiki page "test-search/global-only-test.md" exists with content "# Nebari\n\nDesarrollo de raíces superficiales en bonsái. Técnica de exposición progresiva."
    And a user wiki page "users/other-user-bdd/bonsai/mi-pino/index.md" exists with content "# Mi Pino\n\nPino negro con nebari en desarrollo."
    And the wiki index is rebuilt
    When the wiki is searched for "nebari raices bonsai"
    Then the search results contain a page with path "test-search/global-only-test.md"
    And the search results do not contain pages from "users/"
