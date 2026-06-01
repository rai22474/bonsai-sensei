Feature: Episodic memory — observations flow into the wiki

  Scenario: Dreamer incorporates bonsai observation into wiki
    Given the episodic memory has an observation "Tanaka tiene hojas amarillas en el apice desde hace dos semanas"
    When the wiki dreamer runs synchronously
    Then the wiki page for "Tanaka" exists and contains information about the observation
