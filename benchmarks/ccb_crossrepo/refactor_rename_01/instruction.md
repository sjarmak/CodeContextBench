Standardize HTTP Request class naming across Django, Flask, and requests libraries

The Python web ecosystem has inconsistent naming for HTTP request classes:
- Django uses HttpRequest (mixed case)
- Flask uses Request (generic)
- requests library uses Request and PreparedRequest

Rename the primary request class in each library to HTTPRequest for consistency:
1. In django/django/http/request.py: rename HttpRequest to HTTPRequest and update all references
2. In flask/src/flask/wrappers.py: rename Request to HTTPRequest and update all references
3. In requests/src/requests/models.py: rename Request to HTTPRequest and update all references

Apply changes across all three codebases under /ccb_crossrepo/src/. Update imports, type annotations, and docstrings that reference the old names.
