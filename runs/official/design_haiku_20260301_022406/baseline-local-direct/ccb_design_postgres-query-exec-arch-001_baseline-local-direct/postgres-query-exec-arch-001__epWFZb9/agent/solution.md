# PostgreSQL Query Execution Pipeline: Comprehensive Architectural Analysis

## Files Examined

### Traffic Cop (Top-level Command Processing)
- `src/backend/tcop/postgres.c` — Entry point for query processing, contains `exec_simple_query()`, `pg_parse_query()`, `pg_analyze_and_rewrite_fixedparams()`, `pg_plan_queries()`, `pg_rewrite_query()` functions

### Parser Stage (Lexer + Grammar)
- `src/backend/parser/parser.c` — `raw_parser()` entry point; initializes flex scanner and bison parser (line 42)
- `src/backend/parser/scansup.c` — Scanner support functions
- `src/backend/parser/parse_node.c` — Parse node utilities
- `src/include/parser/parser.h` — Parser API declarations

### Semantic Analyzer Stage
- `src/backend/parser/analyze.c` — `parse_analyze_fixedparams()` (line 105) transforms RawStmt→Query; calls `transformTopLevelStmt()`
- `src/backend/parser/parse_*.c` (15 files) — Semantic analysis for different query clauses
  - `parse_clause.c` — FROM/WHERE clause parsing
  - `parse_expr.c` — Expression parsing
  - `parse_target.c` — SELECT target list parsing
  - `parse_agg.c` — Aggregate handling
  - `parse_func.c` — Function name resolution
  - `parse_oper.c` — Operator resolution
  - `parse_relation.c` — Table/relation resolution
  - `parse_cte.c` — CTE (WITH clause) handling
  - `parse_coerce.c` — Type coercion
  - `parse_collate.c` — Collation handling
  - `parse_type.c` — Type name parsing
  - And others...
- `src/include/parser/analyze.h` — Analysis API

### Query Rewriter Stage
- `src/backend/tcop/postgres.c` — `pg_rewrite_query()` (line 798) calls `QueryRewrite()`
- `src/backend/rewrite/` — Rewrite system (applies views, INSTEAD rules, security policies)

### Optimizer/Planner Stage
- `src/backend/optimizer/plan/planner.c` — `planner()` (line 287), `standard_planner()` (line 303)
- `src/backend/optimizer/plan/planner.c` — `pg_plan_query()` (line 882) calls `planner()`

#### Optimizer Phase 1: Path Generation (Logical Optimization)
- `src/backend/optimizer/path/allpaths.c` (4,433 lines) — `make_one_rel()`, generates all possible access paths
- `src/backend/optimizer/path/joinpath.c` — Join path generation (nested loop, merge, hash joins)
- `src/backend/optimizer/path/indxpath.c` — Index access paths
- `src/backend/optimizer/path/costsize.c` — Cost and row estimate calculations
- `src/backend/optimizer/path/clausesel.c` — Clause selectivity estimation
- `src/backend/optimizer/path/equivclass.c` — Equivalence class handling
- `src/backend/optimizer/path/pathkeys.c` — Sort order path key handling
- `src/backend/optimizer/path/tidpath.c` — TID-based scan paths
- `src/backend/optimizer/path/joinrels.c` — Join relation processing

#### Optimizer Phase 2: Plan Creation (Physical Optimization)
- `src/backend/optimizer/plan/createplan.c` (7,477 lines) — `create_plan()` (line 337) converts best Path→Plan
- `src/backend/optimizer/plan/createplan.c` — `create_plan_recurse()` (line 388) dispatches via `best_path->pathtype` switch

#### Optimizer Preprocessing
- `src/backend/optimizer/prep/prepjointree.c` — Join tree normalization
- `src/backend/optimizer/prep/prepagg.c` — Aggregate preprocessing
- `src/backend/optimizer/prep/prepqual.c` — Qualifier preprocessing
- `src/backend/optimizer/prep/prepunion.c` — UNION preprocessing

#### Optimizer Utilities
- `src/backend/optimizer/util/pathnode.c` — Path node creation
- `src/backend/optimizer/util/clauses.c` — Clause manipulation
- `src/backend/optimizer/util/relnode.c` — Relation node creation
- `src/backend/optimizer/util/restrictinfo.c` — Restriction info (filter predicates)
- `src/backend/optimizer/util/plancat.c` — Access to system catalogs

