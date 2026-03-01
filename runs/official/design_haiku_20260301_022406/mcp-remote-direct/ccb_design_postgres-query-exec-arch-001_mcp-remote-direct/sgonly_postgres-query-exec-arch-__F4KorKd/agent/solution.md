# PostgreSQL Query Execution Pipeline: Parse to Execute

## Files Examined

### Traffic Cop / Entry Point
- **src/backend/tcop/postgres.c** — Main traffic cop: `exec_simple_query()` orchestrates the entire query execution pipeline from parsing through execution

### Parser Subsystem
- **src/backend/tcop/postgres.c:602** — `pg_parse_query()` entry point
- **src/backend/parser/parser.c** — `raw_parser()` initializes Flex/Bison and produces RawStmt trees
- **src/backend/parser/scan.l** — Flex lexer that tokenizes input SQL string
- **src/backend/parser/gram.y** — Bison grammar produces parse tree nodes (SelectStmt, InsertStmt, etc.)

### Semantic Analyzer Subsystem
- **src/backend/tcop/postgres.c:665** — `pg_analyze_and_rewrite_fixedparams()` coordinator
- **src/backend/parser/analyze.c** — `parse_analyze_fixedparams()`, `transformTopLevelStmt()` entry points
- **src/backend/parser/parse_*.c** — Analysis modules:
  - `parse_clause.c` — FROM/WHERE/GROUP BY/ORDER BY clause analysis
  - `parse_expr.c` — Expression and operator analysis
  - `parse_target.c` — Target list analysis
  - `parse_relation.c` — Relation/table alias analysis
  - `parse_cte.c` — Common Table Expression (WITH) analysis
  - `parse_agg.c` — Aggregate function analysis
  - `parse_func.c` — Function call analysis
  - `parse_oper.c` — Operator resolution

### Rewriter Subsystem
- **src/backend/tcop/postgres.c:798** — `pg_rewrite_query()` entry point
- **src/backend/rewrite/rewriteHandler.c** — Main rewrite logic for views and rules
- **src/backend/rewrite/rewriteManip.c** — Rewrite manipulation utilities
- **src/backend/rewrite/rowsecurity.c** — Row-level security policy rewriting

### Planner/Optimizer Subsystem
- **src/backend/optimizer/plan/planner.c:287** — `planner()` entry point, delegates to `standard_planner()`
- **src/backend/optimizer/plan/planner.c:303** — `standard_planner()` orchestrates two-phase optimization
- **Phase 1 — Path Generation:**
  - **src/backend/optimizer/plan/planner.c:435** — `subquery_planner()` entry point
  - **src/backend/optimizer/path/allpaths.c** — `make_one_rel()`, `standard_join_search()` generate alternative paths
  - **src/backend/optimizer/path/costsize.c** — `set_baserel_pathlists()`, cost estimation for all nodes
  - **src/backend/optimizer/path/joinpath.c** — Join path generation (nested loop, hash join, merge join)
  - **src/backend/optimizer/path/joinrels.c** — Join relation enumeration
- **Phase 2 — Plan Generation:**
  - **src/backend/optimizer/plan/planner.c:441** — `create_plan()` converts best Path to Plan tree
  - **src/backend/optimizer/plan/createplan.c** — Node-specific plan creation functions

### Portal Setup
- **src/backend/tcop/pquery.c:67** — `CreateQueryDesc()` wraps PlannedStmt with execution metadata
- **src/backend/tcop/pquery.c** — Portal management (already initialized in postgres.c)

### Executor Subsystem
- **src/backend/executor/execMain.c** — Executor lifecycle:
  - `ExecutorStart()` — Initialize plan state tree
  - `ExecutorRun()` — Execute the plan
  - `ExecutorFinish()` — Finalize execution
  - `ExecutorEnd()` — Clean up resources
- **src/backend/executor/execProcnode.c** — Volcano-style dispatch:
  - `ExecInitNode()` — Recursively initialize PlanState nodes
  - `ExecProcNode()` — Dispatch to node-specific execution functions
  - `ExecEndNode()` — Recursively cleanup PlanState nodes
