Feature: Daily weather alert

  Scenario: Sensei evaluates frost risk and recommends action for registered user
    Given user "weather-alert-test-user" has location "Madrid" registered with chat id "12345"
    When the daily weather alert check runs with frost conditions for "Madrid"
    Then the sensei response for "weather-alert-test-user" mentions frost risk

  Scenario: Sensei confirms safe weather for registered user
    Given user "weather-alert-test-user" has location "Madrid" registered with chat id "12345"
    When the daily weather alert check runs with safe conditions for "Madrid"
    Then the sensei response for "weather-alert-test-user" is non-empty
