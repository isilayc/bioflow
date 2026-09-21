# BioFlow Windows EXE Builder v4

v4 fixes a false-negative self-test from v3.

The v3 `SELF_TEST.txt` could show:

- `streamlit developmentMode=True`
- `internal Streamlit server=PASS`
- `RESULT: FAIL`

That combination means the EXE's frozen Streamlit package *inferred* development
mode from its temporary PyInstaller path, but BioFlow's actual internal server
still started successfully because BioFlow launches it with:

`--global.developmentMode=false`

So the direct config inspection was testing the wrong thing.

v4 keeps the runtime override and changes the self-test so the authoritative
check is the real packaged child server startup. If that child starts, the EXE
passes this part of validation.

The Python 3.10 / PyInstaller bytecode compatibility fix from v2 and the
Streamlit release-mode runtime override from v3 are both retained.

## Run

Extract this ZIP into:

`C:\Users\Işılay\Documents\bioflow`

Overwrite the older builder files and run:

```powershell
python build_bioflow_exe.py
```

Expected success lines in `SELF_TEST.txt`:

```text
BioFlow runtime override=--global.developmentMode=false
internal Streamlit server with release-mode override=PASS
RESULT: PASS
```

Output:

```text
release\BioFlow_v1.0\BioFlow.exe
release\BioFlow_v1.0\SELF_TEST.txt
release\BioFlow_v1.0\BUILD_INFO.txt
```
