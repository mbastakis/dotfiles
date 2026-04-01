" Free space from its default binding so it can be used as a prefix key
unmap <Space>

" Ctrl+a tmux-style prefix using jscommand to intercept next keypress
" Requires "Support JS Commands" enabled in Vimrc Support plugin settings
exmap tmuxPrefix jscommand { const app = this.app; const handler = (e) => { document.removeEventListener('keydown', handler, true); e.preventDefault(); e.stopPropagation(); if (e.key === 'h') { app.commands.executeCommandById('workspace:split-vertical'); } else if (e.key === 'v') { app.commands.executeCommandById('workspace:split-horizontal'); } }; document.addEventListener('keydown', handler, true); }
nmap <C-a> :tmuxPrefix<CR>

" Toggle left sidebar
exmap toggleLeftSidebar obcommand app:toggle-left-sidebar
nmap <Space>e :toggleLeftSidebar<CR>

" Toggle source control view
exmap toggleSourceControl obcommand obsidian-git:open-git-view
nmap <Space>gg :toggleSourceControl<CR>

" Navigate back/forward through file history
exmap goBack obcommand app:go-back
nmap <C-o> :goBack<CR>
exmap goForward obcommand app:go-forward
nmap <C-i> :goForward<CR>

" Follow link under cursor
exmap followLink obcommand editor:follow-link
nmap <CR> :followLink<CR>

" Navigate between panes
exmap focusLeft obcommand editor:focus-left
exmap focusDown obcommand editor:focus-bottom
exmap focusUp obcommand editor:focus-top
exmap focusRight obcommand editor:focus-right
nmap <C-h> :focusLeft<CR>
nmap <C-j> :focusDown<CR>
nmap <C-k> :focusUp<CR>
nmap <C-l> :focusRight<CR>

" Folding (vim-native keybinds)
exmap toggleFold obcommand editor:toggle-fold
exmap foldAll obcommand editor:fold-all
exmap unfoldAll obcommand editor:unfold-all
exmap foldMore obcommand editor:fold-more
exmap foldLess obcommand editor:fold-less
nmap za :toggleFold<CR>
nmap zc :foldMore<CR>
nmap zo :foldLess<CR>
nmap zM :foldAll<CR>
nmap zR :unfoldAll<CR>

" Fold-aware j/k navigation (fixes Anuppuccin theme unfolding on move)
exmap downSkipFold jsfile .obsidian/mdHelpers.js {moveDownSkipFold()}
exmap upSkipFold jsfile .obsidian/mdHelpers.js {moveUpSkipFold()}
nmap j :downSkipFold<CR>
nmap k :upSkipFold<CR>
nmap <Down> :downSkipFold<CR>
nmap <Up> :upSkipFold<CR>
