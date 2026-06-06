Feature: Manage development plans for bonsais via advice

  Scenario: Propose and confirm a development plan
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuromatsu" exists for species "Pinus Sylvestris"
    And "Kuromatsu" has an analysis report in the wiki
    When I request a development plan for "Kuromatsu" as a "planton" in phase "engorde" targeting style "moyogi" with goal "Build a thick trunk with strong taper"
    And I confirm the development plan for "Kuromatsu"
    Then "Kuromatsu" should have an active development plan
    And "Kuromatsu" should have planned works linked to the development plan

  Scenario: Development plan requires a photo or analysis report when none exists
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuromatsu" exists for species "Pinus Sylvestris"
    When I request a development plan for "Kuromatsu" as a "planton" in phase "engorde" targeting style "moyogi" with goal "Build a thick trunk with strong taper"
    Then the agent should ask for a photo before starting the plan

  Scenario: Development plan requires a photo when only old reports exist
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuromatsu" exists for species "Pinus Sylvestris"
    And "Kuromatsu" has an analysis report from a previous year
    When I request a development plan for "Kuromatsu" as a "planton" in phase "engorde" targeting style "moyogi" with goal "Build a thick trunk with strong taper"
    Then the agent should ask for a photo before starting the plan

  Scenario: Executing a design work records the development phase in history
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuromatsu" exists for species "Pinus Sylvestris"
    And "Kuromatsu" has an active development plan with a future work on "2026-06-10"
    When I execute the planned work for "Kuromatsu" via advice
    Then "Kuromatsu" history should contain an event with development phase

  Scenario: Abandoning a development plan records a phase change event
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuromatsu" exists for species "Pinus Sylvestris"
    And "Kuromatsu" has an active development plan with a future work on "2099-12-01"
    When I ask to abandon the development plan for "Kuromatsu" because "Moving to structure phase"
    And I confirm the abandonment
    Then "Kuromatsu" history should contain a phase_change event

  Scenario: Abandon an active development plan
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Kuromatsu" exists for species "Pinus Sylvestris"
    And "Kuromatsu" has an active development plan with a future work on "2099-12-01"
    When I ask to abandon the development plan for "Kuromatsu" because "Changing approach after repot"
    And I confirm the abandonment
    Then "Kuromatsu" should have no active development plan
    And "Kuromatsu" should have no planned works linked to the abandoned plan