#### GEQO (Genetic Query Optimizer) for Large Join Problems
- `src/backend/optimizer/geqo/geqo_main.c` — GEQO entry point for complex joins

### Executor Stage
- `src/backend/executor/execProcnode.c` (987 lines) — Volcano-style execution dispatcher
  - `ExecInitNode()` (line 142) — Initialization via switch on `nodeTag(node)` (line 161)
  - `ExecProcNode()` — Tuple fetch via function pointers (Volcano model)
  - `ExecSetExecProcNode()` (line 430) — Sets function pointer with wrapper
  - `ExecEndNode()` — Cleanup/finalization
- `src/backend/executor/execMain.c` — `ExecutorStart()`, `ExecutorRun()`, `ExecutorEnd()`
- `src/backend/executor/execUtils.c` — Executor utilities

#### Executor Node Types (40+ node implementations)
**Scan Nodes:**
- `nodeSeqscan.c`, `nodeIndexscan.c`, `nodeIndexonlyscan.c`, `nodeBitmapHeapscan.c`
- `nodeTidscan.c`, `nodeFunctionscan.c`, `nodeSubqueryscan.c`, `nodeForeignscan.c`
- `nodeCtescan.c`, `nodeValuesscan.c`, `nodeWorktablescan.c`

**Join Nodes:**
- `nodeNestloop.c`, `nodeMergejoin.c`, `nodeHashjoin.c`, `nodeHash.c`

**Aggregation/Grouping:**
- `nodeAgg.c`, `nodeGroup.c`, `nodeWindowAgg.c`, `nodeSetOp.c`

**Sort/Ordering:**
- `nodeSort.c`, `nodeIncrementalSort.c`, `nodeMaterial.c`

**Other Node Types:**
- `nodeLimit.c`, `nodeUnique.c`, `nodeAppend.c`, `nodeMergeAppend.c`
- `nodeGather.c`, `nodeGatherMerge.c` (parallel execution)
- `nodeModifyTable.c` (INSERT/UPDATE/DELETE)

### Node Definitions
- `src/include/nodes/parsenodes.h` — Raw parse tree node definitions
  - `RawStmt` (line 2081) — Parser output containing raw parse tree
  - `Query` (line 117) — Semantic tree after analysis/rewrite
- `src/include/nodes/plannodes.h` — Plan node definitions
  - `PlannedStmt` (line 46) — Top-level plan statement
  - `Plan` (line 158) — Base class for all plan nodes
- `src/include/nodes/execnodes.h` — Executor state structures (PlanState)
- `src/include/nodes/pathnodes.h` — Path and optimizer info structures

### Node Support Infrastructure
- `src/backend/nodes/copyfuncs.c` — Deep-copy nodes
- `src/backend/nodes/outfuncs.c` — Serialize nodes to text
- `src/backend/nodes/readfuncs.c` — Deserialize nodes from text
- `src/backend/nodes/nodeFuncs.c` — Generic node utilities
- `src/backend/nodes/makefuncs.c` — Node creation helpers

---

## Dependency Chain

### 1. Entry Point: Traffic Cop Dispatcher
**File:** `src/backend/tcop/postgres.c` (line 1011)
**Function:** `exec_simple_query(const char *query_string)`

**Responsibilities:**
- Receives raw SQL string from client
- Manages transaction context (start/commit)
- Coordinates flow through pipeline stages
- Executes query via portal mechanism

### 2. Parse Stage (Syntax Analysis)
**File:** `src/backend/tcop/postgres.c` (line 603)
**Function:** `pg_parse_query(query_string)` → calls `raw_parser(query_string, RAW_PARSE_DEFAULT)`

**Implementation File:** `src/backend/parser/parser.c` (line 42)
**Function:** `raw_parser(const char *str, RawParseMode mode)`

**Operations:**
```
raw_parser()
  ├─ scanner_init() — Initialize flex lexical scanner
  ├─ parser_init() — Initialize bison parser state
  ├─ base_yyparse() — Run parser (grammar-driven)
  ├─ scanner_finish() — Clean up flex state
  └─ return yyextra.parsetree (List<RawStmt>)
```

