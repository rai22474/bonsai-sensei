Feature: Manage bonsai photos via advice

  Scenario: Add a photo to a bonsai
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    When I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then bonsai "Momiji" should have 1 photo

  Scenario: Add multiple photos to a bonsai accumulates them
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" already has 1 photo
    When I send a photo
    And I confirm the photo belongs to bonsai "Momiji"
    Then bonsai "Momiji" should have 2 photos

  Scenario: Add a photo when the bonsai does not exist returns an error
    Given no bonsai named "Fantasma" exists
    When I send a photo
    And I confirm the photo belongs to bonsai "Fantasma"
    Then I should receive an error indicating the bonsai does not exist

  Scenario: Retrieve the latest photo of a bonsai
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask for the latest photo of bonsai "Momiji"
    Then I should receive the photo of bonsai "Momiji" taken on "2025-06-25"

  Scenario: Retrieve a photo by exact date
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask for the photo of bonsai "Momiji" taken on "25 de junio"
    Then I should receive the photo of bonsai "Momiji" taken on "2025-06-25"

  Scenario: Retrieve the photo closest to a given date
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask for the photo of bonsai "Momiji" closest to "1 de abril"
    Then I should receive the photo of bonsai "Momiji" taken on "2025-03-10"

  Scenario: Delete a photo from a bonsai
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" already has 2 photos
    When I request to delete the first photo of bonsai "Momiji"
    And I confirm the photo deletion for bonsai "Momiji"
    Then bonsai "Momiji" should have 1 photo

  Scenario: Cancel a photo deletion preserves the photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" already has 1 photo
    When I request to delete the first photo of bonsai "Momiji"
    And I cancel the deletion with reason "Me equivoqué, no quiero borrarla"
    Then bonsai "Momiji" should still have 1 photo

  Scenario: Delete a photo when the bonsai does not exist returns an error
    Given no bonsai named "Fantasma" exists
    When I request to delete the first photo of bonsai "Fantasma"
    Then I should receive an error indicating the bonsai does not exist
