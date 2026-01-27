# Observability Agent Constitution

## Core Principles

### I. Purpose: Education-Driven Agentic Learning
This project exists to learn how to build agentic applications and explore their use in observability. Every architectural and implementation decision prioritizes learning outcomes over production-grade completeness. Code should demonstrate core patterns clearly, not enterprise-ready robustness.

### II. Minimalism: Core Functionality Only
Only implement features directly necessary for basic interaction with observability systems via agents. No autonomous actions, no autonomous insights, no explanations of metric behavior, and no recommendations. The agent receives a query, retrieves data, and returns results—nothing more. Scope creep is actively avoided through strict validation of feature requests against this principle.

### III. Extensibility: Safe Expansion Foundation
Design the agent architecture with future expansion in mind, even if not implemented now. The single-node LangGraph structure should allow additional nodes and capabilities to be added without refactoring core flow. Tool interfaces should remain stable. Technology choices should not lock in future directions.

### IV. Accuracy & Clarity: Real Data, Clear Output
All data returned to users must reflect actual state from the observability stack. No synthetic data, no inferred values, no confidence scores without explicit grounding. Outputs must be easy to understand—prefer clear text and simple structured formats over raw API responses. Error messages must be explicit and actionable.

### V. For Education & Learning: Pragmatic Testing
Testing is valued for learning outcomes, not coverage metrics. Critical path integration tests are required; unit tests may be skipped if they don't advance understanding. Focus on demonstrating how the agent interacts with real systems, not on achieving test line counts.

### VI. Simplistic Directory Structure
Create nested code directories only when absolutely necessary. The project starts with flat `src/` and `tests/` structures. Subdirectories are added only when a single module grows beyond clear comprehension. Organization is inferred from code; avoid premature structural abstraction.

### VII. Minimal Code: Do Less, Learn More
Every line of code should earn its place. Avoid boilerplate, unnecessary abstraction layers, and "future-proofing" code for features that do not exist. Write the simplest correct implementation. Refactoring is only justified when code clarity degrades or modularity genuinely improves learning value.

## Technology & Implementation Constraints

- **LangGraph**: Limited to single-node graph architecture. No multi-node orchestration or complex state management.
- **LLM Support**: OpenAI and Ollama only. No additional providers unless core requirements change.
- **Grafana Integration**: Use Grafana MCP server exclusively; no direct API calls.
- **Configuration**: Environment variables and config files; no hardcoded credentials.
- **User Interface**: Gradio for lightweight local chat interface. Not intended for production deployment.

## Scope Boundaries

The following are explicitly NOT in scope:

- Metrics querying/analysis (beyond retrieval)
- Anomaly detection or statistical analysis
- Explanations or interpretations of metric behavior
- Recommendations or corrective actions
- Autonomous agent behavior (no unsolicited actions)
- Historical memory or context between sessions
- Complex agent graphs or multi-node orchestration
- Persistence beyond a single chat session

## Governance

**Amendment Process**: Constitution changes require a dated entry in this document and a rationale explaining the version bump. Version changes follow semantic versioning: MAJOR for principle removals/redefinitions, MINOR for new principles or materially expanded guidance, PATCH for clarifications and non-semantic refinements.

**Compliance**: All code and architectural decisions should be evaluated against these principles during design and review. When trade-offs are necessary, the rationale must be documented in commit messages or design notes.

**Development Guidance**: See `.specify/` templates and runtime guidance in project documentation for implementation workflows. This constitution is the source of truth for project values.

**Version**: 1.0.0 | **Ratified**: 2026-01-23 | **Last Amended**: 2026-01-23
