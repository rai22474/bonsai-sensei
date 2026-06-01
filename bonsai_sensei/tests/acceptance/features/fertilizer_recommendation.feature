Feature: Recommend fertilizer for a bonsai via advice

  Scenario: Ask for fertilizer recommendation saves recommendation to wiki
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "Biogold" is registered in the catalog
    When I ask for fertilizer recommendation for "Kaze"
    Then the response should contain a fertilizer recommendation
    And the fertilization plan wiki page for "Kaze" should exist
