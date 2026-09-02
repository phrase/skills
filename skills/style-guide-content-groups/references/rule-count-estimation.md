# Rule-count estimation

When you present the taxonomy (Phase 2), also predict **how many Rules each Style Guide
will spawn**, so the user can see whether a combined Content Group would approach a
per-Content-Group Rule cap. Use the inclusive extractor in
`../assets/estimation-extraction-prompt.md` as the basis — it mirrors what the platform
actually does when it converts a Style Guide into Rules.

## How the estimation prompt counts

- **One requirement per distinct rule statement.** It errs on inclusion, so borderline
  or subjective statements ("tone should feel warm") each count.
- **Examples do NOT add to the count.** They attach to the requirement they illustrate.
- **Restatements count separately.** A rule repeated in a cheat sheet, a summary, or
  across sections is counted once per occurrence.
- **Shared matter doesn't count.** Title, legal notice, metadata, and the change log
  state no requirement.

## Producing the estimate

Work from the Rule content routed to each Content Group (and to Universal) — not built
files, since at Phase 2 they don't exist yet. Count the distinct requirement-bearing
statements in each. Give an **approximate range**, not a false-precise integer (a dense
compound statement can split into two, or two can merge) — treat it as roughly ±15%,
e.g. "~28–32".

## Splitting distributes Rules; it does not reduce them

Splitting a guide doesn't lower the **total** number of Rules — it distributes them so
each Content Group is smaller. Reducing the total (deduplicating, folding, dropping
terminology) is the platform's later rule-conversion step, not this skill's job. So use
these estimates to check that **Universal + any one Content Group** stays under the cap.

## How the estimate maps to the three options

- **Option 1 (Standalone):** each Content Group's file ≈ **Universal + that group**, so
  its count is the sum — and since each file stands alone, that sum is the number to
  check against a cap.
- **Option 2 (Combinable):** the Universal Style Guide ≈ Universal Rules; each Content
  Group's file ≈ that group's Rules. A combined Content Group ≈ Universal + the groups
  you stack — that combined total is what to check against a cap.
- **Option 3 (Combinable + Optimized):** same layout as Option 2, but each file is
  optimized down toward the extracted-Rule count and must land **≤ 50 Rules per Content
  Group**. Use this estimate as the starting point and the target to beat. When a file's
  estimate runs over ~30 Rules (typically Universal), the optimization pass first
  consolidates convention-covered orthography under the language's primary convention
  (RAE / Chicago / Duden / …) as the biggest single reducer — see
  `optimization-playbook.md`.

## Presenting it

Add a table under the taxonomy:

```
Predicted Rules (approximate):

| Style Guide      | Rules (~) |
| Universal        | ~A        |
| <Content Group>  | ~B        |
| <Content Group>  | ~C        |

A combined Content Group stacks them — e.g. Universal + <Group> ≈ A + B.
```

Flag any combination whose total approaches or exceeds a known cap, and note that the
platform's later optimization is what brings a large count back down.
