# LANGUAGE RULES: 
- Ensure all comments and logs are in English.

# DOCUMENTATION RULES: 
- Do not add docstrings to functions/methods if the name is self-explanatory. - Only add docstrings if they explain "why" something is done or complex behavior that isn't obvious from the signature.
- Always add docstrings for tool functions so ADK can use them for tool descriptions, even if the name is self-explanatory.
- Do not use comments inside functions/methods. Instead, ensure function and variable names are self-explanatory. STRICTLY FORBIDDEN to generate comments explaining code logic.

# ERROR HANDLING: 
- Never catch generic Exceptions just for logging purposes. Let them bubble up to the global exception handler.

# IMPORT RULES: 
- Never use relative imports (e.g., `from .module import func`). Always use absolute imports (e.g., `from package.module import func`).
DESIGN RULES:
- Inject external dependencies into functions for testability (e.g., translators, HTTP clients).
- Never use single-letter or abbreviated variable names (e.g., `c`, `e`, `f`). Always use descriptive names, including in list comprehensions and lambda expressions.

# DOMAIN RULES: 
- Keep domain entities in `bonsai_sensei/domain`, not in `bonsai_sensei/database`.

# TESTING RULES:
- Use a single assert per test.
- Always include a descriptive message in asserts.
- Prefer pytest fixtures for test data setup.
- Name tests with a should_ prefix.
- Place fixtures below tests in test files.
- Always include failure messages in assert statements.
- Only test public method, private methods are implementation details. 

