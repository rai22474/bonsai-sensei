Feature: Episodic memory — conversation observations flow into the wiki

  Scenario: Dreamer incorporates bonsai observation from conversation into wiki
    Given species "Ficus retusa" exists with scientific name "Ficus retusa"
    And a bonsai named "Tanaka" exists for species "Ficus retusa"
    When I report "Tanaka tiene hojas amarillas en el apice desde hace dos semanas"
    And the wiki dreamer runs synchronously
    Then the wiki page for "Tanaka" exists and contains information about the observation
