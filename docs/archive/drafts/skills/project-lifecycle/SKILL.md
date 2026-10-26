---
name: project-lifecycle
description: The end-to-end process for a new or larger project, from idea to delivery - Phase 0 setup, discovery phases (ideation, tech stack, data model, spec, roadmap) and the build phase loop - all tracked on the Orchestra board. Use when the user starts a new project, wants to take on a larger build, or says "kickoff".
---

# Project lifecycle: idea to delivery

Every decision is written down and approved before anything is built on it. Each stage ends in a short document the user approves on the Orchestra board; later stages and every subagent work from those documents, not from guesses. Board protocol and orchestration rules are in the `orchestration` skill.

## Fit the process to the project (decide this first)

The stages below are a menu, not a mandate. What is fixed for every project: decisions are written and approved before anything builds on them, every feature has checkable acceptance criteria, and the pitfalls at the end hold. Everything else scales with size and uncertainty.

In Phase 0, propose one track with a one-line reason, as a step with `options` so the user chooses:

| Track | When | Discovery | Build |
|---|---|---|---|
| **Small** | one clear tool or feature, a few sessions of work, known stack | one combined brief (problem, stack, data, acceptance criteria) in a single phase | one or two build phases, usually a single agent working sequentially |
| **Medium** | a real app with several features, mostly known territory | ideation and stack in one phase; data model and spec in a second; roadmap folded into the spec | build phases with lanes where work truly splits |
| **Large** | many features, unknowns, other users, or a hard deadline | every discovery phase below, each approved separately, with spikes | the full build loop with parallel lanes |

Further judgment calls stay yours (say why in the phase notes):
- **Prototype first** whenever one technical question decides the stack. Skip it when the stack is already proven for this kind of work.
- **Go back** to an earlier discovery phase (reopen it, with a reason) when a spike or a build phase shows a decision was wrong. Don't patch around a bad decision.
- **Change tracks** mid-project if the project turns out bigger or smaller than it looked, with the user's approval.
- **Use subagents** only where the work splits cleanly; one agent working straight through is often best, and is the default for small projects.

## On the board

Create the project (`projects/<id>`, with `repoUrl` once there is one) and the discovery phases the chosen track calls for (the full set is below; merge or drop phases for smaller tracks) with `kind: "discovery"`, chained by `deps`, each as a draft the user approves (Draft review protocol). Each discovery phase's steps are its activities; its `deliverables: [{title, path}]` are the documents it produces, and the phase closes when the user approves them. Use step `options` for real choices (stack candidates) and `fields` for questions.

| Phase | Short | Deliverable | Approval means |
|---|---|---|---|
| Phase 0: Setup | P0 | repo, project CLAUDE.md skeleton, README, empty docs/ | the workspace exists and the board tracks it |
| Discovery 1: Ideation | D1 | docs/vision.md | the problem, users, must-haves vs later, non-goals and success criteria are right |
| Discovery 2: Tech stack | D2 | docs/decisions.md (one entry per choice: chosen, rejected, why) + spike results | the stack is chosen, the riskiest piece proven by a throwaway spike |
| Discovery 3: Data model | D3 | docs/data-model.md with a diagram and a worked "day in the life" | entities, relations and lifecycles hold up against real use |
| Discovery 4: Spec | D4 | docs/spec/<feature>.md + acceptance tests + mockups | features are testable; acceptance tests exist before any build |
| Discovery 5: Roadmap | D5 | the build phases as drafts on the board | the order and slicing of build phases |

Build phases follow with `kind: "build"` (the default), each depending on the roadmap and on what it builds on.

## How to run each discovery phase

