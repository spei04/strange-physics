"""Disabled GRID-Q1 qualification entry; enabling requires exact source/runtime admission."""

ENABLED = False

if __name__ == "__main__" and not ENABLED:
    raise SystemExit(
        "GRID-Q1 is disabled pending source, scientific, accounting and storage admission"
    )


def main() -> int:
    if not ENABLED:
        raise SystemExit("GRID-Q1 remains disabled")
    # Nothing below is imported or executed by the disabled entry path.
    import argparse
    import re
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str((root / "tests").resolve()))
    from grid_q1_driver import Driver

    parser = argparse.ArgumentParser(description="Fixed diagnostic; no scientific profile claim")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--authority-sha256", required=True)
    args = parser.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", args.source):
        parser.error("exact source commit required")
    if not re.fullmatch("[0-9a-f]{64}", args.authority_sha256):
        parser.error("exact external admission hash required")
    return 0 if Driver(args.output, args.source, args.authority_sha256).run() else 1


if __name__ == "__main__":
    raise SystemExit(main())
