Feature: Diagnose bonsai health with photo evidence via advice
  # NOTE: blocked by ISSUE-002 (session reset at 50 events)

  @wip
  Scenario: Diagnose a health symptom described before sending a photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I describe "las hojas de Momiji están amarilleando"
    And I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then the bot's response should connect the described symptom with what is visible in the photo
    And the bot's response should include at least one actionable recommendation

  @wip
  Scenario: Proactively identify health issues without prior symptom description
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo and ask "¿Ves algo malo en Momiji?"
    And I confirm the photo belongs to bonsai "Momiji"
    Then the bot's response should describe the visible condition of the tree
    And the bot's response should include at least one observation or recommendation
