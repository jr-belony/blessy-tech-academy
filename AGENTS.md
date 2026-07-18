# AGENTS.md

## Workspace overview
- This workspace contains multiple app-oriented projects and learning folders under the top level.
- Treat each top-level folder as a separate project. Before changing code, identify the specific app or project that the request targets.

## Working conventions
- Inspect the target folder's local documentation and project files before editing. Look for README files, dependency manifests, and entrypoint files such as package.json, pyproject.toml, requirements.txt, manage.py, or similar.
- Follow the existing structure and naming conventions of the selected project instead of introducing new patterns.
- Keep changes focused and scoped to the relevant app. Avoid broad refactors unless the task explicitly requires them.
- Preserve existing configuration and coding style unless the request asks for a migration or modernization.
- When behavior changes, update the most relevant documentation or comments in the same project.

## App-focused workflow
- For app or web work, locate the entrypoint and the closest feature area first (views, routes, controllers, templates, services, tests).
- If tests exist, run the relevant ones before and after making changes.
- If no tests exist, validate with the project's documented commands and keep the change small and verifiable.

## Safety rules
- Do not create new files unless explicitly requested.
- Prefer modifying existing files.
- Always explain changes before applying them.