**Data Output:** List of `RawStmt` nodes (raw parse tree, no semantic analysis)

### 3. Analyze & Rewrite Stage (Semantic Analysis)
**File:** `src/backend/tcop/postgres.c` (line 1189)
**Function:** `pg_analyze_and_rewrite_fixedparams(RawStmt, query_string, paramTypes, numParams, queryEnv)`

**Calls two substages:**

#### 3a. Semantic Analysis
**Implementation File:** `src/backend/parser/analyze.c` (line 105)
**Function:** `parse_analyze_fixedparams(RawStmt *parseTree, ...)`

**Operations:**
```
parse_analyze_fixedparams()
  ├─ make_parsestate() — Create ParseState context
  ├─ transformTopLevelStmt(parseTree) — Main analysis function
  │  ├─ Resolves table/column names (parse_relation.c)
  │  ├─ Resolves function names (parse_func.c)
  │  ├─ Performs type checking (parse_coerce.c)
  │  ├─ Handles aggregates (parse_agg.c)
  │  ├─ Handles subqueries (parse_cte.c)
  │  └─ Produces Query node
  ├─ JumbleQuery() — Compute query hash ID
  ├─ post_parse_analyze_hook() — Allow plugins
  ├─ free_parsestate()
  └─ return Query
```

**Data Output:** Single `Query` node (analyzed parse tree, references resolved)

#### 3b. Query Rewriting
**File:** `src/backend/tcop/postgres.c` (line 798)
**Function:** `pg_rewrite_query(Query *query)`

**Operations:**
```
pg_rewrite_query()
  ├─ For CMD_UTILITY: wrap in list (no rewriting)
  └─ For DML queries:
     ├─ QueryRewrite(query) — Apply INSTEAD rules, view expansion, RLS policies
     └─ return List<Query> (may expand one query to many)
```

**Data Output:** List of `Query` nodes (after rules applied, may have expanded from 1 to N queries)

### 4. Optimization Stage (Logical Planning)
**File:** `src/backend/tcop/postgres.c` (line 970)
**Function:** `pg_plan_queries(List<Query> querytrees, ...)`

For each Query:
```
pg_plan_queries()
  ├─ For each Query in querytrees:
  │  └─ pg_plan_query(Query) — Plan single query
  │
  └─ return List<PlannedStmt> (one PlannedStmt per Query)
```

**File:** `src/backend/tcop/postgres.c` (line 882)
**Function:** `pg_plan_query(Query *querytree, query_string, cursorOptions, boundParams)` → calls `planner()`

**Implementation File:** `src/backend/optimizer/plan/planner.c` (line 287)
**Function:** `planner(Query *parse, query_string, cursorOptions, boundParams)`

This delegates to `standard_planner()` (line 303):

**File:** `src/backend/optimizer/plan/planner.c` (line 303)
**Function:** `standard_planner(Query *parse, ...)`

#### Two-Phase Optimization (Core Algorithm)

**Phase 1: Path Generation (Logical Optimization)**
```
standard_planner()
  ├─ makeNode(PlannerGlobal) — Initialize global planner state
  ├─ Assess parallelism feasibility
  │
  └─ subquery_planner(glob, parse, ...)
     ├─ Handle preprocessing (FROM clause normalization, etc.)
     ├─ make_one_rel(root, parse->fromClause)
     │  ├─ Build RelOptInfo for each relation (via set_rel_size/set_rel_pathlist)
     │  ├─ Generate alternative Paths:
     │  │  ├─ Index scan paths (indxpath.c)
     │  │  ├─ Sequential scan paths
     │  │  ├─ Bitmap scan combinations
     │  │  └─ Apply restrictions (WHERE clauses)
     │  │
     │  ├─ make_rel_from_joinlist() — Join relations (dynamic programming)
     │  │  ├─ Consider all join orders (pruned by DP)
     │  │  ├─ Generate NestLoop paths (nodeNestloop.c)
     │  │  ├─ Generate MergeJoin paths (nodeMergejoin.c)
     │  │  ├─ Generate HashJoin paths (nodeHashjoin.c)
     │  │  └─ Cost each path variant
     │  │
     │  └─ Return RelOptInfo with best (cheapest) Path
     │
     ├─ Cost-based path selection keeps only cheapest paths at each step
     ├─ Return root (PlannerInfo) containing the best paths
     └─ [Multiple subquery levels recursively processed]

Data Structure: Each RelOptInfo has pathlist containing Path nodes with cost estimates
- Path type: generic (cost, rows, sort order)
- Specific: NestPath, MergePath, HashPath, IndexPath, etc.
```

