# Unified Senior AI & Fullstack Engineering Standards

This document defines the mandatory programming standards, architectural philosophy, and processes to ensure high consistency, scalability, maintainability, and high-performance execution. AI Agents and human developers MUST strictly adhere to these rules.

## I. Core Philosophy & Principles
1. **KISS (Keep It Simple, Stupid)**: Do not over-engineer. The simplest solution that meets all requirements is the best one.
2. **Write for Humans**: Code is read much more often than it is written. Use clean code practices so any senior peer can understand the intent without external documentation.
3. **DRY (Don't Repeat Yourself)**: Abstract repeated logic into reusable modules, but avoid "premature abstraction."
4. **YAGNI (You Ain't Gonna Need It)**: Do not implement features or optimizations until they are actually required.
5. **Separation of Concerns (SoC)**: Logic must be isolated by domain. Business logic should never reside in the UI or direct API routing layers.
6. **Statelessness**: Aim for stateless services to facilitate horizontal scaling and easier debugging.
7. **API-First Design**: Define contracts (interfaces/schemas) before implementation. Components communicate via these strictly defined boundaries.

## II. General Coding & Naming Conventions
1. **Naming Styles**:
    - **Variables/Functions**: `snake_case` in Python (e.g., `user_input_text`), `camelCase` in TS/JS.
    - **Classes/Components**: `PascalCase` (e.g., `ChatbotWorkflow`, `SemanticCache`).
    - **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKEN_LIMIT`).
2. **Clarity over Brevity**: Variable and function names must be descriptive. Avoid single-letter variables except for loop indices.
3. **Data Schemas**: Pydantic models or TS Interfaces should end with `Schema` or `Model` to distinguish them from processing logic (e.g., `MessageInputSchema`).
4. **No Print Statements**: Strictly avoid using `print()`. Always use the standard `logging` library with appropriate levels (DEBUG, INFO, WARNING, ERROR).
5. **Strict Typing & Validation**: Mandatory type hints in Python and strict typing in TypeScript. Always use Pydantic (Python) or Zod (TS) to validate incoming data at system boundaries.
6. **No Hard-coding**: Pass configuration parameters via `.env` files or function arguments.

## III. System Architecture & Component Rules
The system follows a "Divide and Conquer" principle. If a module is too complex, break it down (e.g., loaders, processors, chains, interfaces).

### 1. Frontend (The Interface Layer)
- **Modular Components**: Build small, reusable UI units.
- **State Management**: Keep local state local; only lift state when multiple distant components require it.
- **Goal**: Minimize bundle size and maximize accessibility (A11y).

### 2. Backend (The Logic & Data Layer)
- **Robust Error Handling**: Never return raw system errors to the client. Map internal exceptions to standard HTTP status codes.
- **Goal**: Ensure data integrity and secure, low-latency processing.

### 3. LLM Core (The Intelligence Layer)
- **RAG Optimization**: Use hybrid search (Vector + BM25) and semantic caching to reduce latency and costs.
- **Prompt Versioning**: Treat prompts as code. Maintain version control for all system instructions.
- **Agentic Orchestration**: Use frameworks like LangGraph for complex stateful logic; ensure clear state transitions.
- **Library Compliance**: Pass correct data types strictly when calling LangChain/LangGraph functions.

### 4. DevOps & Infrastructure (The Operation Layer)
- **Infrastructure as Code (IaC)**: Environments must be reproducible via scripts or configuration files.
- **Goal**: Zero-friction deployment and high system uptime.

### 5. System Interaction (Unidirectional Flow)
- Data flow should be predictable. **Avoid circular dependencies.**
- Frontend interacts with Backend via API; Backend interacts with LLM Core via specialized services. No component should bypass its immediate neighbor.
- Large components must communicate through standard data schemas without interfering with internal variables.

## IV. Senior Development & Testing Workflow
A Senior Developer does not start writing code immediately. Adhere to this process:
1. **Analysis**: Identify inputs, outputs, and resource constraints (Memory/GPU/Latency).
2. **Architecture**: Sketch the logic or create a flowchart.
3. **Decomposition**: Break down large problems into smaller sub-tasks. Aim for **no more than 50 lines of code per function**.
4. **Implementation**: Write clean code, prioritizing correctness before optimization.
5. **Optimization**: Optimize for memory or speed ONLY after ensuring the baseline runs correctly.

**Testing Workflow:**
Every completed module MUST undergo:
- **Unit Testing**: Test small functions with mock data.
- **Integration Testing**: Test coordination between modules (e.g., Cache to VectorDB).
- **Edge Case Testing**: Test with empty, excessively long, or malformed inputs.

## V. Strict Documentation & System Registry Policy
1. **Self-Documenting Code**: Code should explain "how." Comments should explain "why" (the intent). Explanations must not be longer than the code snippet itself. Use Google Style for Docstrings.
2. **STRICT RULE: Centralized Registry**: There shall be only **ONE** central documentation file: `system_description.md`. **DO NOT** create scattered `.md` files or fragmented documentation in sub-directories.
3. **Content Structure for `system_description.md`**: For every new function, algorithm, or significant component created, you must append an entry containing:
    - **Name**: Technical identifier.
    - **Internal Dependencies**: Libraries or other modules used.
    - **Purpose**: What problem does it solve?
    - **Process Flow**: A concise step-by-step description of its internal logic.
4. **Maintenance Strictness**: Any update to a component's logic MUST be accompanied by an immediate update to its entry in `system_description.md`. Failure to update this registry is considered a critical breaking change.