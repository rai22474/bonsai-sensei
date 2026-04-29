Feature: Critique bonsai design from a stored photo

  Scenario: Design feedback references visible structural elements of the tree
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-01"
    When I ask "¿Qué trabajos de diseño le harías a Momiji?"
    Then I receive design feedback referencing visible structural elements of the tree

  Scenario: No stored photos prompts for a photo before design advice is given
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask "¿Qué trabajos de diseño le harías a Momiji?"
    Then I am asked to provide a photo before receiving design advice
