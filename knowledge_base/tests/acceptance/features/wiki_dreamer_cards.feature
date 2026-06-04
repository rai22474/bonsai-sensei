Feature: Wiki dreamer — enriches wiki from knowledge cards

  Scenario: Dreamer enriches a species page from a new knowledge card
    Given a wiki page "species/ficus-microcarpa.md" exists with content "# Ficus microcarpa\n\nEspecie tropical."
    And a knowledge card about Ficus microcarpa exists at "test-channel/species-card.md"
    When the wiki dreamer runs synchronously
    Then the wiki page "species/ficus-microcarpa.md" contains "poda"

  Scenario: Dreamer updates an existing page with new card information
    Given a wiki page "techniques/poda-de-mantenimiento.md" exists with content "# Poda de mantenimiento"
    And a knowledge card about poda with chupones exists at "test-channel/poda-card.md"
    When the wiki dreamer runs synchronously
    Then the wiki page "techniques/poda-de-mantenimiento.md" contains "chupones"

  Scenario: Dreamer does not run when there are no new cards
    Given no new knowledge cards exist since the last dreamer run
    When the wiki dreamer runs synchronously
    Then the dreamer reports no changes
