My recommendation is to make MATRIX AI the next-generation architecture and FRIDAY its existing working foundation.

Don't throw FRIDAY away and start from scratch. Build MATRIX around the capabilities that already work, gradually replacing weak internal components while retaining existing tools and functionality.

I'd call the document:

MATRIX AI — MASTER DEVELOPMENT & EVOLUTION BLUEPRINT
Recommended
master
specification
 
Local-first
 
RTX
3050
·
8
GB
VRAM

The biggest changes I'd make to your original blueprint are:

Replace the assumption of a traditional multi-agent system with a resource-aware agent orchestration system.

Add a persistent cognitive engine with task recovery.

Make verification evidence-based and calibrated.

Make security independent of the language model.

Add model benchmarking before selecting the best brain.

Add project understanding and dependency-aware code editing.

Make the entire system measurable through repeatable evaluations.

Add strict migration rules so existing FRIDAY capabilities aren't lost.

There are also two important corrections:

A 9B model advertised as 6.6 GB will not necessarily fit completely in 8 GB VRAM alongside its KV cache and runtime overhead.

Windows Job Objects and restricted tokens improve containment, but they do not provide the same isolation as a properly configured VM or container.

Below is the master document I'd actually use to direct development.

Writing


MATRIX AI
Master System Architecture, Development & Evolution Blueprint
Document Version: 1.0
Prepared: 2 November 2026
Project: MATRIX AI
Foundation: Existing FRIDAY Mark XLIX system
Primary Language: Python 3.12
Operating System: Windows
Hardware Target: NVIDIA RTX 3050 8 GB VRAM, 32 GB RAM, 8-core CPU
Deployment: Local-first, single-machine architecture
Primary Objective: Develop a powerful, modular, autonomous local intelligence platform with advanced reasoning, research, memory, coding, multimodal capabilities, tool execution, and controlled agent orchestration.

PART 1 — PROJECT MISSION
1.1 Primary Objective
MATRIX AI is the next evolutionary generation of the existing FRIDAY assistant.

The objective is not to create another basic chatbot.

MATRIX must become a unified local intelligence platform capable of:

Understanding natural-language instructions.
Reasoning through complex problems.
Planning and executing multi-step tasks.
Researching information using online and offline sources.
Reading, understanding, and modifying project files.
Developing, testing, and debugging software.
Controlling supported desktop applications.
Understanding screenshots, images, and documents.
Processing speech and generating natural voice responses.
Maintaining persistent, organized memory.
Retrieving information from previous conversations and projects.
Coordinating specialized AI agents.
Checking its own work independently.
Detecting failures and recovering from interrupted tasks.
Producing complete documents, reports, and project files.
Operating without internet access when necessary.
The system must prioritize actual working capabilities over impressive-looking architecture.

1.2 Core Design Philosophy
The model is the intelligence component. Python is the control and execution infrastructure.

The model proposes decisions, generates plans, reasons about information, and requests tool operations.

Python controls:

Application execution.
Model management.
Agent orchestration.
Task state.
Tool execution.
Memory storage.
File operations.
Permissions.
Security enforcement.
Verification.
Logging.
Resource allocation.
User interface communication.
The model must never be the authority that grants itself permissions.

All external actions must pass through controlled Python interfaces.

1.3 Project Evolution Strategy
MATRIX must evolve from FRIDAY rather than replace it through an unnecessary rewrite.

The existing FRIDAY system is the functional baseline.

Existing capabilities include:

24 exposed tools.
15 skill actions.
Local speech recognition and synthesis.
Desktop and operating system controls.
File processing.
Workspace editing with backups.
Multi-file development agent.
Single-file coding assistant.
Vision and OCR.
Local BM25 retrieval.
Persistent memory.
Independent code auditing.
Verification and temporal edit history.
Python execution protections.
Workspace preview server.
PyQt6 interface.
Phone dashboard.
All existing functionality must be inventoried and preserved unless a documented replacement is demonstrably better.

Migration rule
No working FRIDAY capability may be removed merely because MATRIX introduces a new architectural component.

Every replacement must pass feature-parity tests before the old implementation is retired.

PART 2 — NON-NEGOTIABLE CONSTRAINTS
2.1 Hardware

Resource	Available
GPU	NVIDIA RTX 3050
VRAM	8 GB
System RAM	32 GB
CPU	8 cores
Operating system	Windows
Python	3.12
Initial context target	8,192 tokens
All components must be designed around these constraints.

Do not assume that every model can remain loaded simultaneously.

Do not assume that a model's download size represents its complete runtime memory requirement.

2.2 Infrastructure Restrictions
The initial implementation must not require:

Administrator permissions.
A system reboot.
Docker.
WSL or WSL2.
Windows Sandbox.
Paid cloud AI services.
Remote inference.
External telemetry.
Git is not currently installed. Version-control support may be added later, but it cannot be a development prerequisite.

2.3 Privacy
Local operation is the default.

The following must remain local:

Conversations.
User memory.
Project files.
Code generation.
Local model inference.
Speech recognition.
Text-to-speech.
Local verification.
Application logs.
Internet access must be explicitly controlled.

Network research and external verification must disclose that information leaves the machine and obtain the required user authorization.

Never silently upload files, conversation history, or private information.

2.4 Data Protection
Back up files before modifying them.
Preserve original project files.
Use reversible operations.
Never silently overwrite important data.
Never claim successful execution without actual evidence.
Never conceal failed verification.
Never turn uncertain claims into verified facts.
PART 3 — MASTER ARCHITECTURE
3.1 Architectural Layers
MATRIX should use nine major layers.

