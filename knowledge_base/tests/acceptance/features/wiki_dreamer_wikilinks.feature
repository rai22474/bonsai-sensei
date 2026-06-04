Feature: Wiki dreamer — adds wikilinks gradually across knowledge pages

  Scenario: Dreamer adds a wikilink when a page mentions an entity that has its own page
    Given a wiki page "species/test-juniperus.md" exists with content "# Juniperus\n\nEspecie resistente."
    And a wiki page "techniques/test-wikilink-target.md" exists with content "# Técnica\n\nSe aplica en Juniperus sin enlace."
    And the wikilink tracker is reset for "techniques/test-wikilink-target.md"
    When the wiki dreamer runs synchronously
    Then the wiki page "techniques/test-wikilink-target.md" contains "[[species/test-juniperus.md"

  Scenario: Dreamer processes at most 5 pages per run for wikilinks
    Given 7 knowledge pages exist without wikilinks processed
    When the wiki dreamer runs synchronously
    Then at most 5 pages are marked as wikilink-processed in this run

  Scenario: Dreamer skips pages already processed for wikilinks unless they changed
    Given a wiki page "techniques/test-already-done.md" exists with content "# Done"
    And the wikilink tracker marks "techniques/test-already-done.md" as processed
    When the wiki dreamer runs synchronously
    Then "techniques/test-already-done.md" is not included in the wikilink batch
