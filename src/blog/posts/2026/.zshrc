# Oh My Zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME=""
zstyle ':omz:update' mode reminder

plugins=(
  git
  brew
  common-aliases
  z
  colored-man-pages
  colorize
  zsh-syntax-highlighting
  zsh-autosuggestions
)

source $ZSH/oh-my-zsh.sh

# Pure prompt
autoload -U promptinit; promptinit
prompt pure

# Python version manager
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"

# Additional PATH
. "$HOME/.local/bin/env"
export PATH="$HOME/bin:$PATH"

# Aliases
source ~/myaliases.zsh
