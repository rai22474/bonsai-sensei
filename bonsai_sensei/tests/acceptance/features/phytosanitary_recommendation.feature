Feature: Get phytosanitary advice via online search when no products registered

  Scenario: Ask for phytosanitary advice with no products in catalog returns online recommendations
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    When I ask for phytosanitary advice for "Kaze" against "araña roja"
    Then the response should contain phytosanitary recommendations