User Interface Layer.
Conversation and Context Layer.
Cognitive Intelligence Layer.
Agent Orchestration Layer.
Model Runtime Layer.
Tool and Execution Layer.
Memory and Knowledge Layer.
Verification and Security Layer.
Storage and Diagnostics Layer.
Each layer must have documented interfaces.

Components should communicate through defined Python interfaces and structured data rather than uncontrolled direct dependencies.

3.2 Target Architecture

text
                    MATRIX AI
                        |
                USER INTERFACE
                        |
              CONVERSATION MANAGER
                        |
               INTENT CLASSIFIER
                        |
                COGNITIVE ENGINE
                        |
          +-------------+-------------+
          |             |             |
       PLANNER       MEMORY        CONTEXT
          |             |             |
          +-------------+-------------+
                        |
                AGENT ORCHESTRATOR
                        |
        +---------------+---------------+
        |               |               |
     RESEARCH         CODING          REASONING
      AGENT           AGENT            AGENT
        |               |               |
        +---------------+---------------+
                        |
                 TOOL REGISTRY
                        |
              SECURITY PERMISSION BROKER
                        |
              CONTROLLED EXECUTION
                        |
              VERIFICATION ENGINE
                        |
               QUALITY CONTROLLER
                        |
                RESPONSE MANAGER
                        |
                       USER
This architecture is a logical separation, not a requirement to run nine separate AI models or processes.

PART 4 — MODEL INTELLIGENCE AND RESOURCE MANAGEMENT
4.1 Model Strategy
Create a hardware-adaptive model management system.

The model registry must support different models for different responsibilities.

Proposed roles:


Role	Responsibility
Primary	General reasoning and conversation
Coding	Programming and debugging
Fast	Classification and lightweight requests
Vision	Images and screenshots
Auditor	Independent review
Embedding	Semantic retrieval
Speech	Audio input and output
These are logical roles.

Models must be loaded only when required.

4.2 Initial Model Candidates
The existing Qwen 2.5 7B remains the baseline.

Benchmark these candidates:

Qwen 3.5 9B, if the available runtime and model format support it.
Qwen 2.5 Coder 7B.
Qwen 3.5 4B.
Other compatible quantized models that demonstrate measurable improvements.
Do not select models based solely on parameter count or advertised benchmarks.

Evaluate actual performance on MATRIX tasks.

4.3 Model Evaluation
Create a repeatable benchmark of at least 50 representative tasks.

Include:

Natural-language understanding.
Tool selection.
Multi-step planning.
JSON generation.
Code generation.
Code repair.
Context retention.
Instruction following.
Verification.
Failure recovery.
Measure:

Task completion rate.
Tool-call accuracy.
Invalid tool-call frequency.
Coding test pass rate.
First-token latency.
Tokens per second.
Peak VRAM.
Peak RAM.
Model loading time.
A model should only replace the existing primary model if it provides a meaningful measured improvement without destabilizing the system.

4.4 Model Runtime Abstraction
Support:

Ollama.
llama.cpp-compatible GGUF runtimes.
Compatible OpenAI-style local inference endpoints.
Transformers where hardware permits.
Create a common interface:


python
class ModelBackend:

    def load(self, model_config):
        ...

    def unload(self):
        ...

    def generate(self, messages, config):
        ...

    def stream(self, messages, config):
        ...

    def get_status(self):
        ...
The implementation must use appropriate asynchronous interfaces where needed.

4.5 Resource Manager
Create:

core/resource_manager.py

Responsibilities:

Detect available VRAM.
Detect available RAM.
Monitor CPU utilization.
Monitor model loading.
Estimate model memory requirements.
Schedule model switching.
Unload inactive optional models.
Prevent uncontrolled concurrent model loading.
Report resource shortages.
Provide graceful fallback behavior.
Initial policy:


json
{
  "max_concurrent_large_models": 1,
  "monitor_gpu_memory": true,
  "monitor_system_memory": true,
  "lazy_load_optional_models": true,
  "unload_idle_models": true,
  "allow_cpu_offload": true,
  "protect_application_stability": true
}
The scheduler must never assume that an advertised model size guarantees successful loading.

PART 5 — THE MATRIX COGNITIVE ENGINE
This is one of the most important new components.

Create:

core/cognitive_engine.py

The cognitive engine coordinates understanding, planning, decision-making, execution, and recovery.

5.1 Request Classification
Every incoming request should be classified.

Possible categories:

Conversation.
Information request.
Research.
Coding.
File operation.
Desktop automation.
Document processing.
Memory retrieval.
Complex multi-step task.
High-risk operation.
The classifier should determine:

Required capabilities.
Required models.
Task complexity.
Permission requirements.
Whether planning is necessary.
Whether independent verification is necessary.
Simple requests should not trigger unnecessary agents.

5.2 Planning Engine
Create:

core/task_planner.py

The planner must generate structured task plans.

Every complex plan should contain:

Original objective.
Constraints.
Required tools.
Dependencies.
Execution steps.
Expected results.
Success criteria.
Risk assessment.
Verification requirements.
Failure handling.
Example:


json
{
  "task_id": "task_001",
  "goal": "Improve game fog",
  "status": "PLANNING",
  "steps": [
    {
      "id": 1,
      "action": "Inspect scene initialization",
      "status": "PENDING"
    },
    {
      "id": 2,
      "action": "Locate fog update logic",
      "status": "PENDING"
    },
    {
      "id": 3,
      "action": "Apply guarded modification",
      "status": "PENDING"
    },
    {
      "id": 4,
      "action": "Run regression tests",
      "status": "PENDING"
    }
  ],
  "success_criteria": [
    "Fog becomes visibly denser",
    "Existing animation remains intact",
    "No unrelated functions are modified",
    "Validation passes"
  ]
}
5.3 Persistent Task Manager
Create:

