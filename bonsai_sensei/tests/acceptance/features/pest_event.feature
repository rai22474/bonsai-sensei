Feature: Record pest detection events for a bonsai via advice

  Scenario: Record a pest detection event for a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And pest "araña roja" is registered in the catalog
    When I report detecting "araña roja" on "Kaze"
    And I confirm the pest detection
    Then bonsai "Kaze" should have a pest detection event for "araña roja"

  Scenario: Cannot record a pest event for an unregistered pest
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    When I report detecting "ácaro invisible" on "Kaze"
    Then no confirmation should be pending for the pest detection
    And bonsai "Kaze" should have no pest detection events

  Scenario: Apply phytosanitary treatment linked to a pest detection event
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And pest "araña roja" is registered in the catalog
    And phytosanitary product "aceite de neem" is registered
    And bonsai "Kaze" has a recent pest detection event for "araña roja"
    When I apply "aceite de neem" to "Kaze" with amount "5 ml"
    And I select the pest event for "araña roja" to link
    And I confirm the phytosanitary application
    Then the phytosanitary application on "Kaze" should be linked to the pest detection event

