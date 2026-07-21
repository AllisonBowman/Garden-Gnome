"""Pre-build test tooling for the on-device photo features.

Not shipped (sibling of app/, excluded from Docker/exe) and not collected
by pytest (pytest.ini pins testpaths=tests). Entry points, run from the
garden-gnome/ directory:

    python -m evals.selftest              # offline sanity of this tooling
    python -m evals.checklist --validate  # lint manifest.csv
    python -m evals.checklist --print     # per-photo device checklist
    python -m evals.replay_device ...     # re-grade transcribed device runs

See plantadvocate-vision-test-plan.md at the repo root for the full
procedure.
"""
