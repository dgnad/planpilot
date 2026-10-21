#! /usr/bin/env python3
import logging
import os
import sys
from subprocess import PIPE, Popen

from fasb import start_fasb, start_fasb_interpreter

import utils

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s ::: %(message)s",
)
logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)


def fix_path(path):
    return os.path.join(dirname, path)


def run_fd_translator(domain, instance):
    binary_path = fix_path("translate/translate.py")
    python_exec = sys.executable  # Uses the currently running Python interpreter
    command = [
        python_exec,
        binary_path,
        "--keep-unimportant-variables",
        domain,
        instance,
    ]
    time = utils.get_elapsed_time()
    process = Popen(command, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = process.communicate()
    # if stdout:
    #     print(stdout, file=sys.stdout, end='')

    if stderr:
        print(stderr, file=sys.stderr, end="")
    _, error = process.communicate()
    logging.info(f"translator time: {utils.get_elapsed_time() - time:.2f}s")

    logger.info(f"translator return code: {process.returncode}")
    if process.returncode != 0:
        print(error)
        exit(process.returncode)


def run_plasp(domain, instance, lp, encoding, dump_output, pddl_instance=True):
    binary_path = fix_path("bin/plasp")
    command = [binary_path, "translate", instance]  # SAS+ instance
    if pddl_instance:
        command = [binary_path, "translate", domain, instance]

    with open(lp, "w") as lp_file:
        # First, we add the corresponding sequential encoding to it
        encoding = fix_path("encodings/exact-sequential-horizon.lp")
        if args.encoding == "bounded":
            encoding = fix_path("encodings/bounded-sequential-horizon.lp")
        with open(encoding) as seq_encoding:
            lp_file.write(seq_encoding.read())

        time_steps_encoding = fix_path("encodings/action-per-time-step.lp")
        if args.abstract_time_steps:
            time_steps_encoding = fix_path("encodings/abstract-time-steps.lp")

        with open(time_steps_encoding) as time_encoding:
            lp_file.write(time_encoding.read())

        if args.partial_plan:
            logger.info(f"Using partial plan '{args.partial_plan}'...")
            constraints: str | None = translate_partial_plan_into_constraints(
                args.partial_plan
            )
            lp_file.write("\n%%%%%%% partial plan encoding\n" + constraints + "\n")

        if args.add_constraints_file:
            logger.info(
                f"Using additional constraints of file '{args.add_constraints_file}'..."
            )
            try:
                with open(args.add_constraints_file, "r") as f:
                    constraints = f.readlines()
                    constraints = "".join(constraints)
                    lp_file.write(
                        "\n%%%%%%% partial plan encoding\n" + constraints + "\n"
                    )
            except IOError:
                print(
                    f"Error: File {args.add_constraints_file} does not appear to exist."
                )
                exit(1)

        if args.add_constraints:
            constraints = args.add_constraints.encode().decode("unicode_escape")
            lp_file.write("\n%%%%%%% partial plan encoding\n" + constraints + "\n")

        # Now, we run plasp to produce the instance-specific info
        process = Popen(command, stdout=lp_file, stdin=PIPE, stderr=PIPE, text=True)

    time = utils.get_elapsed_time()
    _, error = process.communicate()
    logging.info(f"plasp time: {utils.get_elapsed_time() - time:.2f}s")

    logger.info(f"plasp return code: {process.returncode}")
    if process.returncode != 0:
        print(error)
        exit(process.returncode)


def run_fasb(lp, horizon, script=None):
    # Parameter arguments are still needed for clingo
    clingo_args = ["-c", f"horizon={horizon}", "0"]

    # TODO: The parameter is reversed due to the Python bindings
    compute_facets = not args.dry

    if args.dry:
        logging.info("Dry startup...")
        logging.info(
            "To compute facets matching some regular expression 're', use the command '!? re'..."
        )

    time = utils.get_elapsed_time()
    try:
        if script:
            logger.info(f"Executing fasb script {script}...")
            start_fasb_interpreter(
                clingo_args,
                lp,
                fix_path(script),
                compute_facets,
                False,
            )
        else:
            logging.info(
                "Starting fasb... To quit the interactive mode, use the command ':q'."
            )
            start_fasb(clingo_args, lp, compute_facets, False)
    except Exception as exc:
        logger.error(f"fasb failed: {exc}")
        sys.exit(1)

    logging.info(f"fasb time: {utils.get_elapsed_time() - time:.2f}s")


def remove_lp_files():
    current_directory = os.getcwd()

    for file_name in os.listdir(current_directory):
        file_path = os.path.join(current_directory, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".lp"):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")


def translate_partial_plan_into_constraints(file_path: str) -> str | None:
    # TODO: give the name of specific format
    """
    Expects actions in specific format.

    Example:
    `a b c (1) d e (1)`
    will be translated into
    `
    :- not occurs(action(("a","b","c")),1).
    :- not occurs(action(("d","e")),2).
    `
    """
    global PARTIAL_PLAN_DELIMITER
    PARTIAL_PLAN_DELIMITER = "(1)"

    try:
        with open(file_path, "r") as f:
            actions = filter(
                lambda x: x,
                map(lambda x: x.strip(), f.read().split(PARTIAL_PLAN_DELIMITER)),
            )
            return "\n".join(
                map(
                    lambda t: translate_action_to_constraint(*t[::-1]),
                    enumerate(actions),
                )
            )
    except Exception as e:
        logger.error(f"could not read partial plan '{file_path}': {e}")


def translate_action_to_constraint(action: str, at: int) -> str:
    """
    Translates whitespace-separated action into integrity constraint.

    Example:
    `a b c` as first action will be translated into
    `:- not occurs(action(("a","b","c")),1).`
    """
    return (
        ":- not occurs(action(("
        + ",".join(map(lambda x: f'"{x}"', action.split(" ")))
        + f")),{at+1})."
    )


if __name__ == "__main__":
    args = utils.parse_arguments()

    domain_file = args.domain
    instance_file = args.instance
    if args.is_pddl_instance and not os.path.isfile(domain_file):
        sys.stderr.write("Error: Domain file does not exist.\n")
        sys.exit()
    if not os.path.isfile(instance_file):
        sys.stderr.write("Error: Instance file does not exist.\n")
        sys.exit()

    if args.is_pddl_instance:
        logger.info("Running translator...")
        run_fd_translator(args.domain, args.instance)
        args.instance = "output.sas"
        # run_plasp(
        #     args.domain,
        #     args.instance,
        #     args.lp_name,
        #     args.encoding,
        #     args.dump_output)

    logger.info("Running plasp...")
    run_plasp("", args.instance, args.lp_name, args.encoding, args.dump_output, False)

    logger.info("Running fasb...")
    run_fasb(args.lp_name, args.horizon, args.script)

    if args.cleanup:
        remove_lp_files()

    logging.info(f"Total time: {utils.get_elapsed_time():.2f}s")
    logger.info("Done!")
