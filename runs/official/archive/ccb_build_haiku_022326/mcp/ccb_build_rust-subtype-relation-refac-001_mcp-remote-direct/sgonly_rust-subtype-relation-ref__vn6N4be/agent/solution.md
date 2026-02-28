# Refactoring: Rename SubtypePredicate to SubtypeRelation

## Executive Summary

This document describes a comprehensive refactoring to rename the `SubtypePredicate` struct to `SubtypeRelation` and its fields `a`/`b` to `sub_ty`/`super_ty` throughout the Rust compiler codebase. The refactoring improves semantic clarity by using descriptive field names instead of opaque `a` and `b`.

## Files Examined

### Core Definitions
- **compiler/rustc_type_ir/src/predicate.rs** — Primary definition of `SubtypePredicate<I: Interner>` struct with fields `a_is_expected`, `a`, and `b`
- **compiler/rustc_public/src/ty.rs** — Public-facing definition of `SubtypePredicate` struct for the stable API
- **compiler/rustc_type_ir/src/predicate_kind.rs** — Enum `PredicateKind<I>` contains variant `Subtype(ty::SubtypePredicate<I>)` at line 78

### Type Aliases & Re-exports
- **compiler/rustc_middle/src/ty/predicate.rs** — Type aliases `SubtypePredicate<'tcx>` and `PolySubtypePredicate<'tcx>`
- **compiler/rustc_middle/src/ty/mod.rs** — Public re-exports of `SubtypePredicate` and `PolySubtypePredicate`

### Trait Bounds & Printing
- **compiler/rustc_type_ir/src/interner.rs** — IrPrint trait bound `IrPrint<ty::SubtypePredicate<Self>>` at line 31
- **compiler/rustc_type_ir/src/ir_print.rs** — Imports `SubtypePredicate` in lines 6, 54
- **compiler/rustc_middle/src/ty/print/pretty.rs** — Print implementation using `.a` and `.b` fields at lines 3257-3261

### Construction Sites (Struct Literals)
- **compiler/rustc_infer/src/infer/mod.rs** — Creates `SubtypePredicate { a_is_expected, a, b }` at lines 719-722 and destructures at line 756
- **compiler/rustc_next_trait_solver/src/solve/mod.rs** — Creates `SubtypePredicate { a_is_expected, a, b }` at lines 112-115 and reads fields at lines 122, 128
- **compiler/rustc_type_ir/src/relate/solver_relating.rs** — Creates `PredicateKind::Subtype(SubtypePredicate { ... })` at lines 200-202, 213-215, 141-143, 154-157

### Destructuring/Pattern Matching Sites
- **compiler/rustc_infer/src/infer/mod.rs** — Pattern match at line 756: `|ty::SubtypePredicate { a_is_expected, a, b }|`, field access at lines 746-747
- **compiler/rustc_type_ir/src/flags.rs** — Pattern match at line 394: `ty::PredicateKind::Subtype(ty::SubtypePredicate { a_is_expected: _, a, b })`
- **compiler/rustc_hir_typeck/src/fallback.rs** — Pattern match at line 353: `ty::PredicateKind::Subtype(ty::SubtypePredicate { a_is_expected: _, a, b })`
- **compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs** — Pattern match at line 93: `ty::PredicateKind::Subtype(ty::SubtypePredicate { a, b, a_is_expected: _ })`
- **compiler/rustc_trait_selection/src/solve/delegate.rs** — Pattern match at line 127: `ty::PredicateKind::Subtype(ty::SubtypePredicate { a, b, .. })`
- **compiler/rustc_trait_selection/src/error_reporting/traits/ambiguity.rs** — Pattern match at line 503: `ty::SubtypePredicate { a_is_expected: _, a, b }`

### Stable API & Conversion
- **compiler/rustc_public/src/unstable/convert/stable/ty.rs** — Stable trait implementation for `SubtypePredicate<'tcx>` at lines 779-788, destructures at line 787

### Test Files
- **tests/rustdoc-js/auxiliary/interner.rs** — Test interner with `SubtypePredicate` associated type

### Rust Analyzer Integration
- **src/tools/rust-analyzer/crates/hir-ty/src/next_solver/predicate.rs** — Type aliases for `SubtypePredicate<'db>` and `PolySubtypePredicate<'db>` at lines 33, 40
- **src/tools/rust-analyzer/crates/hir-ty/src/next_solver/infer/mod.rs** — May reference SubtypePredicate indirectly
- **src/tools/rust-analyzer/crates/hir-ty/src/next_solver/ir_print.rs** — IrPrint implementation for `SubtypePredicate<Self>` at lines 190-196

