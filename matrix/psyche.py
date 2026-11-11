"""Run a locally installed Psyche detector on real inference signals."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory


def calibrated_detector(factory, architecture, calibration):
    with calibration.open("rb") as stream:
        raw = stream.read(16_000_001)
    if len(raw) > 16_000_000:
        raise ValueError("Provide a Psyche calibration file up to 16 MB.")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("The Psyche calibration must contain a JSON object.")
    classifiers = {name: data[name] for name in ("gbm", "svm", "lr") if isinstance(data.get(name), dict)}
    if (
        "weights" not in data and classifiers and "profile" in data
        and str(data.get("format_version", "")).split(".", 1)[0] == "2"
    ):
        # Psyche v2's training export has top-level classifiers. Its file reader
        # also requires a weights object. Keep the classifier values intact.
        with TemporaryDirectory(prefix="matrix-psyche-") as directory:
            normalized = Path(directory) / "calibration.json"
            normalized.write_text(json.dumps({**data, "weights": classifiers}), encoding="utf-8")
            return factory(architecture, calibration_path=normalized)
    return factory(architecture, calibration_path=calibration)


def assess(signals, architecture, calibration):
    with signals.expanduser().open("rb") as stream:
        raw = stream.read(16_000_001)
    if not raw or len(raw) > 16_000_000:
        raise ValueError("Provide a Psyche signal export up to 16 MB.")
    calibration = calibration.expanduser().resolve(strict=True)
    if not calibration.is_file():
        raise ValueError("Provide a local Psyche calibration file.")
    if architecture not in {"dolphin", "qwen3_235b", "minimax"}:
        architecture = Path(architecture).expanduser().resolve(strict=True)
    try:
        from psyche import create_detector
    except ImportError as error:
        raise ValueError("Install the Psyche v2 SDK locally to assess exported signals.") from error
    try:
        detector = calibrated_detector(create_detector, architecture, calibration)
        raw_text = raw.decode("utf-8")
        if raw_text.lstrip().startswith("{"):
            detector.ingest_signals_json(raw_text)
        elif detector.ingest_engine_output(raw_text) is None:
            raise ValueError("The supplied inference output has no Psyche signal envelope.")
        result = detector.classify(raise_on_degenerate=True).to_dict()
    except Exception as error:
        raise RuntimeError(f"Psyche could not assess the signal export: {str(error)[:1_000]}") from error
    if (
        result.get("verdict") not in {"factual", "confabulation"}
        or result.get("degenerate", False)
        or not result.get("n_gen_tokens", 0)
    ):
        raise RuntimeError("Psyche did not return a usable signal assessment.")
    # Reject NaN and infinity as an interchange check.
    json.dumps(result, allow_nan=False)
    return {"schema": "jacked.psyche.v1", "verification": "model_signal_assessment", "result": result}
