"""Harness : lance les algos des dépôts sur une instance, score et loggue.

Usage :
    python harness/run_all.py <instance.in> [--timeout S] [--algos moi,autre1,...]
                              [--tag TAG] [--quiet]

Chaque exécution se fait dans une copie jetable du dépôt (sandbox/<algo>_<pid>),
recréée depuis le clone en lecture seule de repos/. Aucun source n'est modifié :
on copie, on lance, on lit la sortie, on efface la copie.

Résultats ajoutés à results/runs.csv et results/runs.jsonl, et renvoyés
par run_instance() pour la recherche automatique.
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scorer"))
from score import read_instance, evaluate, check_instance  # noqa: E402

REPOS = os.path.join(ROOT, "repos")
SANDBOX = os.path.join(ROOT, "sandbox")
RESULTS = os.path.join(ROOT, "results")
AUTRE3_EXE = os.path.join(SANDBOX, "bin", "autre3.exe")  # compilé depuis repos/APSJeffersonStorck
PY = sys.executable
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Timeout par défaut : voir README du harness (baseline officielle).
DEFAULT_TIMEOUT = 1200  # MOI : 403 s sur videos_worth_spreading, 766 s sur trending_today

ALGOS = ["moi", "autre1", "autre2", "autre3"]

# Variable d'environnement MOI_MAIN : chemin d'un main.py à utiliser à la place de celui du clone
# (le reste du code de MOI vient toujours du clone). Sert à tester une modification de main.py
# faite dans le dépôt de travail, par ex. la recherche locale désactivée (TEST_LOCAL_SEARCH = False).
MOI_MAIN = os.environ.get("MOI_MAIN")
# Variable d'environnement MOI_FLAGS : constantes de main.py à forcer à l'exécution, sans toucher au
# source, par ex. MOI_FLAGS="KNAPSACK=0,TEST_LOCAL_SEARCH=0" pour ne garder que les gloutons
# (le knapsack ne termine pas sur kittens : ~20 s par cache × 500 caches).
MOI_FLAGS = os.environ.get("MOI_FLAGS", "")

# Petit lanceur écrit dans la sandbox : importe main.py, force les constantes, puis fait
# exactement ce que fait le bloc __main__ de main.py pour une instance.
FLAGS_RUNNER = '''import sys
import main as M
for kv in sys.argv[2].split(","):
    k, v = kv.split("=")
    setattr(M, k, bool(int(v)))
res = M.main([sys.argv[1]])
M.create_results_files(res["caches"], f"{M.RESULTS_DIR}/{sys.argv[1].split('/')[-1].split('.')[0]}.out")
'''


def _copy(src_rel, dst, files):
    """Copie les fichiers/dossiers utiles d'un dépôt dans la sandbox, en écriture."""
    src = os.path.join(REPOS, src_rel)
    os.makedirs(dst, exist_ok=True)
    for f in files:
        s = os.path.join(src, f)
        d = os.path.join(dst, f)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy(s, d)
    for dirpath, _, filenames in os.walk(dst):
        for fn in filenames:
            os.chmod(os.path.join(dirpath, fn), 0o666)


def _rmtree(path):
    def onerr(func, p, _):
        os.chmod(p, 0o777)
        func(p)
    shutil.rmtree(path, onerror=onerr)


