# COE 379L Fall 2026 Midterm Project 

This repository contains the provided infrastructure and staged public tests for the 
 COE 379L Fall 2026 midterm project. 
 Read `ASSIGNMENT.md`, then follow `IMPLEMENTATION_STEPS.md` in order. 
 `ARCHITECTURE.md` explains the modules and data flow.


## Completed project artifacts

- `public_benchmark.json`: public scenario results and execution traces.
- `atlas_report.pdf`: two-page evaluation report.
- `atlas_report.tex`: editable report source based on the supplied template.
- `data_flow_diagram.pdf`: single-scenario data flow diagram.
- `data_flow_diagram.png`: diagram image.
- `tests/test_student_cases.py`: three additional deterministic tests.

Run all tests with `uv run pytest`. Recreate the public benchmark with
`uv run atlas-evaluate-scripted > public_benchmark.json`.
