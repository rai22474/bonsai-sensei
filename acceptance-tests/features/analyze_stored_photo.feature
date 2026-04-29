Feature: Analyze a stored bonsai photo via advice

  Scenario: Analyse the latest stored photo by bonsai name
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask to analyse the latest photo of bonsai "Momiji"
    Then the bot's response should contain a visual observation about the photo

  Scenario: Analyse a stored photo by approximate date
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-01-15"
    And bonsai "Momiji" has a photo taken on "2025-06-10"
    When I ask to analyse the photo of bonsai "Momiji" from "enero"
    Then the bot's response should reference the photo taken on "2025-01-15"

  Scenario: Analyse stored photo when no photos exist returns an explanation
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask to analyse the latest photo of bonsai "Momiji"
    Then the bot's response should indicate there are no photos available for "Momiji"
