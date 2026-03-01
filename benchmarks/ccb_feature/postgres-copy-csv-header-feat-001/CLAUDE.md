# postgres-copy-csv-header-feat-001: COPY FROM WITH HEADER MATCH

## Task Type: Feature Implementation (SQL Command Extension)

Implement HEADER MATCH option for PostgreSQL COPY FROM CSV.

## Key Reference Files
- `src/backend/parser/gram.y` — SQL grammar (search for `copy_opt_list`, `HEADER`)
- `src/backend/commands/copy.c` — COPY entry point and option processing
- `src/backend/commands/copyfrom.c` — COPY FROM reader implementation
- `src/include/commands/copy.h` — CopyHeaderChoice enum, CopyFormatOptions struct
- `src/test/regress/sql/copy.sql` — existing regression tests

## Search Strategy
- Search for `CopyHeaderChoice` to find the enum defining header behavior
- Search for `header_line` in copyfrom.c to find where the header row is read/skipped
- Search for `copy_opt_list` in gram.y to find the grammar rule for COPY options
- Search for `attname` or `NameStr` in copyfrom.c for column name access patterns
