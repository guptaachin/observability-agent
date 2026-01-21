# Observability Agent Constitution

A lightweight, extensible foundation for agentic applications in observability.

## Core Principles

### I. Purpose: Learning Agentic Applications
Build foundational knowledge on how to construct agentic applications and explore their practical application in observability contexts. This project serves as a learning platform for understanding agent architectures, not a production system.

**Non-Negotiable**: Decisions prioritize educational value and clarity over production optimization.

### II. Minimalism (NON-NEGOTIABLE)
Implement only core functionality required to fulfill user stories. No advanced features, no autonomous behavior, no unsolicited intelligence.

**What qualifies**: Direct query interpretation, metric retrieval, formatted output.
**What doesn't**: Anomaly detection, multi-step reasoning, recommendations, explanations, corrective actions, state persistence across interactions.

**Rationale**: Minimalism enables rapid iteration, reduces complexity, and keeps focus on core learning objectives.

### III. Extensibility
Establish a stable, minimal foundation that future capabilities can build upon without refactoring core flows.

**How**: Define clear interfaces (contracts), use single-node agent pattern allowing node injection, keep data models stateless, document extension points.

**Example**: Adding a visualization node to the graph should not require changes to existing query node.

### IV. Accuracy & Clarity
All outputs must reflect real data from the observability system. Responses must be understandable and free from jargon or unexplained behavior.

**How**: Query real metrics only (no synthetic data), format results with context (units, time ranges, statistics), provide clear error messages with recovery suggestions.

**Rationale**: Users must trust the system's outputs to use it effectively in learning contexts.

### V. Education & Learning (NON-NEGOTIABLE)
This project prioritizes learning over testing coverage or production hardening.

**Implications**: 
- Tests can focus on core learning objectives rather than exhaustive coverage
- Code clarity takes precedence over optimization
- Comments explain "why" not just "what"
- Simple, readable implementations preferred over clever ones

### VI. Simplistic Directory Structure
Create nested code directories only when absolutely necessary. Prefer flat, co-located structures for discoverability.

**How**: `src/agent/`, `src/tools/`, `src/ui/`, `src/config/` (grouped by responsibility, not hierarchy).

---

## Requirements

### Technical Stack
- **Language**: Python 3.11+
- **Agent Framework**: LangGraph (single-node pattern)
- **LLM Integration**: LangChain (with OpenAI + Ollama support)
- **UI**: Gradio (lightweight, local-first)
- **Observability**: Grafana MCP server (Docker-based)
- **Testing**: pytest (tests can be minimal per learning priority)

### Non-Functional Requirements
- Query execution: < 30 seconds per request
- UI response: < 5 seconds typical
- Configuration: Environment variables + `.env` file
- Deployment: Runnable locally with `python src/main.py`

---

## Governance

### Constitutional Authority
This constitution defines non-negotiable principles for the observability agent project. All decisions must align with these principles or explicitly justify divergence.

### Amendment Process
1. **Propose**: Document proposed change and rationale
2. **Evaluate**: Assess against educational learning objectives
3. **Migrate**: Update dependent artifacts (templates, docs, code)
4. **Version Bump**: 
   - MAJOR: Principle removal/redefinition
   - MINOR: New principle added or section expanded
   - PATCH: Clarifications, wording, typo fixes
5. **Document**: Record change, date, and reason

### Compliance Verification
- Code reviews must verify new code aligns with Minimalism and Accuracy & Clarity
- Architecture decisions must justify extensibility approach
- Documentation must reflect current constitutional state

### Dependent Artifacts
- `.specify/templates/plan-template.md` - Scope and extensibility checks
- `.specify/templates/spec-template.md` - Requirement clarity and accuracy
- `.specify/templates/tasks-template.md` - Task categorization by principle
- `.specify/templates/commands/*.md` - Guidance files (remove agent-specific references)
- `README.md` - Setup and principle overview
- `docs/quickstart.md` - Usage examples reflecting core principles

**Version**: 1.0.0 | **Ratified**: 2026-01-21 | **Last Amended**: 2026-01-21
