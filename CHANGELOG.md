# Changelog

All notable changes to PlanPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Relaxed the Python requirement from `>=3.12,<3.13` to `>=3.12`. 
- Updated the Apptainer container base image from Ubuntu 24.04 to Ubuntu
  26.04 LTS (Resolute Raccoon).
- fasb reasoning is now integrated through its Python bindings (`start_fasb`
  and `start_fasb_interpreter`) instead of invoking prebuilt `fasb` binaries.
  The bindings are built from the Rust sources in `fasb-subtree/`, which rely
  on the `savan` library for answer-set navigation and embed the clingo
  solver.
- Build instructions now use `uv`: `uv sync` creates the virtual environment
  and compiles the `fasb` bindings via maturin. Native requirements are a
  Rust toolchain (1.85+), CMake, and a C/C++ compiler.
- README updated accordingly: new Requirements/Build sections and revised
  Third-Party Software section.

### Removed

- Prebuilt `fasb` binaries (`bin/fasb`, `bin/fasb_interpreter`,
  `bin/fasb-x86_64-unknown-linux-gnu/`); `bin/` now only ships the `plasp`
  binary.
- Unused utility functions for checking prebuilt binaries
  (`is_binary_available`, `check_necessary_files`) from `utils.py`.

### Added

- Top-level `pyproject.toml` and `uv.lock` declaring the `fasb` dependency,
  built as an editable path source from `fasb-subtree/`.
- `fasb-subtree/` as a git subtree of
  [drwadu/fasb](https://github.com/drwadu/fasb).
- Updated Apptainer recipe that builds the `fasb` Python bindings from source
  inside the container image.
