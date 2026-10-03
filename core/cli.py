"""Komut satırı.

  python -m core.cli init                 fikir havuzunu veritabanına aktarır
  python -m core.cli new [--idea ID]      yeni job açar
  python -m core.cli run JOB_ID           job'u kaldığı yerden çalıştırır
  python -m core.cli resume JOB_ID        needs_attention'daki job'u devam ettirir
  python -m core.cli status               job listesi
  python -m core.cli costs                gün/ay harcaması
  python -m core.cli demo                 sahte sağlayıcılarla uçtan uca deneme (ücretsiz, geçici klasörde)
"""
from __future__ import annotations

import argparse
import copy
import sys
import tempfile
from pathlib import Path

from core import settings, states
from core.app import App, NewJobBlocked


def _first_available_idea(app: App) -> str:
    row = app.conn.execute("SELECT id FROM ideas WHERE status = 'available' ORDER BY rowid LIMIT 1").fetchone()
    if row is None:
        sys.exit("Kullanılabilir fikir kalmadı. channels/k1/ideas.yaml dosyasına yeni fikir ekle.")
    return row["id"]


def cmd_status(app: App) -> None:
    rows = app.conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
    if not rows:
        print("Henüz job yok.")
    for r in rows:
        extra = f" — {r['attention_reason']}" if r["attention_reason"] else ""
        print(f"{r['id']}  {r['status']:<16} {r['cost_usd']:>7.2f} $  {r['idea_id']}{extra}")


def cmd_costs(app: App) -> None:
    b = app.config["budget"]
    print(f"Bugün: {app.ledger.day_total():.2f} $ / {b['max_cost_per_day']:.0f} $")
    print(f"Bu ay: {app.ledger.month_total():.2f} $ / {b['max_cost_per_month']:.0f} $")


def cmd_demo(idea_id: str) -> int:
    config = copy.deepcopy(settings.load_config())
    with tempfile.TemporaryDirectory(prefix="k1-demo-") as tmp:
        app = App.open(config=config, data_root=Path(tmp), provider_mode="mock")
        app.sync_ideas()
        job_id = app.create_job(idea_id)
        print(f"Demo job: {job_id} ({idea_id}) — sahte sağlayıcılar, gerçek harcama yok.\n")
        final = app.run(job_id)
        ctx = app.context(job_id)
        for rec in ctx.log.read():
            if rec["event"] == "end":
                print(f"  ✔ {rec['step']:<10} {rec['cost_usd']:>6.2f} $")
        print(f"\nSon durum: {final}")
        print(f"Tahmini maliyet (gerçek fiyatlarla): {app.ledger.job_total(job_id):.2f} $ "
              f"(tavan {config['budget']['max_cost_per_video']:.0f} $)")
        plan = ctx.read_json("shots", "plan.json")
        ai = [k for k, v in plan.items() if v == "ai"]
        timing = ctx.read_json("audio", "timing.json")
        ai_s = sum(t["gen_s"] for t in timing["shots"] if t["id"] in ai)
        print(f"Hibrit mod: {len(ai)}/{len(plan)} sahne AI video ({ai_s} sn), "
              f"kalanı anahtar kare + kamera hareketi.")
        print(f"Video süresi: {timing['total_s']:.1f} sn")
        return 0 if final == states.AWAITING_REVIEW else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m core.cli")
    parser.add_argument("--mock", action="store_true", help="sahte sağlayıcıları kullan")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p_new = sub.add_parser("new")
    p_new.add_argument("--idea")
    for name in ("run", "resume"):
        sub.add_parser(name).add_argument("job_id")
    sub.add_parser("status")
    sub.add_parser("costs")
    p_demo = sub.add_parser("demo")
    p_demo.add_argument("--idea", default="diesel-engine")
    args = parser.parse_args(argv)

    if args.cmd == "demo":
        return cmd_demo(args.idea)

    app = App.open(provider_mode="mock" if args.mock else None)
    if args.cmd == "init":
        print(f"{app.sync_ideas()} fikir veritabanına aktarıldı.")
    elif args.cmd == "new":
        try:
            job_id = app.create_job(args.idea or _first_available_idea(app))
        except NewJobBlocked as e:
            print(f"Yeni job açılmadı: {e}")
            return 1
        print(f"Yeni job: {job_id}")
    elif args.cmd == "run":
        print(f"{args.job_id}: {app.run(args.job_id)}")
    elif args.cmd == "resume":
        print(f"{args.job_id}: {states.resume(app.conn, args.job_id)} durumuna dönüldü")
        print(f"{args.job_id}: {app.run(args.job_id)}")
    elif args.cmd == "status":
        cmd_status(app)
    elif args.cmd == "costs":
        cmd_costs(app)
    return 0


if __name__ == "__main__":
    sys.exit(main())