- **P0 Setup**: `git init`, the project CLAUDE.md skeleton (stack and commands left as TODO until D2), `docs/`, the board project. Ask for the repo URL if the user wants one on GitHub.
- **D1 Ideation**: interview the user (problem, who for, what "done" looks like, constraints: budget, hosting, offline, timeline, skills; non-goals). Send a `researcher` to survey what exists. Write one page. Keep must-haves short; everything else goes to "later".
- **D2 Tech stack**: compare 2-3 stacks against the constraints (offer them as step `options`, with complexity and risk), verify APIs with Context7, then build a throwaway spike of the riskiest piece before committing. Record every choice in docs/decisions.md. Fill in the CLAUDE.md stack and commands.
- **D3 Data model**: entities, relationships, lifecycles and invariants; a diagram; walk a realistic day of use through the model to find missing fields. This becomes the first contract.
- **D4 Spec**: per feature, user stories with testable acceptance criteria (Given/When/Then), edge cases and foreseeable traps; mockups for screens. Write the acceptance tests now (`test-porter` if they come from elsewhere). Measured: specs with acceptance tests made every lane pass first time.
- **Art direction** (any project with visuals that matter: games, illustrated apps), inside D2 or D4 or as its own discovery phase:
  - **Source the art from humans.** Record the choice in docs/decisions.md and every license in CREDITS.md. In order of preference:
    1. a consistent professional asset pack (one artist or studio; CC0 or bought) that covers the asset list;
    2. a commissioned artist for what no pack covers (usually the named cast);
    3. 3D models rendered to sprite sheets.

    Code is for effects, lighting, UI and motion. Never use code-drawn shapes for characters and illustrations.
  - **Not AI-generated art for anything that ships.** Tried seriously on two games (October 2026): single stills were sometimes decent, but consistency across angles and damage states, natural motion, and edits all read as AI-made. It took hours per asset with no end to the iteration. The local toolkit (`~/.claude/tools/art/`) is fine for mood boards, concept sketches and placeholders only. Revisit when models improve.
  - **Coverage before choosing a pack.** Make the asset list first:
    - every character with the directions, animations and states the game needs (walk in 4 directions, attack, hurt, damage stages);
    - environments, props, items, UI and portraits.

    Then check each candidate pack against it. A pack that lacks back views or a needed animation is a future gap.
  - **Don't mix artists within one kind of art.** Characters from two packs read as two games. Where a gap remains, commission it to match the pack, or change the design to fit what exists.
  - **Write `docs/art-direction.md`:**
    - the chosen packs (with links);
    - the palette and lighting the code side must match;
    - scale and proportions (pixel size per tile and character);
    - the quality bar ("would pass in a commercial indie game").
  - **For a commission,** write a brief from the art direction:
    - reference images and a style sheet;
    - the exact deliverables per asset: views, animations with frame counts, states, sizes, file format and layer structure;
    - milestones (sketch, color, final) with review at each;
    - ownership and license terms.

    The owner commissions and pays; Claude prepares the brief and integrates the deliveries.
  - **Get the owner's sign-off** on the chosen packs or the artist's samples before integrating the rest. Taste is the one judgment an AI reviewer does badly.
- **D5 Roadmap**: Build 1 is a walking skeleton (the app runs, tests run, deploy path, one thin feature end to end), mostly sequential. Later phases are vertical slices the user can try, a few hours of agent work each. Plan only the next build phase in detail; later ones stay coarse until their turn.

## Art phases (integrating packs or commissioned art)

Integration splits cleanly by asset group, so this is a good place for parallel lanes.
- **Contracts first (orchestrator):**
  - the asset list mapped to source files (pack and file, or commission deliverable);
  - the loader and animation interfaces the game uses (atlas format, animation names, anchor points, scale);
  - the folder layout;
  - CREDITS.md.
- **Lanes (`lane-builder`, one asset group each, named for it, e.g. `act1-enemies`, `village-npcs`):** slice the sheets, build the atlases, wire the animations and states to the game's events, and match scale and anchors. Each lane owns only its group's folders. Because groups share no interfaces, 6 to 10 lanes are fine; your review load is the limit.
- **Review at every hand-back, before anything reaches the owner:**
  1. Run an `art-reviewer` over the batch in the running game. It looks for mismatched styles, scale or palette between sources, wrong anchors and foot sliding, missing directions or states, and stretched or blurry scaling.
  2. Then look yourself at the riskiest screens.

  Show the owner screenshots or a short clip per area at the gate.

## The build phase loop (repeat until delivery)

1. Draft: steps, lanes split by coupling, complexity and risk, questions and options. User approves on the board.
2. Contracts: schema, interfaces, acceptance tests; reuse existing code where it exists.
3. Lanes: `lane-builder` agents, one worktree each, named for their work.
4. Review: checks (`step_checks.py`, with the affected tests, not the whole suite), a `browser-checker` pass, your spot-check, the user's file comments; one return round.
5. Gate: merge in dependency order, the full suite once on the merged commit (not after every merge when it is slow), metrics (`phase_tokens.py`), update CLAUDE.md and the spec, then the user tries the build.
6. Retro: two or three lines in the phase notes on what to change next time; apply them to the next draft.

