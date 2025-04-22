# functions.zsh - Custom shell functions

# Extract almost any archive
extract() {
  if [ -f "$1" ]; then
    case "$1" in
      *.tar.bz2)   tar xjf "$1"     ;;
      *.tar.gz)    tar xzf "$1"     ;;
      *.bz2)       bunzip2 "$1"     ;;
      *.rar)       unrar e "$1"     ;;
      *.gz)        gunzip "$1"      ;;
      *.tar)       tar xf "$1"      ;;
      *.tbz2)      tar xjf "$1"     ;;
      *.tgz)       tar xzf "$1"     ;;
      *.zip)       unzip "$1"       ;;
      *.Z)         uncompress "$1"  ;;
      *.7z)        7z x "$1"        ;;
      *)           echo "'$1' cannot be extracted via extract()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}

# Find process by name and kill it
killname() {
  ps aux | grep "$1" | grep -v grep | awk '{print $2}' | xargs kill -9
}

# Make directory and enter it.
take() {
	mkdir $1;
	cd $1;
}

# Python virtual environment
# Create a venv
venv() {
	mkdir -p ~/.virtualenvs
	
	python3 -m venv ~/.virtualenvs/$1
}
# Activate python environment
activate() {
	source ~/.virtualenvs/$1/bin/activate
}
deact() {
	deactivate;
}
venvlist() {
	ls ~/.virtualenvs/
}
venvremove() {
	sudo rm -rf ~/.virtualenvs/$1
}