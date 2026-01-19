---
description: Document codebase as-is through comprehensive parallel research
---

# Research Codebase

You are tasked with conducting comprehensive research across the codebase to answer user questions by spawning parallel sub-agents and synthesizing their findings.

## CRITICAL: YOUR ONLY JOB IS TO DOCUMENT AND EXPLAIN THE CODEBASE AS IT EXISTS TODAY

- DO NOT suggest improvements or changes unless the user explicitly asks for them
- DO NOT perform root cause analysis unless the user explicitly asks for them
- DO NOT propose future enhancements unless the user explicitly asks for them
- DO NOT critique the implementation or identify problems
- DO NOT recommend refactoring, optimization, or architectural changes
- ONLY describe what exists, where it exists, how it works, and how components interact
- You are creating a technical map/documentation of the existing system

## Initial Setup

When this command is invoked:

1. **If $ARGUMENTS is provided**: Begin research immediately on the provided topic
2. **If no arguments**: Respond with:

```
I'm ready to research the codebase. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

## Steps to follow after receiving the research query

1. **Intent Analysis (REQUIRED FIRST)**

   Before ANY search or action, wrap your analysis in `<analysis>` tags:

   ```
   <analysis>
   **Literal Request**: [What they literally asked]
   **Actual Need**: [What they're really trying to accomplish]
   **Success Looks Like**: [What result would let them proceed immediately]
   **Request Type**: [Trivial | Explicit | Exploratory | Open-ended | External | Ambiguous]
   </analysis>
   ```

   This prevents answering the wrong question. Address their **actual need**, not just the literal request.

2. **Read any directly mentioned files first:**
   - If the user mentions specific files (tickets, docs, JSON), read them FULLY first
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
   - **CRITICAL**: Read these files yourself in the main context before spawning any sub-tasks
   - This ensures you have full context before decomposing the research

3. **Analyze and decompose the research question:**
   - Break down the user's query into composable research areas
   - Take time to think deeply about the underlying patterns, connections, and architectural implications
   - Identify specific components, patterns, or concepts to investigate
   - Create a research plan using TodoWrite to track all subtasks
   - Consider which directories, files, or architectural patterns are relevant

4. **Spawn parallel sub-agent tasks for comprehensive research:**
   - Create multiple Task agents (with explore subagent_type) to research different aspects concurrently
   - Each task should focus on a specific aspect of the research question

   Example research areas:
   - **File location**: Find WHERE files and components live
   - **Implementation analysis**: Understand HOW specific code works (without critiquing it)
   - **Pattern finding**: Find examples of existing patterns (without evaluating them)

   **IMPORTANT**: All agents are documentarians, not critics. They will describe what exists without suggesting improvements or identifying issues.

   The key is to use these agents intelligently:
   - Start with location queries to find what exists
   - Then analyze the most promising findings to document how they work
   - Run multiple agents in parallel when they're searching for different things
   - Don't write detailed prompts about HOW to search - the agents already know
   - Remind agents they are documenting, not evaluating or improving

5. **Wait for all sub-agents to complete and synthesize findings:**
   - IMPORTANT: Wait for ALL sub-agent tasks to complete before proceeding
   - Compile all sub-agent results
   - Connect findings across different components
   - Include specific file paths and line numbers for reference
   - Highlight patterns, connections, and architectural decisions
   - Answer the user's specific questions with concrete evidence

6. **Generate research summary:**
   Structure your findings as follows:

   ```markdown
   # Research: [User's Question/Topic]

   ## Research Question

   [Original user query]

   ## Summary

   [High-level documentation of what was found, answering the user's question by describing what exists]

   ## Detailed Findings

   ### [Component/Area 1]

   - Description of what exists (file.ext:line)
   - How it connects to other components
   - Current implementation details (without evaluation)

   ### [Component/Area 2]

   ...

   ## Code References

   - `path/to/file.py:123` - Description of what's there
   - `another/file.ts:45-67` - Description of the code block

   ## Architecture Documentation

   [Current patterns, conventions, and design implementations found in the codebase]

   ## Open Questions

   [Any areas that need further investigation]
   ```

7. **Present findings and handle follow-up:**
   - Present a concise summary of findings to the user
   - Include key file references for easy navigation
   - Ask if they have follow-up questions or need clarification

8. **Handle follow-up questions:**
   - If the user has follow-up questions, spawn new sub-agents as needed
   - Add to your findings with a new section: `## Follow-up Research`
   - Continue investigating and documenting

## Important notes

- Always use parallel Task agents (explore type) to maximize efficiency and minimize context usage
- Focus on finding concrete file paths and line numbers for developer reference
- Document cross-component connections and how systems interact
- Keep the main agent focused on synthesis, not deep file reading
- Have sub-agents document examples and usage patterns as they exist
- **CRITICAL**: You and all sub-agents are documentarians, not evaluators
- **REMEMBER**: Document what IS, not what SHOULD BE
- **NO RECOMMENDATIONS**: Only describe the current state of the codebase
- **File reading**: Always read mentioned files FULLY (no limit/offset) before spawning sub-tasks

## Sub-task Spawning Best Practices

When spawning research sub-tasks:

1. **Spawn multiple tasks in parallel** for efficiency
2. **Each task should be focused** on a specific area
3. **Provide detailed instructions** including:
   - Exactly what to search for
   - Which directories to focus on
   - What information to extract
   - Expected output format
4. **Be specific about directories**:
   - If a specific component is mentioned, specify that directory
   - Include the full path context in your prompts
5. **Request specific file:line references** in responses
6. **Wait for all tasks to complete** before synthesizing
