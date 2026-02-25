Feature: Record a transplant for a bonsai via advice

  Scenario: Record a transplant for a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    When I report a transplant for "Kaze" with pot size "20 cm", pot type "cerámica" and substrate "akadama y pomice"
    And I confirm the transplant
    Then bonsai "Kaze" should have a transplant event with pot size "20 cm", pot type "cerámica" and substrate "akadama y pomice"

  Scenario: List transplants for a bonsai
    Given species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Kaze" exists for species "Ficus Retusa"
    And a transplant for "Kaze" has been recorded with pot size "20 cm", pot type "cerámica" and substrate "akadama y pomice"
    When I list the transplants for "Kaze"
    Then the list should mention "20 cm"
