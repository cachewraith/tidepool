# Tidepool shell setup. install.sh adds one line to ~/.bashrc that sources this file.
# Prompt: starship. Colors follow the active theme (see ~/.config/tidepool/current).

[[ $- == *i* ]] || return 0

TP_STATE="${XDG_CONFIG_HOME:-$HOME/.config}/tidepool"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

# History: big, shared across terminals, no duplicates
HISTSIZE=100000
HISTFILESIZE=200000
HISTCONTROL=ignoreboth:erasedups
HISTTIMEFORMAT="%F %T  "
shopt -s histappend checkwinsize cdspell dirspell autocd globstar nocaseglob
PROMPT_COMMAND="history -a${PROMPT_COMMAND:+; $PROMPT_COMMAND}"

# Completion
if [[ -f /usr/share/bash-completion/bash_completion ]]; then
  source /usr/share/bash-completion/bash_completion
fi
bind 'set completion-ignore-case on'
bind 'set show-all-if-ambiguous on'
bind 'set colored-stats on'
bind 'set colored-completion-prefix on'
bind 'set mark-symlinked-directories on'
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Editor
if command -v nvim >/dev/null 2>&1; then export EDITOR=nvim VISUAL=nvim; fi

# Nicer core tools, only when installed
if command -v eza >/dev/null 2>&1; then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -l --icons --group-directories-first --git --header'
  alias la='eza -la --icons --group-directories-first --git --header'
  alias lt='eza --tree --level=2 --icons --group-directories-first'
else
  alias ls='ls --color=auto --group-directories-first'
  alias ll='ls -lh'
  alias la='ls -lah'
fi
if command -v bat >/dev/null 2>&1; then
  alias cat='bat --paging=never --style=plain'
  export MANPAGER="sh -c 'col -bx | bat -l man -p'"
fi
alias grep='grep --color=auto'
alias diff='diff --color=auto'
alias ip='ip -color=auto'
alias ..='cd ..'
alias ...='cd ../..'

# Git
alias gs='git status -sb'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gd='git diff'
alias gsw='git switch'
alias gl='git log --graph --oneline --decorate -20'

# Docker, PHP, Node
alias d='docker'
alias dc='docker compose'
alias dcu='docker compose up -d'
alias dcd='docker compose down'
alias dcl='docker compose logs -f'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias art='php artisan'
alias pn='pnpm'

# System
alias ff='fastfetch'
alias update='sudo pacman -Syu'
alias ports='ss -tulpn'
alias myip='curl -s ifconfig.me; echo'
alias cls='clear'

# Tidepool
alias theme='tp-theme'
alias themes='tp-theme list'
alias game='tp-gamemode toggle'
alias mc='tp-mc'

mkcd() { mkdir -p -- "$1" && cd -- "$1" || return; }

serve() { python -m http.server "${1:-8000}"; }

# Fuzzy cd into any folder below the current one
fcd() {
  local dir
  dir="$(find "${1:-.}" -type d -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | fzf)" && cd "$dir" || return
}

extract() {
  [[ -f "$1" ]] || { echo "extract: $1 is not a file" >&2; return 1; }
  case "$1" in
    *.tar.bz2|*.tbz2) tar xjf "$1" ;;
    *.tar.gz|*.tgz)   tar xzf "$1" ;;
    *.tar.xz)         tar xJf "$1" ;;
    *.tar.zst)        tar --zstd -xf "$1" ;;
    *.tar)            tar xf "$1" ;;
    *.zip)            unzip "$1" ;;
    *.gz)             gunzip "$1" ;;
    *.7z)             7z x "$1" ;;
    *)                echo "extract: unknown archive type: $1" >&2; return 1 ;;
  esac
}

# fzf: theme colors first, then key bindings (Ctrl+R history, Ctrl+T files, Alt+C folders)
[[ -f "$TP_STATE/current/fzf.sh" ]] && source "$TP_STATE/current/fzf.sh"
if command -v fzf >/dev/null 2>&1; then eval "$(fzf --bash 2>/dev/null)"; fi

# zoxide: `z foo` jumps to the folder you use most that matches foo
if command -v zoxide >/dev/null 2>&1; then eval "$(zoxide init bash)"; fi

# Prompt
export STARSHIP_CONFIG="$TP_STATE/current/starship.toml"
if command -v starship >/dev/null 2>&1; then eval "$(starship init bash)"; fi
