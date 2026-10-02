"""
Mesure du score : lance claude_main.py sur chaque instance officielle (un processus par instance,
timeout 20 min), puis fait noter chaque fichier results/<instance>_claude.out par le juge C++.

    python claude_bench.py              -> les 4 instances officielles
    python claude_bench.py kittens      -> une seule
    python claude_bench.py --seq        -> les instances l'une après l'autre (plus de cœurs chacune, ~2 fois plus long)

Le score retenu est celui du juge (judge/judgeHashCode2017.cpp, non modifié, compilé dans results/).
"""
import os
import subprocess
import sys
import time

INSTANCES = ["me_at_the_zoo", "trending_today", "videos_worth_spreading", "kittens"]
TIMEOUT = 20 * 60
JUDGE_SRC = "judge/judgeHashCode2017.cpp"
JUDGE_BIN = "results/judge_bin"


def judge(name):
    out = subprocess.run([JUDGE_BIN, f"instances/{name}.in", f"results/{name}_claude.out"],
                         capture_output=True, text=True).stdout
    return int(out.strip().split("=")[-1]) if "Score" in out else 0


def main(names, sequential=False):
    os.makedirs("results", exist_ok=True)
    if not os.path.exists(JUDGE_BIN) or os.path.getmtime(JUDGE_BIN) < os.path.getmtime(JUDGE_SRC):
        subprocess.run(["g++", "-O2", "-w", "-o", JUDGE_BIN, JUDGE_SRC], check=True)

    start = time.time()
    env = dict(os.environ)
    if sequential:
        # une instance à la fois : chacune dispose de presque tous les cœurs
        env.setdefault("CLAUDE_WORKERS", str(max(1, os.cpu_count() - 2)))

    def launch(name):
        out_file = f"results/{name}_claude.out"
        if os.path.exists(out_file):
            os.remove(out_file)  # pas de vieux fichier noté par erreur
        log = open(f"results/{name}_claude.log", "w")
        return (subprocess.Popen(["timeout", str(TIMEOUT), sys.executable, "claude_main.py", f"instances/{name}.in"],
                                 stdout=log, stderr=subprocess.STDOUT, env=env), time.time())

    procs = {} if sequential else {name: launch(name) for name in names}

    total = 0
    for name in names:
        proc, t0 = launch(name) if sequential else procs[name]
        rc = proc.wait()
        dt = time.time() - t0
        score = judge(name) if rc == 0 and os.path.exists(f"results/{name}_claude.out") else 0
        total += score
        print(f"{name:<24} {score:>9}  [{dt:6.0f}s]" + ("" if rc == 0 else f"  ECHEC rc={rc}"))
    print(f"{'TOTAL':<24} {total:>9}  [{time.time() - start:6.0f}s]")
    return total


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--seq"]
    main(args or INSTANCES, sequential="--seq" in sys.argv[1:])