## Dependency Chain

```
1. DEFINITION (lowest level)
   └─ compiler/rustc_type_ir/src/predicate.rs
      Defines: struct SubtypePredicate<I: Interner> { a_is_expected, a, b }
      Type: generic over Interner trait

2. STABLE API
   └─ compiler/rustc_public/src/ty.rs
      Defines: struct SubtypePredicate { a, b } (simplified public version)
      Re-exports: PredicateKind enum variant SubType(SubtypePredicate)

3. TYPE ALIASES
   ├─ compiler/rustc_middle/src/ty/predicate.rs
   │  Aliases: SubtypePredicate<'tcx>, PolySubtypePredicate<'tcx>
   │  Used in: all rustc_middle and higher-level crates
   │
   └─ compiler/rustc_public/src/unstable/convert/stable/ty.rs
      Conversion: ir::SubtypePredicate<TyCtxt<'tcx>> → crate::ty::SubtypePredicate

4. TRAIT BOUNDS & PRINTING
   ├─ compiler/rustc_type_ir/src/interner.rs
   │  Trait: IrPrint<ty::SubtypePredicate<Self>> bound on Interner
   │
   ├─ compiler/rustc_type_ir/src/ir_print.rs
   │  Imports and re-exports SubtypePredicate in trait definitions
   │
   └─ compiler/rustc_middle/src/ty/print/pretty.rs
      Impl: Display implementation that uses .a and .b fields

5. HIGH-LEVEL RE-EXPORTS
   └─ compiler/rustc_middle/src/ty/mod.rs
      Re-exports: SubtypePredicate, PolySubtypePredicate from ::predicate module

6. USAGE IN INFERENCE
   ├─ compiler/rustc_infer/src/infer/mod.rs
   │  - Line 719: Creates SubtypePredicate from CoercePredicate
   │  - Line 746-747: Accesses .a and .b fields
   │  - Line 756: Pattern matches and destructures
   │
   ├─ compiler/rustc_next_trait_solver/src/solve/mod.rs
   │  - Line 112-115: Creates SubtypePredicate
   │  - Line 122: Accesses .a and .b via goal.predicate.a
   │  - Line 128: Accesses .a and .b for sub operation
   │
   └─ compiler/rustc_type_ir/src/relate/solver_relating.rs
      - Lines 200-202, 213-215, 141-143, 154-157: Creates PredicateKind::Subtype(SubtypePredicate)

7. USAGE IN TYPE CHECKING
   ├─ compiler/rustc_hir_typeck/src/fallback.rs
   │  - Line 353: Pattern matches on Subtype variant and accesses .a, .b
   │
   └─ compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs
      - Line 93: Pattern matches on Subtype variant

8. USAGE IN TRAIT SELECTION
   ├─ compiler/rustc_trait_selection/src/error_reporting/traits/ambiguity.rs
   │  - Line 503: Pattern matches and destructures
   │
   ├─ compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs
   │  - Line 93: Pattern matches
   │
   └─ compiler/rustc_trait_selection/src/solve/delegate.rs
      - Line 127: Pattern matches

9. RUST ANALYZER COMPATIBILITY
   ├─ src/tools/rust-analyzer/crates/hir-ty/src/next_solver/predicate.rs
   │  Type aliases for compatibility
   │
   └─ src/tools/rust-analyzer/crates/hir-ty/src/next_solver/ir_print.rs
      IrPrint implementation
```

## Code Changes

### 1. compiler/rustc_type_ir/src/predicate.rs

**Current (lines 918-922):**
```rust
pub struct SubtypePredicate<I: Interner> {
    pub a_is_expected: bool,
    pub a: I::Ty,
    pub b: I::Ty,
}
```

**Updated:**
```rust
pub struct SubtypeRelation<I: Interner> {
    pub a_is_expected: bool,
    pub sub_ty: I::Ty,
    pub super_ty: I::Ty,
}
```

**Also update line 924:**
```rust
// FROM:
impl<I: Interner> Eq for SubtypePredicate<I> {}

// TO:
impl<I: Interner> Eq for SubtypeRelation<I> {}
```

### 2. compiler/rustc_public/src/ty.rs

