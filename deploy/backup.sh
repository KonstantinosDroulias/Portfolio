#!/usr/bin/env bash
# Nightly: SQLite snapshot + uploaded files. Keeps 14 days. Run by /etc/cron.d/konstantinosdroulias.
set -euo pipefail
B=/srv/konstantinosdroulias/backups; D=/srv/konstantinosdroulias/data; T=$(date +%F)
mkdir -p "$B"
sqlite3 "$D/db.sqlite3" ".backup '$B/db-$T.sqlite3'"
gzip -f "$B/db-$T.sqlite3"
tar -czf "$B/media-$T.tar.gz" -C "$D" media
find "$B" -type f -mtime +14 -delete
