########## GENERAL ##########

# ll, la, l provided by common-aliases plugin
alias c='clear'
alias ..='cd ..'
alias ...='cd ../..'
alias h='history'
alias q='exit'

# Open current folder in Finder
alias o='open .'

########## NETWORK / PORTS ##########

# Find what's running on a port: po 3000
po() { lsof -i :"$1" }

# Kill what's running on a port (tries graceful SIGTERM first)
kp() { kill $(lsof -t -i:"$1") 2>/dev/null || kill -9 $(lsof -t -i:"$1") }

########## PROCESS HELPERS ##########

alias procs='ps aux | sort -nr -k 3 | head -20'
alias memprocs='ps aux | sort -nr -k 4 | head -20'

psg() { ps aux | grep -i "$1" | grep -v grep }

########## GIT ##########

# g, gaa, gb, gc, gcb, gcm, gco, gd, gds, gl, gp provided by git plugin
alias gs='git status'

# Delete merged branches
alias gclean='git branch --merged | grep -v main | xargs git branch -d'

########## DOCKER ##########

alias d='docker'
alias dc='docker compose'
alias dcu='docker compose up'
alias dcd='docker compose down'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias di='docker images'
alias dprune='docker system prune -af'

########## NODE / NPM / PNPM ##########

alias nr='npm run'
alias ni='npm install'
alias nis='npm install --save'
alias nid='npm install --save-dev'

alias pr='pnpm run'
alias pi='pnpm install'

# Clear node_modules + reinstall
alias fixnode='rm -rf node_modules package-lock.json && npm install'

########## LOGGING / DEBUG ##########

# Follow logs (file log)
alias logf='tail -f'

# View top 50 biggest files
alias big='du -ah . | sort -hr | head -50'

########## CLEANUP ##########

# Remove .DS_Store recursively
alias nads='find . -name "*.DS_Store" -type f -delete'

# Cleanup macOS cache safely
alias cleanmac='sudo purge'

########## QUICK DEV HELPERS ##########

# Serve current folder with python (useful for frontend dev)
alias serve='python3 -m http.server 8000'

# Reload shell
alias reload='source ~/.zshrc'
