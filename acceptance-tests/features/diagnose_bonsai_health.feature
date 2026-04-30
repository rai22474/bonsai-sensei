Feature: Diagnose bonsai health from stored photo evidence

  Scenario: Diagnosis connects a described symptom with what is visible in a stored photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-01"
    When I ask "Las hojas de Momiji están amarilleando, ¿qué puede ser?"
    Then I receive a diagnosis connecting the described symptom with what is visible in the photo
    And I receive at least one actionable recommendation

  Scenario: Health issues are identified proactively from a stored photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-01"
    When I ask "¿Ves algo malo en Momiji?"
    Then I receive a description of the visible condition of the tree
    And I receive at least one observation or recommendation

  Scenario: No stored photos prompts for a photo before health advice is given
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask "¿Ves algo malo en Momiji?"
    Then I am asked to provide a photo before receiving health advice