**Phase 2: Plan Creation (Physical Optimization)**
```
standard_planner() continues:
  │
  ├─ fetch_upper_rel(root, UPPERREL_FINAL) — Get final relation with paths
  ├─ get_cheapest_fractional_path(final_rel, tuple_fraction) — Select best Path
  │
  └─ create_plan(root, best_path)  [Line 441, createplan.c:337]
     │
     ├─ create_plan_recurse(root, best_path, CP_EXACT_TLIST)
     │  ├─ switch (best_path->pathtype):
     │  │  ├─ T_SeqScan, T_IndexScan, ... → create_scan_plan()
     │  │  ├─ T_NestLoop, T_MergeJoin, T_HashJoin → create_join_plan()
     │  │  ├─ T_Agg, T_Group, ... → create_group_plan()
     │  │  └─ ... [all plan node types]
     │  │
     │  └─ Recursively calls create_plan() on child paths
     │     └─ Returns Plan tree (mirror structure of Path tree)
     │
     ├─ apply_tlist_labeling() — Add column names to output
     ├─ SS_attach_initplans() — Attach init subplans
     └─ return top_plan (Plan tree)
```

**Data Output:** `Plan` node tree (hierarchical execution instructions)

#### Plan Finalization
```
standard_planner() final steps:
  │
  ├─ SS_finalize_plan(root, top_plan) — Compute parameter sets
  ├─ set_plan_references(root, top_plan) — Convert Var nodes to OUTER/INNER references
  │
  └─ Build PlannedStmt:
     ├─ Copy metadata from Query
     ├─ Attach Plan tree (planTree)
     ├─ Attach subplans, RTEs, rowmarks, etc.
     └─ return result (PlannedStmt)
```

**Data Output:** `PlannedStmt` (complete executable plan with all metadata)

### 5. Portal Creation & Execution
**File:** `src/backend/tcop/postgres.c` (line 1215)
**Function:** `CreatePortal()` — Create unnamed portal
**Function:** `PortalDefineQuery()` — Associate plantree_list with portal
**Function:** `PortalStart()` — Initialize portal

### 6. Execution Stage (Tuple Production)
**File:** `src/backend/executor/execMain.c`
**Function:** `ExecutorStart(QueryDesc, int eflags)` → `InitPlan()`

#### Executor Initialization (Bottom-up tree construction)
```
ExecutorStart()
  └─ InitPlan(estate, plannedstmt)
     │
     └─ ExecInitNode(root_plan, estate, eflags)  [execProcnode.c:142]
        │
        ├─ switch (nodeTag(node)):  [line 161, 40+ cases]
        │  ├─ T_SeqScan → ExecInitSeqScan() → create SeqScanState
        │  ├─ T_IndexScan → ExecInitIndexScan() → create IndexScanState
        │  ├─ T_NestLoop → ExecInitNestLoop() → recursively init children
        │  ├─ T_HashJoin → ExecInitHashJoin() → init hash table builder
        │  ├─ T_Agg → ExecInitAgg() → init aggregation state
        │  └─ ... [one case per Plan node type]
        │
        ├─ ExecSetExecProcNode(result, result->ExecProcNode)
        │  └─ Sets function pointer: result->ExecProcNode = ExecSeqScan (or node-specific)
        │
        └─ Recursively call ExecInitNode() on child plans
           └─ Build parallel PlanState tree (mirrors Plan tree)
```

**Data Structures:**
- `Plan` (plan-time structure) → `PlanState` (runtime structure)
- Each PlanState has:
  - `ExecProcNode` function pointer (specific tuple-fetching function)
  - State for that node (e.g., scan position, aggregate buffer)
  - Links to child PlanStates

