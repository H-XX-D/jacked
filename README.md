# Jacked

Jacked is a local AI workspace assistant built from FRIDAY Mark XLIX and the MATRIX blueprint. It runs model inference, file tools, conversation history, task recovery, and evidence checks on the machine where you launch it. The Python harness uses the standard library.

## Start

Use Python 3.12 or later. Set up a local model runtime and weights once. When Jacked launches the runtime, it binds to loopback, loads the files you selected, and shuts it down on exit.

| Platform | Local model setup | Launch |
| --- | --- | --- |
| macOS | Install MLX LM and keep a local MLX model directory. This Mac already has the Qwen2.5 7B model in its cache. | `python3.12 main.py` |
| Linux | Put a tool-capable GGUF on disk and make `llama-server` available on PATH. | `python3 main.py chat --weights "$HOME/models/model.gguf"` |
| Windows | Put a tool-capable GGUF on disk and make `llama-server.exe` available on PATH. | `py -3.12 main.py chat --weights "C:\Models\model.gguf"` |

The GGUF path also works on macOS. Put a single GGUF under the selected state directory's `models` folder for automatic selection, or set `MATRIX_WEIGHTS`. On macOS, Jacked can discover the cached Qwen2.5 7B MLX model. `doctor` checks the selected backend. See the upstream runtime documentation for platform-specific installations. [MLX LM server](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md) · [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)

```sh
python -m matrix doctor --weights /path/to/model.gguf
python -m matrix run "Read README.md and summarize the project" --weights /path/to/model.gguf --workspace .
python -m matrix chat --workspace .
```

An already-running service can be selected with `--provider ollama`, `--provider openai`, `--provider zeta`, or `--provider zeta09`. Supply its loopback `--url` and local `--model` ID, or set `MATRIX_PROVIDER`, `MATRIX_URL`, and `MATRIX_MODEL`. Use a service with local inference and local weights for offline operation.

## Jarvis desktop

The original Jarvis HUD can run the same local task engine as the terminal. Use a Python environment with PyQt6, Qt Multimedia, and psutil.

```sh
python -m pip install PyQt6 psutil sounddevice
python main.py desktop
```

For a named macOS app with its own microphone usage declaration, build it with the Python interpreter that has the desktop dependencies.

```sh
python scripts/install_macos_desktop.py
open "$HOME/Applications/Jacked Jarvis.app"
```

**Harness** selects the workspace, model, output budget, tool-round limit, guarded write and local-program access, memory, project skill, capsule, local Nexus endpoint, Psyche calibration, CRAMPS checkout, and acceptance checks. **Tasks & exports** opens shared task history, resumes unfinished tasks in read-only mode, and exports JSON, evidence graphs, GAL, AURA, and Medicine Cabinet files. It also runs the Nexus, Psyche, and CRAMPS actions. Their results can be included as reference data in the next task. Module availability shows configured actions and installed dependencies.

The model can discover and load project-local skills during a task. It can search workspace task history, inspect recorded evidence, and export it into the local task store. Configuring Nexus, Psyche, or CRAMPS adds their task tools to the same model loop. Psyche requires genuine inference signal files and a suitable calibration. CRAMPS study checks write reports and require guarded workspace write access.

**Record prompt** requests microphone permission when needed and records up to 30 seconds. Select an input under **Harness → Microphone input**, or use the system default input. Inputs whose native format Qt cannot read use PortAudio through `sounddevice` on the same selected device. Stop recording to transcribe locally with Whisper. Review the transcript in the command field before pressing Enter. **F4** toggles local reply audio through the system output device.

## Work with files and speech

File tools are read-only until you pass `--write`. To overwrite a file, the model must provide the SHA-256 from a read. Jacked backs up the original, writes the replacement, and checks its SHA-256 by reading it back. Python edits must parse before being written.

Enable **Allow local programs with host access** or pass `--execute` to let the model run skill scripts, builds, and tests. Programs receive an argument array and run from the workspace with the host account's access. Each execution has a timeout, bounded output, and a journal receipt containing the arguments and exit status. The workspace boundary applies to the file tools. Local programs have the host account's filesystem and network permissions. Task recovery starts with read-only file tools and local programs disabled.

```sh
python -m matrix run "Create a short summary in summary.txt" --write --workflow
python -m matrix run "Inspect main.py" --require-python main.py --json
python -m matrix run "Load the project skill and run the tests" --execute --skill matrix-workspace
python -m matrix tasks
python -m matrix show TASK_ID
python -m matrix resume TASK_ID
```

