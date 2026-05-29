# Skill Guide

This file is the entry point for skill-related guidance in this repository. Read it first when you need to decide how to use or extend the `.agents/skills/` content.

## Purpose

- Keep agent behavior focused, minimal, and easy to follow.
- Prefer the repo-specific ICP skills under `.agents/skills/icp/` when the task is about Internet Computer work.
- Use official documentation as the primary source when there is any ambiguity.

## Core Rules

1. Keep changes small and targeted.
2. Prefer clear, minimal code over clever code.
3. Keep individual source files short when practical. If a file is getting large, split it only when that improves clarity.
4. Avoid docstrings unless they add real value.
5. Use short comments only when the code would otherwise be hard to understand.
6. Do not create new Markdown files unless the user explicitly asks for documentation changes.
7. When a task matches an ICP-specific skill, follow the skill in `.agents/skills/icp/` before inventing new conventions.
8. Treat official docs and repo-local references as the source of truth.

## How To Use This Folder

- Use `.agents/skills/` for reusable, task-focused guidance.
- Keep each skill focused on one domain or workflow.
- Make rules explicit and actionable so an agent can apply them without guessing.
- Prefer headings, bullets, and examples over long paragraphs.

## Writing Better Skill Files

- Start with the exact use case for the skill.
- List the most important do and do not rules near the top.
- Include examples for rules that are easy to misread.
- Remove typos, vague wording, and duplicated rules.
- Keep the file high-signal so an agent can skim it quickly.

## ICP-Specific Guidance

- Use the skill files in `.agents/skills/icp/` for Internet Computer tasks.
- Prefer official ICP documentation over assumptions or memory.
- Reuse existing repo patterns when they already solve the problem cleanly.

## Review Checklist

- Is the purpose obvious in the first few lines?
- Are the rules specific enough for an agent to follow?
- Does the file say what to do, what not to do, and where to look next?
- Are there any conflicting or outdated instructions that should be removed?