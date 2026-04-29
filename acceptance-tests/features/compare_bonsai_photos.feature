Feature: Compare stored bonsai photos to track progress via advice

  Scenario: Compare two stored photos from different dates
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-01-01"
    And bonsai "Momiji" has a photo taken on "2025-07-01"
    When I ask to compare the photos of "Momiji" from "principio y fin de año"
    Then the bot's response should mention observable changes between the two photos

  Scenario: Comparison with only one available photo explains the limitation
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-01-01"
    When I ask to compare the photos of "Momiji"
    Then the bot's response should indicate only one photo is available
    And the bot's response should offer to analyse the single photo instead

  Scenario: Comparison when no photos exist returns an explanation
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask to compare the photos of "Momiji"
    Then the bot's response should indicate there are no photos available for "Momiji"
