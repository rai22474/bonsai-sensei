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