- **src/backend/executor/node*.c** — Node implementations:
  - `nodeSeqscan.c`, `nodeIndexscan.c` — Base table scans
  - `nodeNestloop.c`, `nodeHashjoin.c`, `nodeMergejoin.c` — Join implementations
  - `nodeAgg.c`, `nodeWindowAgg.c` — Aggregation and windowing
  - `nodeSort.c`, `nodeHash.c` — Sorting and hashing
  - Others for Append, Subplan, ModifyTable, etc.
- **src/backend/executor/execExpr.c**, **execExprInterp.c** — Expression evaluation

### Data Structure Headers
- **src/include/nodes/parsenodes.h** — Query, RawStmt, and SQL statement node definitions
- **src/include/nodes/plannodes.h** — PlannedStmt, Plan, and plan node definitions
- **src/include/nodes/pathnodes.h** — Path, RelOptInfo, and optimizer data structures
- **src/include/nodes/execnodes.h** — PlanState and executor state nodes

---

## Dependency Chain

### 1. Entry Point: Traffic Cop
**File:** `src/backend/tcop/postgres.c:1011`
**Function:** `exec_simple_query(const char *query_string)`

```
exec_simple_query() initializes the query execution pipeline:
├─ Line 1045: start_xact_command() — Begin transaction context
├─ Line 1058: MemoryContextSwitchTo(MessageContext) — Parser memory context
└─ Line 1064: Call pg_parse_query(query_string)
```

### 2. Parser Stage
**File:** `src/backend/tcop/postgres.c:602`
**Function:** `pg_parse_query(const char *query_string) → List<RawStmt>`

```
pg_parse_query() delegates to parser:
├─ Call raw_parser(query_string, RAW_PARSE_DEFAULT)
│   [File: src/backend/parser/parser.c:42]
│   ├─ scanner_init() — Initialize Flex lexer from scan.l
│   ├─ parser_init() — Initialize Bison parser state
│   ├─ base_yyparse() — Run Bison parser with tokens from lexer
│   │   [Flex produces tokens from gram.y terminals]
│   │   [Bison reduces tokens according to gram.y productions]
│   └─ Returns yyextra.parsetree (List<RawStmt>)
└─ Returns raw_parsetree_list
```

**Data Flow:**
- Input: `"SELECT ... FROM ... WHERE ..."`
- Lexer (scan.l): Tokenizes → Token stream
- Parser (gram.y): Builds parse tree → SelectStmt (wrapped in RawStmt)
- Output: `List<RawStmt>` where each RawStmt.stmt is a SelectStmt/InsertStmt/UpdateStmt/DeleteStmt

### 3. Semantic Analyzer Stage
**File:** `src/backend/tcop/postgres.c:665`
**Function:** `pg_analyze_and_rewrite_fixedparams(RawStmt *parsetree, ...) → List<Query>`

```
pg_analyze_and_rewrite_fixedparams():
├─ Line 682: Call parse_analyze_fixedparams(parsetree, ...)
│   [File: src/backend/parser/analyze.c:104]
│   ├─ make_parsestate() — Create parse state context
│   ├─ setup_parse_fixed_parameters() — Register parameter types
│   ├─ transformTopLevelStmt(pstate, parseTree) — Transform RawStmt → Query
│   │   ├─ Dispatches on statement type (SelectStmt, InsertStmt, etc.)
│   │   ├─ parse_clause.c: analyze JOIN/FROM/WHERE
│   │   ├─ parse_expr.c: resolve operators, functions, expressions
│   │   ├─ parse_target.c: validate target list columns
│   │   ├─ parse_relation.c: resolve table/alias references
│   │   ├─ parse_cte.c: process WITH clauses
│   │   ├─ parse_agg.c: validate aggregates
│   │   └─ Returns Query node
│   ├─ JumbleQuery() — Generate stable query ID for statistics
│   └─ Returns Query
├─ Line 691: Call pg_rewrite_query(query)
│   [File: src/backend/tcop/postgres.c:798]
│   └─ Delegates to rewrite_handler() in src/backend/rewrite/rewriteHandler.c
│       ├─ Applies view rewriting (expands view subqueries)
│       ├─ Applies rule rewriting (INSERT/UPDATE/DELETE rules)
│       ├─ Applies row-level security policies
│       └─ Returns List<Query> (may expand 1 query to multiple)
└─ Returns querytree_list (List<Query>)
```

