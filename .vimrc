" In $HOME/vimrc write: source $HOME/usr/bin/.vimrc
"color evening"
filetype plugin indent on
syntax on
highlight Normal guibg=black guifg=white
set autoindent "automatic smart indentation"
"set nofoldenable to prevent annoying folding"
nnoremap Q <nop> "Never accidentally enter stupid ex mode ever again"
set wildignore+=*.exe,*.o,*.chk,*.rkf "ignore certain files when :vs or :sp"
set expandtab "affects the TAB character"
set shiftwidth=2 "affects automatic indentation"
set softtabstop=2 "affects the TAB character"
set background=dark "set appropriate colors for a dark background"
set ignorecase "ignore case during search"
set smartcase "overrides ignorecase if searching with uppercase letters"
set nolist  "list disables linebreak
set ruler "shows the line and column number in the lower-right corner"
set hlsearch "highlights searched strings in a text"
"set nowrap prevents linebreak for long lines when visualizing a file"
set splitright "vertical split on the right instead of left"
set textwidth=0 "prevent linebreak"
set wrapmargin=0 "prevent linebreak"
set wrap
set linebreak
if &diff 
  if expand('%.e') == "F"
    "diff mode ignore whitespace"
    set diffopt+=iwhite
  endif
endif
command W w
command Q q
command Qa qa
command QA qa
command WQ wq
command Wq wq
command Vs vs
command VS vs
if filereadable($HOME."/.tags")
  "look for the .tags file"
  set tags=~/.tags
  "make ctags open routines as new vertical splits with Ctrl+\"
  map <C-\> :vsp <CR>:exec("tag ".expand("<cword>"))<CR>
endif
"Automatically execute commands for certain file types"
autocmd FileType python setlocal shiftwidth=4 softtabstop=4
autocmd BufEnter,BufNew *.f90 setlocal shiftwidth=3 softtabstop=3 diffopt+=iwhiteall
autocmd BufEnter,BufNew *.in  setlocal shiftwidth=2 softtabstop=2
autocmd BufEnter,BufNew *.run set syntax=sh