core/task_manager.py

Tasks must survive application restarts.

Supported states:

CREATED
PLANNING
READY
RUNNING
WAITING_FOR_TOOL
VERIFYING
NEEDS_REVISION
PAUSED
COMPLETED
FAILED
CANCELLED
Persist:

Task ID.
Original request.
Plan.
Current step.
Tool execution history.
Results.
Errors.
Checkpoints.
Retry count.
Verification status.
Completion summary.
The system must support safe recovery from interrupted tasks.

Before resuming, validate that the original workspace and relevant files still match the expected state.

Never blindly repeat a non-idempotent operation.

5.4 Decision Engine
Create:

intelligence/decision_engine.py

Evaluate available approaches before execution.

The engine should consider:

Reliability.
Execution time.
Resource consumption.
Security.
Reversibility.
Tool availability.
Expected outcome.
The objective is not to produce endless internal reasoning.

The objective is to select a practical, testable course of action.

PART 6 — RESOURCE-AWARE AGENT ORCHESTRATION
6.1 Agent Philosophy
MATRIX must use specialized agents where they provide measurable value.

It must not create artificial multi-agent conversations simply to appear intelligent.

Agents may share a model backend, provided their tasks, context, outputs, and responsibilities remain logically independent.

6.2 Agent Roles
Agent 01 — Master Orchestrator
Receives the user request.
Determines task complexity.
Selects the appropriate workflow.
Assigns specialized tasks.
Maintains execution state.
Monitors completion.
Handles failure recovery.
Agent 02 — Research Specialist
Searches the internet when authorized.
Searches local documents.
Retrieves documentation.
Extracts claims.
Tracks dates.
Detects contradictions.
Provides source provenance.
Agent 03 — Coding Specialist
Understands project structure.
Generates code.
Repairs code.
Produces minimal patches.
Generates tests.
Explains dependencies.
Agent 04 — Reasoning Specialist
Decomposes complex problems.
Compares alternatives.
Identifies constraints.
Evaluates proposed approaches.
Detects missing requirements.
Agent 05 — Independent Verification Specialist
Reviews actual changes.
Checks requirements.
Evaluates evidence.
Inspects test results.
Identifies regressions.
Can reject an output.
Agent 06 — Memory Specialist
Retrieves relevant memories.
Identifies useful information.
Organizes approved memories.
Detects duplicate information.
Identifies stale claims.
Agent 07 — Document Specialist
Processes documents.
Extracts structured information.
Creates reports.
Produces downloadable files.
Preserves citations and source references.
6.3 Agent Communication
Use structured task messages.


json
{
  "task_id": "task_001",
  "agent": "coding_agent",
  "status": "COMPLETED",
  "input": "Modify the fog update logic",
  "output": {
    "files_changed": [],
    "changes": [],
    "tests": [],
    "uncertainties": []
  },
  "requires_verification": true
}
Every agent must have:

Maximum execution time.
Maximum retry count.
Maximum output size.
Defined input schema.
Defined output schema.
Explicit completion criteria.
Cancellation support.
No uncontrolled agent loops.

6.4 Independent Review
The auditor must receive the original requirements, original files, modified files, actual diff, and execution results.

It must not simply approve code written by another model.

Where possible, use a different model family or independently generated tests.

If only one suitable local model is available, use deterministic checks and tests as additional independent evidence.

PART 7 — PROJECT UNDERSTANDING ENGINE
This is a major addition to the original architecture.

Create:

core/project_intelligence.py

MATRIX must develop a structured understanding of opened software projects.

Capabilities:

Project file discovery.
Language identification.
Dependency detection.
Entry-point detection.
Function and class indexing.
Import relationship analysis.
Configuration discovery.
Test discovery.
Asset discovery.
Project architecture summaries.
Change impact analysis.
7.1 Project Index
Store:

File paths.
File hashes.
File sizes.
Modification timestamps.
Language.
Functions.
Classes.
Imports.
Dependencies.
Related tests.
Relevant documentation.
Use incremental indexing rather than repeatedly scanning the entire project.

7.2 Change Impact Analysis
Before editing a file, identify:

Which functions depend on it.
Which other files import it.
Which tests cover it.
Which configurations reference it.
Which assets it uses.
The system should prefer minimal changes.

7.3 Editing Rules
Preserve the existing FRIDAY workspace safeguards.

Every modification must:

Identify the exact target file.
Read the relevant original code.
Create a backup.
Generate a targeted patch.
Validate the patch.
Apply the patch.
Inspect the actual diff.
Run relevant tests.
Record the result.
Support rollback.
Never replace large sections of code when a targeted modification is sufficient.

PART 8 — ADVANCED VERIFICATION ENGINE
Create:

verification/evidence_engine.py

Retain and extend the existing FRIDAY verification system.

8.1 Evidence Model
Every important claim should be represented with:

Claim text.
Source identity.
Source type.
Original location.
Retrieval timestamp.
Publication timestamp, when known.
Effective date, when relevant.
Evidence excerpt.
Supporting or contradicting relationship.
Source independence group.
Verification status.
8.2 Source Independence
Do not count repeated copies of one source as independent confirmation.

Identify:

Original sources.
Derivative articles.
Copied documentation.
Mirrors.
Repeated local backups.
Shared upstream references.
A collection of matching files is not automatically a collection of independent witnesses.

8.3 Temporal Verification
Distinguish:

Publication date.
Effective date.
Modification date.
Retrieval date.
Historical validity period.
Support historical questions such as:

What changed?
When did it change?
What was true at a particular time?
Which source supported the earlier value?
8.4 Verification Status
Use:

VERIFIED
STRONGLY_SUPPORTED
PARTIALLY_VERIFIED
AMBIGUOUS
UNVERIFIED
STALE
CONTRADICTED
Do not treat a numerical confidence score as calibrated unless tested against known examples.

Maintain separate assessments for:

Source quality.
Evidence relevance.
Source independence.
Freshness.
Agreement.
Overall claim support.
8.5 Research Network Policy
Offline verification must remain available.

External verification requires authorization.

When authorized:

Retrieve actual source pages where possible.
Preserve source URLs.
Record retrieval times.
Extract publication dates.
Detect stale information.
Identify conflicting claims.
Preserve relevant excerpts.
Record failed retrieval attempts.
Search snippets alone must not be presented as equivalent to complete source verification.

PART 9 — HYBRID MEMORY AND RAG
9.1 Memory Architecture
Create four memory layers.

Short-Term Memory
Current conversation.
Active task.
Recent messages.
Current tool results.
Long-Term Memory
Approved preferences.
Persistent instructions.
Important facts.
Ongoing project information.
Episodic Memory
Previous tasks.
Completed operations.
Troubleshooting history.
Decisions and outcomes.
Semantic Memory
Searchable documents.
Technical knowledge.
Project documentation.
Relevant code passages.
9.2 Storage
Use SQLite for structured data.

Use local vector storage only where benchmarking demonstrates value.

Candidate technologies:

FAISS.
Chroma.
SQLite vector extensions.
Retain BM25 for exact keyword, identifier, function-name, and filename retrieval.

9.3 Hybrid Retrieval
Use:

Exact keyword retrieval.
BM25 ranking.
Semantic embedding retrieval.
Metadata filtering.
Deduplication.
Reranking.
Source provenance.
Combine retrieval methods rather than replacing BM25.

9.4 Memory Maintenance
Implement:

Duplicate detection.
Contradiction detection.
Stale memory detection.
Expiration policies.
Memory provenance.
User-controlled deletion.
Full memory reset.
Approved memory promotion.
Never automatically turn every conversation statement into a permanent verified fact.

9.5 Embedding Resource Policy
Use a small local embedding model.

Prefer CPU execution initially to avoid unnecessary VRAM competition.

Benchmark retrieval quality and latency before expanding the embedding subsystem.

PART 10 — CONTROLLED EXECUTION AND SECURITY
Create:

security/permission_broker.py

security/execution_policy.py

sandbox/worker_manager.py

10.1 Security Philosophy
Security must not depend on the model following instructions correctly.

The Python application must independently enforce:

Tool permissions.
Filesystem permissions.
Network permissions.
Execution limits.
User authorization.
Workspace boundaries.
10.2 Permission Levels
Level 0 — Read-only
Read approved documents.
Search approved files.
Retrieve memory.
Inspect system information.
Level 1 — Limited local operations
Calculations.
Temporary files.
Document analysis.
Non-destructive operations.
Level 2 — Controlled modifications
Project editing.
File creation.
Approved testing.
Reversible workspace operations.
Level 3 — Explicitly authorized operations
External network access.
Dependency installation.
Important filesystem changes.
Consequential system actions.
Permission levels must be enforced by Python, not merely described in prompts.

10.3 Windows Execution Isolation
Investigate and implement the strongest practical unprivileged execution model.

Candidates:

Separate worker processes.
Windows Job Objects.
Restricted access tokens.
Low-integrity execution where practical.
Dedicated temporary directories.
Explicit filesystem allowlists.
Restricted environment variables.
Process and resource limits.
Do not represent these controls as a complete security boundary.

The existing Python AST gate and audit hook must remain as additional defense layers.

Generated JavaScript, shell, and other executable languages must have separate policies.

Do not allow unrestricted generated code to run with the main application's privileges.

10.4 Execution Workflow

text
REQUEST
   |
VALIDATION
   |
PERMISSION CHECK
   |
BACKUP / TEMPORARY WORKSPACE
   |
RESTRICTED EXECUTION
   |
OUTPUT CAPTURE
   |
TESTING
   |
INDEPENDENT REVIEW
   |
APPROVAL / REJECTION
10.5 Security Failure
A security failure must stop the relevant operation.

Do not retry by weakening permissions.

Preserve the error and report the blocked action.

PART 11 — SELF-CORRECTION AND QUALITY CONTROL
Create:

intelligence/reflection.py

verification/quality_controller.py

11.1 Five-Stage Pipeline
Stage 1 — Understand
Identify the actual objective and constraints.

Stage 2 — Plan
Create an explicit plan and success criteria.

Stage 3 — Execute
Use validated tools and controlled operations.

Stage 4 — Verify
Inspect the actual results.

Stage 5 — Correct
Make targeted corrections when failures are understood.

11.2 Retry Policy

json
{
  "self_correction": {
    "enabled": true,
    "maximum_retries": 3,
    "verify_before_delivery": true,
    "stop_on_security_failure": true,
    "require_tests_for_code": true,
    "preserve_original_failure": true
  }
}
A correction attempt must have a specific reason.

Do not repeatedly regenerate code without diagnosing the failure.

11.3 Independent Test Generation
Where practical, the verification agent should generate tests independently of the coding agent.

Test:

Original functionality.
New functionality.
Edge cases.
Regression conditions.
Error handling.
Security boundaries.
11.4 Final Quality Checklist
Before marking a complex task complete:

User requirements understood.
Required operations executed.
Expected files created.
Actual changes inspected.
Tests actually executed.
Test results recorded.
Security checks passed.
Verification status recorded.
Known limitations disclosed.
Rollback information available.
PART 12 — RESEARCH ENGINE
Create:

research/research_engine.py

research/source_manager.py

research/temporal_engine.py

research/citation_manager.py

Capabilities:

Live web research when authorized.
Local documentation retrieval.
Technical documentation search.
News and research retrieval.
Price and comparison research.
Source extraction.
Date tracking.
Historical comparison.
Citation generation.
Contradiction detection.
Research must distinguish:

Current facts.
Historical facts.
Predictions.
Opinions.
Unverified statements.
The system must never fabricate search results, citations, or retrieved documents.

PART 13 — MULTIMODAL SYSTEM
Create:

multimodal/vision.py

multimodal/audio_manager.py

multimodal/speech_to_text.py

multimodal/text_to_speech.py

13.1 Vision
Retain the existing local Qwen vision integration.

Support:

Screenshot analysis.
OCR.
Image understanding.
Document image extraction.
Visual inspection.
Continuous screen monitoring.
13.2 Voice
Retain:

faster-whisper.
Kokoro TTS.
Microphone capture.
Streaming speech.
Interrupt handling.
Mute and playback controls.
13.3 Phone Microphone
Complete real-device validation.

Test:

Browser microphone permissions.
Audio format compatibility.
PCM buffering.
Four-second windows.
Silence detection.
Partial speech.
Long speech.
Background noise.
Duplicate commands.
Dashboard reconnection.
End-to-end command execution.
Record actual measurements.

Synthetic PCM tests must not be treated as proof of real-device functionality.

13.4 Model Scheduling
Optional vision and audio models should load only when needed.

Avoid unnecessary competition for GPU memory.

PART 14 — CONVERSATION AND CONTEXT MANAGEMENT
Create:

core/conversation_manager.py

core/context_manager.py

Support:

Multiple conversations.
Persistent history.
Conversation search.
Streaming.
Message cancellation.
Message regeneration.
Model selection.
Tool visibility.
File attachments.
Conversation export.
Context summarization.
14.1 Context Budgeting
Implement:

Token estimation.
Context allocation.
Recent-message retention.
Relevant memory injection.
Tool-result compression.
Document chunk retrieval.
Task-state injection.
Never assume every model has the same context window.

Never silently discard important task information.

14.2 Prompt Management
Keep separate prompts for:

Main assistant.
Planner.
Coding agent.
Research agent.
Auditor.
Tool selection.
Version prompts and test changes against the evaluation suite.

PART 15 — CENTRALIZED TOOL SYSTEM
Create:

tools/registry.py

All existing FRIDAY tools must be registered through a compatible interface.

Preserve the 24 existing tool declarations during migration.

Every tool must define:

Name.
Description.
Input schema.
Output schema.
Permission level.
Timeout.
Availability.
Error behavior.
Idempotency characteristics where relevant.
15.1 Tool Categories
Group tools into:

Conversation.
Desktop.
Filesystem.
Coding.
Research.
Documents.
Memory.
Verification.
Vision.
Audio.
System monitoring.
Only expose relevant tool definitions to the model for the current task when supported by the existing inference backend.

15.2 Structured Tool Calling
Every tool request must undergo:

Name validation.
Schema validation.
Argument validation.
Permission validation.
Execution.
Result normalization.
Error handling.
Audit logging.
Never execute arbitrary model-generated function names.

PART 16 — DATABASE AND STORAGE
Use SQLite initially.

Create a structured database with migrations.

Recommended tables:


text
conversations
messages
memories
memory_sources
tasks
task_steps
agents
tool_executions
documents
document_chunks
research_sources
research_claims
verification_results
project_indexes
model_registry
system_settings
audit_logs
performance_metrics
Large files should remain in the filesystem.

The database should store metadata and references rather than unnecessary copies of every file.

Protect secrets separately from ordinary application data.

PART 17 — PERFORMANCE AND DIAGNOSTICS
Create:

core/diagnostics.py

core/performance_monitor.py

Measure:

Startup time.
Model load time.
First-token latency.
Generation speed.
Tool execution time.
Verification time.
TTS latency.
STT latency.
Peak VRAM.
Peak RAM.
CPU utilization.
Failed requests.
Retry frequency.
Task completion time.
Use SQLite for local metrics.

Build a performance dashboard.

17.1 Model Scheduling
Support:

Lazy loading.
Idle unloading.
Model switching.
Resource warnings.
CPU fallback where practical.
Maximum concurrent large-model policy.
17.2 Performance Priorities
Optimize in this order:

Tool-call reliability.
Model selection accuracy.
Task completion rate.
Coding reliability.
Startup and inference latency.
Memory and retrieval performance.
Do not optimize token generation speed at the expense of correctness.

PART 18 — USER INTERFACE
Retain the existing PyQt6 interface initially.

Do not rebuild the UI until the core architecture is stable.

Future interface options may include:

FastAPI backend.
WebSocket communication.
React frontend.
Local browser dashboard.
18.1 Main Interface
Display:

Conversation history.
Streaming responses.
Current model.
Active task.
Agent activity.
Tool execution.
File attachments.
Task cancellation.
Verification results.
18.2 System Dashboard
Display:

CPU usage.
RAM usage.
GPU usage.
VRAM usage.
Model loading.
Active tasks.
Tool status.
Recent errors.
Performance metrics.
18.3 Settings
Configure:

Model roles.
Inference backend.
Context size.
Model quantization.
Resource limits.
Memory settings.
Research permissions.
Sandbox permissions.
Voice settings.
Logging.
PART 19 — EVALUATION AND BENCHMARKING
Create:

tests/evaluation/

tests/benchmarks/

The evaluation system is mandatory.

A feature is not complete merely because the model produced a convincing response.