Chat uses recent completed tasks from the same workspace. Add `--memory` to a one-shot task to use that history there. Prompts, answers, tool receipts, and backups stay under `~/.jacked`. Set `MATRIX_STATE_DIR` or pass `--state-dir DIRECTORY` before the subcommand to choose a location. `resume` retries an unfinished task against current files with read-only access. A receipt marked `started` identifies an operation whose result needs inspection.

Speech input uses a local Whisper executable and model. Put them in `~/.jacked/speech`, set `MATRIX_SPEECH_HOME`, or put `whisper-cli` on PATH and set `MATRIX_WHISPER_WEIGHTS`. The input format is mono 16 kHz, 16-bit PCM WAV. Output uses Samantha on macOS, Windows SAPI with an installed voice, or eSpeak NG on Linux. [Whisper.cpp](https://github.com/ggml-org/whisper.cpp)

```sh
python -m matrix transcribe prompt.wav
python -m matrix run --audio prompt.wav --speech-out reply.wav
python -m matrix speak "Hello from Jacked" --output hello.wav
```

## Integrated project elements

`python -m matrix integrations` lists the pinned upstream revisions. The core task loop runs from local assets. External project tools and services are optional extensions.

| Project | Local use |
| --- | --- |
| Recall Memory Substrate | Workspace-scoped history is available in SQLite. `--recall` adds a packet from an installed Recall CLI. [Recall](https://github.com/H-XX-D/recall-memory-substrate) |
| EphemeralSkill | `--skill matrix-workspace` reads the selected project skill and uses esk discovery when present. [EphemeralSkill](https://github.com/H-XX-D/ephemeralskill) |
| AURA | `export --format aiwire` encodes and decodes a task packet with the installed AURA package. [AURA](https://github.com/H-XX-D/AURA) |
| AIDE | Use the terminal and `--json` for the `jacked.task.v1` report. [AIDE](https://github.com/H-XX-D/aide) |
| GAL and RRT | Export typed task evidence as built-in JSON with `--format graph` or as a netlist with `--format gal` and an installed GAL CLI. [GAL](https://github.com/H-XX-D/GAL.Graph_Abstraction_Layer) · [RRT](https://github.com/H-XX-D/RRT-) |
| Nexus | `check-claim` calls a user-selected loopback Nexus service and labels the returned score as a model assessment. [Nexus](https://github.com/H-XX-D/nexus-architecture) |
| CRAMPACS Governance | Predeclared acceptance checks run independently of the model. `cramps-check` also runs the upstream study-package checker from an existing local checkout. [CRAMPACS Governance](https://github.com/H-XX-D/CRAMPACS-Governance) |
| ZetaZero and Zeta v0.9 | Local server profiles support ZetaZero tool calls and Zeta v0.9 text responses. [ZetaZero](https://github.com/H-XX-D/ZetaZero) · [Zeta v0.9](https://github.com/H-XX-D/zeta-zero-point-nine) |
| AI Safety System Design | Python enforces the tool allowlist, workspace boundaries, local routing, execution limits, and acceptance results. [AI Safety System Design](https://github.com/H-XX-D/AI-Safety-System-Design) |
| Orkestra | `--workflow` runs planning, execution, and advisory review on the same local model in sequence. Tool receipts and acceptance checks carry the execution evidence. [Orkestra](https://github.com/H-XX-D/Orkestra) |
| Medicine Cabinet | Import a v1 context capsule with `--capsule`. Export a task as a v1 capsule or tablet without a separate install. [Medicine Cabinet](https://github.com/H-XX-D/Medicine-Cabinet) |
| Psyche v2 | The `psyche` command uses an installed SDK, a compatible calibration, and a genuine signal export from an instrumented model. Ordinary model answers and tool receipts stay distinct from signal assessments. [Psyche v2](https://github.com/H-XX-D/psyche-v2) |

```sh
python -m matrix export TASK_ID --format graph --output task.graph.json
python -m matrix export TASK_ID --format capsule --output task.auractx
python -m matrix export TASK_ID --format tablet --output task.auratab
python -m matrix run "Continue the investigation" --capsule task.auractx --workflow
python -m matrix psyche signals.json --architecture dolphin --calibration calibration.json
```

## FRIDAY and tests

The original archive credits Abdullah Siddiqui and states CC BY-NC 4.0 terms. The [FRIDAY documentation](FRIDAY.md) and [MATRIX blueprint](MATRIX_AI_MASTER_BLUEPRINT.md) are included. The original desktop and Gemini Live mode can be launched explicitly with `python main.py --legacy-friday` after its separate setup.

Run the portable automated suite on any supported host.

```sh
python -m unittest discover -s tests -v
```