**Data Flow:**
- Input: `RawStmt { stmt: SelectStmt { ... } }`
- Semantic Analysis:
  - Resolves table references → RangeTblEntry list
  - Validates column references against catalog
  - Resolves operators/functions with type coercion
  - Identifies aggregates, window functions, subqueries
  - Normalizes expressions
- Rewriting:
  - Expands views into subqueries
  - Applies view rules (ON INSERT, ON UPDATE, etc.)
  - Applies RLS policies
- Output: `List<Query>` where each Query is fully analyzed and rewritten

### 4. Planner/Optimizer Stage
**File:** `src/backend/tcop/postgres.c:900`
**Function:** `planner(Query *parse, ...) → PlannedStmt`

```
planner() [src/backend/optimizer/plan/planner.c:287]:
└─ Calls standard_planner(parse, ...) [Line 295]
   [File: src/backend/optimizer/plan/planner.c:303]

standard_planner() orchestrates two-phase optimization:

PHASE 1: PATH GENERATION (Optimizer's internal representation)
├─ Line 322: Create PlannerGlobal state
├─ Line 435: Call subquery_planner(glob, parse, ...)
│   [File: src/backend/optimizer/plan/planner.c, called from planmain.c]
│   ├─ setup_simple_rel_arrays() — Initialize relation info structures
│   ├─ initsplan.c: Call standard_qp_callback()
│   │   ├─ distribute_quals_to_rels() — Push down WHERE qualifiers
│   │   ├─ preprocess_expression() — Constant folding, simplification
│   ├─ join_search_one_level() → standard_join_search()
│   │   [src/backend/optimizer/path/joinrels.c]
│   │   ├─ make_one_rel() — Generate initial rel-to-rel paths
│   │   │   [src/backend/optimizer/path/allpaths.c]
│   │   │   ├─ For each base relation:
│   │   │   │   ├─ create_seqscan_path() — Sequential scan path
│   │   │   │   ├─ create_index_paths() — Index scan paths (if available)
│   │   │   │   ├─ Cost estimation via set_baserel_pathlists()
│   │   │   │   │   [src/backend/optimizer/path/costsize.c]
│   │   │   │   └─ Add cheapest paths to RelOptInfo.pathlist
│   │   │   └─ For each join combination (nested loop, hash, merge):
│   │   │       ├─ try_nestloop_path()
│   │   │       ├─ try_hashjoin_path()
│   │   │       └─ try_mergejoin_path()
│   │   │           [src/backend/optimizer/path/joinpath.c]
│   │   │           ├─ Estimate join costs
│   │   │           └─ Add to RelOptInfo.pathlist
│   │   ├─ group_by processing via planagg.c
│   │   └─ Returns cheapest paths at each optimization level
│   └─ Returns PlannerInfo *root with optimal Paths in RelOptInfo structures
├─ Line 438: fetch_upper_rel(root, UPPERREL_FINAL, NULL) — Get final relation
├─ Line 439: get_cheapest_fractional_path(final_rel, tuple_fraction) — Best Path

PHASE 2: PLAN GENERATION (Executable plan tree)
├─ Line 441: Call create_plan(root, best_path)
│   [File: src/backend/optimizer/plan/createplan.c]
│   ├─ Recursively converts Path tree to Plan tree
│   ├─ For each Path node type (SeqScanPath, IndexScanPath, NestPath, etc.):
│   │   ├─ create_seqscan_plan() → SeqScan node
│   │   ├─ create_indexscan_plan() → IndexScan node
│   │   ├─ create_nestloop_plan() → NestLoop node with left/right children
│   │   ├─ create_hashjoin_plan() → HashJoin node
│   │   ├─ create_mergejoin_plan() → MergeJoin node
│   │   ├─ create_sort_plan() → Sort node
│   │   ├─ create_agg_plan() → Agg node
│   │   └─ Recursively create_plan() on child Paths
│   └─ Returns top Plan node
├─ setrefs.c: fix_plan_references(root, plan)
│   ├─ Replace Var nodes with proper OUTER/INNER references
│   └─ Finalize plan for execution
└─ Returns PlannedStmt containing:
   ├─ commandType (SELECT, INSERT, UPDATE, DELETE)
   ├─ planTree (Plan node tree)
   ├─ rtable (RangeTblEntry list)
   ├─ paramExecTypes (for parameter binding)
   └─ Other execution metadata
```

