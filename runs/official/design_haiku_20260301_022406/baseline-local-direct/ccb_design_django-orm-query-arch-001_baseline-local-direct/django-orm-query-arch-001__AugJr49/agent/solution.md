# Django ORM Query Compilation Pipeline: QuerySet → SQL

## Files Examined

### Core QuerySet & Manager Files
- **django/db/models/manager.py** — Provides the `Manager` class with `get_queryset()` method; entry point for query building via ORM API (e.g., `Model.objects.filter()`)
- **django/db/models/query.py** — Contains the `QuerySet` class; lazy query builder that defers execution until iteration; manages filter/exclude/values chains via `_filter_or_exclude()` → `_chain()` pattern

### Query & SQL Construction
- **django/db/models/sql/query.py** — The `Query` class; represents a compilable SQL query object; contains alias_map, where node, select/group_by/order_by clauses; bridges high-level QuerySet API to SQL generation
- **django/db/models/sql/where.py** — The `WhereNode` tree structure; hierarchical representation of WHERE/HAVING clauses using AND/OR/XOR connectors; each child is an expression (typically a `Lookup`)
- **django/db/models/sql/compiler.py** — The `SQLCompiler` class; translates `Query` object into executable SQL; contains the critical `compile()` method that dispatches to vendor-specific `as_{vendor}()` methods

### Expression & Lookup System
- **django/db/models/expressions.py** — Base `BaseExpression` and `Expression` classes; defines the expression protocol with `as_sql()`, `resolve_expression()`, and `get_source_expressions()` methods
- **django/db/models/lookups.py** — The `Lookup` class (extends `Expression`); represents individual comparisons (e.g., `field=value`, `field__gt=value`); implements `as_sql()` to generate SQL fragments with parameters

### Backend Operations & Dispatcher
- **django/db/backends/base/operations.py** — `BaseDatabaseOperations.compiler()` method; dynamically loads backend-specific compiler classes via `compiler_module` attribute
- **django/db/backends/postgresql/compiler.py, mysql/compiler.py, etc.** — Backend-specific compiler subclasses that override `as_sql()` for vendor-specific SQL generation

---

## Dependency Chain

### 1. Entry Point: Manager and QuerySet Lazy Construction
```
Model.objects.filter(name='John')
    → Manager.filter()
    → Manager.get_queryset()  [django/db/models/manager.py:150]
    → QuerySet(model=Model, query=sql.Query(model))  [django/db/models/query.py:280-284]
```

**Key Detail**: `QuerySet.__init__` creates a `sql.Query` object (from `django.db.models import sql`). The QuerySet is lazy—no database access yet.

### 2. Filter Building: Lazy Accumulation of Conditions
```
qs.filter(name='John', age__gt=18)
    → QuerySet.filter(args, kwargs)  [django/db/models/query.py:1475]
    → QuerySet._filter_or_exclude(False, args, kwargs)  [query.py:1491]
    → qs._chain()  [creates new QuerySet copy]
    → clone._filter_or_exclude_inplace(negate, args, kwargs)  [query.py:1502]
    → Query.add_q(Q(*args, **kwargs))  [query.py:1506]
```

**Key Detail**: Each filter() call creates a shallow copy of the QuerySet, preserving immutability.

### 3. Q Object Processing → WhereNode Tree Construction
```
Query.add_q(Q(name='John', age__gt=18))
    → Query._add_q(q_object, used_aliases, ...)  [query.py:1654]
    → For each child in Q.children:
        Query.build_filter(child, ...)  [query.py:1460]
            → Query.solve_lookup_type(arg)  [query.py:1316]
                → Splits "age__gt" into parts=["age"], lookups=["gt"]
            → Query.setup_joins(parts, ...)
                → Creates JOIN entries in Query.alias_map if needed
            → Query.build_lookup(lookups, lhs, rhs)  [query.py:1387]
                → lhs.get_lookup(lookup_name)
                → Returns Lookup class (e.g., GreaterThan)
                → Instantiates: lookup_instance = LookupClass(lhs, rhs)
            → Returns WhereNode([lookup_instance])
        → target_clause.add(WhereNode([lookup]), connector)
            → Builds tree of WhereNode(children=[lookup, lookup, ...], connector=AND)
    → Query.where.add(clause, AND)
        → Adds built WhereNode to Query.where (the root WhereNode for the query)
```

**Key Detail**: The Q object becomes a tree of `Lookup` objects inside nested `WhereNode` instances. Each `Lookup` is an `Expression` with `as_sql()` method.

### 4. Execution Trigger: Query Compilation
When the QuerySet is evaluated (iteration, count, get, etc.):
```
for obj in qs:  # or qs.count(), qs[0], etc.
    → QuerySet._fetch_all()  [implicitly triggered]
    → QuerySet._iterator()  [query.py:495]
    → iterable = self._iterable_class(self)  [ModelIterable by default]
    → ModelIterable.__iter__()  [query.py:85]
    → compiler = queryset.query.get_compiler(using=db)  [query.py:88]
```

