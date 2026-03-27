# Working Agreement

This is the lightweight equivalent of a spec-driven, agent-steered workflow for this repo.

## How Codex should work here

- Start from a written spec when implementing any non-trivial feature
- Keep each change focused on one feature slice at a time
- Avoid broad refactors unless the current spec requires them
- Update docs when the shape of the system changes
- Prefer code that is easy to hand over over code that is merely clever

## Definition of done

A feature slice is considered done when:

- The relevant spec is updated or confirmed
- The code is implemented
- Basic verification is performed
- Any new setup or operational detail is documented

## Usage discipline

To reduce surprise usage spikes:

- Ask for one feature or sub-feature at a time
- Prefer short specs over long brainstorming sessions in the middle of implementation
- Keep acceptance criteria explicit
- Pause between phases to review before continuing

## Session pattern

When we start a feature, we should usually have:

- A short problem statement
- A clear scope boundary
- A small list of acceptance criteria
- A note of anything intentionally deferred
