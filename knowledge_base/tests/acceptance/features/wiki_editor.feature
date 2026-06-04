Feature: Wiki editor — admin corrects wiki pages via natural language

  Scenario: Editor fixes a misspelling across multiple pages in batches
    Given a wiki page "test-editor/page-a.md" exists with content "# Página A\n\nUsa Biorren para fertilizar."
    And a wiki page "test-editor/page-b.md" exists with content "# Página B\n\nAplicar Biorren en primavera."
    When the admin sends "corrige Biorren por Biorend en todas las páginas de test-editor"
    Then "test-editor/page-a.md" contains "Biorend"
    And "test-editor/page-b.md" contains "Biorend"
    And "test-editor/page-a.md" does not contain "Biorren"
    And "test-editor/page-b.md" does not contain "Biorren"

  Scenario: Editor updates a specific page with new content
    Given a wiki page "test-editor/species-note.md" exists with content "# Ficus\n\nEspecie tropical."
    When the admin sends "añade a test-editor/species-note.md que el Ficus necesita riego abundante en verano"
    Then "test-editor/species-note.md" contains "verano"

  Scenario: Editor reports pages fixed and pending when batch limit is reached
    Given 6 wiki pages in "test-editor/batch" all containing the word "Biorren"
    When the admin sends "reemplaza Biorren por Biorend en las páginas de test-editor/batch"
    Then the editor response mentions pages were fixed
    And the editor response mentions remaining pages or completion
