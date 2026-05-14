Feature: Manage cultivation work plan for a bonsai via advice

  Scenario: Plan a fertilization for a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "biogrow" is registered
    When I plan a fertilization of "biogrow" with amount "5 ml" for "Kaze" on "2026-03-15"
    And I confirm the planned work
    Then "Kaze" should have a planned fertilization of "biogrow" on "2026-03-15"

  Scenario: Ask about weekend planned works
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "biogrow" is registered
    And "Kaze" has a planned fertilization of "biogrow" with amount "5 ml" for next Saturday
    When I ask what I have planned for the weekend
    Then the response mentions "Kaze"

  Scenario: Planning without a date suggests the next weekend
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "biogrow" is registered
    When I plan a fertilization of "biogrow" with amount "5 ml" for "Kaze" without specifying a date
    And I confirm the planned work
    Then the planned fertilization for "Kaze" is scheduled on a weekend day

  Scenario: Replan removes an outdated planned fertilization
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "biogrow" is registered
    And "Kaze" has a planned fertilization of "biogrow" with amount "5 ml" for next Saturday
    When I ask to remove the planned fertilization of "biogrow" for "Kaze"
    And I confirm the planned work
    Then "Kaze" should have no pending planned works for "biogrow"

  Scenario: Execute a planned fertilization
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And fertilizer "biogrow" is registered
    And "Kaze" has a planned fertilization of "biogrow" with amount "5 ml" on "2026-03-15"
    When I report executing planned work for "Kaze" and "biogrow"
    And I confirm the execution
    Then bonsai "Kaze" should have a fertilizer_application event for "biogrow"
    And "Kaze" should have no pending planned works for "biogrow"