**Current (lines 1511-1514):**
```rust
pub struct SubtypePredicate {
    pub a: Ty,
    pub b: Ty,
}
```

**Updated:**
```rust
pub struct SubtypeRelation {
    pub sub_ty: Ty,
    pub super_ty: Ty,
}
```

**Also update line 1485 in PredicateKind enum:**
```rust
// FROM:
SubType(SubtypePredicate),

// TO:
SubType(SubtypeRelation),
```

### 3. compiler/rustc_middle/src/ty/predicate.rs

**Current (lines 23-24):**
```rust
pub type CoercePredicate<'tcx> = ir::CoercePredicate<TyCtxt<'tcx>>;
pub type SubtypePredicate<'tcx> = ir::SubtypePredicate<TyCtxt<'tcx>>;
```

**Updated:**
```rust
pub type CoercePredicate<'tcx> = ir::CoercePredicate<TyCtxt<'tcx>>;
pub type SubtypeRelation<'tcx> = ir::SubtypeRelation<TyCtxt<'tcx>>;
```

**Also update line 32:**
```rust
// FROM:
pub type PolySubtypePredicate<'tcx> = ty::Binder<'tcx, SubtypePredicate<'tcx>>;

// TO:
pub type PolySubtypeRelation<'tcx> = ty::Binder<'tcx, SubtypeRelation<'tcx>>;
```

### 4. compiler/rustc_middle/src/ty/mod.rs

**Current (lines 91-94):**
```rust
    PolyExistentialPredicate, PolyExistentialProjection, PolyExistentialTraitRef,
    PolyProjectionPredicate, PolyRegionOutlivesPredicate, PolySubtypePredicate, PolyTraitPredicate,
    PolyTraitRef, PolyTypeOutlivesPredicate, Predicate, PredicateKind, ProjectionPredicate,
    RegionOutlivesPredicate, SubtypePredicate, TraitPredicate, TraitRef, TypeOutlivesPredicate,
```

**Updated:**
```rust
    PolyExistentialPredicate, PolyExistentialProjection, PolyExistentialTraitRef,
    PolyProjectionPredicate, PolyRegionOutlivesPredicate, PolySubtypeRelation, PolyTraitPredicate,
    PolyTraitRef, PolyTypeOutlivesPredicate, Predicate, PredicateKind, ProjectionPredicate,
    RegionOutlivesPredicate, SubtypeRelation, TraitPredicate, TraitRef, TypeOutlivesPredicate,
```

**Note:** Keep backward-compatibility aliases for now:
```rust
pub type SubtypePredicate<'tcx> = SubtypeRelation<'tcx>;
pub type PolySubtypePredicate<'tcx> = PolySubtypeRelation<'tcx>;
```

### 5. compiler/rustc_type_ir/src/interner.rs

**Current (lines 30-32):**
```rust
    + IrPrint<ty::NormalizesTo<Self>>
    + IrPrint<ty::SubtypePredicate<Self>>
    + IrPrint<ty::CoercePredicate<Self>>
```

**Updated:**
```rust
    + IrPrint<ty::NormalizesTo<Self>>
    + IrPrint<ty::SubtypeRelation<Self>>
    + IrPrint<ty::CoercePredicate<Self>>
```

### 6. compiler/rustc_type_ir/src/ir_print.rs

**Current (lines 6, 54):**
```rust
    PatternKind, ProjectionPredicate, SubtypePredicate, TraitPredicate, TraitRef, UnevaluatedConst,
...
    SubtypePredicate,
```

**Updated:**
```rust
    PatternKind, ProjectionPredicate, SubtypeRelation, TraitPredicate, TraitRef, UnevaluatedConst,
...
    SubtypeRelation,
```

### 7. compiler/rustc_infer/src/infer/mod.rs

**Current (lines 719-723):**
```rust
let subtype_predicate = predicate.map_bound(|p| ty::SubtypePredicate {
    a_is_expected: false, // when coercing from `a` to `b`, `b` is expected
    a: p.a,
    b: p.b,
});
```

**Updated:**
```rust
let subtype_predicate = predicate.map_bound(|p| ty::SubtypeRelation {
    a_is_expected: false, // when coercing from `a` to `b`, `b` is expected
    sub_ty: p.sub_ty,
    super_ty: p.super_ty,
});
```

**Current (lines 746-747):**
```rust
let r_a = self.shallow_resolve(predicate.skip_binder().a);
let r_b = self.shallow_resolve(predicate.skip_binder().b);
```

