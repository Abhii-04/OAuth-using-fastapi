# FastAPI: a practical course companion

Written for this project on 20 October 2026. Local versions checked: Python 3.12, FastAPI 0.151.0, Pydantic 2.14.1, Starlette 1.9.0.

The goal: understand enough to build, debug, and maintain your own application. Work through the early chapters in order; use the later chapters as references. You do not need to memorize every decorator option.

Examples use modern Pydantic v2 methods. Older courses may use `.dict()` instead of `.model_dump()` or `orm_mode` instead of `from_attributes`.

## Contents

1. [The request journey](#1-the-request-journey)
2. [Setup and your first route](#2-setup-and-your-first-route)
3. [Python syntax you need](#3-python-syntax-you-need)
4. [Where request data comes from](#4-where-request-data-comes-from)
5. [Validation and business logic](#5-validation-and-business-logic)
6. [Responses and errors](#6-responses-and-errors)
7. [A complete CRUD practice app](#7-a-complete-crud-practice-app)
8. [HTML, forms, and static files](#8-html-forms-and-static-files)
9. [Dependencies without the jargon](#9-dependencies-without-the-jargon)
10. [Choosing def or async def](#10-choosing-def-or-async-def)
11. [Databases and transactions](#11-databases-and-transactions)
12. [Authentication and authorization](#12-authentication-and-authorization)
13. [Testing and debugging](#13-testing-and-debugging)
14. [Organizing a growing app](#14-organizing-a-growing-app)
15. [Common supporting features](#15-common-supporting-features)
16. [Deployment basics](#16-deployment-basics)
17. [Practice path and mastery checks](#17-practice-path-and-mastery-checks)
18. [Quick reference](#18-quick-reference)

## 1. The request journey

A request contains a method, URL, headers, and sometimes a body. Your server sends back a status code, headers, and usually a body.

For example, `POST /tasks` might send JSON describing a task. The response might be HTTP 201 with JSON containing the saved task and its new ID.

Think through this sequence:

```text
Client sends request
  -> FastAPI matches method + path
  -> Inputs are extracted; validation and dependencies are resolved
  -> Your route function runs
  -> Your code checks business rules and performs work
  -> FastAPI builds the response
  -> Client receives it
```

That is a useful overview, not an exact ordering guarantee for every dependency and parameter. Dependencies can have their own inputs and validation.

Three parts work together:

| Part | Its job |
| --- | --- |
| Uvicorn | Runs the web server and passes requests to your application |
| FastAPI | Routes requests, resolves dependencies, and integrates validation/docs |
| Pydantic | Parses and validates structured data using your models |

Your code still decides what the application does. FastAPI will not decide whether an order can be cancelled or whether a user owns a task.

**Predict:** If a route expects an integer but receives `hello`, should its business logic run? Usually no: validation rejects the input first.

## 2. Setup and your first route

From this repository:

```bash
uv sync
```

For the existing HTML example:

```bash
uv run uvicorn html_example:app --reload
```

For course experiments, create a separate `practice.py`. Do not paste every independent example into the same file: repeated `app = FastAPI()` assignments replace the application object.

This is a complete first `practice.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello from FastAPI"}
```

Run it:

```bash
uv run uvicorn practice:app --reload
```

`practice:app` means “import the Python module `practice`, then use its variable `app`.” It does not mean a filename containing a colon.

Visit:

- `http://127.0.0.1:8000/`: your endpoint.
- `http://127.0.0.1:8000/docs`: interactive endpoint explorer.
- `http://127.0.0.1:8000/openapi.json`: machine-readable API description.

`@app.get("/")` registers the function for GET requests to `/`. The dictionary becomes JSON. `/docs` describes the API contract; it cannot explain your application's business rules for you.

`--reload` restarts the development server when code changes. Ctrl+C stops it. To run two examples simultaneously, give one `--port 8001`.

[Source: first steps](https://fastapi.tiangolo.com/tutorial/first-steps/).

## 3. Python syntax you need

Understand these before adding authentication or a database:

```python
name: str                    # a string annotation
age: int                     # an integer annotation
completed: bool = False      # boolean with a default
nickname: str | None = None   # string or None; default makes it optional here
names: list[str]              # list of strings
```

In ordinary Python, annotations do not automatically enforce types. FastAPI and Pydantic read them to validate request data.

`None` and “not provided” are different ideas. For a Pydantic model:

```python
from pydantic import BaseModel

class Profile(BaseModel):
    nickname: str | None          # required field; null is allowed
    bio: str | None = None        # may be omitted; defaults to None
```

`Annotated` adds framework information to a type:

```python
from typing import Annotated
from fastapi import Query

# Used as a route parameter:
# limit: Annotated[int, Query(ge=1, le=100)] = 20
```

Read this as “an integer query parameter, between 1 and 100, defaulting to 20.” `ge` means greater than or equal; `le` means less than or equal.

You need functions, dictionaries, classes, imports, exceptions, and context managers (`with`). You can learn async after your first CRUD app works.

## 4. Where request data comes from

This is the most useful table to remember:

| Input | Example | Declaration |
| --- | --- | --- |
| Path | `/tasks/7` | `/tasks/{task_id}` plus `task_id: int` |
| Query | `/tasks?limit=10` | `limit: int = 10` |
| JSON body | `{"title": "Study"}` | Parameter typed as a Pydantic model |
| HTML form | `title=Study` | `Annotated[str, Form()]` |
| Header | `X-Request-ID: abc` | `Annotated[str, Header()]` |
| Cookie | `session_id=abc` | `Annotated[str, Cookie()]` |
| File | multipart upload | `UploadFile` with `File()` |
| Request metadata | client, method, URL | `request: Request` |

A basic scalar parameter that is not in the path usually becomes a query parameter. Use explicit `Body()`, `Header()`, or `Form()` when you need a different source.

### Path and query together

Standalone example:

```python
from typing import Annotated
from fastapi import FastAPI, Path, Query

app = FastAPI()

@app.get("/tasks/{task_id}")
def read_task(
    task_id: Annotated[int, Path(gt=0)],
    include_details: bool = False,
    q: Annotated[str | None, Query(max_length=50)] = None,
):
    return {"id": task_id, "details": include_details, "query": q}
```

Try `/tasks/7?include_details=true&q=study`. Try `/tasks/abc` and `/tasks/0` and inspect the 422 response.

Declare fixed routes like `/tasks/search` before `/tasks/{task_id}`. Routes are matched in order; `search` could otherwise be treated as the ID and fail validation.

### JSON body

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    completed: bool = False

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    return task
```

Send:

```bash
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Learn request bodies"}'
```

Expected: HTTP 201 and a task whose `completed` value is false.

With this single model argument, send the object directly. You do not send `{"task": {...}}` unless you deliberately choose an embedded body shape.

### Headers and cookies

Inside an app that imports `Annotated`:

```python
from fastapi import Header, Cookie

@app.get("/request-info")
def request_info(
    x_request_id: Annotated[str | None, Header()] = None,
    theme: Annotated[str | None, Cookie()] = None,
):
    return {"request_id": x_request_id, "theme": theme}
```

`Header()` maps `x_request_id` to `x-request-id` by default. Header names are case insensitive. A cookie value is client input; receiving it does not prove identity.

[Sources: path parameters](https://fastapi.tiangolo.com/tutorial/path-params/), [query parameters](https://fastapi.tiangolo.com/tutorial/query-params/), [request bodies](https://fastapi.tiangolo.com/tutorial/body/), [headers](https://fastapi.tiangolo.com/tutorial/header-params/).

## 5. Validation and business logic

Separate two questions:

| Question | Where it belongs |
| --- | --- |
| Is `quantity` a positive integer? | Input model / parameter validation |
| Is enough stock available? | Business logic, usually checked against the database |
| Does the requested task exist? | Route/helper/database lookup |
| Does this user own that task? | Authorization logic |

A model cannot know current stock just from an incoming number.

For a small route, ordinary conditions are enough:

```python
from fastapi import HTTPException

# Fragment inside an order route:
# if quantity > available_stock:
#     raise HTTPException(status_code=409, detail="Not enough stock")
```

When rules grow, move them into a regular helper function and call it from the route. Use dependencies for request-related shared requirements; use plain functions for ordinary calculations.

Remember these validation details:

- Parsing may convert compatible inputs. `int` does not necessarily mean “reject every numeric string.” Use strict validation when that distinction matters.
- A one-character minimum accepts a space unless you strip or validate whitespace.
- Pydantic ignores extra fields by default. Use `model_config = ConfigDict(extra="forbid")` if unknown fields should cause an error.
- Client-side checks help users; server-side checks protect the data even when someone bypasses the form.

**Exercise:** Require a nonblank title, maximum 100 characters, then add a separate rule that completed tasks cannot be renamed. Explain which rule depends on stored state.

[Sources: fields](https://docs.pydantic.dev/latest/concepts/fields/), [strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/), [model configuration](https://docs.pydantic.dev/latest/api/config/).

## 6. Responses and errors

### Return the right status

| Status | Use |
| --- | --- |
| 200 | Successful read/update with a response body |
| 201 | Created a resource |
| 204 | Success with no response body |
| 400 | Request rejected by an application check |
| 401 | Missing or invalid authentication |
| 403 | Identity known but action forbidden |
| 404 | Resource not found |
| 409 | Conflict with existing state |
| 422 | Request validation failed |
| 500 | Unexpected server failure |

For bearer authentication, a 401 response should include `WWW-Authenticate: Bearer`.

Raise an error to stop execution:

```python
raise HTTPException(status_code=404, detail="Task not found")
```

Do not `return HTTPException(...)`. Returning `{"error": "missing"}` without changing the status still reports success by default.

FastAPI's default error responses are JSON, including on HTML endpoints. For friendly HTML validation errors, handle the input and render an error template, as `html_example.py` does. A custom exception handler is useful when many routes need the same behavior.

### Control outgoing fields

Add a response model when your public output needs a clear contract:

```python
from pydantic import BaseModel

class UserPublic(BaseModel):
    id: int
    username: str

@app.get("/profile", response_model=UserPublic)
def profile():
    return {"id": 1, "username": "abhi", "password_hash": "internal-value"}
```

The declared output contains `id` and `username`. Keep separate input, database, and public models when their fields differ. Response validation failures indicate a server-side bug, not bad client input.

Returning a `Response` object directly bypasses normal response-model validation/filtering. Be deliberate when using that escape hatch.

[Sources: errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [response models](https://fastapi.tiangolo.com/tutorial/response-model/), [status codes](https://fastapi.tiangolo.com/tutorial/response-status-code/).

## 7. A complete CRUD practice app

**Copy the entire block into a new `practice.py`.** This is an independent application. It does not depend on earlier snippets.

It creates, lists, reads, updates, and deletes tasks. It uses memory so you can understand HTTP behavior before database setup. Restarting loses everything; multiple workers would have separate stores. Keep it to one worker and local practice.

```python
from itertools import count
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI(title="Task practice")

class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=100)

class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=100)
    completed: bool | None = None

    @field_validator("title", "completed")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("Omit the field instead of sending null")
        return value

class TaskPublic(BaseModel):
    id: int
    title: str
    completed: bool

# Demo storage only.
tasks: dict[int, TaskPublic] = {}
next_id = count(1)

def find_task(task_id: int) -> TaskPublic:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", response_model=TaskPublic, status_code=201)
def create_task(payload: TaskCreate):
    task = TaskPublic(id=next(next_id), title=payload.title, completed=False)
    tasks[task.id] = task
    return task

@app.get("/tasks", response_model=list[TaskPublic])
def list_tasks(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return list(tasks.values())[offset:offset + limit]

@app.get("/tasks/{task_id}", response_model=TaskPublic)
def read_task(task_id: int):
    return find_task(task_id)

@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(task_id: int, payload: TaskUpdate):
    task = find_task(task_id)
    changes = payload.model_dump(exclude_unset=True)
    updated = TaskPublic.model_validate({**task.model_dump(), **changes})
    tasks[task_id] = updated
    return updated

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    find_task(task_id)
    del tasks[task_id]
    return Response(status_code=204)
```

The update validator runs for supplied fields. Omitted defaults are not validated here. That allows `{}` but rejects `{"title": null}`. This is a deliberate API policy because stored titles and completion flags cannot be null.

`model_dump(exclude_unset=True)` returns only fields the client actually supplied. If you update only `completed`, the title stays the same. `model_validate()` constructs and validates the updated object.

PATCH means partial update here. PUT conventionally replaces a representation; design and document your own update contract explicitly.

Run:

```bash
uv run uvicorn practice:app --reload
```

Try in order:

```bash
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' -d '{"title":"Study FastAPI"}'
curl http://127.0.0.1:8000/tasks
curl -i -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H 'Content-Type: application/json' -d '{"completed":true}'
curl -i -X DELETE http://127.0.0.1:8000/tasks/1
curl -i http://127.0.0.1:8000/tasks/1
```

After a fresh start, expect 201, 200, 200, 204, then 404. Try a blank title, unknown field, `limit=0`, and explicit null. Predict each result first.

[Sources: partial updates](https://fastapi.tiangolo.com/tutorial/body-updates/), [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/).

## 8. HTML, forms, and static files

Use the existing [HTML example](../html_example.py) and [template](../templates/example.html) for a runnable version.

Flask's `render_template()` corresponds to creating a `Jinja2Templates` object and returning its `TemplateResponse`:

```python
from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="example.html",
        context={"name": "Abhishek", "message": None, "error": None},
    )
```

The dictionary keys become template variables: `{{ name }}` displays the value. `{% if error %}` conditionally displays markup. Keep database operations and business rules in Python.

HTML form fields use `Form()`, not a JSON body model:

```python
from typing import Annotated
from fastapi import Form

@app.post("/greet")
def greet(name: Annotated[str, Form()]):
    return {"message": f"Hello, {name}"}
```

The browser form needs `method="post"`, a matching `action`, and an input with `name="name"`. The `name` attribute determines the submitted key; the `id` connects a label to its input.

A browser form generally sends URL-encoded data; file forms send multipart data. Do not expect an ordinary JSON body and form fields to coexist as separate encodings in the same body. These features need `python-multipart`, already installed here.

For CSS/images, first create a `static/` directory, then mount it:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

Use `<link rel="stylesheet" href="{{ url_for('static', path='/style.css') }}">` in HTML. The relative directory above assumes you start from the project root.

After a successful form submission that saves data, a 303 redirect to a GET page avoids repeating the POST when the user refreshes:

```python
from fastapi.responses import RedirectResponse

# After saving, inside a route:
# return RedirectResponse(url="/tasks", status_code=303)
```

Jinja escapes HTML values by default for HTML templates. Avoid `|safe` on untrusted input. Cookie-authenticated forms that change data also need a CSRF protection strategy.

[Sources: templates](https://fastapi.tiangolo.com/advanced/templates/), [forms](https://fastapi.tiangolo.com/tutorial/request-forms/), [static files](https://fastapi.tiangolo.com/tutorial/static-files/).

## 9. Dependencies without the jargon

A dependency is a function FastAPI calls to provide something your route needs. Common examples: validated pagination, a database session, or the current user.

This is an independent example:

```python
from typing import Annotated
from fastapi import Depends, FastAPI, Query

app = FastAPI()

def pagination(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return {"offset": offset, "limit": limit}

@app.get("/tasks")
def list_tasks(page: Annotated[dict, Depends(pagination)]):
    return page
```

Request `/tasks?offset=10&limit=5`. FastAPI validates the dependency's inputs, calls it, and gives its return value to `page`.

Write `Depends(pagination)`, passing the function itself. `Depends(pagination())` calls it immediately while importing the module, which is generally wrong.

A dependency can raise `HTTPException` to stop a request. Dependencies can also depend on other dependencies. FastAPI normally reuses a dependency result within one request; that does not make it a global cache.

Use `yield` when a resource needs cleanup. The database chapter shows this. If you call a route function directly yourself, FastAPI does not resolve its `Depends()` arguments for you.

[Source: dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/).

## 10. Choosing def or async def

Choose based on the operations inside the route:

| Work | Starting choice |
| --- | --- |
| Normal synchronous database driver | `def` |
| Async database driver with awaited operations | `async def` |
| Async HTTP client | `async def` and `await` |
| Heavy CPU calculation | Separate process/worker when substantial |

FastAPI runs ordinary `def` routes in a thread pool. An `async def` route runs on the event loop and must avoid blocking it.

This is a bad combination:

```python
import time

@app.get("/slow")
async def slow():
    time.sleep(5)  # Blocks the event loop.
    return {"done": True}
```

For a simulated async wait, use `await asyncio.sleep(5)`. For real I/O, use the async API of the library. Changing `def` to `async def` does not make a synchronous library asynchronous.

A regular helper called directly inside an async route is not automatically moved to a thread pool. Async helps overlap waiting; it does not make a CPU-heavy calculation faster.

[Source: concurrency](https://fastapi.tiangolo.com/async/).

## 11. Databases and transactions

Learn the vocabulary first:

| Term | Meaning |
| --- | --- |
| Engine / pool | Shared machinery for reaching the database |
| Session | Unit of database work; tracks operations/objects |
| Model/table | Defines stored data |
| Transaction | Changes that succeed together or roll back together |
| Migration | Versioned change to database structure |

A practical next exercise is replacing the in-memory store with SQLite using SQLModel. Install only when you reach this chapter:

```bash
uv add sqlmodel
```

Standalone file `database_practice.py`:

```python
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine

class Task(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    title: str

class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=1, max_length=100)

class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str

engine = create_engine(
    "sqlite:///./tasks.db",
    connect_args={"check_same_thread": False},
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)  # Local learning setup only.
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.post("/tasks", response_model=TaskPublic, status_code=201)
def create_task(payload: TaskCreate, session: SessionDep):
    task = Task(title=payload.title)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks/{task_id}", response_model=TaskPublic)
def read_task(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

Run `uv run uvicorn database_practice:app --reload`. Creating a task now writes `tasks.db` in the current working directory. Restart and read it again.

`add()` stages the object, `commit()` makes the transaction durable, and `refresh()` reloads database-generated values. `from_attributes=True` lets the output model read attributes from the stored object.

Use a session per request; never share one global Session among requests. SQLite's connection argument above supports its use across threads; it does not make shared sessions safe.

For multi-step operations, commit only after all related changes succeed. Roll back a failed transaction before reusing its session. Database constraints must enforce rules such as unique usernames; checking first in Python alone has race conditions.

`create_all()` creates missing tables; it does not migrate existing columns. Learn Alembic before deploying schema changes. Use parameterized queries or ORM expressions instead of concatenating user input into SQL.

[Sources: database integration](https://fastapi.tiangolo.com/tutorial/sql-databases/), [SQLModel sessions](https://sqlmodel.tiangolo.com/tutorial/session/).

## 12. Authentication and authorization

These are different checks:

- **Authentication:** Who is making the request?
- **Authorization:** May this identity perform this action on this resource?

A valid login does not grant access to everyone else's tasks.

### Understand the bearer helper first

Your current `main.py` uses `OAuth2AuthorizationCodeBearer(token_url=...)`. That call does not match the helper's required arguments: authorization-code flows require both `authorizationUrl` and `tokenUrl`. The camel-case keyword names matter.

For understanding a password-token tutorial, the extraction helper looks like this:

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/token-demo")
def token_demo(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"received_bearer_header": bool(token)}
```

This standalone demo extracts the credential from `Authorization: Bearer ...`. It does **not** establish that the token is genuine. `tokenUrl="token"` describes where tokens are obtained; it does not create a `/token` endpoint. This demo deliberately is not a real authentication system.

### What a real flow must do

For a username/password exercise:

1. Receive credentials over HTTPS.
2. Find the account and verify its stored password hash using a maintained password-hashing library.
3. Reject invalid credentials without exposing which accounts exist.
4. Issue a short-lived token or establish a server-side session.
5. For each protected request, verify the credential and load the user.
6. Check ownership/permissions before reading or changing data.

For signed JWTs, validate the signature with an explicitly allowed algorithm and check expiry and expected claims, including issuer/audience when the design uses them. A JWT payload is readable; a signed JWT is not an encrypted place to store secrets.

Use a shared current-user dependency for verification; routes depend on the resulting user. For a task lookup, query by both task ID and current user ID, or explicitly check ownership before returning it.

For browser applications, HTTP-only secure cookies can be appropriate, with CSRF protection for state changes. For external identity providers, learn their authorization-code flow, including PKCE where applicable. The password-flow tutorial is an exercise, not a universal login architecture.

Do not build a production login system by combining the extraction demo with a hardcoded secret. Password reset, brute-force protection, session/token expiry, and logout/revocation behavior need deliberate implementation.

[Sources: bearer extraction](https://fastapi.tiangolo.com/tutorial/security/first-steps/), [password hashing and JWT verification](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [security class signatures](https://fastapi.tiangolo.com/reference/security/).

## 13. Testing and debugging

Use `/docs` and curl while learning, then add automated tests so changes cannot silently break earlier behavior.

Install test tools when you reach this chapter:

```bash
uv add --dev pytest httpx
```

For the installed versions, `TestClient` with httpx works but emits a Starlette deprecation warning recommending `httpx2`. If your future version removes that compatibility, follow that installed Starlette version's test-client instructions.

With the complete chapter 7 app saved as `practice.py`, create `test_practice.py`:

```python
from fastapi.testclient import TestClient
from practice import app

def test_task_lifecycle():
    with TestClient(app) as client:
        created = client.post("/tasks", json={"title": "Study"})
        assert created.status_code == 201
        task_id = created.json()["id"]

        updated = client.patch(f"/tasks/{task_id}", json={"completed": True})
        assert updated.status_code == 200
        assert updated.json()["title"] == "Study"
        assert updated.json()["completed"] is True

        assert client.delete(f"/tasks/{task_id}").status_code == 204
        assert client.get(f"/tasks/{task_id}").status_code == 404

def test_blank_title_is_rejected():
    with TestClient(app) as client:
        response = client.post("/tasks", json={"title": "   "})
        assert response.status_code == 422
```

Run `uv run pytest -q`.

`json=` sends JSON; `data=` sends form data. Tests should cover normal input, boundaries, invalid input, missing resources, and ownership failures once authentication exists.

For real database tests, use an isolated test database and override `get_session` with `app.dependency_overrides[get_session] = test_session_dependency`. Clear overrides after the test. Never aim destructive tests at production.

### Read a 422 response

Its `detail` list identifies validation failures. `loc` tells you where to look: `body`, `query`, or `path`, followed by the relevant field. Read `msg` and `type`; do not guess from the status alone.

### Debug by locating the boundary

| Symptom | Check first |
| --- | --- |
| 404 | Exact URL and router prefix |
| 405 | HTTP method matches decorator |
| 422 | Field location, names, types, and Content-Type |
| 500 | Server traceback; last relevant application frame |
| HTML shown as quoted text/JSON | Return HTMLResponse or TemplateResponse |
| POST form not reaching route | Form action, method, input name, Form declaration |
| Data vanishes on restart | In-memory store versus actual database |
| Import error starting server | Working directory and module path |
| Works in curl, blocked in browser | Browser console, CORS, cookies, mixed content |

Log useful context such as route, request ID, and error category. Avoid logging passwords, tokens, or sensitive request bodies.

[Sources: testing](https://fastapi.tiangolo.com/tutorial/testing/), [dependency overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/).

## 14. Organizing a growing app

Stay in one file while understanding the basics. Split when different responsibilities become hard to navigate:

```text
app/
  __init__.py
  main.py          # Build app and include routers
  schemas.py       # Request/response models
  models.py        # Database models
  database.py      # Engine and session dependency
  dependencies.py  # Current user and other shared request needs
  routers/
    __init__.py
    tasks.py       # Task endpoints
  services/
    __init__.py
    tasks.py       # Business operations when substantial
```

In `app/routers/tasks.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("")
def list_tasks():
    return []
```

In `app/main.py`:

```python
from fastapi import FastAPI
from app.routers.tasks import router as tasks_router

app = FastAPI()
app.include_router(tasks_router)
```

Run `uv run uvicorn app.main:app --reload`. The final URL is `/tasks`. Router prefixes and decorator paths combine.

Route code should translate HTTP input/output and call business operations. Do not create a service or repository class just to wrap a single straightforward line.

[Source: multiple files and routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

## 15. Common supporting features

### CORS: when the browser frontend has another origin

A frontend at `http://localhost:5173` calling an API at `http://localhost:8000` crosses origins. Scheme, host, and port determine the origin.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Use actual frontend origins. A wildcard is unsuitable for credentialed access. CORS is a browser policy, not authentication; it does not prevent curl or another server from sending requests. A same-origin template app usually needs no CORS setup.

[Source: CORS](https://fastapi.tiangolo.com/tutorial/cors/).

### Uploads

```python
from typing import Annotated
from fastapi import File, UploadFile

@app.post("/uploads")
async def upload(file: Annotated[UploadFile, File()]):
    chunk = await file.read(1024)
    await file.close()
    return {"first_chunk_bytes": len(chunk)}
```

This only demonstrates reading one chunk; it does not save or fully validate an upload. Real upload handling needs total-size limits, allowed formats verified from content where appropriate, generated storage names, and safe storage paths. Client filenames and declared content types are untrusted.

[Source: files](https://fastapi.tiangolo.com/tutorial/request-files/).

### Background tasks

`BackgroundTasks.add_task(function, argument)` schedules work after the response. Use it for small, best-effort work where losing it on a process crash is acceptable. It is not a durable job queue. For reliable deliveries, retries, or heavy jobs, use a worker/queue design.

Do not pass a request's database session to a background job. Give the job identifiers and let it open its own resources.

[Source: background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/).

### Startup and shutdown

Use the application's lifespan context manager for resources created at startup and released at shutdown. The database example uses this pattern. When a lifespan handler is supplied, do not expect legacy startup/shutdown event handlers to run alongside it.

[Source: lifespan](https://fastapi.tiangolo.com/advanced/events/).

### Settings and secrets

Start with environment variables. For validated configuration, install `pydantic-settings`:

```bash
uv add pydantic-settings
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    debug: bool = False

settings = Settings()
```

`DATABASE_URL` must be configured because it has no default. Construct settings once for the application, not on every request. Keep `.env` out of version control; commit an `.env.example` with placeholder values when needed.

[Source: settings](https://fastapi.tiangolo.com/advanced/settings/).

## 16. Deployment basics

A starting server command, after creating `practice.py`, is:

```bash
uv run uvicorn practice:app --host 0.0.0.0 --port 8000
```

`0.0.0.0` listens on available interfaces. It is a bind address, not the browser URL you share. The command alone is not a complete deployment.

Before exposing an application to real users:

- Put HTTPS at the hosting platform or trusted reverse proxy.
- Configure secrets and database access for the environment.
- Run migrations as a deliberate deployment step.
- Use persistent storage; avoid process memory for shared application data.
- Configure process restart behavior, useful logs, and health checks.
- Test authentication and resource ownership checks.
- Back up valuable database data and know how to restore it.

Remove `--reload`. Worker processes have separate memory; increasing workers does not turn your dictionary into shared storage. Choose worker counts according to your host's resources and deployment model.

Learn Docker, proxy configuration, and monitoring when you have an app worth deploying. They are not prerequisites for understanding routes.

[Sources: running a server](https://fastapi.tiangolo.com/deployment/manually/), [deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/).

## 17. Practice path and mastery checks

Use completion criteria rather than a rigid number of days.

| Stage | Build | Move on when you can… |
| --- | --- | --- |
| 1 | Greeting API with path/query input | Predict where every parameter comes from |
| 2 | Chapter 7 task API | Explain 201, 204, 404, and 422 using your own requests |
| 3 | HTML task form | Trace form -> route -> rule -> template |
| 4 | SQLite task storage | Restart the app without losing tasks |
| 5 | User-owned tasks | Prevent user A from reading/changing user B's tasks |
| 6 | Tests and deployment | Reproduce failures and run the app outside reload mode |

For each feature:

1. State the expected behavior in one sentence.
2. Predict one successful and one failing request.
3. Implement the smallest version.
4. Send both requests and inspect status plus body.
5. Explain why each result happened.
6. Add an automated check when a regression would matter.

Try answering without looking up syntax:

- Why is `name: str` usually query input, while `task: TaskCreate` is body input?
- Why can a perfectly valid JSON body still lead to 404 or 409?
- What does `Depends(get_user)` do that calling `get_user()` at import time does not?
- Why is extracting a bearer token insufficient to authenticate a user?
- Why does PATCH need to distinguish omitted values from explicit null?
- Why can an async route still block other requests?
- What happens to dictionary storage after a restart or with two workers?
- Which constraints must live in the database even if Python checks them too?

Delay WebSockets, custom OpenAPI generation, complex middleware, metaprogramming, and advanced dependency scopes until a real requirement appears. First become reliable at inputs, rules, persistence, permissions, and tests.

## 18. Quick reference

| I want to… | Reach for… |
| --- | --- |
| Read an ID from the URL | Path parameter |
| Filter or paginate a list | Query parameters with bounds |
| Accept JSON | Pydantic request model |
| Accept HTML form fields | `Form()` |
| Reject a missing resource | `raise HTTPException(404, ...)` |
| Return only public fields | Response model |
| Render HTML | `Jinja2Templates` + `TemplateResponse` |
| Reuse current-user/session logic | `Depends()` |
| Save data reliably | Database + transaction |
| Partially update data | PATCH + `exclude_unset=True` |
| Call an async library | `async def` + `await` |
| Split endpoint groups | `APIRouter` |
| Reproduce behavior automatically | `TestClient` + pytest |
| Understand an unexpected result | Exact request, response, and traceback |

### Flask translation sheet

| Flask habit | FastAPI equivalent |
| --- | --- |
| `@app.route(..., methods=["POST"])` | `@app.post(...)` |
| `request.args.get(...)` | Typed query parameter |
| `request.get_json()` | Pydantic body model |
| `request.form[...]` | `Form()` parameter |
| `render_template(...)` | `TemplateResponse(...)` |
| `abort(404)` | `raise HTTPException(status_code=404, ...)` |
| Blueprint | `APIRouter` |
| Shared request setup | Often a dependency; sometimes middleware |

You can build good applications with either framework. Learn the request/response model and practice tracing your code; that skill transfers between them.
