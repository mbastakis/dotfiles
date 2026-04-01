// Fold-aware navigation
// Uses Obsidian's native goUp/goDown which respects fold state
// instead of vim's j/k which unfolds sections

function moveUpSkipFold() {
  view.editor.exec('goUp');
}

function moveDownSkipFold() {
  view.editor.exec('goDown');
}
