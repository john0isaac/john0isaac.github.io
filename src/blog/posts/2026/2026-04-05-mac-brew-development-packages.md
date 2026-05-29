---
title: "My Mac Development Setup with Homebrew"
date: 2026-04-05
description: A complete Brewfile of the packages, casks, and VS Code extensions I use for development on Mac.
categories:
  - Mac
tags:
  - Brew
  - Mac
  - Development
  - Setup
comments: true
authors:
  - john0isaac
---

My full [Homebrew](https://brew.sh/) Brewfile for setting up a new Mac for development.

Download the [Brewfile](./Brewfile) and run the following to install everything at once:

```bash
brew bundle --file=Brewfile
```

<!-- more -->

## Taps

Third-party repositories for additional formulae.

```ruby
tap "azure/azd"
tap "microsoft/foundrylocal"
```

## Formulae

### Core Libraries

```ruby
brew "openssl@3"
brew "readline"
brew "freetype"
brew "glib"
brew "cairo"
brew "pkgconf"
```

### Cloud CLIs

```ruby
brew "awscli"
brew "azure-cli"
brew "azure/azd/azd"
brew "gh"
```

### Language & Package Managers

```ruby
brew "python@3.12"
brew "pyenv"
brew "rbenv"
brew "cocoapods"
brew "pnpm"
brew "yarn"
brew "golangci-lint"
```

### Databases & Services

```ruby
brew "mongosh"
brew "redis"
brew "nginx", restart_service: :changed
brew "supervisor"
```

### Media & Graphics Libraries

```ruby
brew "pngquant"
brew "poppler"
brew "sdl2"
brew "sdl2_image"
brew "sdl2_mixer"
```

### Shell & Utilities

```ruby
brew "pure"       # Pretty Zsh prompt
brew "z"          # Directory jumper
brew "duti"       # Set default apps from CLI
brew "enchant"    # Spell checking library
brew "lsusb"      # List USB devices
```

## Casks

### AI Tools

- [Claude](https://claude.ai/) — Anthropic's AI assistant
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — CLI coding agent
- [Copilot CLI](https://githubnext.com/projects/copilot-cli) — GitHub Copilot in the terminal

```ruby
cask "claude"
cask "claude-code"
cask "copilot-cli"
```

### Development

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — Containers
- [iTerm2](https://iterm2.com/) — Terminal emulator
- [Postman](https://www.postman.com/) — API testing
- [Visual Studio Code](https://code.visualstudio.com/) — Code editor
- [Temurin](https://adoptium.net/) — Open-source Java runtime

```ruby
cask "docker-desktop"
cask "iterm2"
cask "postman"
cask "visual-studio-code"
cask "temurin"
```

### Browsers

- [Google Chrome](https://www.google.com/chrome/)
- [Microsoft Edge](https://www.microsoft.com/edge)

```ruby
cask "google-chrome"
cask "microsoft-edge"
```

### Media & Streaming

- [OBS](https://obsproject.com/) — Screen recording & streaming
- [VLC](https://www.videolan.org/vlc/) — Media player

```ruby
cask "obs"
cask "vlc"
```

### Utilities

- [KeyCastr](https://github.com/keycastr/keycastr) — Keystroke visualizer for screencasts
- [Maccy](https://maccy.app/) — Clipboard manager
- [RAR](https://www.win-rar.com/) — Archive tool
- [The Unarchiver](https://theunarchiver.com/) — Archive extractor
- [Transmission](https://transmissionbt.com/) — BitTorrent client
- [wkhtmltopdf](https://wkhtmltopdf.org/) — HTML to PDF converter

```ruby
cask "keycastr"
cask "maccy"
cask "rar"
cask "the-unarchiver"
cask "transmission"
cask "wkhtmltopdf"
```

### Communication

- [Discord](https://discord.com/)
- [TeamViewer](https://www.teamviewer.com/) — Remote desktop

```ruby
cask "discord"
cask "teamviewer"
```

## VS Code Extensions

### Python

```ruby
vscode "ms-python.python"
vscode "ms-python.vscode-pylance"
vscode "ms-python.debugpy"
vscode "ms-python.vscode-python-envs"
vscode "donjayamanne.python-environment-manager"
vscode "charliermarsh.ruff"
vscode "twixes.pypi-assistant"
```

### Jupyter

```ruby
vscode "ms-toolsai.jupyter"
vscode "ms-toolsai.jupyter-keymap"
vscode "ms-toolsai.jupyter-renderers"
vscode "ms-toolsai.vscode-jupyter-cell-tags"
vscode "ms-toolsai.vscode-jupyter-slideshow"
```

### Azure & Cloud

```ruby
vscode "ms-azuretools.azure-dev"
vscode "ms-azuretools.vscode-azureresourcegroups"
vscode "ms-azuretools.vscode-bicep"
vscode "ms-azuretools.vscode-containers"
vscode "ms-azuretools.vscode-docker"
vscode "ms-dotnettools.vscode-dotnet-runtime"
```

### GitHub

```ruby
vscode "github.codespaces"
vscode "github.copilot-chat"
vscode "github.vscode-github-actions"
vscode "github.vscode-pull-request-github"
vscode "anthropic.claude-code"
```

### Databases

```ruby
vscode "mongodb.mongodb-vscode"
vscode "ms-ossdata.vscode-pgsql"
vscode "mtxr.sqltools"
vscode "mtxr.sqltools-driver-mysql"
vscode "mtxr.sqltools-driver-sqlite"
```

### Containers & Remote

```ruby
vscode "docker.docker"
vscode "ms-vscode-remote.remote-containers"
```

### Web & Markup

```ruby
vscode "amandeepmittal.pug"
vscode "syler.sass-indented"
vscode "vue.volar"
vscode "esbenp.prettier-vscode"
vscode "yzhang.markdown-all-in-one"
vscode "davidanson.vscode-markdownlint"
```

### Other

```ruby
vscode "eamodio.gitlens"
vscode "mechatroner.rainbow-csv"
vscode "ms-vscode.makefile-tools"
vscode "shopify.ruby-lsp"
vscode "streetsidesoftware.code-spell-checker"
vscode "tonybaloney.vscode-pets"
```

## UV Tools

```ruby
uv "pre-commit"
uv "specify-cli"
```
