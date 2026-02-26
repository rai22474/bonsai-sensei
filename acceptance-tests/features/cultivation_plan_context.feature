Feature: Cultivation plan agent is aware of available products and bonsai history

  Scenario: Plan fertilization selects from available registered fertilizers
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "BioGrow" is registered
    When I ask to plan a fertilization for "Kaze" on "2026-04-01" without specifying a fertilizer
    And I confirm the planned work
    Then "Kaze" should have a planned fertilization using "BioGrow"

  Scenario: Cultivation agent can consult bonsai event history
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "BioGrow" is registered
    And "Kaze" has been fertilized with "BioGrow"
    When I ask about recent fertilization treatments for "Kaze"
    Then the response mentions "BioGrow"
