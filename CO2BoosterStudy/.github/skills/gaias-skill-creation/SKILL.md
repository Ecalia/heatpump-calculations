---
name: meta_003_skill_creation
description: Use when creating new Skills from scratch, converting existing system prompts or historical prompt library entries into Skill format, or reviewing/improving existing Skills. 
---

# Purpose

This Skill teaches you how to create, convert, and validate Skills in Anthropic format when a recurring or complex task pattern requires domain-specific knowledge that the model does not already possess.

# Prerequisites

**You should understand:**
- The difference between what a model knows from training vs. what must be injected (context engineering)
- The GAIAS architecture: Sub preloads full Skill content for immediate fits, curates awareness list from YAML descriptions
- The Anthropic progressive disclosure model: Tier 1 (description, always loaded) → Tier 2 (SKILL.md body, on activation) → Tier 3 (reference/ files, on demand)

**You do NOT need:**
- Domain expertise in the Skill's subject (this Skill teaches the PROCESS, not the domain)

# Concrete Facts & Parameters

## Skill File Structure

Every Skill file MUST begin with YAML frontmatter:
```yaml
---
name: domain_NNN_brief_description
description: Brief one-paragraph description including: what this Skill does, trigger conditions (domain signals, action verbs, situations), and what it explicitly does NOT cover. 
---
```

The body MUST follow this section order:
1. Purpose — one sentence, action-oriented
2. Prerequisites — specific inputs needed, NOT textbook prerequisites
3. Concrete Facts & Parameters — ONLY what the model does NOT know
4. Procedure — numbered steps with validation gates
5. When to Think More Abstractly — escape conditions for first-principles reasoning
6. Common Failure Modes & Solutions — Problem → Root Cause → Concrete Solution
7. Related Skills — cross-references with relationship description
8. Skill Maintenance Notes — version history, known gaps

## Naming Convention

Format: `[domain]_[NNN]_[brief_description]`
Domains: eng, safety, biz, hr, fin, ops, meta, admin

## Size Constraints

| Size | Symptom | Action |
|------|---------|--------|
| <500 tokens | Barely more than a formula | Combine with related Skill |
| 800-2000 tokens | Single coherent procedure | SWEET SPOT |
| >2000 tokens | Multiple distinct procedures | Decompose into SKILL.md + reference/ |

## Progressive Disclosure File Structure (for large Skills)
```
domain_NNN_description/
  SKILL.md              # Procedure + key decision criteria (800-1500 tokens)
  standard_summary.md  # Loaded when specific step needs regulatory detail
  parameters.md        # Loaded when specific step needs numerical values
  templates.md         # Loaded when generating output documents
```

## Token Value Hierarchy (highest to lowest value per token)

1. Specific numerical values (~5 tokens, irreplaceable) — "R290 LEL = 2.1 vol%"
2. Decision criteria with conditions (~15 tokens) — "IF pressure ratio > 7:1 → reject"
3. Procedural steps with validation gates (~20 tokens)
4. Validated code snippets (~50-100 tokens)
5. Escape hatches and boundaries (~20 tokens)
6. Cross-references to related Skills (~10 tokens)
7. Conceptual explanations — LOWEST VALUE, often removable

## The Description Field — Critical Design Rules

