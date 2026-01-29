# Nix-Manager Search & Sorting Fixes - Implementation Plan

## Overview

Fix two issues in the nix-manager TUI:
1. Search functionality not working
2. Add 3-mode sorting: `name` → `status-asc` → `status-desc`

## Current State Analysis

### Search Implementation
- `SearchInput.tsx:51-61`: Uses OpenTUI `<input>` with `focused` prop
- `App.tsx:240-243`: `/` key enters search mode
- `App.tsx:157-161`: `handleSearchSubmit` commits query on Enter
- **Issue**: Unknown - appears correctly implemented per OpenTUI docs

### Sorting Implementation
- `App.tsx:19`: `type SortMode = "name" | "status"`
- `App.tsx:245-249`: `s` key toggles between 2 modes
- `App.tsx:119-131`: Sort logic - status mode shows synced→missing→extra

## Desired End State

1. **Search**: Typing in search mode filters packages in real-time
2. **Sorting**: 3 modes cycling: `name` (A-Z) → `status-asc` (synced first) → `status-desc` (missing first)
3. **UI**: StatusBar shows current sort mode with direction indicator

## What We're NOT Doing

- Adding new search features (fuzzy matching, regex)
- Changing the search UX flow
- Adding 4th sort mode (Z-A name)

## Implementation Approach

Debug search first, then implement 3-mode sorting.

---

## Phase 1: Debug & Fix Search

### Overview
Investigate and fix the search input not capturing keystrokes.

### Changes Required:

#### 1. Verify search works or identify the issue

**File**: `apps/nix-manager/src/components/SearchInput.tsx`

**Investigation**: Check if the `<input>` component receives focus and fires `onChange`. Potential issues:
- Missing keyboard event propagation
- `useKeyboard` hook in App.tsx intercepting keys before input receives them

**Likely Fix**: The `useKeyboard` in `App.tsx:171` may be capturing all keyboard events. When in search mode, it returns early (`App.tsx:184-186`), but the hook might still consume events.

**Changes**:
1. Test if search actually works (may be user error)
2. If broken: Check if input is receiving focus
3. Consider if App's `useKeyboard` interferes with input events

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles without errors

#### Manual Verification:
- [ ] Press `/` to enter search mode
- [ ] Type characters and see them appear in input
- [ ] Press Enter and see filtered results
- [ ] Press Escape to clear filter

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding to the next phase.

---

## Phase 2: Implement 3-Mode Sorting

### Overview
Change sort from 2-mode toggle to 3-mode cycle: name → status-asc → status-desc

### Changes Required:

#### 1. Update SortMode Type

**File**: `apps/nix-manager/src/App.tsx`
**Line**: 19

```typescript
// Before
type SortMode = "name" | "status"

// After
type SortMode = "name" | "status-asc" | "status-desc"
```

#### 2. Update Sort Toggle Logic

**File**: `apps/nix-manager/src/App.tsx`
**Lines**: 245-249

```typescript
// Before
case "s":
  setSortMode((m) => (m === "name" ? "status" : "name"))
  setSelectedIndex(0)
  break

// After
case "s":
  setSortMode((m) => {
    if (m === "name") return "status-asc"
    if (m === "status-asc") return "status-desc"
    return "name"
  })
  setSelectedIndex(0)
  break
```

#### 3. Update Sort Implementation

**File**: `apps/nix-manager/src/App.tsx`
**Lines**: 119-131

```typescript
// Before
if (sortMode === "status") {
  const statusOrder: Record<string, number> = { synced: 0, missing: 1, extra: 2 }
  result.sort((a, b) => {
    const statusDiff = statusOrder[a.status] - statusOrder[b.status]
    if (statusDiff !== 0) return statusDiff
    return a.name.localeCompare(b.name)
  })
} else {
  result.sort((a, b) => a.name.localeCompare(b.name))
}

// After
if (sortMode === "status-asc") {
  // Synced first, then extra, then missing
  const statusOrder: Record<string, number> = { synced: 0, extra: 1, missing: 2 }
  result.sort((a, b) => {
    const statusDiff = statusOrder[a.status] - statusOrder[b.status]
    if (statusDiff !== 0) return statusDiff
    return a.name.localeCompare(b.name)
  })
} else if (sortMode === "status-desc") {
  // Missing first, then extra, then synced
  const statusOrder: Record<string, number> = { missing: 0, extra: 1, synced: 2 }
  result.sort((a, b) => {
    const statusDiff = statusOrder[a.status] - statusOrder[b.status]
    if (statusDiff !== 0) return statusDiff
    return a.name.localeCompare(b.name)
  })
} else {
  // Name (alphabetical)
  result.sort((a, b) => a.name.localeCompare(b.name))
}
```

#### 4. Update StatusBar Type & Display

**File**: `apps/nix-manager/src/components/StatusBar.tsx`
**Line**: 6

```typescript
// Before
type SortMode = "name" | "status"

// After
type SortMode = "name" | "status-asc" | "status-desc"
```

**Line**: 83

```typescript
// Before
<span fg={colors.blue}>{sortMode === "name" ? "Name" : "Status"}</span>

// After
<span fg={colors.blue}>
  {sortMode === "name" ? "Name" : sortMode === "status-asc" ? "Status ↑" : "Status ↓"}
</span>
```

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles without errors

#### Manual Verification:
- [ ] Press `s` once → shows "Status ↑" with synced packages first
- [ ] Press `s` again → shows "Status ↓" with missing packages first  
- [ ] Press `s` again → shows "Name" with alphabetical order
- [ ] Cycle continues correctly

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding.

---

## Testing Strategy

### Manual Testing Steps:

1. **Search Test**:
   - Run `nix-manager`
   - Press `/`
   - Type "git"
   - Verify input shows "git"
   - Press Enter
   - Verify list shows only packages containing "git"
   - Press Escape
   - Verify filter clears

2. **Sort Test**:
   - Start in "Name" mode (alphabetical)
   - Press `s` → "Status ↑" (synced first, then extra, then missing)
   - Press `s` → "Status ↓" (missing first, then extra, then synced)
   - Press `s` → "Name" (back to alphabetical)

## References

- OpenTUI input docs: `.opencode/skill/opentui/references/components/inputs.md`
- App.tsx search/sort: `apps/nix-manager/src/App.tsx:119-131, 157-168, 240-249`
- SearchInput: `apps/nix-manager/src/components/SearchInput.tsx`
- StatusBar sort display: `apps/nix-manager/src/components/StatusBar.tsx:82-83`
