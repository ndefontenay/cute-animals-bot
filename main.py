"""
Entry points:
  python main.py run       — run one full pipeline cycle
  python main.py upload    — upload approved videos from review queue
  python main.py review    — start local review server on :5000
  python main.py metrics   — poll YouTube metrics for pending videos
  python main.py schedule  — start the APScheduler daemon (daily posting)
"""
import sys


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "run":
        from scheduler.jobs import run_pipeline
        run_pipeline()

    elif cmd == "upload":
        from scheduler.jobs import upload_approved
        upload_approved()

    elif cmd == "review":
        from review.app import app
        print("Review queue running at http://localhost:5000")
        app.run(debug=False, port=5000)

    elif cmd == "metrics":
        from monitor.metrics import poll_pending
        poll_pending()

    elif cmd == "schedule":
        from apscheduler.schedulers.blocking import BlockingScheduler
        from scheduler.jobs import run_pipeline, upload_approved
        from monitor.metrics import poll_pending
        from config.settings import POSTING_HOUR

        scheduler = BlockingScheduler()
        # Generate and score candidates every day at 6am
        scheduler.add_job(run_pipeline, "cron", hour=POSTING_HOUR - 2, minute=0)
        # Upload approved videos at posting hour
        scheduler.add_job(upload_approved, "cron", hour=POSTING_HOUR, minute=0)
        # Poll metrics every 6 hours
        scheduler.add_job(poll_pending, "interval", hours=6)

        print(f"Scheduler started. Posting daily at {POSTING_HOUR}:00 UTC.")
        scheduler.start()

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
