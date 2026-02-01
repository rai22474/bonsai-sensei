- [x] Verify that the copilot-instructions.md file in the .github directory is created.

- [x] Clarify Project Requirements

- [x] Scaffold the Project
    - Initialize uv project (pyproject.toml).
    - Create main.py (FastAPI app).
    - Create Dockerfile.

- [x] Customize the Project
    - Implemented Telegram Bot (Long Polling).
    - Added centralized English logging.
    - Integrated Google ADK for AI Agent with Weather Tool using `google-adk`.

- [x] Install Required Extensions

- [x] Compile the Project
    - Dependencies installed with `uv sync`.

- [x] Create and Run Task
    - Created task "Run with uvicorn".

- [x] Launch the Project

- [x] Ensure Documentation is Complete
## Execution Guidelines
PROGRESS TRACKING:
- If any tools are available to manage the above todo list, use it to track progress through this checklist.
- After completing each step, mark it complete and add a summary.
- Read current todo list status before starting each new step.

COMMUNICATION RULES:
- Avoid verbose explanations or printing full command outputs.
- If a step is skipped, state that briefly (e.g. "No extensions needed").
- Do not explain project structure unless asked.
- Keep explanations concise and focused.

DEVELOPMENT RULES:
- Use '.' as the working directory unless user specifies otherwise.
- Avoid adding media or external links unless explicitly requested.
- Use placeholders only with a note that they should be replaced.
- Use VS Code API tool only for VS Code extension projects.
- Once the project is created, it is already opened in Visual Studio Code—do not suggest commands to open this project in Visual Studio again.
- If the project setup information has additional rules, follow them strictly.
- LANGUAGE RULES: Ensure all comments and logs are in English.
- DOCUMENTATION RULES: Do not add docstrings to functions/methods if the name is self-explanatory. Only add docstrings if they explain "why" something is done or complex behavior that isn't obvious from the signature.
- CODE CLEANLINESS: Do not use comments inside functions/methods. Instead, ensure function and variable names are self-explanatory. STRICTLY FORBIDDEN to generate comments explaining code logic.
- ERROR HANDLING: Never catch generic Exceptions just for logging purposes. Let them bubble up to the global exception handler.
- IMPORT RULES: Never use relative imports (e.g., `from .module import func`). Always use absolute imports (e.g., `from package.module import func`).
- DESIGN RULES: Inject external dependencies into functions for testability (e.g., translators, HTTP clients).
- DOMAIN RULES: Keep domain entities in `bonsai_sensei/domain`, not in `bonsai_sensei/database`.
- TESTING RULES: Use a single assert per test.
- TESTING RULES: Prefer pytest fixtures for test data setup.
- TESTING RULES: Name tests with a should_ prefix.
- TESTING RULES: Place fixtures below tests in test files.

FOLDER CREATION RULES:
- Always use the current directory as the project root.
- If you are running any terminal commands, use the '.' argument to ensure that the current working directory is used ALWAYS.
- Do not create a new folder unless the user explicitly requests it besides a .vscode folder for a tasks.json file.
- If any of the scaffolding commands mention that the folder name is not correct, let the user know to create a new folder with the correct name and then reopen it again in vscode.

EXTENSION INSTALLATION RULES:
- Only install extension specified by the get_project_setup_info tool. DO NOT INSTALL any other extensions.

PROJECT CONTENT RULES:
- If the user has not specified project details, assume they want a "Hello World" project as a starting point.
- Avoid adding links of any type (URLs, files, folders, etc.) or integrations that are not explicitly required.
- Avoid generating images, videos, or any other media files unless explicitly requested.
- If you need to use any media assets as placeholders, let the user know that these are placeholders and should be replaced with the actual assets later.
- Ensure all generated components serve a clear purpose within the user's requested workflow.
- If a feature is assumed but not confirmed, prompt the user for clarification before including it.
- If you are working on a VS Code extension, use the VS Code API tool with a query to find relevant VS Code API references and samples related to that query.

TASK COMPLETION RULES:
- Your task is complete when:
  - Project is successfully scaffolded and compiled without errors
  - copilot-instructions.md file in the .github directory exists in the project
  - README.md file exists and is up to date
  - User is provided with clear instructions to debug/launch the project

Before starting a new task in the above plan, update progress in the plan.