**Updated:**
```rust
let r_a = self.shallow_resolve(predicate.skip_binder().sub_ty);
let r_b = self.shallow_resolve(predicate.skip_binder().super_ty);
```

**Current (line 756):**
```rust
self.enter_forall(predicate, |ty::SubtypePredicate { a_is_expected, a, b }| {
    if a_is_expected {
        Ok(self.at(cause, param_env).sub(DefineOpaqueTypes::Yes, a, b))
    } else {
        Ok(self.at(cause, param_env).sup(DefineOpaqueTypes::Yes, b, a))
    }
})
```

**Updated:**
```rust
self.enter_forall(predicate, |ty::SubtypeRelation { a_is_expected, sub_ty, super_ty }| {
    if a_is_expected {
        Ok(self.at(cause, param_env).sub(DefineOpaqueTypes::Yes, sub_ty, super_ty))
    } else {
        Ok(self.at(cause, param_env).sup(DefineOpaqueTypes::Yes, super_ty, sub_ty))
    }
})
```

### 8. compiler/rustc_next_trait_solver/src/solve/mod.rs

**Current (lines 112-115):**
```rust
predicate: ty::SubtypePredicate {
    a_is_expected: false,
    a: goal.predicate.a,
    b: goal.predicate.b,
```

**Updated:**
```rust
predicate: ty::SubtypeRelation {
    a_is_expected: false,
    sub_ty: goal.predicate.sub_ty,
    super_ty: goal.predicate.super_ty,
```

**Current (lines 121-128):**
```rust
fn compute_subtype_goal(&mut self, goal: Goal<I, ty::SubtypePredicate<I>>) -> QueryResult<I> {
    match (goal.predicate.a.kind(), goal.predicate.b.kind()) {
        ...
        _ => {
            self.sub(goal.param_env, goal.predicate.a, goal.predicate.b)?;
```

**Updated:**
```rust
fn compute_subtype_goal(&mut self, goal: Goal<I, ty::SubtypeRelation<I>>) -> QueryResult<I> {
    match (goal.predicate.sub_ty.kind(), goal.predicate.super_ty.kind()) {
        ...
        _ => {
            self.sub(goal.param_env, goal.predicate.sub_ty, goal.predicate.super_ty)?;
```

### 9. compiler/rustc_type_ir/src/relate/solver_relating.rs

**Current (lines 200-202):**
```rust
ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
    a_is_expected: true,
    a: a,
```

**Updated:**
```rust
ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
    a_is_expected: true,
    sub_ty: a,
```

**Current (lines 213-215):**
```rust
ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
    a_is_expected: false,
    b: b,
```

**Updated:**
```rust
ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
    a_is_expected: false,
    super_ty: b,
```

**Similar changes at lines 141-143 and 154-157**

### 10. compiler/rustc_type_ir/src/flags.rs

**Current (line 394):**
```rust
ty::PredicateKind::Subtype(ty::SubtypePredicate { a_is_expected: _, a, b }) => {
    self.add_ty(a);
    self.add_ty(b);
```

**Updated:**
```rust
ty::PredicateKind::Subtype(ty::SubtypeRelation { a_is_expected: _, sub_ty, super_ty }) => {
    self.add_ty(sub_ty);
    self.add_ty(super_ty);
```

### 11. compiler/rustc_hir_typeck/src/fallback.rs

**Current (lines 353-354):**
```rust
ty::PredicateKind::Subtype(ty::SubtypePredicate { a_is_expected: _, a, b }) => {
    (a, b)
```

**Updated:**
```rust
ty::PredicateKind::Subtype(ty::SubtypeRelation { a_is_expected: _, sub_ty, super_ty }) => {
    (sub_ty, super_ty)
```

### 12. compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs

**Current (lines 93-94):**
```rust
ty::PredicateKind::Subtype(ty::SubtypePredicate { a, b, a_is_expected: _ })
| ty::PredicateKind::Coerce(ty::CoercePredicate { a, b }) => {
```

**Updated:**
```rust
ty::PredicateKind::Subtype(ty::SubtypeRelation { sub_ty, super_ty, a_is_expected: _ })
| ty::PredicateKind::Coerce(ty::CoercePredicate { a, b }) => {
```

### 13. compiler/rustc_trait_selection/src/solve/delegate.rs

