# Google Cloud deployment (later)

This project is designed around a Cloud Run Job that starts, performs one planning/check cycle, sends Telegram messages if needed, and exits.

## Google services

- Artifact Registry: stores the container image.
- Cloud Run Jobs: executes the container.
- Cloud Scheduler: triggers the job on a schedule.
- Secret Manager: stores `TELEGRAM_BOT_TOKEN` and `TWOGIS_API_KEY`.

The exact IAM/service-account wiring will be added when we deploy. No VPS or SSH server is required.

## Important

Never put Telegram or 2GIS keys in Git, Dockerfiles, source code, screenshots, or `.env` committed to Git.
