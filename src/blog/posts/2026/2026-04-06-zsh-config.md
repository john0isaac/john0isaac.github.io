---
title: "My Terminal Setup with Zsh and Oh My Zsh"
date: 2026-04-06
description: "An overview of my terminal configuration using Zsh and Oh My Zsh, including plugins and aliases that enhance my development workflow on macOS."
categories: [Mac]
tags: [zsh, oh-my-zsh, mac, development, setup]
comments: true
authors:
  - john0isaac
---

My full Zsh configuration for a clean, fast, and productive terminal on macOS.
This covers Oh My Zsh, the Pure prompt, version managers, and custom aliases.

<!-- more -->

## Prerequisites

Install the following with [Homebrew](https://brew.sh/):

```bash
brew install pure zsh-syntax-highlighting zsh-autosuggestions pyenv rbenv
```

Install [Oh My Zsh](https://ohmyz.sh/):

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Install [NVM](https://github.com/nvm-sh/nvm):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

## Login Shell — .zprofile

The [.zprofile](./.zprofile) runs once per login session and sets up Homebrew, NVM, and rbenv.

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

# Ruby version manager
export PATH="$HOME/.rbenv/bin:$PATH"
eval "$(rbenv init -)"
```

## Interactive Shell — .zshrc

The [.zshrc](./.zshrc) runs on every new terminal window.

```bash
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
```

### Plugins

| Plugin                    | What it does                                          |
| ------------------------- | ----------------------------------------------------- |
| `git`                     | Git aliases like `gaa`, `gc`, `gco`, `gd`, `gl`, `gp` |
| `brew`                    | Homebrew completions and aliases                      |
| `common-aliases`          | Shortcuts like `ll`, `la`, `l`                        |
| `z`                       | Jump to frequently used directories by partial name   |
| `colored-man-pages`       | Syntax-highlighted man pages                          |
| `colorize`                | Syntax highlighting for file contents                 |
| `zsh-syntax-highlighting` | Highlights commands as you type                       |
| `zsh-autosuggestions`     | Suggests commands from history as you type            |

### Theme — Pure

[Pure](https://github.com/sindresorhus/pure) is a minimal and fast Zsh prompt.
`ZSH_THEME` is set to empty because Pure uses Zsh's built-in `promptinit`
system instead of Oh My Zsh's theme engine.

### Version Managers

- **pyenv** — manages Python versions, initialized in `.zshrc`
- **rbenv** — manages Ruby versions, initialized in `.zprofile`
- **nvm** — manages Node.js versions, initialized in `.zprofile`

## Custom Aliases — myaliases.zsh

The [myaliases.zsh](./myaliases.zsh) file is sourced at the end of `.zshrc`.

### General

```bash
alias c='clear'
alias ..='cd ..'
alias ...='cd ../..'
alias h='history'
alias q='exit'
alias o='open .'      # Open current folder in Finder
```

### Network & Ports

```bash
po() { lsof -i :"$1" }        # Find what's running on a port: po 3000
kp() { kill $(lsof -t -i:"$1") 2>/dev/null || kill -9 $(lsof -t -i:"$1") }  # Kill process on a port
```

### Process Helpers

```bash
alias procs='ps aux | sort -nr -k 3 | head -20'     # Top 20 CPU processes
alias memprocs='ps aux | sort -nr -k 4 | head -20'   # Top 20 memory processes
psg() { ps aux | grep -i "$1" | grep -v grep }        # Search processes
```

### Git

The `git` plugin provides most aliases. These are the extras:

```bash
alias gs='git status'
alias gclean='git branch --merged | grep -v main | xargs git branch -d'
```

### Docker

```bash
alias d='docker'
alias dc='docker compose'
alias dcu='docker compose up'
alias dcd='docker compose down'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias di='docker images'
alias dprune='docker system prune -af'
```

### Node / npm / pnpm

```bash
alias nr='npm run'
alias ni='npm install'
alias nis='npm install --save'
alias nid='npm install --save-dev'
alias pr='pnpm run'
alias pi='pnpm install'
alias fixnode='rm -rf node_modules package-lock.json && npm install'
```

### Utilities

```bash
alias logf='tail -f'             # Follow a log file
alias big='du -ah . | sort -hr | head -50'   # Top 50 biggest files
alias nads='find . -name "*.DS_Store" -type f -delete'   # Remove .DS_Store files
alias cleanmac='sudo purge'      # Clear macOS memory cache
alias serve='python3 -m http.server 8000'     # Quick HTTP server
alias reload='source ~/.zshrc'   # Reload shell config
```

## Replicate This Setup

1. Install the [prerequisites](#prerequisites).
2. Download the config files
   ([.zprofile](./.zprofile), [.zshrc](./.zshrc), [myaliases.zsh](./myaliases.zsh)),
   place them in your home directory, and you're good to go:

   ```bash
   cp .zprofile ~/.zprofile
   cp .zshrc ~/.zshrc
   cp myaliases.zsh ~/myaliases.zsh
   ```

3. Reload the shell:

   ```bash
   source ~/.zshrc
   ```