19.1 Baseline Preservation
The existing 11 FRIDAY capability tests must continue passing.

The original 24 tools must remain functional.

All existing workspace backups and verification behavior must be preserved.

19.2 Test Categories
Functional
Model communication.
Tool execution.
Memory persistence.
File operations.
Workspace editing.
Voice operation.
Vision.
Task persistence.
Research retrieval.
Intelligence
Reasoning.
Planning.
Tool routing.
Context retention.
Multi-step execution.
Error diagnosis.
Recovery.
Security
Path traversal rejection.
Unauthorized file access rejection.
Permission enforcement.
Process restrictions.
Network restrictions.
Malicious document instruction handling.
Backup and rollback.
Reliability
Interrupted tasks.
Model failures.
Tool failures.
Database recovery.
Model switching.
Resource exhaustion.
Application restart.
19.3 Benchmark Reporting
Every evaluation run should record:


text
MODEL:
MODEL VERSION:
QUANTIZATION:
CONTEXT SIZE:
GPU CONFIGURATION:

TASKS:
PASSED:
FAILED:
PARTIAL:

TOOL ACCURACY:
CODING SUCCESS:
VERIFICATION ACCURACY:
AVERAGE LATENCY:
P95 LATENCY:

PEAK VRAM:
PEAK RAM:

KNOWN LIMITATIONS:
Never invent benchmark measurements.

PART 20 — TARGET DIRECTORY STRUCTURE
MATRIX should evolve toward the following logical organization.

Existing FRIDAY files should be migrated gradually.


text
MATRIX_AI/
|
|-- main.py
|-- requirements.txt
|-- README.md
|-- CHANGELOG.md
|
|-- core/
|   |-- application.py
|   |-- friday_engine.py
|   |-- conversation_manager.py
|   |-- context_manager.py
|   |-- cognitive_engine.py
|   |-- task_manager.py
|   |-- task_planner.py
|   |-- orchestrator.py
|   |-- model_manager.py
|   |-- resource_manager.py
|   |-- diagnostics.py
|   |-- event_system.py
|
|-- intelligence/
|   |-- reasoning.py
|   |-- planning.py
|   |-- decision_engine.py
|   |-- reflection.py
|   |-- uncertainty.py
|
|-- agents/
|   |-- base_agent.py
|   |-- research_agent.py
|   |-- coding_agent.py
|   |-- reasoning_agent.py
|   |-- verification_agent.py
|   |-- memory_agent.py
|   |-- document_agent.py
|
|-- research/
|   |-- research_engine.py
|   |-- search_engine.py
|   |-- source_manager.py
|   |-- citation_manager.py
|   |-- temporal_engine.py
|   |-- fact_checker.py
|
|-- memory/
|   |-- memory_manager.py
|   |-- short_term.py
|   |-- long_term.py
|   |-- episodic_memory.py
|   |-- semantic_memory.py
|   |-- memory_retrieval.py
|   |-- vector_store.py
|
|-- intelligence_data/
|   |-- project_index.py
|   |-- code_indexer.py
|   |-- document_indexer.py
|
|-- tools/
|   |-- registry.py
|   |-- filesystem.py
|   |-- calculator.py
|   |-- web_search.py
|   |-- document_reader.py
|   |-- system_monitor.py
|
|-- security/
|   |-- permission_broker.py
|   |-- execution_policy.py
|   |-- path_validator.py
|   |-- audit_logger.py
|
|-- sandbox/
|   |-- executor.py
|   |-- worker_manager.py
|   |-- validation.py
|   |-- test_runner.py
|
|-- verification/
|   |-- evidence_engine.py
|   |-- auditor.py
|   |-- code_validator.py
|   |-- source_validator.py
|   |-- quality_controller.py
|
|-- multimodal/
|   |-- vision.py
|   |-- image_processor.py
|   |-- speech_to_text.py
|   |-- text_to_speech.py
|   |-- audio_manager.py
|
|-- database/
|   |-- database.py
|   |-- schema.py
|   |-- migrations/
|
|-- interface/
|   |-- app.py
|   |-- dashboard.py
|   |-- chat.py
|   |-- settings.py
|
|-- tests/
|   |-- test_capabilities.py
|   |-- test_security.py
|   |-- test_memory.py
|   |-- test_agents.py
|   |-- test_orchestrator.py
|   |-- test_verification.py
|   |-- evaluation/
|   |-- benchmarks/
|
|-- config/
|   |-- model_registry.json
|   |-- application.json
|   |-- permissions.json
|
|-- storage/
|   |-- conversations/
|   |-- memories/
|   |-- documents/
|   |-- generated_files/
|   |-- logs/
|
|-- docs/
    |-- ARCHITECTURE.md
    |-- API.md
    |-- SECURITY.md
    |-- DEVELOPMENT.md
    |-- MIGRATION.md
    |-- BENCHMARKS.md
This is the target organization, not an instruction to move all existing files immediately.

Preserve existing working module locations until compatibility and migration tests are complete.

PART 21 — DEVELOPMENT ROADMAP
Development must proceed incrementally.

Each phase must produce a functional, testable result.

PHASE 0 — EXISTING SYSTEM AUDIT
Priority: Critical

Before writing new code:

Inspect the complete FRIDAY project.
Inventory all 24 tools.
Inventory all 15 skills.
Map existing module dependencies.
Inspect configuration.
Inspect model settings.
Run all 11 existing tests.
Record current performance.
Identify duplicated functionality.
Identify technical debt.
Create a backup of the entire project.
Deliverables:

BASELINE_AUDIT.md
EXISTING_CAPABILITIES.md
ARCHITECTURE_MAP.md
MIGRATION_PLAN.md
Acceptance criteria:

Existing system understood.
All known working capabilities documented.
Existing tests have a recorded baseline.
No original project files modified.
PHASE 1 — MODEL AND PERFORMANCE UPGRADE
Priority: Critical

Implement:

Model benchmarking.
Model registry.
Resource manager.
Model switching.
Fast model routing.
Coding specialist integration.
Tool-call evaluation.
Acceptance criteria:

Existing model still works.
Candidate models are measured.
VRAM limits are respected.
Tool routing is benchmarked.
Failed model loads do not crash the application.
PHASE 2 — COGNITIVE ENGINE
Implement:

Intent classification.
Task planning.
Persistent task state.
Execution checkpoints.
Cancellation.
Recovery.
Success criteria.
Acceptance criteria:

Complex tasks can be planned.
Tasks survive restarts.
Interrupted tasks can resume safely.
Simple requests avoid unnecessary orchestration.
PHASE 3 — PROJECT INTELLIGENCE
Implement:

Project indexing.
Function and class discovery.
Dependency mapping.
Test discovery.
Change impact analysis.
Targeted editing improvements.
Acceptance criteria:

Projects can be indexed.
Relevant code can be located.
Proposed changes are targeted.
Existing workspace safeguards remain active.
PHASE 4 — VERIFICATION UPGRADE
Implement:

Evidence provenance.
Source independence.
Temporal validity.
Contradiction detection.
Calibrated confidence.
Independent test generation.
Improved auditor output.
Acceptance criteria:

Conflicting evidence is identified.
Stale evidence is distinguishable.
Verification results are reproducible.
Unsupported claims remain unverified.
PHASE 5 — MEMORY AND RAG
Implement:

SQLite memory storage.
Episodic memory.
Hybrid retrieval.
Embedding evaluation.
Project knowledge.
Memory expiration.
Contradiction management.
Acceptance criteria:

Memory persists across restarts.
Relevant information is retrieved.
Exact code identifiers remain searchable.
Users can inspect and delete memory.
No unnecessary GPU competition.
PHASE 6 — SECURITY AND EXECUTION
Implement:

Permission broker.
Restricted worker processes.
Windows Job Object integration.
Restricted-token investigation.
Filesystem policies.
Resource limits.
Language-specific execution policies.
Security regression tests.
Acceptance criteria:

Permission checks cannot be bypassed through model instructions.
Unauthorized operations are rejected.
Worker failures do not destabilize MATRIX.
Security limitations are documented honestly.
PHASE 7 — ADVANCED AGENT ORCHESTRATION
Implement:

Specialized agents.
Structured task communication.
Agent scheduling.
Independent review.
Bounded retries.
Failure recovery.
Acceptance criteria:

Agents perform genuinely distinct tasks.
Agent communication is structured.
Resource limits are respected.
Outputs are independently evaluated.
PHASE 8 — MULTIMODAL VALIDATION
Implement:

Real phone microphone tests.
Vision evaluation.
Voice latency measurements.
Audio interruption testing.
Dashboard reconnection testing.
Acceptance criteria:

Real microphone operation verified.
No unsupported claims based on synthetic tests.
Optional models load safely.
Existing voice operation remains functional.
PHASE 9 — INTERFACE AND INTEGRATION
Implement:

Cognitive engine visibility.
Task monitoring.
Agent activity.
Model selection.
Verification reports.
Performance dashboard.
Task recovery controls.
Acceptance criteria:

All major subsystems are accessible.
Long-running operations are visible.
Tasks can be cancelled.
Errors are understandable.
PHASE 10 — FINAL OPTIMIZATION
Implement:

Context optimization.
Retrieval optimization.
Caching.
Model scheduling.
Startup improvements.
Memory cleanup.
Benchmark-driven tuning.
Acceptance criteria:

Stable long-running operation.
No uncontrolled model loading.
No infinite agent loops.
No loss of existing functionality.
Performance improvements demonstrated by measurements.
PART 22 — MASTER DEVELOPMENT RULES
These instructions govern all AI-assisted MATRIX development.

22.1 Inspect Before Building
Always inspect existing files before modifying them.

Determine:

Current architecture.
Existing implementations.
Installed dependencies.
Python version.
Available hardware.
Model runtime.
Existing tests.
Configuration dependencies.
Never assume that a feature is missing simply because it is not in the target directory structure.

22.2 Incremental Development
Implement one phase at a time.

For each phase:

Explain the intended changes.
Identify affected files.
Identify risks.
Create backups.
Implement the smallest practical change.
Run import and syntax checks.
Run relevant unit tests.
Run regression tests.
Inspect the actual diff.
Update documentation.
Report results.
22.3 No Fake Implementations
Never present the following as complete when they are not:

Simulated agents.
Fake tool execution.
Fake internet research.
Placeholder memory.
Unexecuted tests.
Simulated verification.
Invented benchmark results.
Unverified sandbox protections.
Clearly identify incomplete components.

22.4 Backward Compatibility
Preserve:

Existing 24 tools.
Existing 15 skills.
Existing conversation functionality.
Existing desktop controls.
Existing voice capabilities.
Existing workspace editing.
Existing backups.
Existing preview functionality.
Existing configuration where practical.
Existing 11 passing tests.
Do not rename or relocate modules without a tested migration path.

22.5 Change Management
Every modification must be reversible.

Use timestamped backups.

Maintain a change log.

Record the reason for every architectural replacement.

Do not modify the user's actual projects while developing or testing MATRIX unless explicitly authorized.

22.6 Resource Management
Do not assume unlimited VRAM.

Do not load every agent model simultaneously.

Do not run unnecessary parallel inference.