### 5. Compiler Instantiation: Vendor Dispatch Registration
```
Query.get_compiler(using=db)  [query.py:358]
    → connection = connections[using]
    → return connection.ops.compiler(self.compiler)(self, connection, using, elide_empty)
        ↓
    query.compiler = "SQLCompiler"  [query.py:227]
    connection.ops.compiler("SQLCompiler")  [operations.py:385]
        → if cache is None: cache = import_module(self.compiler_module)
        → compiler_module = "django.db.backends.postgresql.compiler"  [backend-specific]
        → return getattr(cache, "SQLCompiler")  [the SQLCompiler class from that module]
        ↓
    SQLCompiler(query, connection, using, elide_empty)  [compiler.py:47]
```

**Key Detail**: Backend detection happens via `connection.vendor` (e.g., "postgresql", "mysql"). Each backend defines `compiler_module` pointing to its compiler implementations.

### 6. SQL Generation: Hierarchical as_sql() Dispatch
```
compiler.execute_sql(result_type=MULTI)  [compiler.py:1592]
    → sql, params = self.as_sql()  [compiler.py:1609]
    → SQLCompiler.as_sql(with_limits=True, with_col_aliases=False)  [compiler.py:754]
        → self.pre_sql_setup(with_col_aliases)
            → self.setup_query(with_col_aliases)
            → self.query.where.split_having_qualify(...)
        → For WHERE clause:
            where, w_params = self.compile(self.where)  [compiler.py:793]
                ↓
            SQLCompiler.compile(node)  [compiler.py:571]
                → vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
                → if vendor_impl: sql, params = vendor_impl(self, self.connection)
                → else: sql, params = node.as_sql(self, self.connection)
                ↓
            WhereNode.as_sql(compiler, connection)  [where.py:116]
                → For each child in self.children:
                    sql, params = compiler.compile(child)  [where.py:151]
                        ↓
                    Lookup.as_sql(compiler, connection)  [lookups.py:256]
                        → lhs_sql, params = self.process_lhs(compiler, connection)
                            → compiler.compile(self.lhs)
                            → Recursively compiles column reference (Col, F expression, etc.)
                        → rhs_sql, rhs_params = self.process_rhs(compiler, connection)
                            → Compiles right-hand side value or expression
                        → rhs_sql = self.get_rhs_op(connection, rhs_sql)
                            → connection.operators[self.lookup_name] % rhs_sql
                            → Maps lookup name (e.g., "gt") to database operator (e.g., ">")
                        → return "%s %s" % (lhs_sql, rhs_sql), params
                → result = ["WHERE", sql1, "AND", sql2, ...]  [as_sql joins children]
        → Build SELECT, FROM, GROUP BY, HAVING, ORDER BY, LIMIT clauses similarly
        → return " ".join(result), all_params
```

### 7. SQL Execution
```
cursor.execute(sql, params)  [compiler.py:1622]
    → Database driver executes SQL with parameter binding
    → Results fetched via cursor.fetchmany() or fetchone()
    → compiler.results_iter(results)
    → Return rows to QuerySet iterator
```

---

## Analysis

### Design Patterns Identified

#### 1. **Lazy Evaluation & Builder Pattern**
- `QuerySet` accumulates filter conditions without executing SQL
- Each `.filter()` returns a new `QuerySet` clone with updated `Query` object
- SQL only generated when the QuerySet is evaluated (iteration, count, get, etc.)
- This enables:
  - Query composition: `qs.filter(...).exclude(...).order_by(...)`
  - Deferred evaluation: conditions can be refined before execution
  - Potential for query optimization before compilation

#### 2. **Composite Visitor Pattern (Expression/Lookup System)**
- **Expression Protocol**: All compilable objects inherit from `BaseExpression` and implement:
  - `as_sql(compiler, connection) → (sql_string, params)`
  - `resolve_expression(query, ...) → resolved_expression`
  - `get_source_expressions() → [child_expr, ...]`
- **Visitor**: The `SQLCompiler` visits expressions and calls their `as_sql()` method
- **Recursive Composition**: Expressions can contain child expressions, forming a tree:
  - `WhereNode([Lookup(F('age'), Value(18)), ...])` is a tree
  - Each node knows how to compile itself to SQL with parameters

#### 3. **Vendor Dispatch Mechanism: `as_{vendor}()` Pattern**
The `compile()` method in SQLCompiler checks for vendor-specific implementations:
```python
def compile(self, node):
    vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
    if vendor_impl:
        sql, params = vendor_impl(self, self.connection)
    else:
        sql, params = node.as_sql(self, self.connection)
    return sql, params
```
- Allows backend-specific SQL generation without polluting base classes
- Example: `Lookup.as_oracle()` for Oracle-specific conditional wrapping
- Example: `SQLiteNumericMixin.as_sqlite()` for CAST handling
- Fallback to `as_sql()` for default (PostgreSQL, MySQL, etc.)

