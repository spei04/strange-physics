"""Run and resume local investigations; export validated observations."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from strange_physics.contracts import (
    Checkpoint,
    Experiment,
    ExperimentSpace,
    Message,
    ObservationBundle,
)
from strange_physics.sdk import RandomAgent, run_agent
from strange_physics.session import LocalSession
from strange_physics.worlds import reference_world


def write_private(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(content)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    create = commands.add_parser(
        "investigate", help="create a trusted local reference investigation"
    )
    create.add_argument("--family", choices=("spring", "radial", "velocity"), default="spring")
    create.add_argument("--directory", type=Path, required=True)
    create.add_argument("--seed", type=int, default=7)
    create.add_argument("--particles", type=int, default=3)
    create.add_argument("--budget", type=int, default=40)
    create.add_argument("--noise", type=float, default=0.002)
    create.add_argument("--stationary", action="store_true")
    resume = commands.add_parser("resume", help="resume from a private local run journal")
    resume.add_argument("--directory", type=Path, required=True)
    for command in (create, resume):
        command.add_argument("--agent-seed", type=int, default=0)
        command.add_argument("--max-new-experiments", type=int)
    inspect = commands.add_parser("inspect", help="validate an exported observation bundle")
    inspect.add_argument("path", type=Path)
    schema = commands.add_parser("schema", help="export a public JSON schema")
    schema.add_argument("contract", choices=("experiment", "space", "observations", "checkpoint"))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "schema":
            models: dict[str, type[Message]] = {
                "experiment": Experiment,
                "space": ExperimentSpace,
                "observations": ObservationBundle,
                "checkpoint": Checkpoint,
            }
            print(json.dumps(models[args.contract].model_json_schema(), indent=2))
            return 0
        if args.command == "inspect":
            if args.path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("observation bundle exceeds the 64 MiB local inspection limit")
            bundle = ObservationBundle.model_validate_json(args.path.read_bytes())
        else:
            agent = RandomAgent(args.agent_seed)
            if args.max_new_experiments is not None and args.max_new_experiments < 0:
                raise ValueError("maximum new experiments cannot be negative")
            if args.command == "investigate":
                world = reference_world(
                    args.family,
                    seed=args.seed,
                    particles=args.particles,
                    budget=args.budget,
                    changed=not args.stationary,
                    noise=args.noise,
                )
                session = LocalSession.create(args.directory / "session.sqlite", uuid4().hex, world)
            else:
                session = LocalSession.open(args.directory / "session.sqlite")
            with session:
                bundle = run_agent(session, agent, max_new_experiments=args.max_new_experiments)
            write_private(args.directory / "observations.json", bundle.model_dump_json(indent=2))
        failed = sum(record.status == "failed" for record in bundle.records)
        print(
            json.dumps(
                {
                    "run_id": bundle.run_id,
                    "experiments": len(bundle.records),
                    "budget": bundle.space.budget,
                    "failed": failed,
                },
                sort_keys=True,
            )
        )
        return 1 if failed else 0
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
