import pathlib
W0 = pathlib.Path("../submissions/w0_v15stack_control.py").read_text()
TPL = pathlib.Path("wrapper_template.py").read_text()
VAR = {
    "B":  dict(MODE="B", C_START="99", D_LIMIT="0"),
    "C1": dict(MODE="C", C_START="8",  D_LIMIT="0"),
    "C2": dict(MODE="C", C_START="3",  D_LIMIT="0"),
    "D4": dict(MODE="D", C_START="99", D_LIMIT="4"),
    "D8": dict(MODE="D", C_START="99", D_LIMIT="8"),
}
for name, p in VAR.items():
    body = TPL.replace("__MODE__", p["MODE"]).replace("__C_START__", p["C_START"]).replace("__D_LIMIT__", p["D_LIMIT"])
    d = pathlib.Path(name); d.mkdir(exist_ok=True)
    (d / "main.py").write_text(W0 + "\n" + body)
    print(name, "written", len(W0) + len(body), "bytes")
