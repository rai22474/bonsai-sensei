Feature: Describe a bonsai photo on upload via advice

  Scenario: Model describes what it sees when a photo is uploaded
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then the bot's response should contain a visual observation about the image

  Scenario: Model describes photo even when the bonsai has no prior history
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then bonsai "Momiji" should have 1 photo
    And the bot's response should contain a visual observation about the image
