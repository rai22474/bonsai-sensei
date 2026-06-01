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
    And bonsai "Momiji" has a photo taken on "2026-03-10"
    And bonsai "Momiji" has a photo taken on "2026-06-25"
    When I ask for the photo of bonsai "Momiji" closest to "1 de abril de 2026"
    Then I should receive the photo of bonsai "Momiji" taken on "2026-03-10"

  Scenario: Listing registered photo dates does not display the images
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask which photos bonsai "Momiji" has registered
    Then I should receive the photo dates in the text without any images being sent

  Scenario: Asking to show photos of a bonsai displays the images
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask to show the photos of bonsai "Momiji"
    Then I should receive the images in the response

  Scenario: Delete a photo from a bonsai
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    And bonsai "Momiji" has a photo taken on "2025-06-25"
    When I ask to delete a photo of bonsai "Momiji"
    And I select the photo taken on "2025-06-25"
    And I confirm the photo deletion
    Then bonsai "Momiji" should have 1 photo

  Scenario: Cancel a photo deletion preserves the photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Momiji" exists for species "Acer Palmatum"
    And bonsai "Momiji" has a photo taken on "2025-03-10"
    When I ask to delete a photo of bonsai "Momiji"
    And I select the photo taken on "2025-03-10"
    And I cancel the photo deletion with reason "Me equivoqué, no quiero borrarla"
    Then bonsai "Momiji" should still have 1 photo

  Scenario: Delete a photo when the bonsai does not exist returns an error
    Given no bonsai named "Fantasma" exists
    When I ask to delete a photo of bonsai "Fantasma"
    Then I should receive an error indicating the bonsai does not exist
