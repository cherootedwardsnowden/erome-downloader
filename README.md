# ⬡ Erome Downloader — made wıth aı

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c97e?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-6c47ff?style=for-the-badge)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-9b75ff?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-3.0.0-bf47ff?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/cherootedwardsnowden/erome-downloader?style=for-the-badge&color=f0a020)

<br/>

**A fast, feature-rich GUI downloader for Erome albums.**  
Parallel chunked downloading, real-time speed meters, thumbnail previews, automatic album folders, and a polished dark UI — all in one Python script.

<br/>

[Features](#-features) · [Installation](#-installation) · [Usage](#-usage) · [Settings](#%EF%B8%8F-settings) · [Architecture](#-architecture) · [FAQ](#-faq) · [Contributing](#-contributing) · [License](#-license)

</div>

---

## 📸 Preview

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ⬡ EROME DL                              Scanning album…        ⚙  v3.0  │
├──────────────────────────────────────────────────────────────────────────┤
│  Album URL  [ https://www.erome.com/a/XXXXXXXXX             ] [🔍 Scan]  │
│  Save Path  [ ~/Downloads/AlbumTitle/                        ] [📁 Pick]  │
├──────────────────────────────────────────────────────────────────────────┤
│  📹 12 Videos Found    [⬇ Download All]   [✖ Cancel All]                 │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  #01  sample_video_720p                                  │
│  │            │  🔗 …v8.erome.com/…/sample_720p.mp4           [HD]       │
│  │  thumbnail │  ████████████████░░░░░  74%                              │
│  └────────────┘  74%  ·  312.4 / 421.8 MB  ·  9.2 MB/s   ETA 12s        │
│                                                         [✖ Cancel]       │
│  ┌────────────┐  #02  another_video_720p                                 │
│  │            │  🔗 …v8.erome.com/…/another_720p.mp4          [HD]       │
│  │  thumbnail │  ████████░░░░░░░░░░░░░  38%                              │
│  └────────────┘  38%  ·  161.0 / 398.2 MB  ·  8.4 MB/s   ETA 28s        │
│                                                         [✖ Cancel]       │
├──────────────────────────────────────────────────────────────────────────┤
│  📋 Activity Log                                           [Clear]        │
│  [12:34:01] ✓ Done: sample_video_720p.mp4                                │
│  [12:34:03] · Started: another_video_720p                                │
│  [12:34:03] · Started: third_video_720p                                  │
├──────────────────────────────────────────────────────────────────────────┤
│  📹 Total: 12  |  ✓ Done: 4  |  ⬇ Active: 3  |  ✗ Failed: 0  |  ⚡ 27 MB/s │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ✦ Features

### ⚡ Download Engine

| Feature | Details |
|---|---|
| **Multi-chunk parallel download** | Each file is split into 1–16 byte-range requests downloaded simultaneously, saturating your full bandwidth |
| **Concurrent album downloads** | Download 1–10 videos in parallel (configurable) |
| **HTTP connection pooling** | All requests share a persistent session — no repeated TCP handshakes |
| **Smart retry with backoff** | Automatically retries on HTTP 429/500/502/503/504 with exponential delay |
| **Graceful fallback** | If the server doesn't support byte-range, seamlessly falls back to single-stream |
| **Per-video cancel & retry** | Each download can be independently cancelled and restarted |

### 🎨 Interface

- **Professional dark GUI** — Built with CustomTkinter; smooth corners, gradient accents, cohesive dark theme
- **Thumbnail previews** — Each video card loads its poster image in the background, displayed with rounded corners
- **Live progress** — Per-card display: percentage, MB/s speed, `X.X / Y.Y MB` size, and ETA
- **Color-coded states** — Queued / Active / Done / Cancelled / Error visible at a glance
- **Activity log panel** — Every event timestamped and logged; one-click clear
- **Stats bar** — Real-time totals: Videos / Completed / Active downloads / Errors / Current speed
- **Settings dialog** — All tuning options exposed via sliders, no config file editing needed

### 📁 File & Folder Management

- Auto-creates a folder named after the album title → `~/Downloads/AlbumTitle/`
- Strips illegal filesystem characters (`/ \ : * ? " < > |`) from folder and file names
- Save path changeable at runtime without restarting
- Temporary chunk files are stored in a hidden `.tmp_chunks/` subdirectory and cleaned up automatically

### 🧠 Smart Scraping

- Deduplication — the same MP4 URL is never listed or downloaded twice
- Quality selection — prefers 720p / HD source when multiple quality levels exist
- Extracts album title from `<h1>` or `<title>` tag for folder naming
- Full `requests.Session` with realistic browser headers to avoid blocks

---

## 📦 Installation

### Requirements

- Python **3.10** or newer
- pip

### 1 — Clone the repository

```bash
git clone https://github.com/yourusername/erome-downloader.git
cd erome-downloader
```

### 2 — Install dependencies

```bash
pip install customtkinter requests beautifulsoup4 pillow
```

> **Windows users:** If `tkinter` is missing, reinstall Python and make sure the *tcl/tk* component is checked.  
> **Linux users:** You may need `sudo apt install python3-tk` on Debian/Ubuntu.

### 3 — Run

```bash
python erome_downloader.py
```

That's it — no config, no database, no setup wizard.

---

## 🚀 Usage

### Basic download

1. Open the app with `python erome_downloader.py`
2. Paste an Erome album URL into the **Album URL** field, e.g.:
   ```
   https://www.erome.com/a/AbCdEfGh
   ```
3. Click **🔍 Scan** (or press `Enter`)
4. Wait for the video list to populate with thumbnails
5. Click **⬇ Download All** — or click the individual **⬇ Download** button on any card

Videos are saved to:
```
<Save Path> / <Album Title> / video_name_720p.mp4
```

### Download a single video

Click the **⬇ Download** button on a specific card instead of using *Download All*.

### Cancel a download

Click the **✖ Cancel** button on an active card, or use **✖ Cancel All** in the action bar to stop everything at once.

### Retry a failed or cancelled download

After a failure or cancellation the button changes to **🔄 Retry** — click it to restart that video.

### Change the save folder

Click **📁 Pick** next to the save path field and choose a directory. The album subfolder will be created inside it automatically.

---

## ⚙️ Settings

Open the settings panel by clicking the **⚙** button in the top-right corner.

| Setting | Default | Range | Description |
|---|---|---|---|
| **Concurrent downloads** | 3 | 1 – 10 | How many videos download at the same time |
| **Chunks per file** | 8 | 1 – 16 | Parallel byte-range connections per file |
| **Chunk size (KB)** | 512 | 64 – 4096 | Size of each chunk buffer |
| **Retry count** | 3 | 0 – 10 | Attempts before marking a video as failed |
| **Connection timeout (s)** | 20 | 5 – 120 | Seconds to wait when connecting to server |

### Recommended presets

| Connection | Concurrent | Chunks | Chunk size |
|---|---|---|---|
| Fast broadband (100+ Mbps) | 5 | 16 | 1024 KB |
| Average broadband (20–100 Mbps) | 3 | 8 | 512 KB |
| Slow / mobile | 2 | 4 | 256 KB |
| Server rate-limited | 1 | 4 | 256 KB |

---

## 🏗 Architecture

```
erome_downloader.py
│
├── Constants & Theme ────────── COLORS dict, HTTP_HEADERS, DEFAULT_SETTINGS
│
├── Image Utilities ───────────  make_rounded(), make_thumbnail(), placeholder_thumb()
│
├── Network / Scraping ────────  make_session()  →  fetch_album(url)
│   │                              • BeautifulSoup HTML parse
│   │                              • Deduplication of <source> tags
│   │                              • 720p / HD quality preference
│   └── HTTP Session ──────────  HTTPAdapter with retry + connection pool
│
├── ChunkedDownloader ─────────  Core download engine
│   ├── _get_file_size()         HEAD request for Content-Length
│   ├── _supports_range()        HEAD request checks Accept-Ranges header
│   ├── _download_range()        Downloads one byte chunk with retry loop
│   ├── _download_stream()       Fallback single-stream download
│   └── run()                    Orchestrates parallel chunks → assemble parts
│
├── GUI Components
│   ├── Tooltip ───────────────  Hover tooltip helper
│   ├── LogPanel ──────────────  Timestamped activity log textbox
│   ├── StatsBar ──────────────  Bottom statistics row
│   ├── VideoCard ─────────────  Per-video widget with thumbnail, progress, buttons
│   │   └── State machine:       IDLE → QUEUED → ACTIVE → DONE / CANCELLED / ERROR
│   └── SettingsDialog ────────  CTkToplevel with slider controls
│
├── DownloadManager ───────────  Thread pool orchestrator
│   ├── submit(card, folder)     Queues a card and calls _pump()
│   ├── _pump()                  Fills worker slots up to concurrency limit
│   ├── _worker(card, folder)    Runs ChunkedDownloader, updates card state
│   └── cancel_all()             Sets cancel events on all queued/active cards
│
└── App (Main Window) ─────────  ctk.CTk root
    ├── _build_header()
    ├── _build_url_bar()
    ├── _build_action_bar()
    ├── _build_video_list()      CTkScrollableFrame with VideoCard widgets
    ├── _build_log()
    ├── _build_stats()
    └── _start_scan()            Spawns scan thread → _on_scan_ok() → VideoCards
```

### Data flow

```
User pastes URL
      │
      ▼
fetch_album(url)          — scrapes page, returns {album_id, album_title, videos[]}
      │
      ▼
VideoCard widgets created — thumbnail fetched in background thread
      │
User clicks Download
      │
      ▼
DownloadManager.submit()  — sets card QUEUED, adds to internal queue
      │
      ▼
_pump() fires _worker()   — sets card ACTIVE, creates ChunkedDownloader
      │
      ├── HEAD request → file size + range support check
      ├── N parallel _download_range() threads → N .tmp part files
      ├── Parts assembled into final .mp4
      └── Card set DONE / ERROR / CANCELLED
```

---

## 📋 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `customtkinter` | ≥ 5.2 | Modern dark-themed Tkinter widgets |
| `requests` | ≥ 2.31 | HTTP client with session and retry adapter |
| `beautifulsoup4` | ≥ 4.12 | HTML parsing for album scrape |
| `pillow` | ≥ 10.0 | Thumbnail image loading and rounded-corner masking |

All standard library — `tkinter`, `threading`, `concurrent.futures`, `pathlib`, `hashlib`, `re`, `io`, `math` — no extra installs needed.

---

## ❓ FAQ

**Q: The scan button doesn't find any videos.**  
A: Some albums may require a logged-in session or have region restrictions. Try opening the URL in your browser first to confirm it loads.

**Q: Downloads are slow even with 16 chunks.**  
A: The server may be rate-limiting connections per IP. Reduce *Chunks per file* to 4 and *Concurrent downloads* to 2 in Settings.

**Q: I see a `connection timeout` error.**  
A: Increase the *Connection timeout* slider in Settings, or check your internet connection.

**Q: Can I download images too, not just videos?**  
A: Currently the tool targets `<video><source>` MP4 tags only. Image support may be added in a future release.

**Q: The app crashes on Linux with a `_tkinter` error.**  
A: Install the system Tkinter package:
```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

**Q: Where are my downloaded files?**  
A: Inside the save path you configured, in a subfolder named after the album:
```
~/Downloads/
└── AlbumTitle/
    ├── video_01_720p.mp4
    ├── video_02_720p.mp4
    └── ...
```

**Q: How do I increase speed further?**  
A: Set *Chunks per file* to **16** and *Concurrent downloads* to **5** in Settings. Make sure your connection isn't the bottleneck — run a speed test to confirm.

---

## 🗂 Project Structure

```
erome-downloader/
├── erome_downloader.py   # Single-file application — everything is here
├── README.md             # This file
├── LICENSE               # MIT License
└── .gitignore
```

---

## 🔧 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Make your changes and test them
4. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add image download support"
   ```
5. **Push** and open a **Pull Request**

### Commit message convention

```
feat:     New feature
fix:      Bug fix
perf:     Performance improvement
ui:       GUI / visual change
refactor: Code restructure without behavior change
docs:     Documentation only
```

### Ideas for contributions

- [ ] Image (`.jpg` / `.webp`) download support
- [ ] Download queue persistence (resume after restart)
- [ ] System tray icon and notifications
- [ ] Dark / light theme toggle
- [ ] Batch URL input (multiple albums at once)
- [ ] Proxy support
- [ ] Download speed limit / throttle option
- [ ] CLI mode (no GUI, for scripting)

---

## ⚠️ Disclaimer

This tool is provided for **personal, educational, and archival use only**.  
You are solely responsible for ensuring you have the right to download any content you access.  
The author does not endorse or encourage any violation of third-party terms of service, copyright law, or applicable regulations.


Made with Python · CustomTkinter · ♥

If this project helped you, consider giving it a ⭐

</div>
