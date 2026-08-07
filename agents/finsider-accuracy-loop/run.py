#!/usr/bin/env python3
"""launchd entrypoint for the Finsider continuous accuracy supervisor."""

import os
import sys


SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SOURCE_DIR)

from accuracy_loop.supervisor import Supervisor  # noqa: E402


def main():
    runtime_dir = os.environ.get(
        "FINSIDER_ACCURACY_RUNTIME",
        "/Users/dm3n/finsider-platform/.accuracy-supervisor",
    )
    return Supervisor(runtime_dir=runtime_dir, source_dir=SOURCE_DIR).run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
