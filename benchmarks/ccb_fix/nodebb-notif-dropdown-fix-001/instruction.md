# Fix Notifications and Category Selector Dropdown Issues

**Repository:** NodeBB/NodeBB
**Language:** JavaScript
**Difficulty:** hard

## Problem

In NodeBB v4.4.3, the notifications dropdown and the category selector in topic fork/move modals display inconsistent behavior after recent changes to async loading and dropdown class handling. Notifications load asynchronously, but the dropdown may fail to refresh or toggle correctly when opened. In the fork/move topic modals, the category selector is assigned a `dropup` class, which causes the menu to appear in the wrong place and sometimes behaves inconsistently.

## Key Components

- Notifications dropdown component — async loading and toggle logic
- Category selector in fork/move topic modals — dropdown positioning and `dropup` class handling
- Dropdown class management utilities

## Task

1. Locate the notifications dropdown code and fix the async loading/refresh race condition so the dropdown toggles correctly when opened
2. Locate the category selector in fork/move topic modals and fix the `dropup` class placement issue so menus render with proper positioning
3. Ensure dropdown interaction is stable and consistent across both components
4. Run existing tests to ensure no regressions

## Success Criteria

- Opening the notifications dropdown always displays the latest notifications without UI glitches or race conditions
- Category selector menus in fork/move topic modals render with correct placement and stable interaction
- All existing tests pass

---

**Base commit:** `8fd8079a84d8e71ab02eaa69ef15cb33fcea85c7`
**Instance ID:** `instance_NodeBB__NodeBB-eb49a64974ca844bca061744fb3383f5d13b02ad-vnan`