**Data Flow:**
- Input: `Query` with analyzed table/expression structure
- Path Generation Phase:
  - Creates multiple Path alternatives for accessing relations
  - Estimates cost of each path (I/O, CPU)
  - Selects cheapest path at each optimization level
  - Data Structure: `Path` (SeqScanPath, IndexScanPath, NestPath, HashPath, etc.)
- Plan Generation Phase:
  - Converts best Path → executable Plan tree
  - Plan tree mirrors Path tree structure
  - Data Structure: `Plan` (SeqScan, IndexScan, NestLoop, HashJoin, etc.)
- Output: `PlannedStmt` containing Plan tree ready for execution

### 5. Portal & Execution Setup
**File:** `src/backend/tcop/postgres.c:1215-1234`

```
Portal setup and execution initiation:
├─ Line 1215: CreatePortal("") — Create unnamed portal
├─ Line 1224: PortalDefineQuery(portal, ..., plantree_list, ...)
│   [File: src/backend/tcop/pquery.c]
│   └─ Stores PlannedStmt in portal for later execution
├─ Line 1234: PortalStart(portal, NULL, 0, InvalidSnapshot)
│   [File: src/backend/tcop/pquery.c]
│   └─ Prepares portal (snapshot, resource owner management)
└─ Line 1273: PortalRun(portal, FETCH_ALL, true, receiver, receiver, &qc)
    [File: src/backend/tcop/pquery.c:685]
    ├─ Sets up execution context
    └─ Dispatches to ProcessQuery()
```

### 6. Executor Stage
**File:** `src/backend/tcop/pquery.c:685`
**Function:** `PortalRun(Portal portal, ...) → bool`

```
PortalRun() → ProcessQuery() → Executor lifecycle:

EXECUTOR INITIALIZATION:
├─ CreateQueryDesc(PlannedStmt, ...) [src/backend/tcop/pquery.c:67]
│   └─ Wraps PlannedStmt with:
│       ├─ sourceText (original SQL string)
│       ├─ snapshot (visibility snapshot)
│       ├─ params (bound parameters)
│       ├─ dest (result receiver)
│       └─ Returns QueryDesc
├─ ExecutorStart(QueryDesc, eflags) [src/backend/executor/execMain.c]
│   ├─ CreateExecutorState() — Allocate per-query context
│   ├─ Call ExecInitNode() [src/backend/executor/execProcnode.c:142]
│   │   ├─ Recursively initializes entire Plan tree
│   │   ├─ For each Plan node type (SeqScan, NestLoop, etc.):
│   │   │   ├─ ExecInitSeqScan() → Creates ScanState
│   │   │   ├─ ExecInitNestLoop() → Creates NestLoopState
│   │   │   │   ├─ Recursively ExecInitNode() on left/right plans
│   │   │   │   └─ Creates join state
│   │   │   ├─ ExecInitAgg() → Creates AggState
│   │   │   ├─ ExecInitSort() → Creates SortState
│   │   │   └─ Other node-specific initializers
│   │   ├─ CreateExprContext() — Per-tuple expression evaluation context
│   │   ├─ ExecInitExpr() — Prepare expression trees for execution
│   │   └─ Returns root PlanState (parallel structure to Plan tree)
│   └─ AfterTriggerBeginQuery() — Initialize trigger handling

VOLCANO-STYLE EXECUTION:
├─ ExecutorRun(QueryDesc, ForwardScanDirection, 0) [src/backend/executor/execMain.c:297]
│   ├─ ExecutePlan(estate, estate->planstate, execute_once, tcount, direction, receiver)
│   │   [src/backend/executor/execMain.c:350+]
│   │   └─ Repeatedly call ExecProcNode() [src/backend/executor/execProcnode.c:165]
│   │       ├─ VOLCANO-STYLE DISPATCH (demand-pull pipeline):
│   │       │   ├─ if node is SeqScanState:
│   │       │   │   └─ ExecSeqScan() → Returns next tuple
│   │       │   ├─ else if node is NestLoopState:
│   │       │   │   ├─ ExecNestLoop() [src/backend/executor/nodeNestloop.c]
│   │       │   │   ├─ Calls ExecProcNode(left_planstate) to get left tuple
│   │       │   │   ├─ For each left tuple, calls ExecProcNode(right_planstate)
│   │       │   │   ├─ Evaluates join condition
│   │       │   │   └─ Returns joined tuple if condition passes
│   │       │   ├─ else if node is HashJoinState:
│   │       │   │   └─ ExecHashJoin() — Hash-based join
│   │       │   ├─ else if node is AggState:
│   │       │   │   └─ ExecAgg() — Aggregate computation
│   │       │   └─ ... other node types
│   │       ├─ ExecEvalExpr() [src/backend/executor/execExpr.c]
│   │       │   └─ Evaluate expressions in per-tuple context
│   │       ├─ ResetExprContext() — Clear per-tuple memory
│   │       └─ Return TupleTableSlot
│   ├─ Send tuple to dest receiver (result display, INSERT INTO, etc.)
│   └─ Repeat until no more tuples or count exhausted

EXECUTOR FINALIZATION:
├─ ExecutorFinish(QueryDesc) [src/backend/executor/execMain.c]
│   └─ ExecPostprocessPlan() — Finish any unfinished ModifyTable nodes
└─ ExecutorEnd(QueryDesc) [src/backend/executor/execMain.c:466]
    ├─ ExecEndNode() [src/backend/executor/execProcnode.c:215]
    │   ├─ Recursively finalizes entire PlanState tree
    │   ├─ Close table/index scans
    │   ├─ Release buffer pins
    │   ├─ Free hash tables, sort buffers, etc.
    │   └─ ExecEndSeqScan(), ExecEndNestLoop(), ExecEndAgg(), ...
    ├─ AfterTriggerEndQuery() — Finalize triggers
    └─ FreeExecutorState() — Free per-query context
```

