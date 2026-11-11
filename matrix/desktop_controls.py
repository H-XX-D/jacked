"""Human controls for the same task, model, and module interfaces used by the CLI."""

import json
from argparse import Namespace
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QInputDialog, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)
from PyQt6.QtMultimedia import QMediaDevices

from matrix.integrations import cramps_check, export_content, nexus_claim
from matrix.psyche import assess
from matrix.tasks import TaskStore


def configure(parent, config):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Jacked Harness")
    layout = QVBoxLayout(dialog)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    body = QWidget()
    form = QFormLayout(body)
    scroll.setWidget(body)
    layout.addWidget(scroll)
    dialog.resize(700, 750)
    spec = config["model"]
    model_provider = QComboBox()
    model_provider.addItems(["auto", "mlx", "llamacpp", "ollama", "openai", "zeta", "zeta09"])
    model_provider.setCurrentText(spec["provider"])
    form.addRow("Backend", model_provider)

    def path_field(label, value, *, directory=False):
        field = QLineEdit(value or "")
        button = QPushButton("Choose…")
        row = QHBoxLayout()
        row.addWidget(field)
        row.addWidget(button)
        wrapper = QWidget()
        wrapper.setLayout(row)
        form.addRow(label, wrapper)

        def choose():
            if directory:
                name = QFileDialog.getExistingDirectory(dialog, label, field.text())
            else:
                name, _ = QFileDialog.getOpenFileName(dialog, label, field.text())
            if name:
                field.setText(name)

        button.clicked.connect(choose)
        return field

    workspace = path_field("Workspace", config["workspace"], directory=True)
    weights = path_field("Model file", spec.get("weights"))
    model_dir = QPushButton("Choose MLX model directory…")
    model_dir.clicked.connect(lambda: set_directory(dialog, weights))
    form.addRow("", model_dir)
    url = QLineEdit(spec.get("url", ""))
    model = QLineEdit(spec.get("model", ""))
    form.addRow("Loopback URL", url)
    form.addRow("Model ID", model)
    output_tokens = QSpinBox()
    output_tokens.setRange(128, 32_768)
    output_tokens.setValue(spec.get("max_tokens", 700))
    form.addRow("Output token limit", output_tokens)
    rounds = QSpinBox()
    rounds.setRange(1, 64)
    rounds.setValue(config.get("max_rounds", 8))
    form.addRow("Tool rounds", rounds)
    skill = QLineEdit(config.get("skill") or "")
    form.addRow("Project skill", skill)
    capsule = path_field("Context capsule", config.get("capsule"))
    nexus = QLineEdit(config.get("nexus_url") or "")
    form.addRow("Nexus loopback URL", nexus)
    psyche_calibration = path_field("Psyche calibration", config.get("psyche_calibration"))
    psyche_architecture = QLineEdit(config.get("psyche_architecture", "dolphin"))
    form.addRow("Psyche architecture", psyche_architecture)
    cramps_checkout = path_field("CRAMPS source checkout", config.get("cramps_checkout"), directory=True)
    microphone = QComboBox()
    microphone.addItem("System default input", "")
    for device in QMediaDevices.audioInputs():
        microphone.addItem(device.description(), bytes(device.id()).hex())
    microphone.setCurrentIndex(max(0, microphone.findData(config.get("microphone_device", ""))))
    form.addRow("Microphone input", microphone)
    python_checks = QLineEdit(", ".join(
        item["path"] for item in config.get("requirements", []) if item["check"] == "python"
    ))
    hashes = QLineEdit(", ".join(
        f"{item['path']}={item['sha256']}" for item in config.get("requirements", []) if item["check"] == "sha256"
    ))
    form.addRow("Python checks (comma separated)", python_checks)
    form.addRow("Expected PATH=SHA256", hashes)
    flags = {}
    for key, title in (
        ("write_requested", "Allow guarded workspace writes"),
        ("execute_requested", "Allow local programs with host access"),
        ("local_memory_requested", "Use task history"),
        ("friday_memory_requested", "Use FRIDAY memory"),
        ("recall_requested", "Enable Recall"),
        ("workflow_requested", "Plan, execute and review"),
    ):
        checkbox = QCheckBox(title)
        checkbox.setChecked(bool(config.get(key)))
        flags[key] = checkbox
        form.addRow("", checkbox)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if not dialog.exec():
        return None

    path = lambda field: field.text().strip() or None
    provider = model_provider.currentText()
    owned = provider in {"auto", "mlx", "llamacpp"}
    args = Namespace(
        provider=provider, weights=Path(path(weights)) if owned and path(weights) else None,
        url=None if owned else path(url), model=None if owned else path(model), timeout=spec["timeout"],
        max_tokens=output_tokens.value(),
        require_python=[part.strip() for part in python_checks.text().split(",") if part.strip()],
        require_sha256=[part.strip() for part in hashes.text().split(",") if part.strip()],
    )
    updated = {**config, **{key: field.isChecked() for key, field in flags.items()}}
    updated.update(
        skill=path(skill), capsule=path(capsule), nexus_url=path(nexus), max_rounds=rounds.value(),
        psyche_calibration=path(psyche_calibration), psyche_architecture=path(psyche_architecture) or "dolphin",
        cramps_checkout=path(cramps_checkout),
        microphone_device=microphone.currentData(),
    )
    return path(workspace), args, updated


