# TTS audio cleanup (production scheduling)

## Why cleanup is needed

Assistant TTS saves temporary MP3 files under `MEDIA_ROOT/tts/`. Without cleanup, disk usage grows indefinitely. Puzzle 18A added a safe cleanup command; this document explains how to run it on a schedule **outside** the FastAPI process.

## What gets deleted

Cleanup (`python -m scripts.cleanup_tts_audio`) removes **only**:

- Files in `{MEDIA_ROOT}/tts/` (default: `media/tts/`)
- Regular files with extension `.mp3`
- Files whose modification time is **older** than `TTS_AUDIO_TTL_HOURS` (default: **24**)

## What is NOT deleted

Cleanup does **not** touch:

- Listing images and user uploads in `MEDIA_ROOT/` (outside `tts/`)
- Placeholder images (e.g. `/media/placeholders/...`)
- Non-`.mp3` files (even inside `tts/`)
- Fresh TTS files still within the TTL window
- Any path outside `MEDIA_ROOT/tts/`

Assistant conversation history in the database is unchanged. Old `tts_audio_url` values in message metadata may return HTTP 404 after the file is removed — expected for expired audio.

## Environment variables

| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `MEDIA_ROOT` | Root media directory | `media` |
| `TTS_AUDIO_TTL_HOURS` | Age threshold for deletion | `24` |

Use the same `.env` as the API so paths match production storage.

## Manual run

From the backend project root:

```bash
python -m scripts.cleanup_tts_audio
```

With explicit TTL:

```bash
python -m scripts.cleanup_tts_audio --ttl-hours 24
```

Logs include counts, for example:

```text
tts_cleanup deleted=10 skipped=3 errors=0 ttl_hours=24 path=.../media/tts
tts_cleanup finished deleted=10 skipped=3 ttl_hours=24
```

Exit code `1` only if some files failed to delete (`error_count > 0`).

## systemd timer (Linux)

1. Copy and edit examples (paths, user, Python venv):

   - `docs/deployment/tts-cleanup-systemd.service.example`
   - `docs/deployment/tts-cleanup-systemd.timer.example`

2. Install:

   ```bash
   sudo cp tts-cleanup-systemd.service.example /etc/systemd/system/aivai-tts-cleanup.service
   sudo cp tts-cleanup-systemd.timer.example /etc/systemd/system/aivai-tts-cleanup.timer
   sudo systemctl daemon-reload
   sudo systemctl enable --now aivai-tts-cleanup.timer
   ```

3. Check:

   ```bash
   systemctl list-timers aivai-tts-cleanup.timer
   sudo systemctl start aivai-tts-cleanup.service   # one-off test
   journalctl -u aivai-tts-cleanup.service -n 50
   ```

Default schedule: once per day at 03:15 local time.

## cron

See `docs/deployment/tts-cleanup-cron.example`. Typical pattern: nightly run from project root with log append.

```bash
crontab -e
# paste the line from the example file (adjust paths)
```

## Docker Compose (optional one-off service)

Example override: `docs/deployment/tts-cleanup-docker-compose.override.example.yml`

Not merged automatically. Use when you want a manual or CI-triggered cleanup container sharing the app image and `media` volume:

```bash
docker compose -f docker-compose.yml -f docs/deployment/tts-cleanup-docker-compose.override.example.yml --profile cleanup run --rm tts-cleanup
```

## Kubernetes CronJob

See `docs/deployment/tts-cleanup-k8s-cronjob.example.yaml`.

Apply after replacing image name, namespace, volume mounts, and `envFrom` secret. Schedule default: daily at 03:15 UTC.

```bash
kubectl apply -f docs/deployment/tts-cleanup-k8s-cronjob.example.yaml
kubectl get cronjob aivai-tts-cleanup
```

## Design constraints (Puzzle 18B)

- No background scheduler inside FastAPI
- No Celery / Redis
- Cleanup is **not** triggered per HTTP request
- Runtime API code is unchanged; scheduling is ops-only

## Related code

- `app/services/tts_cleanup_service.py` — `cleanup_old_tts_files()`
- `scripts/cleanup_tts_audio.py` — CLI entrypoint
- `app/core/config.py` — `TTS_AUDIO_TTL_HOURS`
