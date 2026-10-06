// Runs the trusted project runner after every file change made by the agent
// and appends the result to the tool output, so the agent sees FAIL/PASS.
// OpenCode 1.x plugin API: "tool.execute.after". The V2 ctx.tool.hook API from the slides does not exist here.
import { appendFile } from "node:fs/promises"

const EDIT_TOOLS = new Set(["edit", "write", "patch", "multiedit"])
const MAX_LINES = 40

export const CheckAfterEdit = async ({ $, directory }) => ({
  "tool.execute.after": async (input, output) => {
    if (!EDIT_TOOLS.has(input.tool)) return

    const result = await $`sh scripts/check.sh`.cwd(directory).nothrow().quiet()
    const text = `${result.stdout}${result.stderr}`.trim().split("\n").slice(-MAX_LINES).join("\n")
    const verdict = result.exitCode === 0 ? "PASS" : "FAIL"

    output.output += `\n\n[check-after-edit] sh scripts/check.sh → ${verdict} (exit ${result.exitCode})\n${text}`

    // Local audit log: event and exit code only, no source contents.
    const entry = { at: new Date().toISOString(), tool: input.tool, file: input.args?.filePath ?? null, exit: result.exitCode }
    await appendFile(`${directory}/.opencode/hook.log`, JSON.stringify(entry) + "\n").catch(() => {})
  },
})