#### 4. **Tree-Based Query Representation**
- `Query` object contains:
  - `where`: Root `WhereNode` with hierarchical AND/OR/XOR logic
  - `alias_map`: JOIN tracking by alias
  - `select`, `order_by`, `group_by`, `annotations`: Clause definitions
- Each filter adds a subtree to `where`
- `WhereNode.as_sql()` recursively joins children with connector logic

#### 5. **Dynamic Lookup Resolution**
- Field types register lookup classes (e.g., `DateField.gt`, `CharField.iexact`)
- `lhs.get_lookup(name)` retrieves the appropriate `Lookup` class
- Supports transforms: `field__year__gte` → Transform('year') → Lookup('gte')
- Extensible: Custom fields/lookups register via `RegisterLookupMixin`

### Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **Manager** | Provides entry point (`get_queryset()`); proxies QuerySet methods |
| **QuerySet** | High-level ORM API; lazy query builder; manages iteration |
| **Query** | Internal SQL query object; stores WHERE/SELECT/GROUP/ORDER clauses; coordinates compilation |
| **SQLCompiler** | Converts Query into SQL; manages schema introspection; dispatches to vendors |
| **WhereNode** | Tree structure for WHERE/HAVING conditions; recursive SQL generation |
| **Lookup** | Represents a single comparison (e.g., field=value, field>value); generates SQL fragment |
| **Expression** | Base class for compilable components (Value, F, Case, Aggregate, etc.) |
| **Backend Operations** | Provides vendor-specific operators, SQL keywords, and compiler classes |

### Data Flow Description

1. **QuerySet Construction Phase** (no DB access):
   - User calls `Model.objects.filter(age__gt=18)`
   - Manager creates QuerySet with empty Query object
   - Filter decorates Query with WhereNode tree of Lookups
   - Multiple filters build up nested WhereNode structure

2. **Compilation Phase** (triggered on evaluation):
   - QuerySet iteration/count/get/etc. triggers `_fetch_all()`
   - Compiler instantiation: `query.get_compiler(using=db)` looks up backend-specific SQLCompiler class
   - `SQLCompiler.as_sql()` traverses Query structure
   - Recursively calls `compile(child)` on all expressions
   - Vendor dispatch: checks for `as_{vendor}()` method on each expression
   - Fallback to `as_sql()` if no vendor implementation

3. **Execution Phase** (database interaction):
   - Final SQL string and parameters passed to database driver
   - Cursor executes query
   - Results iterated by QuerySet, converted to model instances

### Interface Contracts Between Components

**Expression Protocol**:
```python
# Every compilable object must implement:
def as_sql(self, compiler, connection):
    """Return (sql_string, params) tuple."""
    pass

def resolve_expression(self, query, allow_joins=True, reuse=None, summarize=False, for_save=False):
    """Prepare expression for compilation (resolve F(), handle JOINs, etc.)."""
    pass

def get_source_expressions(self):
    """Return list of child expressions for traversal."""
    pass
```

**Lookup Protocol** (extends Expression):
```python
def process_lhs(self, compiler, connection):
    """Compile left-hand side (column reference)."""
    return sql, params

def process_rhs(self, compiler, connection):
    """Compile right-hand side (value or expression)."""
    return sql, params

def get_rhs_op(self, connection, rhs):
    """Get database operator for this lookup (e.g., '>' for 'gt')."""
    return connection.operators[self.lookup_name] % rhs
```

**Compiler Protocol**:
```python
def compile(self, node):
    """Dispatch node.as_sql() with vendor fallback."""
    vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
    return vendor_impl(self, self.connection) if vendor_impl else node.as_sql(self, self.connection)

def execute_sql(self, result_type=MULTI):
    """Generate SQL and execute against database."""
    sql, params = self.as_sql()
    cursor.execute(sql, params)
    return results
```

**Backend Operations Protocol**:
```python
def compiler(self, compiler_name):
    """Return compiler class for 'SQLCompiler', 'SQLInsertCompiler', etc."""
    module = import_module(self.compiler_module)  # backend-specific
    return getattr(module, compiler_name)
```

---

## Summary

The Django ORM query compilation pipeline implements a sophisticated **lazy evaluation + expression tree + visitor pattern** architecture. QuerySets defer SQL generation until execution by accumulating filter conditions in a `Query` object containing a hierarchical `WhereNode` tree of `Lookup` expressions. Upon evaluation, the backend-specific `SQLCompiler` recursively traverses this tree, dispatching each expression's `as_sql()` method (with vendor-specific `as_{vendor}()` fallbacks) to generate parameterized SQL fragments, which are composed into a final statement and executed against the database. This design decouples the high-level ORM API from SQL generation, supports multiple database backends through the vendor dispatch mechanism, and enables query optimization before compilation.
