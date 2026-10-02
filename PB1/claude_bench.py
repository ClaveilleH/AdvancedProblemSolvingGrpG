"""
Mesure du score : lance claude_main.py sur chaque instance officielle (un processus par instance,
timeout 20 min), puis fait noter chaque fichier results/<instance>_claude.out par le juge C++.

    python claude_bench.py              -> les 4 instances officielles
    python claude_bench.py kittens      -> une seule

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


def main(names):
    os.makedirs("results", exist_ok=True)
    if not os.path.exists(JUDGE_BIN) or os.path.getmtime(JUDGE_BIN) < os.path.getmtime(JUDGE_SRC):
        subprocess.run(["g++", "-O2", "-w", "-o", JUDGE_BIN, JUDGE_SRC], check=True)

    start = time.time()
    procs = {}
    for name in names:
        out_file = f"results/{name}_claude.out"
        if os.path.exists(out_file):
            os.remove(out_file)  # pas de vieux fichier noté par erreur
        log = open(f"results/{name}_claude.log", "w")
        procs[name] = (subprocess.Popen(["timeout", str(TIMEOUT), sys.executable, "claude_main.py", f"instances/{name}.in"],
                                        stdout=log, stderr=subprocess.STDOUT), time.time())

    total = 0
    for name, (proc, t0) in procs.items():
        rc = proc.wait()
        dt = time.time() - t0
        score = judge(name) if rc == 0 and os.path.exists(f"results/{name}_claude.out") else 0
        total += score
        print(f"{name:<24} {score:>9}  [{dt:6.0f}s]" + ("" if rc == 0 else f"  ECHEC rc={rc}"))
    print(f"{'TOTAL':<24} {total:>9}  [{time.time() - start:6.0f}s]")
    return total


if __name__ == "__main__":
    main(sys.argv[1:] or INSTANCES)
