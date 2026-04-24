Feature: Manage phytosanitary products via advice

  Scenario: Create a phytosanitary product via advice
    When I request to register phytosanitary product "Neem Oil"
    And I confirm the phytosanitary creation for "Neem Oil"
    Then phytosanitary product "Neem Oil" should exist
    And phytosanitary product "Neem Oil" should have a wiki page

  Scenario: Update phytosanitary recommended amount via advice
    Given phytosanitary product "Neem Oil" exists
    When I request to update phytosanitary product "Neem Oil" with recommended amount "3 ml/L"
    And I confirm the phytosanitary update for "Neem Oil"
    Then phytosanitary product "Neem Oil" should have recommended amount "3 ml/L"

  Scenario: Delete a phytosanitary product via advice
    Given phytosanitary product "Copper Soap" exists
    When I request to delete phytosanitary product "Copper Soap"
    And I confirm the phytosanitary deletion for "Copper Soap"
    Then phytosanitary product "Copper Soap" should not exist

  Scenario: List phytosanitary products via advice
    Given phytosanitary product "Copper Soap" exists
    When I request the phytosanitary list
    Then phytosanitary list includes "Copper Soap"
