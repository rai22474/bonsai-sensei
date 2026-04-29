Feature: Identify bonsai species from a photo via advice

  Scenario: Identify species from an uploaded photo
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Desconocido" exists for species "Acer Palmatum"
    When I send a photo and ask "¿Qué especie crees que es este árbol?"
    And I confirm the photo belongs to bonsai "Desconocido"
    Then the bot's response should name a species

  Scenario: Species identification offers to update the bonsai record
    Given species "Acer Palmatum" exists with scientific name "Acer palmatum"
    And a bonsai named "Desconocido" exists for species "Acer Palmatum"
    When I send a photo and ask "¿Qué especie crees que es este árbol?"
    And I confirm the photo belongs to bonsai "Desconocido"
    Then the bot's response should name a species
    And the bot's response should offer to update the bonsai record with the identified species
