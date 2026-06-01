Feature: Manage fertilization plans for bonsais via advice

  Scenario: Propose and confirm a fertilization plan
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Hanako" exists for species "Ficus Retusa"
    And fertilizer "Biogold" is registered
    When I request a fertilization plan for "Hanako" from "2026-09-01" to "2026-11-30"
    And I confirm the fertilization plan for "Hanako"
    Then "Hanako" should have an active fertilization plan
    And "Hanako" should have planned works linked to the fertilization plan

  Scenario: Abandon an active fertilization plan
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Hanako" exists for species "Ficus Retusa"
    And fertilizer "Biogold" is registered
    And "Hanako" has an active fertilization plan with a future work on "2099-12-01"
    When I ask to abandon the fertilization plan for "Hanako" because "Switching to organic only"
    And I confirm the abandonment
    Then "Hanako" should have no active fertilization plan
    And "Hanako" should have no planned works linked to the abandoned plan