**Current (line 127):**
```rust
ty::PredicateKind::Subtype(ty::SubtypePredicate { a, b, .. })
```

**Updated:**
```rust
ty::PredicateKind::Subtype(ty::SubtypeRelation { sub_ty, super_ty, .. })
```

Also update the usage on the following lines that use `a` and `b` to use `sub_ty` and `super_ty`.

### 14. compiler/rustc_trait_selection/src/error_reporting/traits/ambiguity.rs

**Current (line 503):**
```rust
let ty::SubtypePredicate { a_is_expected: _, a, b } = data;
```

**Updated:**
```rust
let ty::SubtypeRelation { a_is_expected: _, sub_ty, super_ty } = data;
```

Also update line 509 that uses `a`:
```rust
// FROM:
a.into(),

// TO:
sub_ty.into(),
```

### 15. compiler/rustc_middle/src/ty/print/pretty.rs

**Current (lines 3257-3261):**
```rust
ty::SubtypePredicate<'tcx> {
    self.a.print(p)?;
    write!(p, " <: ")?;
    p.reset_type_limit();
    self.b.print(p)?;
```

**Updated:**
```rust
ty::SubtypeRelation<'tcx> {
    self.sub_ty.print(p)?;
    write!(p, " <: ")?;
    p.reset_type_limit();
    self.super_ty.print(p)?;
```

### 16. compiler/rustc_public/src/unstable/convert/stable/ty.rs

**Current (lines 779-788):**
```rust
impl<'tcx> Stable<'tcx> for ty::SubtypePredicate<'tcx> {
    type T = crate::ty::SubtypePredicate;

    fn stable(
        &self,
        tables: &mut Tables<'tcx>,
        cx: &CompilerCtxt<'tcx>,
    ) -> Self::T {
        let ty::SubtypePredicate { a, b, a_is_expected: _ } = self;
        crate::ty::SubtypePredicate { a: a.stable(tables, cx), b: b.stable(tables, cx) }
```

**Updated:**
```rust
impl<'tcx> Stable<'tcx> for ty::SubtypeRelation<'tcx> {
    type T = crate::ty::SubtypeRelation;

    fn stable(
        &self,
        tables: &mut Tables<'tcx>,
        cx: &CompilerCtxt<'tcx>,
    ) -> Self::T {
        let ty::SubtypeRelation { sub_ty, super_ty, a_is_expected: _ } = self;
        crate::ty::SubtypeRelation { sub_ty: sub_ty.stable(tables, cx), super_ty: super_ty.stable(tables, cx) }
```

### 17. src/tools/rust-analyzer/crates/hir-ty/src/next_solver/predicate.rs

**Current (lines 33, 40):**
```rust
pub type SubtypePredicate<'db> = ty::SubtypePredicate<DbInterner<'db>>;
...
pub type PolySubtypePredicate<'db> = Binder<'db, SubtypePredicate<'db>>;
```

**Updated:**
```rust
pub type SubtypeRelation<'db> = ty::SubtypeRelation<DbInterner<'db>>;
...
pub type PolySubtypeRelation<'db> = Binder<'db, SubtypeRelation<'db>>;
```

**Also add compatibility aliases:**
```rust
pub type SubtypePredicate<'db> = SubtypeRelation<'db>;
pub type PolySubtypePredicate<'db> = PolySubtypeRelation<'db>;
```

### 18. src/tools/rust-analyzer/crates/hir-ty/src/next_solver/ir_print.rs

**Current (lines 190-196):**
```rust
impl<'db> IrPrint<ty::SubtypePredicate<Self>> for DbInterner<'db> {
    fn print(
        t: &ty::SubtypePredicate<Self>,
        fmt: &mut std::fmt::Formatter<'_>,
    ) -> std::fmt::Result {
        Self::print_debug(t, fmt)
```

**Updated:**
```rust
impl<'db> IrPrint<ty::SubtypeRelation<Self>> for DbInterner<'db> {
    fn print(
        t: &ty::SubtypeRelation<Self>,
        fmt: &mut std::fmt::Formatter<'_>,
    ) -> std::fmt::Result {
        Self::print_debug(t, fmt)
```

### 19. tests/rustdoc-js/auxiliary/interner.rs

**Current:**
```rust
type SubtypePredicate: Copy + Debug + Hash + Eq;
```

**Updated:**
```rust
type SubtypeRelation: Copy + Debug + Hash + Eq;
```