The YAML description is the discovery mechanism. Requirements:
- typical trigger enumeration (list every concrete use case)
- Domain signals (specific terminology from the user's request)
- Action verbs (size, calculate, assess, draft, classify, review)
- Catch-all fallback (final sentence capturing edge cases)
- Maximum ~1024 characters

GOOD: "Use when performing explosion protection (Explosionsschutz) zone classification for facilities handling flammable refrigerants, particularly R290. Covers ATEX zone determination using IEC 60079-10-1, ventilation assessment, ignition source identification per TRGS 723, equipment selection by zone, and Explosionsschutzdokument generation per BetrSichV §6. Do NOT use for non-flammable refrigerants or general fire safety."

BAD: "Helps with safety" / "Explosion protection expert" / "Use for R290 work"

# Procedure

## Step 1: Architecture Decision

Determine if a Skill is the RIGHT artifact:
- One-time or rare → do NOT create a Skill
- Recurring workflow, general knowledge only → reusable system prompt, not a Skill
- Recurring procedure requiring facts model LACKS → SKILL
- Large reference knowledge (standards, regulations) → reference document loaded by a Skill

## Step 2: Verify 3-Instance Rule

Has this pattern occurred 3+ times? Will it recur? Does it need facts the model lacks?
IF any answer is NO → do not create a Skill.

## Step 3: Write YAML Frontmatter FIRST

Write `name` and `description` before writing the body. If you cannot write a specific, exhaustive description, you do not understand the Skill's scope yet. Narrow it.

## Step 4: Extract Novel Knowledge

Read the source material. For every line, ask: "Would a competent AI model certainly surface this fact without the Skill?"
- YES → remove it (trivial textbook dump)
- NO → keep it (genuine novel or complicated content)

What models genuinely LACK: company-specific values/decisions/conventions, specific regulatory clause references and their practical application, equipment specifications, hard-won failure mode lessons, institutional workflow decisions.

What models already KNOW: thermodynamic cycles, project management frameworks, German corporate law in general, engineering fundamentals, programming basics.

## Step 5: Write the Body

Follow the template section order exactly (Purpose → Prerequisites → Concrete Facts → Procedure → When to Think Abstractly → Failure Modes → Related Skills → Maintenance Notes).

Write as you would brief a competent junior who knows the domain but NOT your specific workflow. Not a textbook student (too basic). Not a peer expert (too terse).

After each major procedure step, include a validation gate:
"CHECK: [condition]? IF NOT → [specific corrective action]"

## Step 6: Converting a Historical Prompt

1. EXTRACT unique knowledge — highlight ONLY lines with facts, values, procedures, or decisions the model cannot derive. A 500-line prompt typically yields 50-100 lines of genuine novel content.
2. DISCARD persona/identity framing — "You are an expert in..." belongs in system prompts, not Skills.
3. DISCARD textbook explanations — if it explains what FMEA is or how a heat pump works, remove it.
4. RESTRUCTURE into Skill format — extracted knowledge becomes Concrete Facts and Procedure.
5. DECOMPOSE if >2000 tokens — core procedure → SKILL.md, reference tables → reference/ files. SKILL.md references when to load: "For Step N, load reference/filename.md."
6. WRITE YAML frontmatter — fresh description with exhaustive triggers and anti-triggers.

CHECK: Does the converted Skill have YAML frontmatter? Does the description contain specific trigger conditions AND anti-triggers? Is the body under 2000 tokens?

## Step 7: Validate (7 Questions Test)

1. Recurrence: Will this be done 3+ times?
2. Specificity: What does the model NOT already know?
3. Freedom Level: How dangerous is a wrong answer? (High danger → low freedom in procedure)
4. Trigger Clarity: Can the description specify WHEN this activates?
5. Verification: How will the agent know output is correct?
6. Boundaries: What should this NOT be used for?
7. Token Budget: Core procedure under 2000 tokens?

## Step 8: Register

- Add to skill-index.json (id, name, description, triggers, anti_triggers, file, status: "draft")
- Naming: [domain]_[NNN]_[brief_description]

# When to Think More Abstractly

IF the source material is genuinely novel (no recurring pattern established), do not force-create a Skill. Note the pattern for future reference.

IF a historical prompt contains no novel facts (all content is general knowledge the model already has), it should NOT become a Skill — it is already covered by base intelligence.

IF the task requires creative exploration or strategic thinking where procedures would constrain quality, a Skill is the wrong artifact.

IF source material describes machine-specific procedures without access to actual documentation, do NOT fabricate content — flag as requiring real documentation input.

# Common Failure Modes & Solutions

## Problem 1: Textbook Dump
Skill body contains general knowledge the model already has.
**Root cause:** Author explains concepts rather than providing facts.
**Solution:** For every line, apply the test: "Would the model know this without the Skill?" If yes, delete it ruthlessly.

## Problem 2: Missing YAML Frontmatter
Skill has no `name` or `description` in YAML format at the top.
**Root cause:** Author used body-level headers for triggers instead.
**Solution:** ALL trigger/anti-trigger information belongs in the YAML `description` field. The body should NOT duplicate discovery information.

## Problem 3: Over-Generic Description
Sub preloads the Skill on unrelated tasks because description is too vague.
**Root cause:** Description uses broad categories ("safety", "engineering") instead of specific domain terminology.
**Solution:** Use concrete domain signals, action verbs, and explicit anti-triggers in the description.

## Problem 4: Monolithic Skill (>2000 tokens)
Skill tries to cover too much, diluting Ego's context window.
**Root cause:** Not decomposed into SKILL.md + reference/ documents.
**Solution:** Core procedure and key decision criteria in SKILL.md. Detailed tables, standard summaries, templates in reference/ subdirectory.

## Problem 5: Fabricated Content
Skill contains machine-specific values or procedures that were invented, not sourced.
**Root cause:** Agent lacks access to real documentation and fills gaps with plausible-sounding data.
**Solution:** Only include knowledge sourced from actual company documents, test data, or verified standards. Flag gaps explicitly.

## Problem 6: Over-Steering
Skill is so prescriptive it blinds the agent to cross-domain considerations.
**Root cause:** No "When to Think Abstractly" section; procedure too rigid for the risk level.
**Solution:** Include escape conditions. Match freedom level to consequence of error. A Skill should be a handrail, not blinders.

# Related Skills

- **meta_001_first_principles:** When a Skill's procedure breaks down, fall back to first principles reasoning
- **meta_002_frame_detection:** When creating a Skill, verify you are solving the right problem (not formalizing the wrong approach)
- **ops_002_code_development:** For the registration step (editing skill-index.json, git operations)

# Skill Maintenance Notes

**Version History:**
- v1.0 (2026-02-08): Initial creation
- v2.0 (2026-02-13): Rebuilt from v1. Added YAML frontmatter (was missing — critical gap). Restructured body to follow Prompt-Design template exactly. Added prompt-to-skill conversion procedure. Added progressive disclosure decomposition. Previous version preserved as meta_003_skill_creation-v1.md.
- v3.0 (2026-02-13): Complete rewrite following Prompt-Design.instructions.md template. Added proper YAML frontmatter with exhaustive description. Restructured all sections to match template order. Moved trigger/anti-trigger info from body headers into YAML description. Added Skill Maintenance Notes.

**Known Gaps:**
- No automated token counting — size validation is manual estimate
- No integration with automated testing pipeline for Skill quality measurement
- Progressive disclosure reference/ loading not yet implemented in n8n workflow