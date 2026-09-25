# CLAUDE.md

Write Your Python Program (WYPP): a beginner-friendly Python environment. Two parts ship together:

- **VS Code extension** (TypeScript, `src/`), which adds a RUN button and a program-flow visualization.
- **`wypp` Python package** (`python/code/wypp/`), the teaching language: records, dynamic type checking of annotations, `check(...)` tests and localized (German/English) error messages. It is also published to PyPI.

## Layout

- `src/extension.ts`: extension entry point. It runs `python/code/wypp/runYourProgram.py` in a terminal, with `python/code` on the path.
- `src/programflow-visualization/`: Python-Tutor-like visualization. See its `README.md` for the architecture.
  - `backend/` spawns `pytrace-generator/main.py` to produce traces.
  - `graph-model.ts` and `reachability.ts` hold pure logic (unit-tested).
  - `web/` is the webview UI (ELK layout), bundled by `scripts/build-web.mjs` with esbuild.
- `python/code/wypp/`: the runtime (`runner.py`, `typecheck.py`, `records.py`, `errors.py`, `i18n.py`, ...).
- `python/code/typeguard/`: vendored copy of typeguard. Always import it through `wypp/myTypeguard.py`, never directly.
- `pytrace-generator/`: standalone tracer for the visualization, with its own tests.
- `elk-task/`, `visualization-plan.md`: design notes for ongoing visualization work.

## Commands

TypeScript (run from the repo root):

```sh
npm install
npm run build          # tsc + web bundle -> out/
npm test               # compile, typecheck web, eslint, mocha unit tests (out/test/unit)
npm run watch:web      # rebuild the webview on change (serve out/programflow-visualization/web)
```

Python (run from `python/`; needs Python 3.12–3.14):

```sh
./allTestsForPyVersion                     # unit + integration + file tests
./allTestsForPyVersion --unit tests/test_record.py
python3 fileTests.py --only file-test-data/basics/foo.py
python3 fileTests.py --record file-test-data/basics/foo.py [--lang en]
./run somefile.py                          # run a file with wypp
python3 ../pytrace-generator/test/runTests.py
```

## Definition of done

A change is done when all of the following apply:

1. The tests for every part you touched pass:
   - TypeScript (`src/`): `npm test`.
   - Python runtime (`python/code/`): `./allTestsForPyVersion` in `python/`.
   - Tracer (`pytrace-generator/`): `python3 pytrace-generator/test/runTests.py`.
2. New behavior has a test: a unit test, or a file test in `python/file-test-data/`. A bug fix comes with a test that reproduces the bug.
3. Changed error output has been re-recorded with `--record` in both German and English (`--lang en`), and you have reviewed the diff of the recorded files.
4. Every new user-facing message is wrapped in `tr()` from `i18n.py`, with a German translation added there.
5. You have tried visualization UI changes in a browser (`npm run watch:web`) or in the extension.
6. `ChangeLog.md` has an entry for every user-visible change. `README.md` is updated if documented behavior changed.
7. No stray debug output, scratch files or build artifacts (`out/`, `*.vsix`, `dist/`) are committed.

## Conventions

- **File tests** live in `python/file-test-data/`. Each `foo.py` has expected `foo.out`/`foo.err` files (German) and optional `foo.out_en`/`foo.err_en` files (English). If a change alters error output, re-record with `--record` and review the diff.
- A file test named `*_ok.py` is expected to exit with code 0. Every other file test is expected to exit with code 1.
- A file test that relies on forward references contains the line `# from __future__ import annotations`, commented out. Python 3.14 doesn't need the import. On Python < 3.14, `fileTestsLib.py` runs a temporary copy with the line uncommented.
- CI runs `npm test` and the Python tests on 3.12, 3.13 and 3.14.
- The version lives in `package.json`. The Python package reads it from there (see `python/setup.py` and `wypp/version.py`). Update `ChangeLog.md` when you release.
- `mkdist` packages the `.vsix` (with `vsce`) and the Python distribution. The `*.vsix` files in the root are build artifacts.

## Version control

- Do not create commits unless explicitly ask for.

