import argparse
import errno
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def get_elapsed_time():
    """
    Return the CPU time taken by the python process and its child
    processes.
    """
    if os.name == "nt":
        # The child time components of os.times() are 0 on Windows.
        raise NotImplementedError("cannot use get_elapsed_time() on Windows")
    return sum(os.times()[:4])


def find_domain_filename(task_filename):
    """
    Find domain filename for the given task using automatic naming rules.
    """
    dirname, basename = os.path.split(task_filename)

    domain_basenames = [
        "domain.pddl",
        basename[:3] + "-domain.pddl",
        "domain_" + basename,
        "domain-" + basename,
    ]

    for domain_basename in domain_basenames:
        domain_filename = os.path.join(dirname, domain_basename)
        if os.path.exists(domain_filename):
            return domain_filename


def parse_arguments():
    parser = argparse.ArgumentParser(description="Wrapper to pipeline plasp and fasb.")
    parser.add_argument(
        "-i",
        "--instance",
        required=True,
        help="The path to the PDDL/SAS instance file.",
    )
    parser.add_argument(
        "-d",
        "--domain",
        default=None,
        help="(Optional) The path to the PDDL domain file. If none is "
        "provided, the system will try to automatically deduce "
        "it from the instance filename.",
    )
    parser.add_argument(
        "--partial-plan", help="The path to the file containing partial plan."
    )
    parser.add_argument(
        "--add-constraints", help="String containing additional contraints.", type=str
    )
    parser.add_argument(
        "--add-constraints-file",
        help="The path to the file containing additional contraints.",
    )
    parser.add_argument(
        "--dry",
        help="If true, facets will not be computed at startup.",
        action="store_true",
    )
    parser.add_argument(
        "--horizon", required=True, type=int, help="Horizon used by clingo."
    )
    parser.add_argument(
        "--lp-name",
        default="instance.lp",
        type=str,
        help="Name of intermediate logic program (lp) file.",
    )
    parser.add_argument(
        "--encoding",
        default="exact",
        type=str,
        choices=["exact", "bounded"],
        help="Type of ASP encoding.",
    )
    parser.add_argument(
        "--abstract-time-steps",
        action="store_true",
        help="If true, it only reports that actions occur some time during the plans, but "
        "without specifying when.",
    )
    parser.add_argument(
        "--script",
        type=str,
        help="The path to the fasb script; for non-interactive mode.",
    )
    parser.add_argument(
        "--dump-output",
        action="store_true",
        help="dump the output of tools.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean all LP files in the folder after execution.",
    )

    args = parser.parse_args()
    args.is_pddl_instance = True
    if args.instance.endswith(".sas"):
        args.is_pddl_instance = False
    if args.domain is None and args.is_pddl_instance:
        args.domain = find_domain_filename(args.instance)
        if args.domain is None:
            raise RuntimeError(
                f'Could not find domain filename that matches instance file "{args.domain}"'
            )

    return args


def write_lines_to_file(file_path, lines):
    try:
        with open(file_path, "w") as file:
            for line in lines:
                file.write(line + "\n")
        # print(f"Successfully wrote {len(lines)} lines to {file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")
