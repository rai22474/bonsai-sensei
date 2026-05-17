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

  Scenario: Record pest detection and apply phytosanitary treatment linked to pest event
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And pest "araña roja" is registered in the catalog
    And phytosanitary product "Aceite de Neem" is registered
    When I report detecting "araña roja" on "Kaze"
    And I confirm the pest detection
    And I confirm that I applied a treatment
    And I select "Aceite de Neem" as the treatment product
    Then bonsai "Kaze" should have a pest detection event for "araña roja"
    And bonsai "Kaze" should have a phytosanitary treatment linked to the pest detection

  Scenario: After recording pest detection on bonsai with active phytosanitary plan, plan review is proposed
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And pest "araña roja" is registered in the catalog
    And bonsai "Kaze" has an active phytosanitary plan
    When I report detecting "araña roja" on "Kaze"
    And I confirm the pest detection
    Then a phytosanitary plan review should be proposed
