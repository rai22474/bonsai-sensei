Feature: Wiki review — admin confirms or reverts dreamer changes via API

  Scenario: Admin confirms a page changed by the dreamer
    Given a wiki page "bonsai/review-test/index.md" with content "# Review test bonsai"
    When a review session is created for the uncommitted wiki changes
    Then the review session has "bonsai/review-test/index.md" as pending
    When the admin confirms page 0 of the review session
    Then "bonsai/review-test/index.md" is in the confirmed list
    And "bonsai/review-test/index.md" is no longer pending

  Scenario: Admin reverts a page changed by the dreamer
    Given a wiki page "bonsai/revert-test/index.md" with content "# Revert test bonsai"
    When a review session is created for the uncommitted wiki changes
    Then the review session has "bonsai/revert-test/index.md" as pending
    When the admin reverts page 0 of the review session
    Then "bonsai/revert-test/index.md" is no longer pending
    And the wiki page "bonsai/revert-test/index.md" no longer exists
