# FastAPI HTML, explained through a working example

For the full learning path, read [FastAPI: a practical course companion](docs/FASTAPI_GUIDE.md).

Run from this directory:

```bash
uv sync
uv run uvicorn html_example:app --reload
```

Open http://127.0.0.1:8000/ in a browser. `html_example` means
`html_example.py`; `app` is the FastAPI object inside it.

Read `html_example.py` beside `templates/example.html`.

1. Visiting `/` calls `home()`, which renders the HTML template.
2. Submitting the form sends its fields to `POST /check`.
3. `Form()` puts those fields into Python arguments.
4. `check_age()` runs ordinary Python validation and `if/else` logic.
5. `TemplateResponse` renders the same template with the result.

## The Flask equivalents

| Flask | FastAPI |
| --- | --- |
| `@app.route("/", methods=["GET"])` | `@app.get("/")` |
| `request.args.get("name", "friend")` | Route argument `name: str = "friend"` |
| `request.form["age"]` | Route argument `age: Annotated[str, Form()]` |
| `render_template("example.html", name=name)` | `templates.TemplateResponse(request=request, name="example.html", context={"name": name})` |

`request: Request` gives the template access to request information, including
URL generation. FastAPI supplies this object; you don't pass it yourself.

`context` is just the dictionary of values available to Jinja.
`{"name": "Abhishek"}` makes `{{ name }}` display `Abhishek`.
Jinja's `{% if error %}` decides which HTML to display; the Python route
decides whether there is an error in the first place.

## Where does real logic go?

Inside the route, before returning a response. Start with normal Python
conditions; extract helper functions when the logic grows. Database lookups
and checks such as whether a username already exists fit there too.

You can use ordinary `def` routes. Use `async def` when you need to `await`
asynchronous operations, such as an async database call.

Returning a dictionary normally produces JSON. Returning a `TemplateResponse`
produces rendered HTML. `response_class=HTMLResponse` also documents that the
endpoint returns HTML.

## Check the branches

- Visit `/?name=Abhishek` to try a query parameter.
- Submit age `17` and then `18`: the result changes at that boundary.
- The browser checks required fields and numeric limits, but clients can bypass
  that. The Python route checks them again.
- To test server validation directly:

  ```bash
  curl -i -X POST http://127.0.0.1:8000/check -d 'name=Abhishek&age=abc'
  ```

  Expect HTTP 400 and an HTML page saying the age must be a whole number.

The example does not save submissions. It evaluates each request independently.

References: [Templates](https://fastapi.tiangolo.com/advanced/templates/) and
[Form data](https://fastapi.tiangolo.com/tutorial/request-forms/).