def set_directory(parent, field):
    path = QFileDialog.getExistingDirectory(parent, "MLX model directory", field.text())
    if path:
        field.setText(path)


def task_menu(parent, button, state, on_resume, show, defer, module_status):
    menu = QMenu(button)
    formats = {
        "Task report": ("json", "json"), "Evidence graph": ("graph", "json"),
        "GAL netlist": ("gal", "gal"), "AURA AIWire": ("aiwire", "aiwire"),
        "Medicine Cabinet capsule": ("capsule", "auractx"),
        "Medicine Cabinet tablet": ("tablet", "auratab"),
    }

    def choose_task():
        store = TaskStore(state)
        try:
            tasks = store.list()
        finally:
            store.close()
        labels = [f"{row['id']} · {row['status']} · {row['goal']}" for row in tasks]
        if not labels:
            QMessageBox.information(parent, "Tasks", "Your task history is empty.")
            return None
        choice, accepted = QInputDialog.getItem(parent, "Tasks", "Choose a task", labels, 0, False)
        return tasks[labels.index(choice)]["id"] if accepted else None

    def view():
        task_id = choose_task()
        if task_id:
            def read():
                store = TaskStore(state)
                try:
                    return export_content(store.get(task_id), store.receipts(task_id), "json", state).decode()
                finally:
                    store.close()
            defer("TASK EVIDENCE", read)

    def export(label, name, extension):
        task_id = choose_task()
        if not task_id:
            return
        path, _ = QFileDialog.getSaveFileName(parent, label, f"task-{task_id}.{extension}")
        if not path:
            return

        def write():
            store = TaskStore(state)
            try:
                content = export_content(store.get(task_id), store.receipts(task_id), name, state)
                with Path(path).open("xb") as destination:
                    destination.write(content)
            finally:
                store.close()
            return f"Saved {path}"
        defer(label.upper(), write)

    menu.addAction("Inspect a task", view)
    menu.addAction("Resume a task", lambda: on_resume(task_id) if (task_id := choose_task()) else None)
    exports = menu.addMenu("Export a task")
    for label, (name, extension) in formats.items():
        exports.addAction(label, lambda _=False, l=label, n=name, e=extension: export(l, n, e))
    menu.addSeparator()
    menu.addAction("Assess a claim with Nexus", lambda: nexus_dialog(parent, defer))
    menu.addAction("Inspect inference signals with Psyche", lambda: psyche_dialog(parent, defer))
    menu.addAction("Check a CRAMPS study", lambda: cramps_dialog(parent, defer))
    menu.addAction("Show module availability", lambda: defer(
        "MODULE AVAILABILITY", lambda: json.dumps(module_status(), indent=2),
    ))
    return menu


def nexus_dialog(parent, defer):
    url, ok = QInputDialog.getText(parent, "Nexus", "Local Nexus URL")
    if not ok or not url.strip():
        return
    claim, ok = QInputDialog.getMultiLineText(parent, "Nexus", "Claim")
    if not ok or not claim.strip():
        return
    evidence, ok = QInputDialog.getMultiLineText(parent, "Nexus", "Evidence JSON", "{}")
    if ok:
        defer("NEXUS ASSESSMENT", lambda: json.dumps(
            nexus_claim(url.strip(), claim.strip(), json.loads(evidence)), indent=2,
        ), attach=True)


def psyche_dialog(parent, defer):
    signals, _ = QFileDialog.getOpenFileName(parent, "Psyche signal export")
    if not signals:
        return
    calibration, _ = QFileDialog.getOpenFileName(parent, "Psyche calibration")
    if not calibration:
        return
    arch, ok = QInputDialog.getText(parent, "Psyche", "Architecture preset or descriptor path", text="dolphin")
    if ok and arch.strip():
        defer("PSYCHE ASSESSMENT", lambda: json.dumps(assess(Path(signals), arch.strip(), Path(calibration)), indent=2), attach=True)


def cramps_dialog(parent, defer):
    checkout = QFileDialog.getExistingDirectory(parent, "CRAMPS source checkout")
    if not checkout:
        return
    study = QFileDialog.getExistingDirectory(parent, "CRAMPS study package")
    if study:
        defer("CRAMPS STUDY CHECK", lambda: json.dumps(cramps_check(Path(checkout), Path(study), "auto"), indent=2), attach=True)
