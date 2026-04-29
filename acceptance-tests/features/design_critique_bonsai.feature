Feature: Critique bonsai design from a stored photo via advice

  Scenario: Design feedback based on the latest stored photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-01"
    When I ask "¿Qué trabajos de diseño le harías a Momiji?"
    Then the bot's response should reference visible structural elements of the tree

  Scenario: Design feedback without stored photos asks for a photo first
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask "¿Qué trabajos de diseño le harías a Momiji?"
    Then the bot's response should ask for a photo before giving design advice
