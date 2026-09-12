"""MLflow-compatible Experiment Tracking and Artifact Storage Engine."""

import json
import os
import shutil
import time
import uuid
from typing import Any, Dict, List, Optional

from app.config.settings import get_settings

settings = get_settings()


class MLflowTracker:
    """Manages MLflow-format experiments, runs, parameters, step-wise metrics, and artifacts."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or os.path.join(settings.UPLOAD_DIR, "mlflow")
        self.experiments_dir = os.path.join(self.base_dir, "experiments")
        os.makedirs(self.experiments_dir, exist_ok=True)

    def _exp_dir(self, experiment_id: str) -> str:
        return os.path.join(self.experiments_dir, str(experiment_id))

    def _runs_dir(self, experiment_id: str) -> str:
        return os.path.join(self._exp_dir(experiment_id), "runs")

    def _find_run_dir(self, run_id: str) -> Optional[Tuple_Path_Exp := str]:
        """Locate run folder by searching across experiments."""
        if not os.path.exists(self.experiments_dir):
            return None
        for exp_id in os.listdir(self.experiments_dir):
            r_dir = os.path.join(self._runs_dir(exp_id), run_id)
            if os.path.exists(r_dir):
                return r_dir
        return None

    def create_experiment(self, name: str, tags: Dict[str, str] | None = None) -> str:
        """Create new experiment with unique ID."""
        existing = self.get_experiment_by_name(name)
        if existing:
            return existing["experiment_id"]

        exp_id = str(uuid.uuid4())
        exp_path = self._exp_dir(exp_id)
        runs_path = self._runs_dir(exp_id)
        os.makedirs(runs_path, exist_ok=True)

        meta = {
            "experiment_id": exp_id,
            "name": name,
            "artifact_location": exp_path,
            "lifecycle_stage": "active",
            "tags": tags or {},
            "created_at": time.time(),
        }

        with open(os.path.join(exp_path, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return exp_id

    def get_or_create_experiment(self, name: str, tags: Dict[str, str] | None = None) -> str:
        """Fetch existing experiment ID by name or create a new one."""
        existing = self.get_experiment_by_name(name)
        if existing:
            return existing["experiment_id"]
        return self.create_experiment(name, tags)

    def get_experiment_by_name(self, name: str) -> Dict[str, Any] | None:
        """Find experiment by name."""
        if not os.path.exists(self.experiments_dir):
            return None
        for exp_id in os.listdir(self.experiments_dir):
            meta_path = os.path.join(self._exp_dir(exp_id), "meta.json")
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, encoding="utf-8") as f:
                        meta = json.load(f)
                    if meta.get("name") == name:
                        return meta
                except Exception:
                    continue
        return None

    def get_experiment(self, experiment_id: str) -> Dict[str, Any] | None:
        """Get experiment metadata by ID."""
        meta_path = os.path.join(self._exp_dir(experiment_id), "meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments."""
        results = []
        if not os.path.exists(self.experiments_dir):
            return results
        for exp_id in os.listdir(self.experiments_dir):
            exp = self.get_experiment(exp_id)
            if exp:
                runs_dir = self._runs_dir(exp_id)
                run_count = len(os.listdir(runs_dir)) if os.path.exists(runs_dir) else 0
                exp["run_count"] = run_count
                results.append(exp)
        return results

    def start_run(
        self,
        experiment_id: str,
        run_name: str | None = None,
        tags: Dict[str, str] | None = None,
    ) -> str:
        """Initialize and start a new MLflow tracking run."""
        run_id = str(uuid.uuid4())
        name = run_name or f"run_{run_id[:8]}"
        run_dir = os.path.join(self._runs_dir(experiment_id), run_id)

        os.makedirs(os.path.join(run_dir, "params"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "metrics"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "tags"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "artifacts"), exist_ok=True)

        now = time.time()
        meta = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "run_name": name,
            "status": "RUNNING",
            "start_time": now,
            "end_time": None,
            "artifact_uri": os.path.join(run_dir, "artifacts"),
            "lifecycle_stage": "active",
        }

        with open(os.path.join(run_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        if tags:
            self.set_tags(run_id, tags)

        return run_id

    def log_param(self, run_id: str, key: str, value: Any) -> None:
        """Log a hyperparameter / configuration parameter for a run."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return
        params_dir = os.path.join(run_dir, "params")
        os.makedirs(params_dir, exist_ok=True)
        with open(os.path.join(params_dir, str(key)), "w", encoding="utf-8") as f:
            f.write(str(value))

    def log_params(self, run_id: str, params: Dict[str, Any]) -> None:
        """Log multiple parameters."""
        for k, v in params.items():
            self.log_param(run_id, k, v)

    def log_metric(
        self,
        run_id: str,
        key: str,
        value: float,
        step: int = 0,
        timestamp: float | None = None,
    ) -> None:
        """Log a scalar metric point with timestamp and step for tracking convergence."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return
        metrics_dir = os.path.join(run_dir, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        ts = timestamp or time.time()
        line = f"{ts} {value} {step}\n"
        with open(os.path.join(metrics_dir, str(key)), "a", encoding="utf-8") as f:
            f.write(line)

    def log_metrics(self, run_id: str, metrics: Dict[str, float], step: int = 0) -> None:
        """Log multiple metrics."""
        ts = time.time()
        for k, v in metrics.items():
            if v is not None:
                self.log_metric(run_id, k, float(v), step=step, timestamp=ts)

    def set_tag(self, run_id: str, key: str, value: str) -> None:
        """Set a metadata tag for a run."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return
        tags_dir = os.path.join(run_dir, "tags")
        os.makedirs(tags_dir, exist_ok=True)
        with open(os.path.join(tags_dir, str(key)), "w", encoding="utf-8") as f:
            f.write(str(value))

    def set_tags(self, run_id: str, tags: Dict[str, str]) -> None:
        """Set multiple tags."""
        for k, v in tags.items():
            self.set_tag(run_id, k, v)

    def log_artifact(self, run_id: str, local_file_path: str, artifact_path: str | None = None) -> None:
        """Copy a local file into the run's artifact directory."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir or not os.path.exists(local_file_path):
            return
        target_dir = os.path.join(run_dir, "artifacts")
        if artifact_path:
            target_dir = os.path.join(target_dir, artifact_path)
            os.makedirs(target_dir, exist_ok=True)
        if os.path.isfile(local_file_path):
            shutil.copy2(local_file_path, target_dir)
        elif os.path.isdir(local_file_path):
            dest = os.path.join(target_dir, os.path.basename(local_file_path))
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(local_file_path, dest)

    def log_dict(self, run_id: str, dictionary: Dict[str, Any], artifact_file: str) -> None:
        """Save a dictionary as a JSON file in the run's artifact repository."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return
        target_path = os.path.join(run_dir, "artifacts", artifact_file)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(dictionary, f, indent=2)

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        """Mark a run as finished or failed and record completion timestamp."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return
        meta_path = os.path.join(run_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            meta["status"] = status
            meta["end_time"] = time.time()
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

    def get_run(self, run_id: str) -> Dict[str, Any] | None:
        """Retrieve full run details including parameters, latest metrics, tags, and artifacts."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return None

        meta_path = os.path.join(run_dir, "meta.json")
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        # Read parameters
        params = {}
        params_dir = os.path.join(run_dir, "params")
        if os.path.exists(params_dir):
            for p in os.listdir(params_dir):
                with open(os.path.join(params_dir, p), encoding="utf-8") as f:
                    params[p] = f.read().strip()

        # Read latest metrics
        metrics = {}
        metrics_dir = os.path.join(run_dir, "metrics")
        if os.path.exists(metrics_dir):
            for m in os.listdir(metrics_dir):
                with open(os.path.join(metrics_dir, m), encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip().split()
                        if len(last_line) >= 2:
                            try:
                                metrics[m] = float(last_line[1])
                            except ValueError:
                                pass

        # Read tags
        tags = {}
        tags_dir = os.path.join(run_dir, "tags")
        if os.path.exists(tags_dir):
            for t in os.listdir(tags_dir):
                with open(os.path.join(tags_dir, t), encoding="utf-8") as f:
                    tags[t] = f.read().strip()

        # Read artifacts list
        artifacts = self.list_artifacts(run_id)

        duration_ms = None
        if meta.get("start_time") and meta.get("end_time"):
            duration_ms = round((meta["end_time"] - meta["start_time"]) * 1000.0, 2)

        return {
            "run_id": run_id,
            "experiment_id": meta.get("experiment_id"),
            "run_name": meta.get("run_name", f"run_{run_id[:8]}"),
            "status": meta.get("status", "FINISHED"),
            "start_time": meta.get("start_time"),
            "end_time": meta.get("end_time"),
            "duration_ms": duration_ms,
            "parameters": params,
            "metrics": metrics,
            "tags": tags,
            "artifacts": artifacts,
        }

    def list_runs(self, experiment_id: str) -> List[Dict[str, Any]]:
        """List all runs under an experiment sorted by start time descending."""
        runs_dir = self._runs_dir(experiment_id)
        if not os.path.exists(runs_dir):
            return []

        runs = []
        for r_id in os.listdir(runs_dir):
            run_data = self.get_run(r_id)
            if run_data:
                runs.append(run_data)

        runs.sort(key=lambda x: x.get("start_time") or 0.0, reverse=True)
        return runs

    def get_metric_history(self, run_id: str, metric_key: str) -> List[Dict[str, Any]]:
        """Get the full time series of a metric for learning curves."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return []
        metric_file = os.path.join(run_dir, "metrics", metric_key)
        if not os.path.exists(metric_file):
            return []

        history = []
        with open(metric_file, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        ts = float(parts[0])
                        val = float(parts[1])
                        step = int(parts[2])
                        history.append(
                            {
                                "step": step,
                                "value": round(val, 6),
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
                            }
                        )
                    except ValueError:
                        continue
        return history

    def list_artifacts(self, run_id: str, path: str = "") -> List[Dict[str, Any]]:
        """List files in the run's artifact directory."""
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return []
        art_dir = os.path.join(run_dir, "artifacts", path)
        if not os.path.exists(art_dir):
            return []

        items = []
        for entry in os.listdir(art_dir):
            full = os.path.join(art_dir, entry)
            is_dir = os.path.isdir(full)
            size = os.path.getsize(full) if not is_dir else 0
            rel_path = os.path.join(path, entry).replace("\\", "/")
            items.append(
                {
                    "path": rel_path,
                    "is_dir": is_dir,
                    "file_size_bytes": size,
                }
            )
        return items


# Singleton instance
mlflow_tracker = MLflowTracker()
