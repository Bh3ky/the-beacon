# Backend Guidelines

## Framework Callback Typing

When implementing FastAPI or Starlette callback hooks, type the function to the framework callback contract first, not to the narrowest runtime subtype you expect.

Apply this rule to:

- exception handlers
- middleware callables
- lifespan hooks
- other framework-registered callbacks

### Why

Framework registration APIs usually accept broad callback types such as:

- `Request | WebSocket`
- `Exception`

If our handler is annotated too narrowly, static type checkers will report valid runtime code as incompatible with the framework API.

Typical example:

- framework expects `ExceptionHandler`
- our function is annotated as `(_: Request, exc: ApiError) -> JSONResponse`

Runtime may be fine, but the type checker will complain because:

- `ApiError` is narrower than `Exception`
- `Request` is narrower than `Request | WebSocket`

### Rule

Prefer callback signatures that are compatible with the framework API:

```python
async def handler(request: Request, exc: Exception) -> JSONResponse:
    ...
```

Then narrow internally with:

- `isinstance(...)`
- shared helper functions
- controlled `cast(...)` only when necessary

### Default Preference

1. Align the callback signature with the framework type.
2. Narrow inside the function body if needed.
3. Use `cast(...)` at registration only as a fallback, not as the default pattern.

### Project-Specific Note

For API exception handlers in this repo:

- avoid leaving persistent type-check noise around `app.add_exception_handler(...)`
- prefer broad handler signatures plus small internal formatting helpers over narrowly typed framework callbacks
