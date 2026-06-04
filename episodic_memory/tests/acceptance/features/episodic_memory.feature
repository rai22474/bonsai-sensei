Feature: Episodic Memory API

  Scenario: Episode appears in observations after submission
    When a conversation episode about "Yamadori tiene manchas negras" is submitted for user "obs-user-1"
    Then the observations since submission contain content from the episode

  Scenario: Observations aggregate episodes from all users
    Given a conversation episode about "Ficus necesita riego" is submitted for user "obs-user-2"
    And a conversation episode about "Olmo tiene hojas caídas" is submitted for user "obs-user-3"
    Then the observations since the beginning contain content from both users

  Scenario: Memory search returns relevant facts for a user
    Given a conversation episode about "Tanaka tiene hojas amarillas en el apice" is submitted for user "search-user-1"
    When memory is searched for user "search-user-1" with query "hojas amarillas"
    Then the search results are not empty

  Scenario: Memory search is isolated per user
    Given a conversation episode about "Bonsai de pino necesita fertilizante" is submitted for user "isolated-user-1"
    When memory is searched for user "isolated-user-2" with query "pino fertilizante"
    Then the search results are empty