def _run(cmd, cwd, timeout, stdin=None, stdout=None):
    """Lance cmd ; renvoie (statut, durée, code, stderr tronqué)."""
    t = time.perf_counter()
    p = subprocess.Popen(cmd, cwd=cwd, stdin=stdin, stdout=stdout or subprocess.DEVNULL,
                         stderr=subprocess.PIPE,
                         creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    try:
        _, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.communicate()
        return "timeout", time.perf_counter() - t, None, ""
    dt = time.perf_counter() - t
    err = (err or b"").decode("utf-8", "replace")[-400:]
    return ("ok" if p.returncode == 0 else "crash"), dt, p.returncode, err


def run_algo(algo, inst_path, timeout):
    """Exécute un algo dans sa sandbox ; renvoie (statut, durée, chemin de sortie, stderr)."""
    box = os.path.join(SANDBOX, f"{algo}_{os.getpid()}")
    if os.path.exists(box):
        _rmtree(box)
    inst_path = os.path.abspath(inst_path)
    out_keep = os.path.join(box + "_out.txt")
    try:
        if algo == "moi":
            _copy("AdvancedProblemSolvingGrpG", box, ["main.py", "utils.py", "algos"])
            if MOI_MAIN:
                shutil.copy(MOI_MAIN, os.path.join(box, "main.py"))
            os.makedirs(os.path.join(box, "results"))
            # main.py découpe les chemins sur '/', on passe donc un chemin en '/'
            if MOI_FLAGS:
                with open(os.path.join(box, "run_flags.py"), "w") as f:
                    f.write(FLAGS_RUNNER)
                cmd = [PY, "run_flags.py", inst_path.replace("\\", "/"), MOI_FLAGS]
            else:
                cmd = [PY, "main.py", inst_path.replace("\\", "/")]
            st, dt, code, err = _run(cmd, box, timeout)
            name = os.path.basename(inst_path).split(".")[0] + ".out"
            out = os.path.join(box, "results", name)
        elif algo == "autre1":
            _copy("hashcode-2017-streaming-videos", box, ["main.py", "score.py"])
            out = os.path.join(box, "out.txt")
            # mode juge (stdin -> stdout), sans affichage verbeux
            with open(inst_path, "rb") as fi, open(out, "wb") as fo:
                st, dt, code, err = _run([PY, "main.py"], box, timeout, stdin=fi, stdout=fo)
        elif algo == "autre2":
            _copy("hashcode_2017", box, ["solution.py"])
            out = os.path.join(box, "out.txt")
            st, dt, code, err = _run([PY, "solution.py", inst_path, out], box, timeout)
        elif algo == "autre3":
            os.makedirs(box)
            out = os.path.join(box, "result.txt")
            st, dt, code, err = _run([AUTRE3_EXE, inst_path], box, timeout)
        else:
            raise ValueError(algo)
        if os.path.exists(out):
            shutil.copy(out, out_keep)
        elif os.path.exists(out_keep):
            os.remove(out_keep)
        return st, dt, out_keep, err
    finally:
        if os.path.exists(box):
            _rmtree(box)


def run_instance(inst_path, algos=ALGOS, timeout=DEFAULT_TIMEOUT, tag="", keep_dir=None,
                 log=True, quiet=False):
    inst = read_instance(inst_path)
    incoh = check_instance(inst)
    size = os.path.getsize(inst_path)
    rows = []
    for algo in algos:
        st, dt, out, err = run_algo(algo, inst_path, timeout)
        if st == "ok" and os.path.exists(out):
            ev = evaluate(inst_path, out, inst)
            if not ev["valid"]:
                st = "invalid"
            sc = ev["score"]
            verr = ev["error"]
        else:
            sc, verr = 0, None
            if st == "ok":
                st = "no_output"
        if keep_dir and os.path.exists(out):
            os.makedirs(keep_dir, exist_ok=True)
            shutil.copy(out, os.path.join(keep_dir, f"{algo}.out"))
        if os.path.exists(out):
            os.remove(out)
        row = dict(date=time.strftime("%Y-%m-%d %H:%M:%S"), tag=tag,
                   instance=os.path.relpath(inst_path, ROOT).replace("\\", "/"),
                   bytes=size, V=inst["V"], E=inst["E"], R=inst["R"], C=inst["C"], X=inst["X"],
                   algo=algo, status=st, score=sc, time_s=round(dt, 3),
                   error=(verr or err.strip().splitlines()[-1] if (verr or err.strip()) else "")
                   if st != "ok" else "",
                   coherent=not incoh)
        rows.append(row)
        if not quiet:
            print(f"  {algo:7s} {st:8s} score={sc:>16} t={dt:8.2f}s {row['error'][:80]}", flush=True)
    if log:
        os.makedirs(RESULTS, exist_ok=True)
        csv_path = os.path.join(RESULTS, "runs.csv")
        new = not os.path.exists(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            if new:
                w.writeheader()
            w.writerows(rows)
        with open(os.path.join(RESULTS, "runs.jsonl"), "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows, incoh


def metric(rows):
    """(ratio, écart) : score(moi) / max(score autres), départage moi - max autres."""
    sc = {r["algo"]: r["score"] for r in rows}
    others = max(v for k, v in sc.items() if k != "moi")
    me = sc.get("moi", 0)
    ratio = float("inf") if others == 0 and me > 0 else (me / others if others else 0.0)
    return ratio, me - others


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--algos", default=",".join(ALGOS))
    ap.add_argument("--tag", default="")
    ap.add_argument("--keep", default=None, help="dossier où garder les sorties")
    a = ap.parse_args()
    print(f"== {a.instance} ({os.path.getsize(a.instance)} octets)")
    rows, incoh = run_instance(a.instance, a.algos.split(","), a.timeout, a.tag, a.keep)
    if incoh:
        print(f"  ATTENTION instance incohérente : {incoh[:3]}")
    if "moi" in a.algos and len(rows) > 1:
        r, d = metric(rows)
        print(f"  ratio = {r:.6g}   écart = {d}")
