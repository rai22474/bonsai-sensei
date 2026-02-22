Feature: Apply fertilizer to a bonsai via advice

  Scenario: Apply fertilizer to a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "BioGrow" is registered
    When I report applying "BioGrow" fertilizer to "Kaze" with amount "5 ml"
    And I confirm the fertilizer application
    Then bonsai "Kaze" should have a fertilizer application of "BioGrow" with amount "5 ml"

  Scenario: Cannot apply an unregistered fertilizer to a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    When I report applying "UnknownGrow" fertilizer to "Kaze" with amount "5 ml"
    Then no confirmation should be pending for the fertilizer application
    And bonsai "Kaze" should have no fertilizer application events

  Scenario: List fertilizer applications for a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "BioGrow" is registered
    And fertilizer "NitroPlus" is registered
    And "BioGrow" has been applied to "Kaze" with amount "5 ml"
    And "NitroPlus" has been applied to "Kaze" with amount "10 g"
    When I list the fertilizer applications for "Kaze"
    Then the list should contain a fertilizer application of "BioGrow" with amount "5 ml"
    And the list should contain a fertilizer application of "NitroPlus" with amount "10 g"
