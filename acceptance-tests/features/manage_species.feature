Feature: Manage bonsai species via advice

  Scenario: Create a species via advice
    Given no species named "Ficus Retusa" exists
    When I request to register species "Ficus Retusa" with scientific name "Ficus retusa"
    And I confirm the species creation for "Ficus Retusa" with scientific name "Ficus retusa"
    Then species "Ficus Retusa" should exist

  Scenario: Update a species via advice
    Given species "Juniperus Procumbens" exists with scientific name "Juniperus procumbens"
    When I request to update species "Juniperus Procumbens" scientific name to "Juniperus chinensis"
    And I confirm the update for species "Juniperus Procumbens"
    Then species "Juniperus Procumbens" should have scientific name "Juniperus chinensis"

  Scenario: Delete a species via advice
    Given species "Ulmus Parvifolia" exists with scientific name "Ulmus parvifolia"
    When I request to delete species "Ulmus Parvifolia"
    And I confirm the deletion for species "Ulmus Parvifolia"
    Then species "Ulmus Parvifolia" should not exist
