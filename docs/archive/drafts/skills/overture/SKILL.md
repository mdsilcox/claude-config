---
name: overture
description: Enabling, persisting and restoring Overture plans (overture-mcp). Use only when the user asks for Overture in a project, or when an Overture plan is active.
---

# Overture plans

Overture is off by default: it is not a user-level MCP server, because it opens a window in every project. Use the Orchestra board instead. Only when the user asks for Overture in a project, enable it there with `claude mcp add overture-mcp -s local -- cmd /c npx -y overture-mcp` (the session needs a restart to load it), and remove it with `claude mcp remove overture-mcp -s local` when the plan is done. The rest of this section applies only while it is enabled.

The Overture MCP server keeps plans in memory only; restarting the machine (or the server) loses the plan, its statuses and the user's field answers. The user values the plan visualization, so every project that uses Overture keeps a durable copy in the repo.

**Where:** `.overture/plan.xml` at the workspace root, committed to git alongside the work it describes.

**When to write it:**
- As soon as a plan is approved (after `get_approval` returns approved, or the user approves in chat).
- After every `request_plan_update` (merge the operations into the file so it always matches what Overture shows).
- After every node status change (`completed`, `failed`, `skipped`): set that node's `status` attribute.
- When the user fills dynamic fields or picks a branch: record answers as the field's `value` attribute and note the selected branch.

**What it contains:** the full plan XML in the same schema `submit_plan` accepts, with current statuses and answers, plus a short header comment giving the Overture project id, the selected branches, and how to restore. Never write `secret`-type field values (API keys, tokens); leave those blank.

**Restoring after a restart:** if `get_resume_info` reports no active plan for the project:
1. Ask the user to open the Overture UI first. It only counts status updates it receives while open, so updates sent before it connects leave its progress counter at 0.
2. `submit_plan` with the contents of `.overture/plan.xml` (pass `workspace_path`; the project id stays the same).
3. Re-send `update_node_status(..., "completed")` for every node whose status is `completed` in the file. Submit ignores the `status` attribute.
4. Tell the user to re-pick any branch the left-hand requirements panel asks for; it is cosmetic for finished branches.
