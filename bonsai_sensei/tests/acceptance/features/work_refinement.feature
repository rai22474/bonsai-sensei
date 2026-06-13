Feature: Work documentation sessions (kiroku)

  Scenario: Pre-work analysis session saves wiki under the plan directory
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Naruto" exists for species "Pinus Sylvestris"
    And "Naruto" has an active development plan with a "mekiri" planned on "2026-09-15"
    When I start a pre-work session for "Naruto" via advice
    And I select the only planned work
    And I discuss the work with "¿Cuántos brotes debo dejar por rama?"
    And I close the kiroku session
    Then a refinement wiki page should exist for "Naruto" under the plan directory
    And the "mekiri" planned work for "Naruto" should have its refinement_wiki_path set

  Scenario: Post-work result session saves wiki under the plan directory
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Naruto" exists for species "Pinus Sylvestris"
    And "Naruto" has an active development plan with a "poda" planned on "2026-09-20"
    When I start a post-work session for "Naruto" via advice
    And I select the only planned work
    And I discuss the work with "He cortado ramas cruzadas y reducido la copa un 30%"
    And I close the kiroku session
    Then a result wiki page should exist for "Naruto" under the plan directory
    And the "poda" planned work for "Naruto" should have its result_wiki_path set

  Scenario: Photos sent during session are analyzed contextually and not added to bonsai gallery
    Given species "Pinus Sylvestris" exists with scientific name "Pinus sylvestris"
    And a bonsai named "Naruto" exists for species "Pinus Sylvestris"
    And "Naruto" has an active development plan with a "alambrado" planned on "2026-09-25"
    When I start a post-work session for "Naruto" via advice
    And I select the only planned work
    And I send a photo during the session
    And I discuss the work with "El alambrado ha quedado bien distribuido"
    And I close the kiroku session
    Then a result wiki page should exist for "Naruto" under the plan directory
    And the result wiki page should contain photo analysis
    And the bonsai gallery for "Naruto" should not contain the session photo