**Volcano-Style Executor Dispatch:**
- Each PlanState node has a slot function pointer (`ps_ProcNode`)
- ExecProcNode() calls the node's function
- Each node implementation:
  1. Calls ExecProcNode() on child nodes (demand-pull)
  2. Evaluates filters/aggregations
  3. Returns next tuple or NULL
- Execution is recursive top-down data flow bottom-up
- Each node executes until it exhausts its input
- Memory is freed in a per-tuple context to avoid accumulation

---

## Analysis

### Design Patterns Identified

#### 1. **Pipeline Architecture (Data Flow Pattern)**
The query execution follows a classic staged pipeline where each stage transforms the input into a higher-level representation:
- **Lexical** (raw text) → **Syntactic** (RawStmt) → **Semantic** (Query) → **Logical** (Query after rewrite) → **Physical** (PlannedStmt) → **Execution** (PlanState)

Each stage is independent and operates on well-defined data structures that are passed to the next stage.

#### 2. **Two-Phase Optimization (Optimizer Pattern)**
The planner uses a two-phase optimization strategy:
1. **Path Phase**: Generates multiple Path alternatives with cost estimates, explores join orderings, index availability
2. **Plan Phase**: Converts the best Path to an executable Plan tree

This separation allows the optimizer to explore many paths efficiently without generating full Plan trees for each alternative.

#### 3. **Volcano Model Executor (Iterator Pattern)**
The executor implements the Volcano/Cascades iterator model:
- Each PlanState node is a module that produces one tuple at a time
- When called, a node:
  1. Calls its children to get tuples (demand-pull)
  2. Applies its operation (scan, join, aggregate, etc.)
  3. Returns the result tuple
- This is implemented via function pointers in PlanState nodes
- Allows for:
  - Pipelined execution (no need to materialize all intermediate results)
  - Partial/LIMIT execution (stop when limit is reached)
  - Streaming joins and aggregations

#### 4. **Parallel Read-Only Data Structures (Plan Tree)**
- **Plan Tree** (created by planner) is read-only throughout execution
- **PlanState Tree** (created by executor) is the mutable execution state
- This separation allows plan reuse without modification

#### 5. **Context-Based Memory Management**
- Per-query context: Holds query plan and long-lived data
- Per-tuple context: Holds temporary per-tuple expression evaluation results
- Contexts are freed hierarchically to avoid memory leaks

