"""
Implements the 'stpipe list' command, which lists available
Step subclasses.
"""
import sys

import argparse
import re

from .command import Command
from .. import entry_points


class ListCommand(Command):
    @classmethod
    def get_name(cls):
        return "list"

    @classmethod
    def add_subparser(cls, subparsers):
        epilog = """
examples:
  list available pipeline and step classes:
    stpipe list
  list only pipelines:
    stpipe list --pipelines-only
  list steps in the jwst package:
    stpipe list --steps-only jwst.*
    """.strip()

        parser = subparsers.add_parser(
            cls.get_name(),
            epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="list available classes",
            help="list available classes",
    )

        parser.add_argument("pattern", metavar="<pattern>", help="restrict classes to glob pattern (case-insensitive)", nargs="?")

        group = parser.add_mutually_exclusive_group()
        group.add_argument("--pipelines-only", help="list only pipeline classes", action="store_true", default=False)
        group.add_argument("--steps-only", help="list only step classes", action="store_true", default=False)

    @classmethod
    def run(cls, args):
        steps = entry_points.get_steps()

        if args.steps_only:
            steps = [s for s in steps if not s.is_pipeline]
        elif args.pipelines_only:
            steps = [s for s in steps if s.is_pipeline]

        steps = sorted(steps, key=lambda s: s.class_name)

        if args.pattern is not None:
            steps = _filter_pattern(args.pattern, steps)

        if len(steps) > 0:
            for step in steps:
                if step.class_alias is not None:
                    print(f"{step.class_name} ({step.class_alias})")
                else:
                    print(step.class_name)
        else:
            print("(no matching classes)", file=sys.stderr)

        return 0


def _filter_pattern(pattern, steps):
    pattern = re.compile(re.escape(pattern.lower()).replace(r"\*", ".*"))

    return [
        s for s in steps
        if pattern.fullmatch(s.class_name.lower()) or (s.class_alias is not None and pattern.fullmatch(s.class_alias.lower()))
    ]
