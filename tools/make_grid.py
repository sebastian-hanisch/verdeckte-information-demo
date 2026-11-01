"""Rechnet die Messreihen (Gleichgewichtsfamilie, Verbote, Größenvergleich, Regret-Verfahren in Kuhn und Leduc, Sampling, Anmeldung und Kontrolle) neu und schreibt
data/tables.json samt Erzeuger-Hash.

Aufruf (im Demo-Ordner, mit dem Test-venv):  python tools/make_grid.py [--workers 6]
Ändert sich eine Quelldatei aus vdi_experiments.TABLE_SOURCES, stimmt der Hash nicht mehr (tests/test_measurements.py schlägt an, die App zeigt die Reihen dann nicht);
danach diesen Aufruf wiederholen. Die Zufallsströme hängen nur an (Zufalls-Seed, Zelle): die Reihen sind bei gleichem Code Zahl für Zahl dieselben, auch bei anderer Zahl von Prozessen
(Zeiten ausgenommen). Höchstens sechs Prozesse."""

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vdi_experiments as XP  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    start = time.time()
    jobs = XP.jobs()
    results = {}
    with ProcessPoolExecutor(max_workers=min(args.workers, 6)) as ex:
        for job, res in ex.map(XP.run_job, jobs, chunksize=1):
            results[job] = res
            print(f"fertig: {job}  ({time.time() - start:.0f} s)", flush=True)
    XP.write_json(XP.TABLES_FILE, XP.assemble_payload(results))
    print(f"geschrieben: {XP.TABLES_FILE}  ({time.time() - start:.0f} s, Hash {XP.tables_hash()}, {len(jobs)} Aufträge)")


if __name__ == "__main__":
    main()
