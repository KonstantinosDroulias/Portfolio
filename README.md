# konstantinosdroulias.com

Personal site + blog with its own CMS. Django 5.2, SQLite, plain templates, one CSS file, a little vanilla JS. No build step.

- Public: `/`, `/writing/` (topics, tags, search, pages), `/writing/<slug>/`, `/work/`, `/about/`, `/contact/`, `/cv/`, `/feed/`, `/sitemap.xml`, `/robots.txt`
- CMS: `/admin/` (sign in at `/admin/login/`; there is no link to it on the site). Posts in Markdown with toolbar,
  preview, drag/paste image upload and a cover image; messages from the contact form; contact info, socials,
  “Now” list and CV upload; your profile (photo → face-cropped avatar, bio, password); users (owner only).
- Signed-in users see an admin bar on the site: Admin panel / Edit post on the left, their avatar + username on the right.
- Text-only content (Work projects, What I do, Tools) lives in `kd/content.py`.

## Run the tests (Mac)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DEBUG=1 DATA_DIR=/tmp/kd-test .venv/bin/python manage.py test kd
```

## Deploy

`bin/deploy.sh` rsyncs to the VPS, installs requirements, migrates, collects static and restarts.

| | |
|---|---|
| Server | `root@drouliasvps.cloud`, `/srv/konstantinosdroulias/{app,venv,data,backups}`, user `kd` |
| Service | `konstantinosdroulias.service` (gunicorn socket `/run/konstantinosdroulias/app.sock`) |
| nginx | site `konstantinosdroulias` (www and http → https apex), snippet `konstantinosdroulias-proxy.conf`, login rate limit in `conf.d/konstantinosdroulias-limits.conf` |
| HTTPS | certbot cert `konstantinosdroulias.com` (+ www), webroot `/var/www/html` |
| Secrets | `/srv/konstantinosdroulias/.env` (SECRET_KEY, optional SMTP) |
| Backups | `/usr/local/bin/konstantinosdroulias-backup` nightly 02:40 (`/etc/cron.d/konstantinosdroulias`), 14 days in `backups/` |
| First run | `manage.py setup_site` creates the owner `konstantinos`, his profile and the launch posts (safe to rerun) |

Contact-form email: messages are always stored in the CMS. To also email them, set `EMAIL_HOST=smtp.gmail.com`,
`EMAIL_HOST_USER=me@konstantinosdroulias.com` and a Google app password in `.env`, then `systemctl restart konstantinosdroulias`.
