# Deploy on GCP e2-micro (Free Tier)

**Cost: $0/month** — one e2-micro VM runs the dashboard + scraper 24/7 within
Google's Always Free quota (US regions only).

---

## What you need
- A Google account
- A credit card (required to activate GCP — you won't be charged if you stay within free limits)
- The code pushed to GitHub on branch `claude/marine-data-scraper-5HAea`

---

## Step 1 — Create a GCP project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project → New Project**
3. Name it `marine-scraper` → **Create**
4. Make sure billing is enabled (required for free tier)

---

## Step 2 — Create the e2-micro VM

In the GCP Console:

1. Go to **Compute Engine → VM Instances → Create Instance**
2. Fill in:

| Field | Value |
|-------|-------|
| Name | `marine-scraper` |
| Region | `us-central1` (or `us-east1` / `us-west1`) — **must be US for free tier** |
| Zone | any in that region |
| Machine type | `e2-micro` (2 vCPU, 1 GB RAM) |
| Boot disk | **Ubuntu 22.04 LTS**, 30 GB Standard persistent disk |
| Firewall | ✅ Allow HTTP traffic, ✅ Allow HTTPS traffic |

3. Click **Create**

> The 30 GB disk and e2-micro in a US region are **always free**.

---

## Step 3 — Open port 5000 (dashboard)

1. Go to **VPC Network → Firewall → Create Firewall Rule**
2. Fill in:

| Field | Value |
|-------|-------|
| Name | `allow-marine-dashboard` |
| Direction | Ingress |
| Targets | All instances in the network |
| Source IP ranges | `0.0.0.0/0` |
| Protocols/ports | TCP `5000` |

3. Click **Create**

> Or use port 80 with nginx (see Step 7 for optional nginx setup).

---

## Step 4 — SSH into the VM

In the VM Instances list, click the **SSH** button next to your instance.
A browser terminal opens.

---

## Step 5 — Install dependencies and clone the repo

```bash
# Update system
sudo apt update && sudo apt install -y python3-pip python3-venv git screen

# Clone your repo
git clone https://github.com/taqi4/offline-quiz-app.git
cd offline-quiz-app/marine-data-scraper

# Switch to the feature branch
git checkout claude/marine-data-scraper-5HAea

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Initialise the database
python main.py init-db
```

---

## Step 6 — Run the app (dashboard + scraper together)

Use `screen` so the app keeps running after you close the SSH window.

```bash
# Start a screen session
screen -S marine

# Inside screen: activate venv and start the combined server
source venv/bin/activate
python serve_all.py
```

The dashboard is now running at `http://<YOUR-VM-IP>:5000`

**Find your VM's external IP:**
GCP Console → Compute Engine → VM Instances → look at the **External IP** column.

**Detach from screen** (app keeps running): press `Ctrl+A` then `D`

**Re-attach later:** `screen -r marine`

---

## Step 7 — Run the initial scrape

Once the server is up, trigger the first data collection from the UI:

1. Open `http://<YOUR-VM-IP>:5000`
2. In the **Scraper Control** panel, click any scraper name to run it immediately
3. Or SSH back in and run: `python main.py run-all`

---

## Step 8 — Keep it running on reboot (systemd service)

So the app auto-starts if the VM reboots:

```bash
# Create the service file
sudo nano /etc/systemd/system/marine-scraper.service
```

Paste this (replace `YOUR_USERNAME` with your Linux username — run `whoami` to check):

```ini
[Unit]
Description=Marine Data Scraper
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/offline-quiz-app/marine-data-scraper
ExecStart=/home/YOUR_USERNAME/offline-quiz-app/marine-data-scraper/venv/bin/python serve_all.py
Restart=always
RestartSec=10
Environment=PORT=5000

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable marine-scraper
sudo systemctl start marine-scraper

# Check it's running
sudo systemctl status marine-scraper

# View live logs
sudo journalctl -u marine-scraper -f
```

---

## Step 9 (Optional) — Use port 80 with nginx

So you can access the dashboard at `http://<IP>` without the `:5000`:

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/marine
```

Paste:

```nginx
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/marine /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

Now open port 80 in GCP Firewall (the **Allow HTTP traffic** checkbox you ticked
in Step 2 already does this). Dashboard is at `http://<YOUR-VM-IP>`.

---

## Staying within the free tier

| Resource | Free limit | Our usage |
|----------|-----------|-----------|
| e2-micro VM | 720 hrs/month | ~744 hrs — stays free |
| Disk | 30 GB | ~2–5 GB (SQLite + exports) ✅ |
| Outbound bandwidth | 1 GB/month free | Dashboard traffic only — likely < 1 GB ✅ |
| Inbound (scraping pages) | **Free, unlimited** | All scraping is inbound ✅ |

**If you exceed 1 GB outbound** (only if many users download exports): ~$0.08–0.12/GB extra.

---

## Useful commands on the VM

```bash
# Check app status
sudo systemctl status marine-scraper

# View logs
sudo journalctl -u marine-scraper -f

# Restart after a code update
cd ~/offline-quiz-app && git pull origin claude/marine-data-scraper-5HAea
source marine-data-scraper/venv/bin/activate
cd marine-data-scraper && pip install -r requirements.txt
sudo systemctl restart marine-scraper

# Manual DB backup
cp ~/offline-quiz-app/marine-data-scraper/data/marine_companies.db ~/backup_$(date +%Y%m%d).db

# Check disk usage
df -h
```

---

## Summary

```
VM:       e2-micro, us-central1, Ubuntu 22.04
Disk:     30 GB standard persistent
Cost:     $0/month (Always Free)
Access:   http://<EXTERNAL-IP>:5000   (or port 80 with nginx)
Process:  systemd → serve_all.py → gunicorn + scheduler thread
```
