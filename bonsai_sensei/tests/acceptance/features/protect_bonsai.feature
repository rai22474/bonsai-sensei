Feature: Protect bonsai at night

  Scenario: Advise protection for nighttime frost risk
    Given a bonsai collection with frost-sensitive bonsais
    When I ask "Dime si mis bonsais deben estar protegidos esta noche en Madrid"
    Then I get a protection recommendation

  Scenario: Advise no protection for mild night
    Given a bonsai collection with frost-sensitive bonsais
    When I ask "Dime si mis bonsais deben estar protegidos esta noche en Madrid"
    Then I get a protection recommendation
