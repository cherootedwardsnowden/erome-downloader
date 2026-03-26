#!/usr/bin/env python3
# =============================================================================
#  ███████╗██████╗  ██████╗ ███╗   ███╗███████╗    ██████╗ ██╗
#  ██╔════╝██╔══██╗██╔═══██╗████╗ ████║██╔════╝    ██╔══██╗██║
#  █████╗  ██████╔╝██║   ██║██╔████╔██║█████╗      ██║  ██║██║
#  ██╔══╝  ██╔══██╗██║   ██║██║╚██╔╝██║██╔══╝      ██║  ██║██║
#  ███████╗██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗    ██████╔╝███████╗
#  ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝    ╚═════╝ ╚══════╝
#
#  Erome Album Downloader  ·  Professional Edition  ·  v3.0
#  ─────────────────────────────────────────────────────────────────
#  Özellikler:
#    ✦ Paralel çok-parçalı (chunk) indirme — maksimum bant genişliği kullanımı
#    ✦ Albüm adına göre otomatik klasör oluşturma
#    ✦ Tüm videoları aynı anda indirme (thread pool)
#    ✦ Gerçek zamanlı hız / ETA / MB göstergesi
#    ✦ İptal, duraklat, yeniden dene
#    ✦ Thumbnail önizleme (yumuşak köşeli)
#    ✦ Ayarlar paneli (eşzamanlı indirme sayısı, parça sayısı, chunk boyutu)
#    ✦ İndirme geçmişi logu
#    ✦ Renk temalı profesyonel karanlık GUI
#  ─────────────────────────────────────────────────────────────────
#  Gereksinimler:
#    pip install customtkinter requests beautifulsoup4 pillow
# =============================================================================

from __future__ import annotations

import os
import re
import sys
import io
import math
import time
import queue
import threading
import hashlib
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse, unquote

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont
import requests
from bs4 import BeautifulSoup

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & THEME
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME    = "Erome DL  ·  Professional"
APP_VERSION = "3.0.0"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":           "#080810",
    "surface":      "#0f0f1a",
    "surface2":     "#141420",
    "card":         "#181826",
    "card_hover":   "#1e1e2e",
    "border":       "#252538",
    "border2":      "#2e2e4a",
    "accent":       "#6c47ff",
    "accent_light": "#9b75ff",
    "accent2":      "#bf47ff",
    "success":      "#22c97e",
    "success_bg":   "#0d3326",
    "warning":      "#f0a020",
    "warning_bg":   "#321a04",
    "danger":       "#f04545",
    "danger_bg":    "#320d0d",
    "info":         "#47b8ff",
    "text":         "#dde2f0",
    "text_dim":     "#8890b0",
    "text_muted":   "#454566",
    "overlay":      "#0a0a14cc",
}

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.6367.82 Safari/537.36"
    ),
    "Accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":  "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding":  "gzip, deflate, br",
    "Connection":       "keep-alive",
    "Referer":          "https://www.erome.com/",
    "Sec-Fetch-Dest":   "document",
    "Sec-Fetch-Mode":   "navigate",
    "Sec-Fetch-Site":   "same-origin",
    "Cache-Control":    "no-cache",
}

# Default settings
DEFAULT_SETTINGS = {
    "concurrent_downloads": 3,
    "chunks_per_file":      8,
    "chunk_size_kb":        512,
    "retry_count":          3,
    "retry_delay":          2,
    "connection_timeout":   20,
    "read_timeout":         60,
    "save_path":            str(Path.home() / "Downloads"),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  IMAGE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def make_rounded(img: Image.Image, radius: int = 12) -> Image.Image:
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (img.width - 1, img.height - 1)],
                           radius=radius, fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, mask=mask)
    return out


def make_thumbnail(img: Image.Image,
                   w: int = 180, h: int = 100,
                   bg: tuple = (20, 20, 38, 255),
                   radius: int = 10) -> Image.Image:
    img.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), bg)
    ox = (w - img.width)  // 2
    oy = (h - img.height) // 2
    canvas.paste(img.convert("RGBA"), (ox, oy))
    return make_rounded(canvas, radius)


def placeholder_thumb(w: int = 180, h: int = 100) -> Image.Image:
    img = Image.new("RGBA", (w, h), (24, 24, 40, 255))
    draw = ImageDraw.Draw(img)
    # Play triangle
    cx, cy = w // 2, h // 2
    pts = [(cx - 14, cy - 18), (cx - 14, cy + 18), (cx + 18, cy)]
    draw.polygon(pts, fill=(80, 60, 160, 200))
    return make_rounded(img, 10)


# ═══════════════════════════════════════════════════════════════════════════════
#  NETWORK / SCRAPING
# ═══════════════════════════════════════════════════════════════════════════════

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HTTP_HEADERS)
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=20,
        pool_maxsize=40,
        max_retries=requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        ),
    )
    s.mount("https://", adapter)
    s.mount("http://",  adapter)
    return s


_SESSION = make_session()
_SESSION_LOCK = threading.Lock()


