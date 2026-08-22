// TODO(remove): This plugin is a temporary workaround — delete it (and its
// entry in the top-level "plugin" array of opencode.jsonc) once wcs/gpt no
// longer fabricates the subagent `sessionID` argument. Added 2026-08-21 on
// opencode2 beta-17823, right after the subagent-resume feature (PR #43172)
// added the optional `sessionID` field and GPT via the WCS/LiteLLM gateway
// started filling it with the parent session ID, breaking every fresh
// subagent spawn (upstream #43297/#43610/#43619, closed as model/gateway
// behavior). To test whether it's still needed: disable the plugin, restart
// the service, and run
//   opencode2 run --model wcs/gpt "Use the subagent tool to spawn the
//   web-researcher subagent with the task: reply with exactly SUBAGENT_OK."
// If that succeeds without the plugin, it can go.
//
// Works around GPT models behind the WCS/LiteLLM gateway fabricating the
// optional `sessionID` continuation argument on fresh subagent calls: they
// copy the parent session ID (or invent one), and OpenCode rejects the call
// because only an existing child session ID is valid there (upstream
// #43297/#43610/#43619, closed as model/gateway behavior).
//
// This hooks tool execution and drops a `sessionID` argument that is either
// the parent session's own ID or doesn't resolve to an existing session, so
// OpenCode spawns a fresh child session instead of erroring. Legitimate
// resumes (real child session IDs returned by earlier subagent calls) pass
// through untouched. The hook payload is
// {tool, sessionID (parent), agent, messageID, id, input (mutable args)}.

function isSubagentTool(name) {
  return typeof name === "string" && (name === "task" || name.startsWith("subagent"))
}

export default {
  id: "strip-fabricated-subagent-session",
  async setup(context) {
    await context.tool.hook("execute.before", async (call) => {
      if (!isSubagentTool(call.tool)) return
      const args = call.input
      if (!args || typeof args !== "object") return
      const sid = args.sessionID
      if (typeof sid !== "string" || sid.length === 0) return
      if (sid !== call.sessionID) {
        const existing = await Promise.resolve(context.session.get(sid)).catch(() => undefined)
        if (existing) return
      }
      delete args.sessionID
    })
  },
}