#### Executor Iteration (Top-down tuple fetching)
```
ExecutorRun(queryDesc, direction, count)
  │
  ├─ ExecutePlan(estate, planstate, ...) — Main execution loop
  │  │
  │  └─ for each tuple needed:
  │     │
  │     └─ ExecProcNode(top_planstate)  [Volcano model]
  │        │
  │        ├─ Calls function pointer: (*planstate->ExecProcNode)(planstate)
  │        │  └─ e.g., ExecSeqScan(planstate) → fetches next heap tuple
  │        │
  │        └─ Returns TupleTableSlot with tuple or NULL (end)
  │           │
  │           ├─ If leaf node (SeqScan):
  │           │  └─ Reads from heap pages via buffer manager
  │           │
  │           ├─ If join node (NestLoop):
  │           │  ├─ Calls ExecProcNode(outer_child)
  │           │  └─ Calls ExecProcNode(inner_child) for each outer tuple
  │           │
  │           └─ If aggregation node (Agg):
  │              ├─ Accumulates tuples in hash/sort aggregation state
  │              └─ Returns aggregate results when input exhausted
  │
  ├─ Apply output tuple sink (copy to client buffer via printtup)
  └─ return tuple count
```

**Execution Model:** Volcano/Iterator model
- Each node is a generator (ExecProcNode)
- Child calls are pull-based (parent calls child repeatedly)
- Tuples flow bottom-up through plan tree
- Natural pipelining with buffering only at specific points (sorts, hash joins)

#### Executor Finalization
```
ExecutorEnd(queryDesc)
  │
  └─ ExecEndNode(top_planstate)  [execProcnode.c, ExecEndNode case]
     │
     ├─ switch (nodeTag(plan)):  [Dispatch to node-specific cleanup]
     │  ├─ T_SeqScan → ExecEndSeqScan() — close scan state
     │  ├─ T_HashJoin → ExecEndHashJoin() — free hash table memory
     │  ├─ T_Agg → ExecEndAgg() — flush final aggregates
     │  └─ ... [cleanup for each node type]
     │
     └─ Recursively ExecEndNode(child_planstate)
        └─ Release memory, file handles, etc.
```

---

## Analysis

### Design Patterns Identified

#### 1. **Pipeline/Dataflow Architecture**
The query execution is organized as a strict pipeline with clear stages:
- **Parse**: Syntax validation and raw AST production
- **Analyze**: Semantic validation and reference resolution
- **Rewrite**: Rule application and query transformation
- **Optimize**: Logical and physical optimization
- **Execute**: Tuple production via iterator model

Each stage produces well-defined intermediate data structures:
```
SQL String → RawStmt → Query → PlannedStmt → PlanState Tree → Tuples
```

#### 2. **Two-Phase Optimization (Separation of Concerns)**

**Phase 1 - Path Generation (Logical):** `src/backend/optimizer/path/allpaths.c`
- Generates multiple candidate execution strategies (Paths)
- Focus: logical correctness and cost estimation
- Dynamic programming for join order selection
- Cost-based pruning keeps only viable alternatives
- Output: RelOptInfo with pathlist

**Phase 2 - Plan Creation (Physical):** `src/backend/optimizer/plan/createplan.c`
- Selects best Path, converts to Plan tree
- Maps logical operators to physical operators
- Attaches implementation details (sort orders, output columns)
- Line 395-414: Dispatch via `switch (best_path->pathtype)` converts Path→Plan

**Benefits:**
- Cost model independent of plan generation
- Easy to add new plan types without changing all paths
- Clean separation between logical and physical optimization

#### 3. **Volcano/Iterator Model (Push-up from Leaves)**

**Initialization Phase (Bottom-up construction):**
- ExecInitNode recursively builds state tree
- Each node knows its specific ExecProcNode function
- Mirrors plan tree structure in memory

**Execution Phase (Top-down fetching):**
```
for each result_tuple needed:
  tup = ExecProcNode(top_node)  // Call iterator function
  // Recursively:
  //   ExecProcNode(top_node) → ExecNestLoop → calls ExecProcNode(children)
  //   When all outer tuples: stop
```

**Function Pointer Dispatch (not switch statement):**
```c
ExecSetExecProcNode(result, result->ExecProcNode);  // Line 391, execProcnode.c
// Each node's ExecInit* sets result->ExecProcNode to node-specific function:
// ExecSeqScan, ExecIndexScan, ExecNestLoop, ExecHashJoin, ExecAgg, etc.

// At runtime:
TupleTableSlot *slot = (*planstate->ExecProcNode)(planstate);  // Call via pointer
```