def fetch_album(url: str, timeout: tuple = (15, 30)) -> dict:
    """
    Scrape erome album page.
    Returns:
        {
          'album_id':   str,
          'album_title': str,
          'videos':     [ {'index', 'title', 'mp4_url', 'poster_url', 'quality'} ]
        }
    """
    with _SESSION_LOCK:
        resp = _SESSION.get(url, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Album title ────────────────────────────────────────────────────────────
    h1 = soup.find("h1")
    album_title = (h1.get_text(strip=True) if h1 else "")
    if not album_title:
        album_title = soup.title.string.strip() if soup.title else "album"

    # Sanitize for folder name
    album_title = re.sub(r'[\\/:*?"<>|]', "_", album_title).strip()[:80] or "album"

    # ── Album ID from URL ──────────────────────────────────────────────────────
    m = re.search(r'/a/([A-Za-z0-9_-]+)', url)
    album_id = m.group(1) if m else hashlib.md5(url.encode()).hexdigest()[:8]

    # ── Collect videos (deduplicated by mp4 URL) ───────────────────────────────
    seen_urls: set[str] = set()
    videos: list[dict] = []

    for video_tag in soup.find_all("video"):
        poster = (video_tag.get("data-poster")
                  or video_tag.get("poster")
                  or "")

        sources = video_tag.find_all("source")

        # Prefer 720p if multiple qualities exist
        best: Optional[dict] = None
        for source in sources:
            src = source.get("src", "").strip()
            if not src or not src.lower().endswith(".mp4"):
                continue
            if src in seen_urls:
                continue
            label = source.get("label", "")
            res   = source.get("res", "")
            quality = label or res or "?"
            entry = {"src": src, "label": label, "res": res,
                     "quality": quality, "poster": poster}
            if "720" in quality or "HD" in label.upper():
                best = entry
                break
            if best is None:
                best = entry

        if best and best["src"] not in seen_urls:
            seen_urls.add(best["src"])
            idx = len(videos) + 1
            # Derive filename from URL
            fname = unquote(Path(urlparse(best["src"]).path).stem)
            fname = re.sub(r'[\\/:*?"<>|]', "_", fname)
            if not fname:
                fname = f"video_{idx:03d}"
            videos.append({
                "index":      idx,
                "title":      fname,
                "mp4_url":    best["src"],
                "poster_url": best["poster"],
                "quality":    best["quality"],
            })

    return {
        "album_id":    album_id,
        "album_title": album_title,
        "videos":      videos,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  MULTI-CHUNK PARALLEL DOWNLOADER
# ═══════════════════════════════════════════════════════════════════════════════

class ChunkedDownloader:
    """
    Downloads a single file using N parallel byte-range requests.
    Falls back to single-stream if server doesn't support ranges.
    """

    def __init__(self,
                 url: str,
                 dest_path: str,
                 n_chunks: int = 8,
                 chunk_size: int = 512 * 1024,
                 retry: int = 3,
                 retry_delay: float = 2.0,
                 timeout: tuple = (15, 60),
                 on_progress: Optional[Callable] = None,
                 cancel_event: Optional[threading.Event] = None):
        self.url          = url
        self.dest_path    = dest_path
        self.n_chunks     = n_chunks
        self.chunk_size   = chunk_size
        self.retry        = retry
        self.retry_delay  = retry_delay
        self.timeout      = timeout
        self.on_progress  = on_progress
        self.cancel       = cancel_event or threading.Event()

        self._lock        = threading.Lock()
        self._downloaded  = 0
        self._total       = 0
        self._start_time  = 0.0
        self._speed_buf: list[tuple] = []   # (timestamp, bytes)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_file_size(self, session: requests.Session) -> int:
        try:
            r = session.head(self.url, timeout=self.timeout, allow_redirects=True)
            return int(r.headers.get("content-length", 0))
        except Exception:
            return 0

    def _supports_range(self, session: requests.Session) -> bool:
        try:
            r = session.head(self.url, timeout=self.timeout, allow_redirects=True)
            return (r.headers.get("accept-ranges", "").lower() == "bytes"
                    and int(r.headers.get("content-length", 0)) > 0)
        except Exception:
            return False

    def _report(self, delta: int):
        """Thread-safe progress update."""
        with self._lock:
            self._downloaded += delta
            now = time.time()
            self._speed_buf.append((now, delta))
            # Keep only last 2 seconds for speed calculation
            cutoff = now - 2.0
            self._speed_buf = [(t, b) for t, b in self._speed_buf if t >= cutoff]
            speed_bytes = sum(b for _, b in self._speed_buf) / max(
                self._speed_buf[-1][0] - self._speed_buf[0][0], 0.001
            ) if len(self._speed_buf) > 1 else 0

            pct = int(self._downloaded * 100 / self._total) if self._total else 0
            elapsed = now - self._start_time
            eta_s = ""
            if speed_bytes > 100 and self._total:
                remaining = self._total - self._downloaded
                eta_sec   = remaining / speed_bytes
                if eta_sec < 60:
                    eta_s = f"{eta_sec:.0f}s"
                else:
                    eta_s = f"{eta_sec/60:.1f}dk"

            if speed_bytes >= 1024 * 1024:
                speed_s = f"{speed_bytes/1024/1024:.1f} MB/s"
            elif speed_bytes >= 1024:
                speed_s = f"{speed_bytes/1024:.0f} KB/s"
            else:
                speed_s = f"{speed_bytes:.0f} B/s"

            dl_mb    = self._downloaded / 1024 / 1024
            total_mb = self._total      / 1024 / 1024

        if self.on_progress:
            self.on_progress(pct, speed_s, dl_mb, total_mb, eta_s)

    def _download_range(self, session: requests.Session,
                        start: int, end: int,
                        tmp_path: str) -> bool:
        """Download bytes [start, end] with retries."""
        headers = {"Range": f"bytes={start}-{end}"}
        for attempt in range(self.retry):
            if self.cancel.is_set():
                return False
            try:
                r = session.get(self.url, headers=headers,
                                stream=True, timeout=self.timeout)
                r.raise_for_status()
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        if self.cancel.is_set():
                            return False
                        if chunk:
                            f.write(chunk)
                            self._report(len(chunk))
                return True
            except Exception as e:
                if attempt < self.retry - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        return False

    def _download_stream(self, session: requests.Session) -> bool:
        """Single-stream fallback."""
        for attempt in range(self.retry):
            if self.cancel.is_set():
                return False
            try:
                r = session.get(self.url, stream=True, timeout=self.timeout)
                r.raise_for_status()
                with open(self.dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        if self.cancel.is_set():
                            return False
                        if chunk:
                            f.write(chunk)
                            self._report(len(chunk))
                return True
            except Exception:
                if attempt < self.retry - 1:
                    time.sleep(self.retry_delay)
        return False

    # ── Public ────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        self._start_time = time.time()
        session = make_session()

        total = self._get_file_size(session)
        self._total = total

        use_range = (total > 0 and self.n_chunks > 1
                     and self._supports_range(session))

        if not use_range:
            # Simple stream download
            return self._download_stream(session)

        # ── Parallel chunk download ────────────────────────────────────────────
        tmp_dir = Path(self.dest_path).parent / ".tmp_chunks"
        tmp_dir.mkdir(exist_ok=True)

        chunk_size  = math.ceil(total / self.n_chunks)
        ranges      = []
        for i in range(self.n_chunks):
            start = i * chunk_size
            end   = min(start + chunk_size - 1, total - 1)
            if start <= total - 1:
                ranges.append((i, start, end))

        tmp_files = [str(tmp_dir / f"{Path(self.dest_path).stem}_part{i}.tmp")
                     for i in range(len(ranges))]

        success_flags = [False] * len(ranges)

        with ThreadPoolExecutor(max_workers=min(self.n_chunks, len(ranges))) as ex:
            futures = {
                ex.submit(self._download_range, make_session(),
                          start, end, tmp_files[i]): i
                for i, (idx, start, end) in enumerate(ranges)
            }
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    success_flags[i] = fut.result()
                except Exception:
                    success_flags[i] = False

        if self.cancel.is_set() or not all(success_flags):
            for tf in tmp_files:
                try:
                    os.remove(tf)
                except Exception:
                    pass
            return False

        # ── Assemble parts ────────────────────────────────────────────────────
        with open(self.dest_path, "wb") as out:
            for tf in tmp_files:
                with open(tf, "rb") as inp:
                    out.write(inp.read())
                os.remove(tf)

        try:
            tmp_dir.rmdir()
        except Exception:
            pass

        return True


# ═══════════════════════════════════════════════════════════════════════════════
#  GUI COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Tooltip ───────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self.tip, text=self.text,
                       background="#1a1a2e", foreground="#c0c0e0",
                       relief="flat", bd=1,
                       font=("Consolas", 9),
                       padx=8, pady=4)
        lbl.pack()

    def _hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ── Log Panel ─────────────────────────────────────────────────────────────────

class LogPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent,
                         fg_color=C["surface"],
                         corner_radius=10,
                         border_width=1,
                         border_color=C["border"],
                         **kwargs)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self, fg_color="transparent", height=32)
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="📋  Log",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text_dim"]).grid(row=0, column=0, sticky="w")

        self.clear_btn = ctk.CTkButton(
            hdr, text="Temizle", width=60, height=22,
            corner_radius=6,
            fg_color=C["card"], hover_color=C["card_hover"],
            font=ctk.CTkFont(size=10),
            text_color=C["text_dim"],
            command=self.clear,
        )
        self.clear_btn.grid(row=0, column=1, sticky="e")

        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=C["bg"],
            text_color=C["text_dim"],
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=8,
            wrap="word",
            state="disabled",
        )
        self.textbox.grid(row=1, column=0, sticky="nsew",
                          padx=8, pady=(4, 8))

    def log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "·", "ok": "✓", "warn": "!", "err": "✗"}.get(level, "·")
        line = f"[{ts}] {prefix} {msg}\n"
        self.textbox.configure(state="normal")
        self.textbox.insert("end", line)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")


