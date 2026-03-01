# vscode-custom-fold-region-feat-001: Named Folding Regions with Navigation

## Task Type: Feature Implementation (Editor Feature)

Implement custom named folding regions with quick-pick navigation in VS Code.

## Key Reference Files
- `src/vs/editor/contrib/folding/browser/folding.ts` — main folding contribution
- `src/vs/editor/contrib/folding/browser/foldingRanges.ts` — FoldingRanges data structure
- `src/vs/editor/contrib/folding/browser/indentRangeProvider.ts` — reference range provider
- `src/vs/editor/contrib/gotoSymbol/browser/goToCommands.ts` — navigation command pattern
- `src/vs/platform/quickinput/common/quickInput.ts` — QuickInput service interface

## Search Strategy
- Search for `FoldingRangeProvider` to understand the provider extension point
- Search for `#region` in folding/ to find existing region marker handling
- Search for `registerEditorAction` in contrib/ to find command registration patterns
- Search for `IQuickInputService` to understand quick-pick integration
- Use `find_references` on `FoldingRanges` to see how ranges feed into the editor