**Advantages:**
- Minimal overhead (function pointer vs switch)
- Natural pipelining (tuples flow up the tree)
- Easy to plug in new node types (just add ExecInit*/Exec* functions)

#### 4. **Dispatcher Pattern with Static and Dynamic Dispatch Hybrid**

At initialization time (static dispatch via switch):
```c
switch (nodeTag(node)):  // Line 161, execProcnode.c
  case T_SeqScan:
    result = ExecInitSeqScan(...);
    break;
  case T_NestLoop:
    result = ExecInitNestLoop(...);
    break;
  // 40+ cases
```

At runtime (dynamic dispatch via function pointers):
```c
(*planstate->ExecProcNode)(planstate)  // No switch, just indirect call
```

**Benefit:** Fast initialization path uses switch (compiler can optimize), fast execution uses function pointers (cache-friendly).

#### 5. **Node Type System (Tagged Union)**
All AST and plan node types tagged with NodeTag enum:
```c
typedef enum NodeTag {
  T_RawStmt, T_SelectStmt, T_Query, T_Plan, T_SeqScan, T_NestLoop, ...
} NodeTag;

// Every node starts with:
typedef struct SomeNode {
  NodeTag type;
  ...
} SomeNode;
```

Enables:
- Runtime type checking via `IsA(node, type)`
- Polymorphic node operations (copy, compare, print)
- Generic node traversal

#### 6. **Recursive Tree Processing**
Plan/Path trees are inherently recursive:
- ExecInitNode recursively processes children
- create_plan recursively processes child paths
- ExecEndNode recursively finalizes children
- Maximizes code reuse and maintains tree structure

#### 7. **Cost-Based Optimization with Heuristic Pruning**

Dynamic programming with pruning (joinrels.c, allpaths.c):
- Enumerate join orders using DP algorithm
- At each DP step, keep only best paths for each relation subset
- For large n, use GEQO (genetic algorithm) as fallback
- Result: Tractable optimization despite exponential search space

#### 8. **Separation of Planning from Execution**

Plan nodes are immutable during execution:
- No side effects during planning
- Transaction semantics isolated in executor
- Allows plan caching (prepared statements)
- Multiple executions of same plan possible

### Component Responsibilities

**Traffic Cop (postgres.c):**
- Receives raw SQL from client
- Coordinates pipeline stages
- Manages transaction context
- Implements portal interface

**Parser (parser/parser.c + lex/gram.y):**
- Lexical analysis (flex)
- Syntactic analysis (bison)
- No semantic checking, no table access
- Input: SQL string; Output: RawStmt list

**Analyzer (parser/analyze.c + parse_*.c):**
- Semantic validation
- Name resolution (tables, columns, functions)
- Type checking and coercion
- Input: RawStmt; Output: Query

**Rewriter (rewrite/rewriteHandler.c):**
- Apply view expansion
- Apply INSTEAD rules
- Apply row-level security policies
- Input: Query; Output: Query list (possibly expanded)

**Optimizer Path Generation (optimizer/path/allpaths.c):**
- Generate candidate access paths
- Estimate costs using selectivity estimation
- Consider index availability
- Dynamic programming for join orders
- Output: RelOptInfo with Path alternatives

**Optimizer Plan Creation (optimizer/plan/createplan.c):**
- Select best Path
- Convert Path to Plan tree
- Attach implementation details
- Output: Plan tree

**Executor Initialization (executor/execProcnode.c, ExecInitNode):**
- Build state tree from plan tree
- Set up runtime execution context
- Initialize per-node state (buffers, cursors, etc.)
- Output: PlanState tree with function pointers

**Executor Runtime (executor/nodeXxx.c, ExecProcNode):**
- Fetch tuples via Volcano model
- Implement join algorithms (nested loop, merge, hash)
- Implement grouping/aggregation
- Implement sorting (when needed)
- Output: TupleTableSlots with result tuples

### Data Flow Description

