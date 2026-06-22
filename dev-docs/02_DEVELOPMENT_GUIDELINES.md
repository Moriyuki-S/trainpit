# Development Guidelines

This document is for internal development. It records the engineering rules and
decision criteria for implementing the `train` display.

## Principles

- Start with a small API.
- Keep training loop integration lightweight.
- Separate public API from internal implementation details.
- Treat TTY and non-TTY output as distinct rendering modes.
- Prioritize state updates over rendering; rendering may be delayed or skipped.
- Update README and public docs only after the implementation and API stabilize.

## Tooling

- Python 3.11 or later
- uv
- pytest
- ruff
- zensical

Do not add a runtime dependency until the implementation clearly needs one.

## Coding Guidelines

- Represent display state explicitly, likely with dataclasses.
- Write explicit type annotations for function parameters, return values, class
  attributes, and public API boundaries.
- Prefer precise standard collection types such as `Mapping[str, float]` or
  `Sequence[str]` over untyped `dict` and `list`.
- Avoid `Any` unless the value is intentionally unconstrained and the reason is
  clear from the surrounding code.
- Make time access injectable so tests can be deterministic.
- Keep renderers focused on converting state into output.
- Keep terminal detection behind output stream `isatty()`.
- Do not leak private module details through the public API.

## Error Handling

- Do not swallow exceptions raised by the user's training loop.
- On exception, render the last known state when possible, then re-raise.
- Decide during implementation whether renderer failures should interrupt the
  training loop.

## Display Guidelines

- Do not imitate `tqdm` as a progress-bar-first UI.
- Prefer a compact btop-style terminal dashboard direction for TTY output.
- TTY output should update the same terminal area.
- Non-TTY output should use readable plain text lines.
- Non-TTY output should use trainpit-specific structured log lines.
- Do not show percent or ETA when totals are unknown.
- Omit optional values that were not provided.
- Keep the layout stable as values change.

## Testing Guidelines

- Test state updates with focused unit tests.
- Test renderers with deterministic text output.
- Test TTY and non-TTY branching.
- Test rate limiting with a fake clock.
- Test normal completion and exception lifecycle behavior.

## Codex Edit Checks

After editing files, Codex must run the test suite, linter, and formatter check
before reporting the work as complete:

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

If one of these commands cannot be run, Codex must report the reason and the
remaining risk. Run the documentation build when documentation behavior changes:

```sh
uv run zensical build
```
