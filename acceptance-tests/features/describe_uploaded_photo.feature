Feature: Describe a bonsai photo on upload

  Scenario: Visual description is returned after uploading a photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then I receive a visual description of the photo

  Scenario: Photo is saved and described even when the bonsai has no prior history
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then bonsai "Momiji" should have 1 photo
    And I receive a visual description of the photo
