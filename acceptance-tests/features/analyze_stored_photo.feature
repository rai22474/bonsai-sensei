Feature: Analyze a stored bonsai photo

  Scenario: Visual description is returned for the latest stored photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask to analyse the latest photo of bonsai "Momiji"
    Then I receive a visual description of the photo

  Scenario: Photo from approximate date is identified and described
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-01-15"
    And bonsai "Momiji" has a photo taken on "2025-06-10"
    When I ask to analyse the photo of bonsai "Momiji" from "enero"
    Then I receive an analysis of the photo taken on "2025-01-15"

  Scenario: No photos available returns an explanation
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask to analyse the latest photo of bonsai "Momiji"
    Then I am informed that no photos are available for "Momiji"
