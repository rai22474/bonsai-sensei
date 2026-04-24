Feature: Manage fertilizers via advice

  Scenario: Create a fertilizer via advice
    When I request to register fertilizer "BioGrow"
    And I confirm the fertilizer creation for "BioGrow"
    Then fertilizer "BioGrow" should exist
    And fertilizer "BioGrow" should have a wiki page

  Scenario: Update fertilizer recommended amount via advice
    Given fertilizer "BioGrow" exists
    When I request to update fertilizer "BioGrow" with recommended amount "5 ml/L"
    And I confirm the fertilizer update for "BioGrow"
    Then fertilizer "BioGrow" should have recommended amount "5 ml/L"

  Scenario: Delete a fertilizer via advice
    Given fertilizer "BioDrop" exists
    When I request to delete fertilizer "BioDrop"
    And I confirm the fertilizer deletion for "BioDrop"
    Then fertilizer "BioDrop" should not exist

  Scenario: List fertilizers via advice
    Given fertilizer "BioBloom" exists
    When I request the fertilizer list
    Then fertilizer list includes "BioBloom"
