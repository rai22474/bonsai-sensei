Feature: Episodic memory — observations flow into the wiki with dual taxonomy routing

  Scenario: Dreamer routes bonsai observation to user bonsai zone
    Given the episodic memory has an observation from user "obs-user-bdd-001" about "Tanaka tiene hojas amarillas en el apice desde hace dos semanas"
    When the wiki dreamer runs synchronously
    Then the wiki page "users/obs-user-bdd-001/bonsai/tanaka/index.md" exists and contains "amarill"

  Scenario: Dreamer routes technique observation to user techniques-notes
    Given the episodic memory has an observation from user "obs-user-bdd-002" about "Probé el alambrado en mis pinos el mes pasado, la madera estaba muy flexible y los movimientos quedaron bien fijados, mejor resultado que cuando lo intenté en otoño"
    When the wiki dreamer runs synchronously
    Then a wiki page exists under "users/obs-user-bdd-002/techniques-notes/" containing "alambrado"

  Scenario: Dreamer routes global observation to global wiki
    Given the episodic memory has a global observation about "La araña roja Tetranychus urticae se trata con abamectina en verano"
    When the wiki dreamer runs synchronously
    Then a wiki page exists in the global wiki containing "abamectina"
