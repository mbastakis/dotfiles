---
name: mermaid-diagrams
description: Create, find, adapt, or improve Mermaid diagrams for software architecture, interactions, data flow, infrastructure, lifecycles, control flow, and processes. Use the local Graphlet and Smithers libraries for structural references when useful.
---

# Mermaid Diagrams

Understand the target before choosing references. The request and project are the source of truth; library diagrams supply structural ideas, not architectural facts.

Libraries:

- `~/Documents/notes/5-Sources/Graphlet Mermaid Diagrams/` for broad software architecture and interaction patterns.
- `~/Documents/notes/5-Sources/Smithers Orchestration Patterns/` for control-flow primitives, composite orchestration patterns, and concrete workflow recipes.

## Route

- **Small, specified diagram:** draw directly; browse references only when they would materially improve the structure.
- **Repository architecture:** inspect the project first, choose distinct views, then browse for a reference suited to each view.
- **Find examples:** return existing diagrams and explain the prospective role of each; do not draw.
- **Improve a diagram:** identify its communication problem before browsing or editing.

## Repository Architecture

Derive the architecture from documentation, manifests, deployment configuration, entry points, major modules, adapters, persistence, and external integrations.

Choose only views supported by the evidence. Commonly useful views are:

1. system context
2. internal components or containers
3. representative runtime sequence
4. deployment and infrastructure
5. one focused lifecycle, authentication, background process, or data-flow view

Use `flowchart` for topology and processes, `sequenceDiagram` for ordered interactions, `stateDiagram-v2` for lifecycles, and `erDiagram` for data relationships.

**Done when:** each chosen view answers a distinct architectural question and its required relationships are known or explicitly uncertain.

## Browse References

Choose the library by communication need: Graphlet for architecture and interactions; Smithers for branching, loops, retries, fan-out/fan-in, human gates, orchestration, and workflow recipes. Search filenames and Mermaid source by architectural purpose—for example reverse proxy, authentication, request lifecycle, container boundary, provisioning, retry, or background work. Inspect promising diagrams directly.

For a substantial diagram, choose one primary structural reference and optionally one secondary reference for a specific concern. Prefer similarity of relationships and communication goal over title similarity. Reject references that imply unsupported architecture.

**Done when:** each selected reference has a clear role, and unsuitable patterns have not leaked into the target design.

## Draw

Adapt useful direction, participant ordering, boundaries, decision placement, edge semantics, and failure-path structure. Include only components and relationships supported by project evidence, user-provided facts, or explicit assumptions.

Do not represent absent infrastructure as a component. Put negative findings and evidence limits in notes instead.

**Done when:** every node and edge is supported or qualified, and each diagram remains readable for its intended audience.

## Validate and Report

Check Mermaid syntax, readable labels, distinct views, and absence of copied reference-domain entities. Do not present plausible third-party internals as verified behavior.

For substantial architecture documentation, briefly name the primary reference and its role beside each diagram. For small diagrams, omit reference commentary unless it helps the user review the result.

**Done when:** the output is syntactically credible, evidence-grounded, and clear about material uncertainty.
