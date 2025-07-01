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
