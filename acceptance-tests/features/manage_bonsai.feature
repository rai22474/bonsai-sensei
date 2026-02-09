Feature: Manage bonsai via advice

  Scenario: Create a bonsai via advice
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    When I request to register bonsai "Momiji" for species "Acer Palmatum"
    And I confirm the bonsai creation for "Momiji"
    Then bonsai "Momiji" should exist

  Scenario: Update a bonsai name via advice
    Given species "Pinus Thunbergii" exists with scientific name "Pinus thunbergii"
    And a bonsai named "Kumo" exists for species "Pinus Thunbergii"
    When I request to rename bonsai "Kumo" to "Kumo Azul"
    And I confirm the bonsai update for "Kumo"
    Then bonsai "Kumo Azul" should exist

  Scenario: Delete a bonsai via advice
    Given species "Juniperus Chinensis" exists with scientific name "Juniperus chinensis"
    And a bonsai named "Sora" exists for species "Juniperus Chinensis"
    When I request to delete bonsai "Sora"
    And I confirm the bonsai deletion for "Sora"
    Then bonsai "Sora" should not exist
