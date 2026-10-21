# PlanPilot: Navigating the Plan Space with Facets

PlanPilot is a tool that allows the user to interactively navigate on the *plan
space* of a planning problem. For example, the user can interactively
(de)activate *facets* of the plans, in order to understand the plan space
better.

Right now, PlanPilot supports classical planning problems described in PDDL or SAS+.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) (Python package manager used for the build)
- Rust toolchain (rustc/cargo 1.85 or later), CMake, and a C/C++ compiler.
  These are needed to build the `fasb` Python bindings from `fasb-subtree/`,
  which compile the embedded [clingo](https://github.com/potassco/clingo)
  solver and the [savan](https://crates.io/crates/savan) reasoning library.
- The `plasp` binary (shipped in [bin/plasp](bin/plasp)).

All Python dependencies are declared in [pyproject.toml](pyproject.toml) and
pinned in [uv.lock](uv.lock).

## Build

Create a virtual environment and build the `fasb` Python bindings with

```bash
uv sync
```

This compiles the Rust crate in `fasb-subtree/` (via
[maturin](https://www.maturin.rs)) and installs it as the importable `fasb`
module into `.venv/`.

Alternatively, build an Apptainer container (which performs all of the above
inside the image) as follows:

```bash
apptainer build planpilot.sif Apptainer.planpilot
```

## Usage

Basic usage:

```bash
uv run python planpilot.py -i /path/to/instance.pddl --horizon HORIZON

```

where `HORIZON` is a positive number.

When using the container:

```bash
./planpilot.sif -i /path/to/instance.pddl --horizon HORIZON

```

### Beluga Usage

For example, consider the Beluga Challenge with a horizon of 17 and a single fixed action at time step 12. One can enumerate or reason about the importance of the PlanPilot as follows:

```bash
./planpilot.sif -i benchmarks/beluga-exp-solvable/problem_3_s45_j3_r2_oc44_f3.pddl --horizon 17 --script scripts/list-facets.fasb --add-constraints ":- not occurs(action(("pick-up-rack","jig0002","factory_trailer_1","rack00","fside","bside","n25","n05","n30")), 12)."

./planpilot.sif -i benchmarks/beluga-exp-solvable/problem_3_s45_j3_r2_oc44_f3.pddl --horizon 17 --script scripts/facet-reason.fasb --add-constraints ":- not occurs(action(("pick-up-rack","jig0002","factory_trailer_1","rack00","fside","bside","n25","n05","n30")), 12)."
```

To start interactive mode, use the following command: Then, navigation in the plans space is possible with the `fasb` commands listed below.
```bash
./planpilot.sif -i benchmarks/beluga-exp-solvable/problem_46_s89_j3_r2_oc32_f3.pddl --horizon 17
```

### Other arguments:

- -h, --help            show this help message and exit
- -i INSTANCE, --instance INSTANCE
                        The path to the PDDL/SAS instance file.
-  -d DOMAIN, --domain DOMAIN
                        (Optional) The path to the PDDL domain file. If none is provided, the system will try to automatically deduce it from the instance filename.
-  --partial-plan PARTIAL_PLAN
                        The path to the file containing partial plan.
-  --add-constraints ADD_CONSTRAINTS
                        String containing additional constraints.
-  --add-constraints-file ADD_CONSTRAINTS_FILE
                        The path to the file containing additional constraints.
-  --dry                 If true, facets will not be computed at startup.
-  --horizon HORIZON     Horizon used by clingo.
-  --lp-name LP_NAME     Name of intermediate logic program (lp) file.
-  --encoding {exact,bounded}
                        Type of ASP encoding.
-  --abstract-time-steps
                        If true, it only reports that actions occur some time during the plans, but without specifying when.
-  --script SCRIPT       The path to the fasb script; for non-interactive mode.
-  --dump-output         dump the output of tools.
-  --cleanup             Clean all LP files in the folder after execution.


The program first encodes the planning problem as an answer set program using
`plasp` (Gebser et al. 2011; Dimoulos et al. 2019; [link to
repo](https://github.com/potassco/plasp). Reasoning over the resulting answer
sets is then performed by `fasb` (Fichte et al. AAAI 2022; [link to
repo](https://github.com/drwadu/fasb)). Instead of calling a prebuilt `fasb`
binary, the reasoning is now integrated through the Python bindings of `fasb`
(`start_fasb` for interactive mode, `start_fasb_interpreter` for running
scripts), which are built from the Rust sources in
[fasb-subtree/](fasb-subtree/) and rely on the [savan](https://github.com/drwadu/savan)
library for answer-set navigation. The original `README.md` and `LICENSE` of
`fasb` can be found in the directory `fasb-subtree/`.

## `fasb` Commands

Below is a list of the "essential" commands of `fasb`. We also comment on how they relate to the planning context:

- `! n`: list `n` different answer sets (*plans*, in our context). If `n` is not given,
  all answer sets will be listed
- `?`: display all facets
- `#!`: count the number of answer sets (plans)
- `#?`: count the number of atomic facets (meaningful operators)
- `#!!`: query for each facet how much its activation decreases the number of answer sets, and the remaining number of answer sets
- `#??`: query for each facet how much its activation decreases the number of facets, and the remaining number of facets
- `|= %`: display all implied/entailed atoms, i.e., landmarks given the current navigation route and plan horizon
- `|= %%`: display all impossible atoms with respect to the current navigation route and plan horizon
- `+ FACET`: activate the facet `FACET`. Use the same string for `FACET` as
  listed when using the command `#??`.
- `- FACET`: deactivate the facet `FACET`. Use the same string for `FACET` as
  listed when using the command `#??`
- `:q`: quit `fasb`

See [here](https://github.com/drwadu/fasb/blob/main/src/config.rs) for more commands.

## Third-Party Software

We utilize for grounding the [Fast Downward](https://www.fast-downward.org/latest/) translator ([files](translate)).

This project includes the following third-party tools under their original licenses:

- plasp: A PDDL-to-ASP translator. The binary is redistributed under the MIT License; the license text can be found in [bin/LICENSE-plasp.md](bin/LICENSE-plasp.md).

- fasb: A Facet-based Answer Set Browser. The complete Rust sources are maintained as a git subtree in [fasb-subtree/](fasb-subtree/) and built into Python bindings at compile time. Distributed under the MIT License; the license text and original documentation can be found in the [fasb-subtree/](fasb-subtree/) directory.

- savan: The answer-set navigation and reasoning library used by `fasb`. It is pulled in as a Rust dependency (crate version pinned in [fasb-subtree/Cargo.lock](fasb-subtree/Cargo.lock)) at build time.
