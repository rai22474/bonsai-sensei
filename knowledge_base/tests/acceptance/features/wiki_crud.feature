Feature: Wiki CRUD — read, write, delete and list wiki pages via REST API

  Scenario: Write and read a wiki page
    Given no wiki page exists at "test-crud/hello.md"
    When a wiki page "test-crud/hello.md" is written with content "# Hello\nTest content"
    Then reading "test-crud/hello.md" returns content containing "Hello"

  Scenario: Overwrite an existing wiki page
    Given a wiki page "test-crud/overwrite.md" exists with content "# Original"
    When a wiki page "test-crud/overwrite.md" is written with content "# Updated"
    Then reading "test-crud/overwrite.md" returns content containing "Updated"
    And reading "test-crud/overwrite.md" does not contain "Original"

  Scenario: Delete a wiki page
    Given a wiki page "test-crud/to-delete.md" exists with content "# Delete me"
    When the wiki page "test-crud/to-delete.md" is deleted
    Then the wiki page "test-crud/to-delete.md" does not exist

  Scenario: List wiki pages in a directory
    Given a wiki page "test-crud/list/page-a.md" exists with content "# A"
    And a wiki page "test-crud/list/page-b.md" exists with content "# B"
    When wiki files in "test-crud/list" are listed
    Then the file list contains "test-crud/list/page-a.md"
    And the file list contains "test-crud/list/page-b.md"

  Scenario: Read a non-existent wiki page returns not found
    Given no wiki page exists at "test-crud/missing.md"
    When "test-crud/missing.md" is read
    Then the result indicates the page was not found
