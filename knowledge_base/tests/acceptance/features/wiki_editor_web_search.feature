Feature: Wiki editor — searches the web to enrich wiki content

  Scenario: Editor searches web and writes result to wiki page
    Given no wiki page exists at "test-search-web/trichoderma.md"
    When the admin sends "busca en web qué es Trichoderma harzianum y crea la página test-search-web/trichoderma.md con lo que encuentres"
    Then "test-search-web/trichoderma.md" exists in the wiki
    And "test-search-web/trichoderma.md" contains relevant content about "Trichoderma"

  Scenario: Editor combines web search with existing wiki content
    Given a wiki page "test-search-web/biogold.md" exists with content "# Biogold\n\nFertilizante orgánico."
    When the admin sends "busca en web más información sobre Biogold fertilizante bonsai y añádela a test-search-web/biogold.md"
    Then "test-search-web/biogold.md" has more content than before
