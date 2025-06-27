**Automation Tool for Warp Workflows**

Think deeply about this task before proceeding. You will act as a tool for automating the creation of warp workflows.

**Variables:**

command: $ARGUMENTS
output_dir: $ARGUMENTS

**ARGUMENTS PARSING:**
Parse the following arguments from "$ARGUMENTS":
1. `command` - The command to add as a warp workflow
2. `output_dir` - Directory where iterations will be saved

**PHASE 1: UNDERSTANDING THE COMMAND**
Read and deeply understand the command. This command defines:
- What command we want to add as a warp workflow
- The specific requirements for the warp workflow

**PHASE 2**: Generate arguments for the warp workflow based on the command:
- Identify all necessary arguments for the command
- Determine default values and descriptions for each argument
- Ensure all arguments are clearly defined and documented
- You will generate arguments and this auto-generated arguments are mentioned below as [ARGUMENT_NAME_1, ARGUMENT_NAME_2, ..., ARGUMENT_NAME_X] in the YAML specification.

**PHASE 3: OUTPUT DIRECTORY RECONNAISSANCE** 
Thoroughly analyze the `output_dir` to understand the current state:
- List all existing files and their naming patterns
- Identify the highest iteration number currently present
- Analyze the content evolution across existing iterations
- Understand the trajectory of previous generations
- Determine what gaps or opportunities exist for new iterations

**Agent Task Specification:**
```
TASK: Generate warp workflow for [COMMAND] in [OUTPUT_DIR]

CONTEXT:
- Command to add: [COMMAND]
- Current output directory: [OUTPUT_DIR]

REQUIREMENTS:
1. Read and understand the command 
2. Analyze existing iterations in [OUTPUT_DIR]
3. Generate a new warp workflow file

SPECIFICATION:
```yaml
---
name: ""
command: "[COMMAND]"
description: ~
arguments:
  - name: "[ARGUMENT_NAME_1]"
    arg_type: Text
    description: "[DESCRIPTION_OF_ARGUMENT_1]"
    default_value: "[DEFAULT_VALUE_OF_ARGUMENT_1]"
  - name: "[ARGUMENT_NAME_2]"
    arg_type: Text
    description: "[DESCRIPTION_OF_ARGUMENT_2]"
    default_value: "[DEFAULT_VALUE_OF_ARGUMENT_2]"
- name: "[ARGUMENT_NAME_X]"
  arg_type: Text
  description: "[DESCRIPTION_OF_ARGUMENT_X]"
  default_value: "[DEFAULT_VALUE_OF_ARGUMENT_X]"
tags: []
shells: []
```

FILE_PATH: [OUTPUT_DIR]/[UNIQUE_FILE_NAME].yaml
```

DELIVERABLE: Single yaml file as specified, with unique innovative content
```

**EXECUTION PRINCIPLES:**

**Quality & Uniqueness:**
- Each command must be genuinely unique and valuable
- Build upon previous work while introducing novel elements
- Maintain consistency with the original specification
- Ensure proper file organization and naming

**Scalability & Efficiency:**
- Think deeply about the evolution trajectory across parallel streams

Begin execution with deep analysis of this command and the output directory.
