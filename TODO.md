# TODO: Add snaphappy mcp tool claude code command
CREATE a new command file in @data/claude/.claude/commands/take_screenshot.md
INSTRUCT the agent to create a new command file
PLAN the command file to include:
- Title: Take Screenshot
- Description: Capture a screenshot of the current screen
- Command: snaphappy mcp tool claude code
- Arguments: Which screen to capture
The argument should be plaintext explaining the window and the context of the screenshot
INSTRUCT the agent to explain what it sees and add the contents of the screenshot to it's context
Make the agent to understand the screenshot in depth

#TODO: Rsync performance optimization
REFLECT on the rsync performance
USE the rsync command to see how much time it takes to transfer files
ANALYZE the output and identify any bottlenecks
The rsync currently syncs not many files, so it should be fast
SUGGEST optimizations if necessary
PLAN how to improve the rsync performance
IMPLEMENT the optimizations

#TODO: Remove the backup features
Currently in the config and settings of our TUI there are backup features
REFLECT on the necessity of these features
We are not using a lot of these features in the code
CONSIDER removing them to simplify the codebase
HIGHLIGHT where these backup would be useful but understand that stow already has a backup features so we don't need for stow and a lot of other tools
IDENTIFY the files and code that implement these backup features
PLAN how to remove the backup features

#TODO: Add support for terminal completion
Currently the cli does not support terminal completion
REFLECT on the necessity of terminal completion
CONSIDER adding terminal completion to the cli
RESEARCH how to implement terminal completion in the cli
IDENTIFY the files and code that implement the cli
PLAN how to add terminal completion to the cli
