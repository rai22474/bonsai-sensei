Feature: Diagnose bonsai health with photo evidence
  # NOTE: blocked by ISSUE-002 (session reset at 50 events)

  @wip
  Scenario: Diagnosis connects described symptom with photo evidence
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I describe "las hojas de Momiji están amarilleando"
    And I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then I receive a diagnosis connecting the described symptom with what is visible in the photo
    And I receive at least one actionable recommendation

  @wip
  Scenario: Health issues are identified proactively without prior symptom description
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo and ask "¿Ves algo malo en Momiji?"
    And I confirm the photo belongs to bonsai "Momiji"
    Then I receive a description of the visible condition of the tree
    And I receive at least one observation or recommendation