## Summary of Changes by Category

### Struct/Type Definitions (2 files)
- `rustc_type_ir/predicate.rs`: Rename struct + rename fields a→sub_ty, b→super_ty
- `rustc_public/ty.rs`: Rename struct + rename fields a→sub_ty, b→super_ty

### Type Aliases (2 files)
- `rustc_middle/ty/predicate.rs`: Update type aliases, add compatibility aliases
- `rustc-analyzer/hir-ty/next_solver/predicate.rs`: Update type aliases, add compatibility aliases

### Imports/Re-exports (3 files)
- `rustc_middle/ty/mod.rs`: Update re-exports
- `rustc_type_ir/interner.rs`: Update trait bound
- `rustc_type_ir/ir_print.rs`: Update imports

### Construction Sites (3 files)
- `rustc_infer/infer/mod.rs`: 2 construction sites, 2 field accesses, 1 pattern match
- `rustc_next_trait_solver/solve/mod.rs`: 1 construction site, 2 field accesses
- `rustc_type_ir/relate/solver_relating.rs`: 4 construction sites

### Destructuring/Pattern Matching (6 files)
- `rustc_type_ir/flags.rs`: 1 pattern match
- `rustc_hir_typeck/fallback.rs`: 1 pattern match
- `rustc_trait_selection/error_reporting/overflow.rs`: 1 pattern match
- `rustc_trait_selection/solve/delegate.rs`: 1 pattern match
- `rustc_trait_selection/error_reporting/ambiguity.rs`: 1 pattern match + 1 field use
- `rustc_infer/infer/mod.rs`: 1 pattern match

### Print/Display Implementations (2 files)
- `rustc_middle/ty/print/pretty.rs`: Update print impl using .a and .b
- `rustc-analyzer/hir-ty/next_solver/ir_print.rs`: Update impl signature

### Stable API (1 file)
- `rustc_public/unstable/convert/stable/ty.rs`: Update Stable trait impl

## Verification Strategy

After implementing these changes, verify that:

1. **Compilation**: The compiler builds without errors in all affected crates:
   - `cargo build -p rustc_type_ir`
   - `cargo build -p rustc_middle`
   - `cargo build -p rustc_infer`
   - `cargo build -p rustc_trait_selection`
   - `cargo build -p rustc_next_trait_solver`
   - `cargo build -p rustc_hir_typeck`

2. **No Stale References**: Verify no remaining references to old names:
   ```bash
   grep -r "\.a\|\.b" compiler/rustc_*/src --include="*.rs" | grep SubtypePredicate
   grep -r "SubtypePredicate {" compiler/rustc_*/src --include="*.rs" | grep -v "SubtypeRelation"
   ```

3. **Type Safety**: Run type checking on affected modules
4. **Rust Analyzer**: Ensure rust-analyzer changes are compatible
5. **Tests**: Run test suite to ensure behavioral correctness

## Implementation Notes

### Backward Compatibility
- Keep type aliases `SubtypePredicate<'tcx>` and `PolySubtypePredicate<'tcx>` as aliases to the new names for external crates
- The compiler itself uses the new names directly
- Rust Analyzer includes both names for compatibility

### Field Semantics
- `a` → `sub_ty` (the subtype in the relation)
- `b` → `super_ty` (the supertype in the relation)
- `a_is_expected` remains unchanged (indicates whether the subtype is expected, used in error reporting)

### Error Reporting
The semantics of `a_is_expected` remains:
- When true: subtype is expected, supertype is inferred
- When false: supertype is expected, subtype is inferred
This maintains compatibility with error reporting and diagnostics.

## Key Insights

1. **Interner Polymorphism**: The generic `SubtypeRelation<I: Interner>` in `rustc_type_ir` is the source of truth. All other definitions are either aliases or conversions.

2. **PredicateKind Dependency**: The `Subtype` variant in `PredicateKind` enum carries `SubtypeRelation` data. Any code working with predicates indirectly references this type.

3. **Field Access Pattern**: Most usage sites access fields via pattern matching or direct field selection. Field names must match in both pattern matches and struct literals.

4. **Print Implementation**: The pretty printer explicitly accesses `.a` and `.b` to format subtype relations as `A <: B`, which must be updated to use the new field names.

5. **Stable API**: The `rustc_public` crate provides a simplified public version of `SubtypeRelation` without the `a_is_expected` field, which only matters for internal compiler logic.
