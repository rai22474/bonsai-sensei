Feature: Apply phytosanitary treatment to a bonsai via advice

  Scenario: Apply phytosanitary treatment to a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And phytosanitary product "NimBio" is registered
    When I report applying "NimBio" phytosanitary treatment to "Kaze" with amount "3 ml"
    And I confirm the phytosanitary application
    Then bonsai "Kaze" should have a phytosanitary application of "NimBio" with amount "3 ml"

  Scenario: Cannot apply an unregistered phytosanitary product to a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    When I report applying "UnknownProduct" phytosanitary treatment to "Kaze" with amount "3 ml"
    Then no confirmation should be pending for the phytosanitary application
    And bonsai "Kaze" should have no phytosanitary application events

  Scenario: List phytosanitary treatments for a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And phytosanitary product "NimBio" is registered
    And phytosanitary product "CopperShield" is registered
    And "NimBio" phytosanitary treatment has been applied to "Kaze" with amount "3 ml"
    And "CopperShield" phytosanitary treatment has been applied to "Kaze" with amount "2 g"
    When I list the phytosanitary treatments for "Kaze"
    Then the treatment list should contain "NimBio" with amount "3 ml"
    And the treatment list should contain "CopperShield" with amount "2 g"