Prefer efficient orchestration over artificial agent concurrency.

22.7 Honest Reporting
Never claim:

A feature works when it has not been tested.
A source is verified when it is not.
A security boundary is complete when it is not.
A model is faster without measurements.
A task is complete when required steps failed.
PART 23 — DOCUMENTATION REQUIREMENTS
Maintain:

README.md
ARCHITECTURE.md
API.md
SECURITY.md
DEVELOPMENT.md
MIGRATION.md
CHANGELOG.md
BENCHMARKS.md
CAPABILITIES.md
KNOWN_LIMITATIONS.md
Documentation must describe actual implementation status.

Maintain a capability classification:


Status	Meaning
IMPLEMENTED	Function exists
TESTED	Function passed documented tests
VERIFIED	Relevant behavior independently confirmed
PARTIAL	Some functionality remains incomplete
EXPERIMENTAL	Unproven or unstable
PLANNED	Not implemented
BLOCKED	Cannot currently be implemented under constraints
A planned feature must never be described as implemented.

PART 24 — REQUIRED DEVELOPMENT REPORT
At the end of every phase, produce:


text
MATRIX AI DEVELOPMENT REPORT

PHASE:
DATE:
STATUS:

OBJECTIVES:

FILES CREATED:

FILES MODIFIED:

FILES REMOVED:
(Include justification)

FEATURES IMPLEMENTED:

FEATURES STILL INCOMPLETE:

TESTS EXECUTED:

TESTS PASSED:

TESTS FAILED:

REGRESSION RESULTS:

PERFORMANCE RESULTS:

SECURITY CONSIDERATIONS:

KNOWN LIMITATIONS:

BACKUP LOCATION:

ROLLBACK PROCEDURE:

NEXT PHASE:
A phase cannot be marked complete if its mandatory acceptance criteria have not been met.

PART 25 — FINAL SYSTEM OBJECTIVE
The finished MATRIX AI platform should combine:

A powerful local conversational assistant.
Hardware-adaptive model management.
Advanced reasoning and planning.
Persistent task execution.
Resource-aware agent orchestration.
Local and authorized online research.
Evidence-based temporal verification.
Long-term memory.
Hybrid document and code retrieval.
Project architecture understanding.
Controlled code generation and editing.
Automated testing and correction.
Independent auditing.
Desktop and application automation.
Image and screen understanding.
Local speech recognition.
Natural text-to-speech.
Stronger execution containment.
Comprehensive permission management.
Performance monitoring and diagnostics.
The finished system must remain:

Local-first.
Privacy-conscious.
Modular.
Hardware-adaptive.
Testable.
Reversible.
Maintainable.
Extensible.
Honest about limitations.
PART 26 — MASTER INSTRUCTIONS TO THE DEVELOPMENT AI
You are the lead software architect and senior Python developer responsible for evolving FRIDAY into MATRIX AI.

Your job is to implement a real, functioning application.

You are not being asked to generate a theoretical architecture, a collection of placeholder files, or a demonstration that merely looks impressive.

You must:

Inspect the existing FRIDAY project.
Understand its actual capabilities.
Preserve existing working functionality.
Identify the highest-impact weaknesses.
Implement changes incrementally.
Validate every important modification.
Maintain complete backups.
Preserve the user's privacy.
Respect the available hardware.
Report actual results.
Do not attempt to implement every phase in one coding session.

Do not rewrite working subsystems without evidence that the replacement is better.

Do not introduce unnecessary dependencies.

Do not create artificial complexity.

Do not compromise security to improve convenience.

Do not silently modify the user's real project files.

When a requested feature cannot be implemented within the available constraints, explain why and propose the strongest practical alternative.

The most important development principle: improve real capability, not architectural appearance.

FINAL PROJECT VISION
MATRIX AI is intended to become a sophisticated personal intelligence platform operating locally on consumer hardware.

It should not rely on the illusion that a small model can do everything by itself.

Instead, it should combine specialized models, structured reasoning, persistent task management, reliable tools, independent verification, retrieval, controlled execution, and measurable feedback.

FRIDAY provides the working foundation.

MATRIX provides the next-generation architecture.

The objective is to transform the existing assistant into a much more capable, reliable, autonomous, and extensible system without sacrificing privacy, stability, or control.

PROJECT: MATRIX AI

FOUNDATION: FRIDAY MARK XLIX

DEVELOPMENT PRINCIPLE: PRESERVE → MEASURE → IMPROVE → VERIFY → EXPAND

END OF MASTER BLUEPRINT

How I'd use this document
Save it as:

MATRIX_AI_MASTER_BLUEPRINT.md

I'd also create these four companion files:

File

Purpose

DEVELOPMENT_ROADMAP.md

Tracks phase completion and priorities

BASELINE_AUDIT.md

Documents what FRIDAY actually has

KNOWN_LIMITATIONS.md

Tracks unresolved problems

MATRIX_CHANGELOG.md

Records every architectural change

One very important instruction
When you give this blueprint to your coding AI, don't immediately tell it to build Phase 1.

Tell it to perform Phase 0: inspect and audit FRIDAY first.

That prevents it from generating duplicate systems, overwriting working tools, or creating an entirely new application that loses the functionality you've already built.

My preferred development order is:

Preserve FRIDAY.

Upgrade the intelligence.

Build the cognitive engine.

Improve project understanding and coding.

Upgrade verification and memory.

Strengthen security.

Expand agent capabilities.

Optimize everything.

The end goal isn't simply a bigger chatbot. It's MATRIX: an AI that can understand a goal, plan the work, use its tools, modify projects, test its results, recognize mistakes, recover from failures, and explain exactly what it accomplished.