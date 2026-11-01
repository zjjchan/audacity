# Design Justification and Agent Governance

## 1. Design Justification
I implemented an Automated Issue Triage & Diagnostic Verification for Audacity. Because Audacity receives an extremely large amount of issue traffic (over 1,914 open issues; 68 new issues in an 11-day sample from Oct 20–31, 2026, averaging ~43/week), and has about 1.9k opened issues, it probably would benefit heavily from agentic automation to help with triaging. Repository data showed that about 70% (48 of 68) of sampled issues sat with no comments for several days. In issue #12439, a user reported a "desactivated" export menu. Maintainers only replied after 4 days, commenting that they could not reproduce the issue following the steps outlined. An AI agent outperforms simple automation in issue triaging as it can understands natural language semantics, allowing it to parse what issues are genuine and what may be lacking details, along with potential duplicate issues.

The main risks would be prompt injection and runaway actions as issue text is generally untrusted external input. Thus, I deliberately prevented the agent from being able to close or delete issues, merge PRs, push commits or modify licensing/CLA files. These are enforced via zero write permissions and Github Agentic Workflow `safe-outputs`, rather than prompt instructions.

One alternative I rejected was automating PR code reviewing and merging due to high security risks, as well as the fact that the large amount of open issues seemed like a much more glaring problem Audacity had.

*Measured Period & Limitations*: Sampled 68 issues from Oct 20–31, 2026 via GitHub API. Limitation: Metrics omit private triage on Audacity Discord and forum threads.

## 3. Governance Summary
| Control | Status | Implementation Details |
| :--- | :--- | :--- |
| **Identity** | Implemented | Attributed to `github-actions[bot]` via GitHub Actions agent runtime (`issue-triage.lock.yml`). |
| **Least Privilege**| Implemented | Strict read-only tokens (`contents: read`, `issues: read`); network restricted to `api.github.com`. |
| **Safe Outputs** | Implemented | Enforced schema: `add-comment` (max 1), `add-labels` (max 3 from strict whitelist). |
| **Human Approval** | Implemented | Agent outputs are strictly advisory; only human maintainers can close issues or merge PRs. |
| **Budgets** | Implemented | Job timeout of 5 minutes (`timeout-minutes: 5`), per-issue concurrency locks, max 200 runs/week quota. |
| **Audit Trail** | Implemented | Actions execution logs, SHA-pinned lock file, model invocation transcripts stored in `evals/golden/`. |
| **Kill Switch** | Implemented | Maintainers can disable workflow or cancel active runs in 2 taps via GitHub Mobile app. |
| **Drift Detection**| Implemented | Weekly cron CI workflow reruns `evals/run_evals.py` on 11 golden tasks to detect quality drift. |
| **Accountability** | Implemented | CODEOWNERS on `.github/` and `.claude/skills/`; maintainers remain legally responsible per `AI_POLICY.md`. |

*Untrusted inputs*: Issue titles, bodies, and comments. *Allowed actions*: Post 1 triage comment, apply up to 3 whitelisted labels.

## 4. Agent Bill of Materials (BOM)
- **Model**: GitHub Copilot CLI Engine (`copilot: 1.0.103`), pinned via SHA in `.github/workflows/issue-triage.lock.yml`.
- **Instructions**: `AGENTS.md`, `.github/copilot-instructions.md`, `.claude/skills/issue-triage/SKILL.md`.
- **Tools & MCP Servers**: `validate_labels.py` (label whitelist), `search_duplicates.py` (symptom search), GitHub MCP, Safeoutputs MCP.
- **Permissions**: `contents: read`, `issues: read` (no write/admin permissions).
- **Data Sources**: Current issue payload, repository issue index, repository label taxonomy (76 labels).
- **Logs & Evals**: GitHub Actions runner logs, `evals/golden/actual_outputs/`, `evals/golden/transcripts/`.
- **Responsible Humans**: Audacity Maintainer Team (`@audacity/maintainers`).

## 5. Governance Questions
1. Instructions to the agent to close stale issues claiming maintainer approval is ignored as the agent does not have issue-close tools and permissions. Whitelist script drops unapproved labels (`admin-override`).
2. A weekly scheduled CI workflow will rerun the 11 golden evaluation tasks in `evals/golden/`. If label precision, duplicate detection or schema validation results come to be below the threshold, the CI run will fail and maintainers will be notified.
3. Github actions will group (`issue-triage-${{ issue.number }}`) queue jobs. Once weekly quota (200 runs) is reached, the subsequent 100 runs will skip LLM inference, and issues will be tagged with `triage/queued-backlog`.
4. The agent is strictly constrained by read-only permissions (`contents: read`, `issues: read`) and `safe-outputs`. Therefore even if MCP output is malicious, the agent can at most only output 1 comment and up to 3 whitelisted labels on the current issue.
5. The maintainer must open the repository on the GitHub mobile app or the Github website, navigate to Actions > Issue Triage Agent > ... > Disable workflow and stop the active runs by tapping the executing run and then tapping on Cancel run.

## 6. Test Findings and Unresolved Items
- **CI Execution & Fallback Justification**: Multiple attempts to run the workflow end-to-end in GitHub Actions were conducted on branch `cs467-assignment3` (runs 41278947963, 41281425633, 41282180032, 41282888011, 41283405313, 41283813029, 41285830885). All failed during agent execution due to GitHub Copilot Student tier token restrictions rejecting automated external CLI inference (`400 Model Not Supported` and `400 reasoning_effort "medium" was provided, but model does not support reasoning_effort`). Per assignment contingency, we conducted a dry-run evaluation using a dedicated coding assistant instance with the identical configuration (`AGENTS.md`, `SKILL.md`, `validate_labels.py`, `search_duplicates.py`) across all 11 test cases (10 historical issues + 1 adversarial injection). Full transcripts are captured in `evals/golden/transcripts/` and actual outputs in `evals/golden/actual_outputs/`.
- **Verified Controls**: Least privilege (read-only enforcement), Safe outputs (max 1 comment, max 3 labels), Label whitelist sanitization (dropped `admin-override`), Duplicate detection (correctly flagged candidate duplicates for #12625 -> #12606, #12626 -> #10500, #12532 -> #12109), Missing info detection (#12439), and Prompt injection rejection (#99999).
- **Unverified Controls**: AWF eBPF network firewall packet filtering, Actions runner hard timeout enforcement, and automated GitHub bot token rotation (blocked by CI token rejection).
- **Unresolved Items**: External forum threads (`forum.audacityteam.org`) remain unindexed; non-English bug reports require manual translation before applying platform tags.

## 7. AI-Use Statement
The workflow architecture, claude skills, supporting scripts AGENTS.md and changes to CONTRIBUTING.md were generated using AI. Historical issue data and repository metrics were manually queried using github API, with detailed confirmed to match. In DESIGN.md, only the governance summary, agent bills of materials and test findings are AI generated. Everything else, such as the design justification, was written by me. AI generated explanations were reviewed and edited where I saw fit to do so.