#### 6. **Hook-Based Extensibility**
PostgreSQL allows plugins to intercept execution at multiple points:
- `planner_hook` - Plugin planner implementation
- `ExecutorStart_hook`, `ExecutorRun_hook`, `ExecutorEnd_hook` - Plugin executor hooks
- `post_parse_analyze_hook` - Post-analysis hook
- This enables extensions, query logging, and custom planning strategies

### Component Responsibilities

| Component | Responsibility | Data Structures |
|-----------|-----------------|-----------------|
| **Traffic Cop (exec_simple_query)** | Orchestrate pipeline, manage contexts, transaction control | RawStmt list → Query list → PlannedStmt list |
| **Lexer (scan.l)** | Tokenize SQL string | Raw characters → Token stream |
| **Parser (gram.y)** | Build parse tree from tokens | Token stream → RawStmt (SelectStmt/InsertStmt/etc.) |
| **Analyzer** | Semantic validation, resolve references | RawStmt → Query (with rtable, joins validated) |
| **Rewriter** | Apply rules, views, RLS policies | Query → Query list (possibly expanded) |
| **Planner/Path Generator** | Generate alternative execution paths | Query → RelOptInfo with Path list (Paths with costs) |
| **Planner/Plan Creator** | Convert best path to executable plan | Best Path → Plan tree (SeqScan/NestLoop/etc.) |
| **Executor** | Execute plan tree | PlannedStmt + PlanState tree → Result tuples |
| **Portal** | Interface between protocol and executor | Holds PlannedStmt and manages snapshots/resources |

### Data Flow Through Pipeline

```
Raw SQL String
    ↓ [LEXER: scan.l]
Token Stream
    ↓ [PARSER: gram.y]
RawStmt (SelectStmt/InsertStmt/UpdateStmt/etc.)
    ↓ [ANALYZER: analyze.c + parse_*.c]
Query (analyzed, resolved references)
    ↓ [REWRITER: rewriteHandler.c]
Query (after rules, views, RLS applied)
    ↓ [OPTIMIZER PATH PHASE: allpaths.c, costsize.c]
RelOptInfo trees with Path lists (alternatives with costs)
    ↓ [OPTIMIZER SELECT BEST PATH]
Cheapest Path tree
    ↓ [OPTIMIZER PLAN PHASE: createplan.c]
PlannedStmt (Plan tree: SeqScan/NestLoop/etc.)
    ↓ [PORTAL SETUP]
QueryDesc (PlannedStmt + metadata)
    ↓ [EXECUTOR INIT: ExecInitNode]
PlanState tree (parallel structure to Plan tree)
    ↓ [EXECUTOR RUN: ExecProcNode via Volcano dispatch]
TupleTableSlot (results sent to dest receiver)
    ↓ [EXECUTOR END: ExecEndNode cleanup]
Query Completion
```

### Interface Contracts Between Components

1. **Parser → Analyzer**: RawStmt must have valid stmt node (SelectStmt, InsertStmt, etc.). Analyzer produces Query with all references resolved.

2. **Analyzer → Rewriter**: Query is complete and analyzable. Rewriter may produce multiple Queries (view expansion) or modified single Query.

3. **Rewriter → Optimizer**: Query is fully analyzed and rewritten. Optimizer produces PlannedStmt with complete Plan tree.

4. **Optimizer → Executor**: PlannedStmt.planTree must be valid Plan node tree with all necessary metadata (cost, cardinality estimates). Executor produces PlanState mirror tree.

5. **Executor → Destination**: Each call to ExecProcNode() returns a TupleTableSlot (or NULL when done). Dest receiver processes each tuple.

---

## Summary

The PostgreSQL query execution pipeline implements a classical database architecture with careful separation of concerns. Starting from the raw SQL string in `exec_simple_query()`, the query flows through:

1. **Parser** (Flex/Bison) produces abstract syntax trees
2. **Semantic Analyzer** validates and resolves all references against the catalog
3. **Rewriter** applies database rules, views, and row-level security policies
4. **Two-Phase Optimizer** explores alternative execution paths and selects the best one
5. **Volcano-Style Executor** executes the plan tree using a demand-pull pipeline model

Each stage operates on progressively more refined data structures (RawStmt → Query → PlannedStmt → PlanState), enabling plan caching, parallelization, and plugin extensibility. The Volcano executor's iterator model allows PostgreSQL to efficiently handle large result sets through pipelined execution and memory-efficient per-tuple processing.