```
1. PARSE PHASE (Traffic Cop → Parser)
   Input:  SELECT a, b FROM table WHERE x > 5
   Process: Lexer tokenizes → Parser builds syntax tree
   Output: RawStmt { SelectStmt { ... } }

2. ANALYZE PHASE (Traffic Cop → Analyzer)
   Input:  RawStmt { SelectStmt { table: "table", ... } }
   Process:
     - Resolve "table" to RangeTableEntry (catalog lookup)
     - Resolve "a", "b", "x" to actual columns
     - Check types (b > 5 requires compatible types)
   Output: Query {
     rtable: [RTE for "table"],
     targetList: [Var(a), Var(b)],
     jointree: FromExpr with WHERE x > 5
   }

3. REWRITE PHASE (Traffic Cop → Rewriter)
   Input:  Query { ... }
   Process:
     - Check if "table" is a view → if so, expand to underlying query
     - Check for INSTEAD rules → apply if present
     - Apply row-level security filters
   Output: Query (possibly modified or expanded to multiple queries)

4. OPTIMIZE PHASE (Phase 1: Paths)
   Input:  Query { rtable: [...], conditions: [x > 5], ... }
   Process:
     - RelOptInfo for "table" created
     - Generate Paths:
       * SeqScan Path (read all rows)
       * IndexScan Path (if index on x exists)
     - Estimate costs based on stats
     - Choose best Path (likely IndexScan if x > 5 is selective)
   Output: Path tree with costs

5. OPTIMIZE PHASE (Phase 2: Plans)
   Input:  Path tree (best SeqScan or IndexScan)
   Process:
     - Convert Path to Plan node
     - Attach output columns (a, b)
   Output: Plan tree:
     SeqScan {
       relationName: "table",
       targetList: [Var(a), Var(b)],
       filter: (x > 5)
     }

6. EXECUTOR INIT PHASE (Executor → Init)
   Input:  Plan tree
   Process:
     - ExecInitNode called recursively on plan tree
     - For SeqScan: creates SeqScanState with scan iterator
     - Sets SeqScanState->ExecProcNode = ExecSeqScan
   Output: PlanState tree with function pointers set

7. EXECUTOR RUN PHASE (Executor → Run)
   Process:
     for tuple_count > 0:
       slot = ExecProcNode(top_planstate)  // Call ExecSeqScan
       if slot is NULL: break
       tuple = extract_tuple(slot)
       send_to_client(tuple)

   Inside ExecSeqScan():
     - Read next page from buffer manager
     - Extract next tuple matching filter (x > 5)
     - Return tuple in TupleTableSlot or NULL when done

8. Output: Result tuples sent to client
```

### Interface Contracts Between Components

| Stage | Function | Input | Output | Invariants |
|-------|----------|-------|--------|-----------|
| Parser | `raw_parser()` | SQL string | `List<RawStmt>` | No semantic checking; may contain invalid tables/columns |
| Analyzer | `parse_analyze_fixedparams()` | `RawStmt` | `Query` | All names resolved; types checked; references valid |
| Rewriter | `pg_rewrite_query()` | `Query` | `List<Query>` | May expand to multiple queries; maintains semantic equivalence |
| Optimizer | `planner()` | `Query` | `PlannedStmt` | Plan is executable; all Paths explored and best selected |
| Executor | `ExecutorStart()` | `PlannedStmt` | `PlanState` | PlanState tree ready for iteration; ExecProcNode pointers set |
| Executor | `ExecProcNode()` | `PlanState` | `TupleTableSlot` | Tuple or NULL; called repeatedly until NULL |

---

## Summary

PostgreSQL's query execution pipeline is a sophisticated multi-stage system implementing classical compilation and execution architecture patterns. The **pipeline/dataflow design** organizes processing into well-separated stages (parse, analyze, rewrite, optimize, execute), each with clean input/output interfaces and well-defined intermediate representations (RawStmt → Query → PlannedStmt → tuples).

The **two-phase optimization** (path generation in allpaths.c + plan creation in createplan.c) cleanly separates logical optimization (which strategies are possible?) from physical optimization (which strategy is fastest?). This enables cost-based selection while maintaining code modularity and extensibility.

The **Volcano/iterator execution model** combined with **hybrid static/dynamic dispatch** achieves both simplicity and performance: initialization uses a switch statement for optimal startup, while execution uses function pointers for minimal per-tuple overhead and natural pipelining through the plan tree. The 40+ executor node types (scans, joins, aggregation, sorting, etc.) all follow this pattern, making it easy to add new node types without modifying core executor logic.