# ── Stats Bar ─────────────────────────────────────────────────────────────────

class StatsBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=C["surface2"],
                         corner_radius=0, height=28, **kwargs)
        self.grid_propagate(False)
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self):
        cols = [
            ("total",    "📹  Toplam: 0"),
            ("done",     "✓  Tamamlanan: 0"),
            ("active",   "⬇  Aktif: 0"),
            ("failed",   "✗  Hatalı: 0"),
            ("speed",    "⚡  —"),
        ]
        for i, (key, text) in enumerate(cols):
            lbl = ctk.CTkLabel(
                self, text=text,
                font=ctk.CTkFont(size=10),
                text_color=C["text_muted"],
            )
            lbl.grid(row=0, column=i, padx=14, pady=0, sticky="w")
            self._labels[key] = lbl
            if i < len(cols) - 1:
                sep = ctk.CTkLabel(self, text="|",
                                   text_color=C["border2"],
                                   font=ctk.CTkFont(size=11))
                sep.grid(row=0, column=i, padx=(0, 0), sticky="e")

    def update(self, **kwargs):
        icons = {
            "total":  "📹  Toplam: ",
            "done":   "✓  Tamamlanan: ",
            "active": "⬇  Aktif: ",
            "failed": "✗  Hatalı: ",
            "speed":  "⚡  ",
        }
        colors = {
            "total":  C["text_dim"],
            "done":   C["success"],
            "active": C["accent_light"],
            "failed": C["danger"],
            "speed":  C["info"],
        }
        for key, val in kwargs.items():
            if key in self._labels:
                self._labels[key].configure(
                    text=f"{icons.get(key, '')}{val}",
                    text_color=colors.get(key, C["text_muted"]),
                )


