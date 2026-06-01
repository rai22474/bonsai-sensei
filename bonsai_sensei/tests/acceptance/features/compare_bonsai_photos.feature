Feature: Compare stored bonsai photos to track progress

  Scenario: Observable changes are described when comparing two photos from different dates
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-01-01"
    And bonsai "Momiji" has a photo taken on "2025-07-01"
    When I ask to compare the photos of "Momiji" from "principio y fin de año"
    Then I receive a description of observable changes between the two photos

  Scenario: Only one photo available returns an explanation and offers to analyse it
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-01-01"
    When I ask to compare the photos of "Momiji"
    Then I am informed that only one photo is available
    And I am offered to analyse the single photo instead

  Scenario: No photos available returns an explanation
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I ask to compare the photos of "Momiji"
    Then I am informed that no photos are available for "Momiji"
