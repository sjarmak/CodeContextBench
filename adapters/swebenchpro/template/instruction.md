# Task

{problem_statement}

---

**Repo:** `{repo}`
**Base commit:** `{base_commit}`
**Instance ID:** `{instance_id}`
**Language:** `{repo_language}`

---

## ⚠️ CRITICAL: This is an implementation task ⚠️

**MANDATORY FIRST STEP - DO THIS BEFORE ANYTHING ELSE:**

🚨 RUN THE TEST SUITE FIRST - DO NOT EDIT ANY FILES UNTIL YOU RUN THE TESTS! 🚨

The problem statement above describes a bug or feature request from a real GitHub issue. Your job is to **implement the code changes** that resolve it, NOT to explore or explain the codebase.

**STRICT WORKFLOW - FOLLOW THIS ORDER:**

**STEP 1 (MANDATORY): RUN TESTS BEFORE ANY EDITS**
   - Find the test command for this project (usually: `go test ./...`, `pytest`, `npm test`, etc.)
   - Run ALL tests to see which ones fail
   - Read the test COMPILATION errors and FAILURE messages carefully
   - These errors tell you EXACTLY what interface, methods, and types to implement
   - ❌ DO NOT EDIT ANY CODE FILES YET ❌

**STEP 2: Read the test files**
   - Examine what the tests actually call and expect
   - Note exact method names, types, and signatures from test code
   - If tests call `cache.Delete()`, you must implement `Delete()` not `Remove()` or any synonym

**STEP 3: Identify files that need changes**
   - Explore the codebase to find relevant source files

**STEP 4: Implement the fix**
   - NOW you can edit source files
   - Match the EXACT interface the tests expect (method names, types, etc.)
   - The tests define the contract - implement exactly what they call

**STEP 5: Run tests again to verify**
   - Tests must compile AND pass
   - If they fail, read errors carefully and iterate until they pass

**WHY THIS ORDER MATTERS:**
Tests define the contract. If you implement code BEFORE running tests, you will guess wrong about method names and interfaces, causing compilation failures.

**Critical rules:**
- ❌ DO NOT edit source files before running tests
- ❌ DO NOT stop after exploring - you MUST implement code changes
- ❌ DO NOT invent new names - use EXACT names from test code
- ✅ DO run tests FIRST to discover the expected interface
- ✅ DO run tests AFTER to verify your implementation