Final phase: hardening (security review, performance, backups, error handling, user guide) and release.

## Autonomous mode (no owner during the build)

Use it only when the owner says so in the kickoff. Everything above still applies, with these changes:

- **The brief replaces the owner's approvals.** The owner's brief or spec is the only direction. Never ask questions; decide, and log every decision with its reason in DECISIONS.md.
- **A critic replaces each approval.** Before a phase closes (discovery or build), a critic agent with fresh context (the project's critic definition, or `general-purpose` with its rubric) reviews it and writes a verdict file that is never overwritten. The phase passes only on the critic's pass rule. Record each round on the board (`rounds` with the critic's scores) and in the phase notes. Discovery drafts don't wait for approval; they go to the critic instead. Never write to `approvals` or `inputs`: those stay the owner's.
- **State lives outside the conversation.** Keep `PROGRESS.md` (phase, done, next, known issues) and the board current. After every context compaction, re-read PROGRESS.md, DECISIONS.md and the board before acting.
- **The owner can still steer.** Read `controls` and `comments` at every gate as usual, and obey them.
- **Commit at every gate** with the main branch green and runnable, so stopping at any moment leaves a working product. Push only to a private remote the owner set up; never create or publish anything public.
- **Guardrails:** work only inside the project folder; no system or global config changes, no new MCP servers, no accounts, keys or paid services; install only the project's own dependencies; download nothing beyond them unless the brief allows it.
- **Budget and stopping:** keep the machine awake (the app's keep-awake option). Check plan usage at every gate (`get_usage`); at about 85% of the weekly limit, finish the current step, commit, write the final report and stop. Also stop when the brief's definition of done is met and the final critic passes.
- **Permissions:** if an action is refused, log it in PROGRESS.md and route around it; never stall waiting for an answer.
- **Final report** (`REPORT.md`): what was built, how to run it, every critic verdict per phase (first and final scores), known issues, time and tokens (`phase_tokens.py` over the whole run), and the decisions that mattered most.
- **Vault:** write reusable findings at the usual writing moments, as the vault skill describes.
- **Art sources need the owner even here.** Either the brief settles them (the chosen packs or the commissioned art, with licenses), or the run uses clearly marked placeholders, proposes packs on the board, tells the owner and pauses before integrating. Never ship AI-generated art, and never buy anything or commission anyone yourself.

## Pitfalls (each cost real time before)

- **Parallel too early.** Sequential work loses 39-70% when split across agents. Phase 0, the discovery phases and Build 1 run mostly sequentially; parallel lanes start once the skeleton and contracts exist.
- **Lanes split by file list instead of coupling.** Two lanes that need the same interface collide; merge them or make the interface a contract first.
- **A stale spec.** When reality forces a change, update the spec and log the decision in the same commit.
- **Phases too big to try.** If the user can't try it at the gate, split it.
- **Skipping the spike.** The stack is the most expensive decision to undo; prove the riskiest piece first.
- **Building before approval.** Never launch a phase whose approval isn't `approved`, and never treat a discovery document as settled until its phase is closed.
- **A slow inner loop.** One project's 35 to 52 minute suite, re-run by every reviewer and run concurrently, ate a large share of its development time. A similar game with a 3 minute suite moved several times faster. Budgets: the check a lane or reviewer runs per round stays under about 3 minutes, and the full suite under about 10. When the full suite passes 10 minutes, speeding it up becomes a planned step, not an afterthought.
  - Keep logic in pure modules tested without a browser, such as rules that emit events which the UI only replays.
  - Add debug hooks that jump straight to a state instead of playing up to it, and fast-forward real-time parts while keeping one real-speed test per feature.
  - Merge end-to-end tests that replay the same flows.
  - Run independent browser tests in parallel workers.
  - Lanes and review rounds run only the affected tests. The full suite runs once per gate on a frozen commit, and only one heavy suite runs on the machine at a time (several at once crash browsers).
  - Reviewers and critics read that run's result instead of re-running it.
- **Unverifiable "done".** Every feature needs acceptance criteria a test or a browser check can confirm.
