Feature: Mimamori daily reflection

  Scenario: User with planned works receives a daily reflection
    Given user "weekend-reminder-test-user" has chat id "99001" registered
    And species "Ficus Retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Hanako" exists for species "Ficus Retusa"
    And "Hanako" has a fertilization planned for next Saturday
    When the mimamori triggers
    Then the response for "weekend-reminder-test-user" mentions "Hanako"

  Scenario: User with no planned works receives a reflection
    Given user "weekend-reminder-test-user" has chat id "99001" registered
    When the mimamori triggers
    Then the response for "weekend-reminder-test-user" is non-empty

  Scenario: Mimamori alerts about fertilization plan misaligned with design plan
    Given user "weekend-reminder-test-user" has chat id "99001" registered
    And species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuro" exists for species "Pinus Sylvestris"
    And "Kuro" has an outdated fertilization plan
    And "Kuro" has a newer active design plan
    When the mimamori triggers
    Then the response for "weekend-reminder-test-user" mentions "Kuro"
