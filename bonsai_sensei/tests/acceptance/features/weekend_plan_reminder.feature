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
