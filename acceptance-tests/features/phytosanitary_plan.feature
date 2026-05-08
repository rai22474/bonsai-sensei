Feature: Manage phytosanitary plans for bonsais via advice

  Scenario: Propose and confirm a phytosanitary plan
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Hanako" exists for species "Ficus Retusa"
    And phytosanitary product "Neem Oil" is registered
    When I request a phytosanitary plan for "Hanako" from "2026-09-01" to "2026-11-30"
    And I confirm the phytosanitary plan for "Hanako"
    Then "Hanako" should have an active phytosanitary plan
    And "Hanako" should have planned works linked to the phytosanitary plan

  Scenario: Abandon an active phytosanitary plan
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Hanako" exists for species "Ficus Retusa"
    And phytosanitary product "Neem Oil" is registered
    And "Hanako" has an active phytosanitary plan with a future treatment on "2099-12-01"
    When I ask to abandon the phytosanitary plan for "Hanako" because "Switching to biological products only"
    And I confirm the phytosanitary plan abandonment
    Then "Hanako" should have no active phytosanitary plan
    And "Hanako" should have no planned works linked to the abandoned phytosanitary plan
