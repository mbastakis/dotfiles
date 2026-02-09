#!/bin/bash
# Shell script test file with intentional format/lint issues

# Inconsistent spacing
function greet() {
  local name=$1
  if [ "$name" == "" ]; then
    name="World"
  fi
  echo "Hello, $name!"
}

# Missing quotes around variables
function process_files() {
  for file in $1/*; do
    if [ -f $file ]; then
      echo "Processing $file"
    fi
  done
}

# Unused variable
unused_var=42

# Very long line
function long_function() {
  local arg1=$1
  local arg2=$2
  local arg3=$3
  local arg4=$4
  local arg5=$5
  echo "Arguments: $arg1 $arg2 $arg3 $arg4 $arg5"
}

# Missing error handling
function risky_operation() {
  cd /some/directory
  rm -rf *
  cd -
}

# Using deprecated test syntax
function check_file() {
  if [ -e "$1" ]; then
    echo "File exists"
  fi
}

# Inconsistent indentation
function parse_config() {
  local config_file=$1
  if [ -f "$config_file" ]; then
    source "$config_file"
    echo "Config loaded"
  fi
}

# Main execution
main() {
  greet "John"

  # Unquoted variable expansion
  file_path=/tmp/test.txt
  echo $file_path

  # Using [ instead of [[
  if [ $USER = "root" ]; then
    echo "Running as root"
  fi

  # Command substitution without quotes
  files=$(ls /tmp)
  echo $files

  # Missing 'local'
  global_var="This should be local"
}

main "$@"