# ── Video Card ────────────────────────────────────────────────────────────────

class VideoCard(ctk.CTkFrame):

    STATUS_IDLE      = "idle"
    STATUS_QUEUED    = "queued"
    STATUS_ACTIVE    = "active"
    STATUS_DONE      = "done"
    STATUS_CANCELLED = "cancelled"
    STATUS_ERROR     = "error"

    def __init__(self, parent, info: dict, on_download, on_cancel, **kwargs):
        super().__init__(
            parent,
            fg_color=C["card"],
            corner_radius=12,
            border_width=1,
            border_color=C["border"],
            **kwargs,
        )
        self.info        = info
        self.on_download = on_download
        self.on_cancel   = on_cancel
        self.status      = self.STATUS_IDLE
        self._cancel_ev  = threading.Event()
        self._photo      = None

        self._build()
        self._fetch_thumbnail()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        # ── Thumbnail ─────────────────────────────────────────────────────────
        ph = ImageTk.PhotoImage(placeholder_thumb())
        self._photo = ph

        self.thumb_frame = ctk.CTkFrame(self, width=180, height=100,
                                        fg_color=C["surface2"],
                                        corner_radius=10)
        self.thumb_frame.grid(row=0, column=0, rowspan=4,
                              padx=(10, 10), pady=10, sticky="ns")
        self.thumb_frame.grid_propagate(False)

        self.thumb_lbl = ctk.CTkLabel(self.thumb_frame, text="",
                                      image=ph, width=180, height=100)
        self.thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Badge ───────────────────────────────────────────────────────────────
        self.badge = ctk.CTkLabel(
            self.thumb_frame,
            text=f"  #{self.info['index']:02d}  ",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=C["accent"], text_color="white", corner_radius=5,
        )
        self.badge.place(x=5, y=5)

        # Quality tag ─────────────────────────────────────────────────────────
        q = self.info.get("quality", "")
        if q:
            ctk.CTkLabel(
                self.thumb_frame,
                text=f"  {q}  ",
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=C["info"], text_color="white", corner_radius=5,
            ).place(relx=1, x=-5, y=5, anchor="ne")

        # ── Info ──────────────────────────────────────────────────────────────
        self.title_lbl = ctk.CTkLabel(
            self, text=self.info["title"],
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=C["text"], anchor="w",
        )
        self.title_lbl.grid(row=0, column=1, sticky="ew",
                            padx=(0, 10), pady=(12, 1))

        url = self.info["mp4_url"]
        short = ("…" + url[-52:]) if len(url) > 55 else url
        self.url_lbl = ctk.CTkLabel(
            self, text=f"🔗 {short}",
            font=ctk.CTkFont(size=9),
            text_color=C["text_muted"], anchor="w",
        )
        self.url_lbl.grid(row=1, column=1, sticky="ew",
                          padx=(0, 10), pady=(0, 2))

        # ── Progress ──────────────────────────────────────────────────────────
        self.prog_bar = ctk.CTkProgressBar(
            self, height=7, corner_radius=4,
            fg_color=C["surface2"],
            progress_color=C["accent"],
        )
        self.prog_bar.set(0)
        self.prog_bar.grid(row=2, column=1, sticky="ew",
                           padx=(0, 10), pady=(2, 4))

        # ── Bottom row ────────────────────────────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=3, column=1, sticky="ew",
                 padx=(0, 10), pady=(0, 10))
        bot.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            bot, text="Hazır",
            font=ctk.CTkFont(size=10),
            text_color=C["text_muted"], anchor="w",
        )
        self.status_lbl.grid(row=0, column=0, sticky="w")

        # ETA label
        self.eta_lbl = ctk.CTkLabel(
            bot, text="",
            font=ctk.CTkFont(size=10),
            text_color=C["text_muted"], anchor="center",
        )
        self.eta_lbl.grid(row=0, column=1, padx=8)

        self.dl_btn = ctk.CTkButton(
            bot, text="⬇  İndir",
            width=110, height=30, corner_radius=8,
            fg_color=C["accent"],
            hover_color=C["accent2"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._btn_click,
        )
        self.dl_btn.grid(row=0, column=2, sticky="e")

    # ── Thumbnail fetch ───────────────────────────────────────────────────────

    def _fetch_thumbnail(self):
        url = self.info.get("poster_url", "")
        if not url:
            return

        def worker():
            try:
                r = requests.get(url, headers=HTTP_HEADERS, timeout=10)
                r.raise_for_status()
                raw = Image.open(io.BytesIO(r.content))
                thumb = make_thumbnail(raw)
                photo = ImageTk.PhotoImage(thumb)
                self.after(0, lambda: self._apply_thumb(photo))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _apply_thumb(self, photo):
        self._photo = photo
        self.thumb_lbl.configure(image=photo)

    # ── Button logic ─────────────────────────────────────────────────────────

    def _btn_click(self):
        if self.status == self.STATUS_ACTIVE:
            self._cancel_ev.set()
            self.on_cancel(self)
        elif self.status in (self.STATUS_IDLE,
                             self.STATUS_CANCELLED,
                             self.STATUS_ERROR):
            self.on_download(self)

    # ── State transitions ─────────────────────────────────────────────────────

    def set_queued(self):
        self.status = self.STATUS_QUEUED
        self._cancel_ev.clear()
        self.prog_bar.set(0)
        self.prog_bar.configure(progress_color=C["accent"])
        self.status_lbl.configure(text="Sırada…",
                                  text_color=C["warning"])
        self.dl_btn.configure(text="⏳  Sırada",
                              fg_color=C["warning_bg"],
                              hover_color=C["warning_bg"],
                              text_color=C["warning"],
                              state="disabled")
        self.badge.configure(fg_color=C["warning"])

    def set_active(self, dest_folder: str):
        self.status = self.STATUS_ACTIVE
        self._cancel_ev.clear()
        self.status_lbl.configure(text="İndiriliyor…",
                                  text_color=C["accent_light"])
        self.dl_btn.configure(text="✖  İptal",
                              fg_color=C["danger_bg"],
                              hover_color=C["danger_bg"],
                              text_color=C["danger"],
                              state="normal")
        self.badge.configure(fg_color=C["accent"])

    def update_progress(self, pct: int, speed: str,
                        dl_mb: float, total_mb: float, eta: str):
        self.prog_bar.set(pct / 100)
        size_s = (f"{dl_mb:.1f} / {total_mb:.1f} MB"
                  if total_mb > 0
                  else f"{dl_mb:.1f} MB")
        self.status_lbl.configure(
            text=f"{pct}%  ·  {size_s}  ·  {speed}",
            text_color=C["accent_light"],
        )
        self.eta_lbl.configure(
            text=f"ETA {eta}" if eta else "",
            text_color=C["text_muted"],
        )

    def set_done(self, filepath: str):
        self.status = self.STATUS_DONE
        self.prog_bar.set(1)
        self.prog_bar.configure(progress_color=C["success"])
        fname = Path(filepath).name
        self.status_lbl.configure(text=f"✓  {fname}",
                                  text_color=C["success"])
        self.eta_lbl.configure(text="")
        self.dl_btn.configure(text="✓  Tamam",
                              fg_color=C["success_bg"],
                              hover_color=C["success_bg"],
                              text_color=C["success"],
                              state="disabled")
        self.badge.configure(fg_color=C["success"])
        self.configure(border_color=C["success"])

    def set_cancelled(self):
        self.status = self.STATUS_CANCELLED
        self.prog_bar.set(0)
        self.status_lbl.configure(text="İptal edildi",
                                  text_color=C["warning"])
        self.eta_lbl.configure(text="")
        self.dl_btn.configure(text="🔄  Tekrar",
                              fg_color=C["accent"],
                              hover_color=C["accent2"],
                              text_color="white",
                              state="normal")
        self.badge.configure(fg_color=C["text_muted"])

    def set_error(self, msg: str):
        self.status = self.STATUS_ERROR
        self.prog_bar.set(0)
        self.prog_bar.configure(progress_color=C["danger"])
        short = msg[:60] + "…" if len(msg) > 63 else msg
        self.status_lbl.configure(text=f"Hata: {short}",
                                  text_color=C["danger"])
        self.eta_lbl.configure(text="")
        self.dl_btn.configure(text="🔄  Tekrar",
                              fg_color=C["accent"],
                              hover_color=C["accent2"],
                              text_color="white",
                              state="normal")
        self.badge.configure(fg_color=C["danger"])
        self.configure(border_color=C["danger"])


# ── Settings Dialog ────────────────────────────────────────────────────────────

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings: dict, on_save):
        super().__init__(parent)
        self.title("⚙  Ayarlar")
        self.geometry("480x400")
        self.resizable(False, False)
        self.configure(fg_color=C["surface"])
        self.grab_set()

        self._settings = dict(settings)
        self._on_save  = on_save
        self._vars: dict[str, tk.Variable] = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="⚙  Ayarlar",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=C["text"],
        ).grid(row=0, column=0, pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color=C["card"],
                            corner_radius=10)
        form.grid(row=1, column=0, padx=20, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        rows = [
            ("concurrent_downloads", "Eşzamanlı indirme sayısı",
             1, 10, 1, "Aynı anda kaç video indirilsin"),
            ("chunks_per_file",      "Parça sayısı (chunk)",
             1, 16, 1, "Dosya başına paralel bağlantı sayısı"),
            ("chunk_size_kb",        "Chunk boyutu (KB)",
             64, 4096, 64, "Her parçanın maksimum boyutu"),
            ("retry_count",          "Yeniden deneme",
             0, 10, 1, "Hata durumunda kaç kez denensin"),
            ("connection_timeout",   "Bağlantı timeout (sn)",
             5, 120, 5, "Sunucuya bağlanma süresi"),
        ]

        for i, (key, label, mn, mx, step, tip) in enumerate(rows):
            ctk.CTkLabel(form, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color=C["text"],
                         anchor="w").grid(
                row=i, column=0, padx=(14, 10), pady=(10, 0), sticky="w")

            var = tk.IntVar(value=self._settings.get(key, DEFAULT_SETTINGS[key]))
            self._vars[key] = var

            slider = ctk.CTkSlider(
                form, from_=mn, to=mx, number_of_steps=(mx - mn) // step,
                variable=var,
                width=140,
                progress_color=C["accent"],
                button_color=C["accent_light"],
            )
            slider.grid(row=i, column=1, padx=(0, 8), pady=(10, 0), sticky="e")

            val_lbl = ctk.CTkLabel(form, textvariable=var,
                                   width=40, font=ctk.CTkFont(size=11),
                                   text_color=C["accent_light"])
            val_lbl.grid(row=i, column=2, padx=(0, 14), pady=(10, 0))

        # bottom padding
        ctk.CTkLabel(form, text="", height=10,
                     fg_color="transparent").grid(
            row=len(rows), column=0, columnspan=3)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=2, column=0, pady=18)

        ctk.CTkButton(btn_row, text="İptal", width=100,
                      fg_color=C["card"], hover_color=C["card_hover"],
                      text_color=C["text_dim"],
                      command=self.destroy).grid(row=0, column=0, padx=8)

        ctk.CTkButton(btn_row, text="Kaydet", width=100,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      command=self._save).grid(row=0, column=1, padx=8)

    def _save(self):
        for key, var in self._vars.items():
            self._settings[key] = var.get()
        self._on_save(self._settings)
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
#  DOWNLOAD MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadManager:
    """
    Manages a thread pool that processes VideoCard download jobs.
    """

    def __init__(self, settings: dict, log_cb, stats_cb):
        self._settings  = settings
        self._log       = log_cb
        self._stats_cb  = stats_cb
        self._executor: Optional[ThreadPoolExecutor] = None
        self._queue: list[tuple] = []   # (card, dest_folder)
        self._active: set        = set()
        self._lock               = threading.Lock()
        self._n_done             = 0
        self._n_fail             = 0
        self._n_total            = 0

    def _make_executor(self) -> ThreadPoolExecutor:
        return ThreadPoolExecutor(
            max_workers=self._settings["concurrent_downloads"],
            thread_name_prefix="dl_worker",
        )

    def submit(self, card: VideoCard, dest_folder: str):
        with self._lock:
            self._n_total += 1
            card.set_queued()
            self._queue.append((card, dest_folder))

        self._pump()
        self._update_stats()

    def _pump(self):
        """Start workers up to the concurrency limit."""
        if self._executor is None:
            self._executor = self._make_executor()

        with self._lock:
            max_w = self._settings["concurrent_downloads"]
            while (len(self._active) < max_w and self._queue):
                card, folder = self._queue.pop(0)
                self._active.add(id(card))
                self._executor.submit(self._worker, card, folder)

    def _worker(self, card: VideoCard, dest_folder: str):
        card.after(0, lambda: card.set_active(dest_folder))
        self._log(f"Başladı: {card.info['title']}", "info")

        fname = re.sub(r'[\\/:*?"<>|]', "_", card.info["title"])
        if not fname.lower().endswith(".mp4"):
            fname += ".mp4"
        dest_path = os.path.join(dest_folder, fname)

        def progress(pct, speed, dl_mb, total_mb, eta):
            card.after(0, lambda: card.update_progress(
                pct, speed, dl_mb, total_mb, eta))
            self._update_stats(speed=speed)

        dl = ChunkedDownloader(
            url         = card.info["mp4_url"],
            dest_path   = dest_path,
            n_chunks    = self._settings["chunks_per_file"],
            chunk_size  = self._settings["chunk_size_kb"] * 1024,
            retry       = self._settings["retry_count"],
            retry_delay = self._settings.get("retry_delay", 2),
            timeout     = (self._settings["connection_timeout"],
                           self._settings.get("read_timeout", 60)),
            on_progress = progress,
            cancel_event= card._cancel_ev,
        )

        try:
            ok = dl.run()
        except Exception as e:
            ok = False
            err_msg = str(e)
            card.after(0, lambda: card.set_error(err_msg))
            self._log(f"Hata: {card.info['title']} — {err_msg}", "err")
            with self._lock:
                self._n_fail += 1
        else:
            if card._cancel_ev.is_set():
                card.after(0, card.set_cancelled)
                self._log(f"İptal: {card.info['title']}", "warn")
            elif ok:
                card.after(0, lambda: card.set_done(dest_path))
                self._log(f"Tamamlandı: {fname}", "ok")
                with self._lock:
                    self._n_done += 1
            else:
                card.after(0, lambda: card.set_error("İndirme başarısız"))
                self._log(f"Başarısız: {card.info['title']}", "err")
                with self._lock:
                    self._n_fail += 1

        with self._lock:
            self._active.discard(id(card))

        self._pump()
        self._update_stats()

    def cancel_all(self):
        with self._lock:
            for card, _ in self._queue:
                card._cancel_ev.set()
                card.after(0, card.set_cancelled)
            self._queue.clear()

    def _update_stats(self, speed: str = ""):
        with self._lock:
            total  = self._n_total
            done   = self._n_done
            active = len(self._active)
            fail   = self._n_fail
        self._stats_cb(
            total=total, done=done, active=active,
            failed=fail, speed=speed or "—",
        )

    def update_settings(self, settings: dict):
        self._settings = settings
        if self._executor:
            self._executor._max_workers = settings["concurrent_downloads"]


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("960x820")
        self.minsize(820, 600)
        self.configure(fg_color=C["bg"])

        self._settings    = dict(DEFAULT_SETTINGS)
        self._cards:  list[VideoCard] = []
        self._album_info: Optional[dict] = None
        self._scan_thread: Optional[threading.Thread] = None

        self._manager: Optional[DownloadManager] = None

        self._build_layout()
        self._manager = DownloadManager(
            self._settings,
            log_cb   = lambda m, lv="info": self.after(0, lambda: self._log.log(m, lv)),
            stats_cb = lambda **kw: self.after(0, lambda: self._stats.update(**kw)),
        )

    # ── Master layout ─────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)   # video list
        self.grid_rowconfigure(4, weight=0)   # log

        self._build_header()
        self._build_url_bar()
        self._build_action_bar()
        self._build_video_list()
        self._build_log()
        self._build_stats()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["surface"],
                           corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            hdr, text="  ⬡ EROME DL",
            font=ctk.CTkFont(family="Courier New", size=17, weight="bold"),
            text_color=C["accent"],
        )
        logo.grid(row=0, column=0, padx=18, pady=14, sticky="w")

        self._header_status = ctk.CTkLabel(
            hdr, text="Albüm URL'si girin ve Tara'ya basın",
            font=ctk.CTkFont(size=11),
            text_color=C["text_muted"],
        )
        self._header_status.grid(row=0, column=1, sticky="e", padx=10)

        # Settings button
        ctk.CTkButton(
            hdr, text="⚙", width=34, height=30,
            corner_radius=8,
            fg_color=C["card"], hover_color=C["card_hover"],
            font=ctk.CTkFont(size=14),
            text_color=C["text_dim"],
            command=self._open_settings,
        ).grid(row=0, column=2, padx=(0, 6))

        ctk.CTkLabel(
            hdr, text=f"v{APP_VERSION}  ",
            font=ctk.CTkFont(size=9),
            text_color=C["text_muted"],
        ).grid(row=0, column=3, padx=(0, 10))

    # ── URL bar ───────────────────────────────────────────────────────────────

    def _build_url_bar(self):
        bar = ctk.CTkFrame(self, fg_color=C["surface2"],
                           corner_radius=0)
        bar.grid(row=1, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="  Albüm URL",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text_dim"],
                     width=90).grid(row=0, column=0, pady=14, sticky="w")

        self._url_entry = ctk.CTkEntry(
            bar,
            placeholder_text="https://www.erome.com/a/XXXXXXXXX",
            height=40, corner_radius=10,
            fg_color=C["card"],
            border_color=C["border"],
            border_width=1,
            text_color=C["text"],
            font=ctk.CTkFont(size=12),
        )
        self._url_entry.grid(row=0, column=1, padx=(0, 8), pady=14,
                             sticky="ew")
        self._url_entry.bind("<Return>", lambda _: self._start_scan())

        self._scan_btn = ctk.CTkButton(
            bar, text="🔍  Tara",
            width=110, height=40, corner_radius=10,
            fg_color=C["accent"],
            hover_color=C["accent2"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=2, padx=(0, 10), pady=14)

        # Folder row
        ctk.CTkLabel(bar, text="  Kayıt Yeri",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text_dim"],
                     width=90).grid(row=1, column=0, pady=(0, 12), sticky="w")

        self._folder_lbl = ctk.CTkLabel(
            bar, text=self._settings["save_path"],
            font=ctk.CTkFont(size=10),
            text_color=C["text_muted"],
            anchor="w",
        )
        self._folder_lbl.grid(row=1, column=1, padx=(0, 8), pady=(0, 12),
                              sticky="ew")

        ctk.CTkButton(
            bar, text="📁  Değiştir",
            width=110, height=32, corner_radius=8,
            fg_color=C["card"], hover_color=C["card_hover"],
            border_width=1, border_color=C["border"],
            font=ctk.CTkFont(size=11), text_color=C["text_dim"],
            command=self._choose_folder,
        ).grid(row=1, column=2, padx=(0, 10), pady=(0, 12))

    # ── Action bar ────────────────────────────────────────────────────────────

    def _build_action_bar(self):
        self._action_bar = ctk.CTkFrame(self, fg_color=C["surface"],
                                        corner_radius=0, height=44)
        self._action_bar.grid(row=2, column=0, sticky="ew")
        self._action_bar.grid_propagate(False)
        self._action_bar.grid_columnconfigure(1, weight=1)
        self._action_bar.grid_remove()

        self._found_lbl = ctk.CTkLabel(
            self._action_bar, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["success"],
        )
        self._found_lbl.grid(row=0, column=0, padx=16, pady=10)

        self._album_lbl = ctk.CTkLabel(
            self._action_bar, text="",
            font=ctk.CTkFont(size=11),
            text_color=C["text_dim"],
        )
        self._album_lbl.grid(row=0, column=1, sticky="w")

        btn_frame = ctk.CTkFrame(self._action_bar, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=10)

        self._dl_all_btn = ctk.CTkButton(
            btn_frame, text="⬇  Tümünü İndir",
            height=32, width=150, corner_radius=8,
            fg_color=C["success"],
            hover_color="#1aad68",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._download_all,
        )
        self._dl_all_btn.grid(row=0, column=0, padx=(0, 6))

        self._cancel_all_btn = ctk.CTkButton(
            btn_frame, text="✖  Tümünü İptal",
            height=32, width=140, corner_radius=8,
            fg_color=C["danger_bg"],
            hover_color=C["danger_bg"],
            border_width=1, border_color=C["danger"],
            text_color=C["danger"],
            font=ctk.CTkFont(size=12),
            command=self._cancel_all,
        )
        self._cancel_all_btn.grid(row=0, column=1)

    # ── Video list ────────────────────────────────────────────────────────────

    def _build_video_list(self):
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=C["bg"],
            scrollbar_button_color=C["border2"],
            scrollbar_button_hover_color=C["accent"],
            corner_radius=0,
        )
        self._scroll.grid(row=3, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        self._empty_lbl = ctk.CTkLabel(
            self._scroll,
            text="Yukarıya bir Erome albüm URL'si girin ve 🔍 Tara'ya tıklayın.\n\n"
                 "Videolar burada listelenecek.",
            font=ctk.CTkFont(size=14),
            text_color=C["text_muted"],
            justify="center",
        )
        self._empty_lbl.grid(row=0, column=0, pady=80)

    # ── Log ───────────────────────────────────────────────────────────────────

    def _build_log(self):
        self._log = LogPanel(self, height=140)
        self._log.grid(row=4, column=0, sticky="ew",
                       padx=10, pady=(4, 0))
        self._log.grid_rowconfigure(1, weight=0)

    # ── Stats bar ─────────────────────────────────────────────────────────────

    def _build_stats(self):
        self._stats = StatsBar(self)
        self._stats.grid(row=5, column=0, sticky="ew")

    # ── Folder chooser ────────────────────────────────────────────────────────

    def _choose_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self._settings["save_path"])
        if folder:
            self._settings["save_path"] = folder
            self._folder_lbl.configure(text=folder)

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self):
        def on_save(new_settings):
            self._settings.update(new_settings)
            if self._manager:
                self._manager.update_settings(self._settings)
            self._log.log("Ayarlar kaydedildi.", "ok")

        SettingsDialog(self, self._settings, on_save)

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _start_scan(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin.")
            return
        if self._scan_thread and self._scan_thread.is_alive():
            return

        self._clear_cards()
        self._scan_btn.configure(state="disabled", text="⏳  Tarıyor…")
        self._header_status.configure(
            text="Albüm sayfası inceleniyor…", text_color=C["warning"])
        self._log.log(f"Tarıyor: {url}")

        self._scan_thread = threading.Thread(
            target=self._scan_worker, args=(url,), daemon=True)
        self._scan_thread.start()

    def _scan_worker(self, url: str):
        try:
            info = fetch_album(url,
                               timeout=(self._settings["connection_timeout"],
                                        self._settings.get("read_timeout", 60)))
            self.after(0, lambda: self._on_scan_ok(info))
        except Exception as e:
            tb = traceback.format_exc()
            self.after(0, lambda: self._on_scan_err(str(e), tb))

    def _on_scan_ok(self, info: dict):
        self._scan_btn.configure(state="normal", text="🔍  Tara")
        self._album_info = info
        videos = info["videos"]

        if not videos:
            self._header_status.configure(
                text="Video bulunamadı.", text_color=C["warning"])
            self._empty_lbl.configure(text="Bu albümde video bulunamadı.")
            self._log.log("Video bulunamadı.", "warn")
            return

        n = len(videos)
        self._header_status.configure(
            text=f"✓  {n} video bulundu  ·  {info['album_title']}",
            text_color=C["success"])
        self._found_lbl.configure(text=f"📹  {n} Video")
        self._album_lbl.configure(text=f"📁  {info['album_title']}")
        self._action_bar.grid()
        self._empty_lbl.grid_remove()

        self._log.log(
            f"{n} video bulundu — Albüm: {info['album_title']} [{info['album_id']}]",
            "ok")

        for v in videos:
            card = VideoCard(
                self._scroll, v,
                on_download=self._on_card_download,
                on_cancel=self._on_card_cancel,
            )
            card.grid(row=v["index"] - 1, column=0,
                      sticky="ew", padx=12, pady=(6, 0))
            self._cards.append(card)

        # Bottom spacer
        ctk.CTkLabel(self._scroll, text="", height=16,
                     fg_color="transparent").grid(
            row=len(videos), column=0)

        self._stats.update(total=n)

    def _on_scan_err(self, msg: str, tb: str):
        self._scan_btn.configure(state="normal", text="🔍  Tara")
        self._header_status.configure(
            text=f"Hata: {msg[:55]}", text_color=C["danger"])
        self._log.log(f"Tarama hatası: {msg}", "err")
        messagebox.showerror("Tarama Hatası",
                             f"{msg}\n\nDetay:\n{tb[-400:]}")

    # ── Download handlers ─────────────────────────────────────────────────────

    def _get_album_folder(self) -> str:
        base = self._settings["save_path"]
        if self._album_info:
            safe = re.sub(r'[\\/:*?"<>|]', "_",
                          self._album_info["album_title"])[:80].strip()
            folder = os.path.join(base, safe)
        else:
            folder = base
        os.makedirs(folder, exist_ok=True)
        return folder

    def _on_card_download(self, card: VideoCard):
        folder = self._get_album_folder()
        self._manager.submit(card, folder)
        self._log.log(f"Kuyruğa eklendi: {card.info['title']}")

    def _on_card_cancel(self, card: VideoCard):
        self._log.log(f"İptal: {card.info['title']}", "warn")

    def _download_all(self):
        folder = self._get_album_folder()
        queued = 0
        for card in self._cards:
            if card.status in (VideoCard.STATUS_IDLE,
                               VideoCard.STATUS_CANCELLED,
                               VideoCard.STATUS_ERROR):
                self._manager.submit(card, folder)
                queued += 1
        if queued:
            self._log.log(
                f"{queued} video indirme kuyruğuna eklendi → {folder}", "ok")

    def _cancel_all(self):
        self._manager.cancel_all()
        self._log.log("Tüm indirmeler iptal edildi.", "warn")

    def _clear_cards(self):
        for card in self._cards:
            card.destroy()
        self._cards.clear()
        self._album_info = None
        self._action_bar.grid_remove()
        self._empty_lbl.grid()
        self._empty_lbl.configure(text="Tarıyor…")
        self._stats.update(total=0, done=0, active=0, failed=0, speed="—")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        pass
