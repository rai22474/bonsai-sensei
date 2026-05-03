Feature: Diagnose bonsai health from stored photo evidence

  Scenario: Health analysis is returned for the latest stored photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-01"
    When I ask to analyse the health of the latest photo of bonsai "Momiji"
    Then I receive a health analysis of the photo
    And I receive at least one actionable recommendation

  Scenario: No stored photos prompts for a photo before health advice is given
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask to analyse the health of the latest photo of bonsai "Momiji"
    Then I am asked to provide a photo before receiving health advice
