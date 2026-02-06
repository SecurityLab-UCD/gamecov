# AGENTS.md - Project Context for Coding Agents

## Project Purpose

ToDo

## Repository Layout

ToDo

## Core Pipeline

ToDo

## Key Modules

ToDo

## Environment and Dependencies

- Python 3.11 managed with `uv` (see `pyproject.toml`).


### Library Usage

ToDo

## Testing

```bash
# Run tests in parallel using all available CPU cores
uv run pytest -n auto
```

## Development

- Before start working, refresh your knowledge from contents in `.agents` first.
- Always update README.md and AGENTS.md when you introduce new features or libraries.
- Always write unit tests for integration testing and functional testing of new features.
- Always test your code after your implementation.
- All functions must be fully typed with type hints with input parameters and return types.
  All global constants must also be typed.
  Local variables' types are optional as long as the types can be easily inferred.
- Use f-strings for string interpolation.
- Use `TypedDict`, `Literal`, `Protocol`, and `TypeVar` from `typing` module when appropriate.
- Always run `mypy`, and `ruff` to ensure code quality after updating code in `src/`.
- Never commit changes or create PRs. Suggest commit messages to the human developer for review after your changes to the codebase.
- Always use `typer` to handle CLI commands.

### Scratch Space to Show Your Work and Progress

- Use `.agents/sandbox/` for throwaway exploration that will not be committed.
- Use `.agents/notes/` for longer-term notes that may be useful later. Always write down your plans and reasoning for future reference when encountering major tasks, like adding a feature.
- Use `.agents/accomplished/` for recording completed tasks and the summary of what we did, this may be useful for future reference.
