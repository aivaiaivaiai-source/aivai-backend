"""Tkinter GUI for offline human labeling (3B-2P3 — 11-class taxonomy)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from benchmarks.media_classification.private_seed import LABEL_TAXONOMY
from benchmarks.media_classification.private_seed.labeling import (
    BUTTON_KEYS,
    KEY_TO_LABEL,
    LABEL_HINTS_RU,
    LABEL_RU,
    LabelingSession,
    load_display_preview,
)


class LabelingApp:
    def __init__(self, session: LabelingSession) -> None:
        self.session = session
        self.root = tk.Tk()
        self.root.title("AiVai Private Seed — Human Labeling (11 classes)")
        self.root.geometry("1100x920")
        self.root.minsize(900, 700)

        self._photo: ImageTk.PhotoImage | None = None
        self._closing = False

        self._build_ui()
        self._bind_keys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.refresh()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        self.header_var = tk.StringVar()
        ttk.Label(top, textvariable=self.header_var, font=("Segoe UI", 14, "bold")).pack(
            anchor=tk.W
        )
        self.progress_var = tk.StringVar()
        ttk.Label(top, textvariable=self.progress_var, font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=(4, 0)
        )
        self.current_label_var = tk.StringVar()
        ttk.Label(
            top, textvariable=self.current_label_var, font=("Segoe UI", 10, "italic")
        ).pack(anchor=tk.W, pady=(2, 0))

        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True)

        img_frame = ttk.Frame(body, padding=8)
        img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(img_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        side = ttk.Frame(body, padding=8)
        side.pack(side=tk.RIGHT, fill=tk.Y)
        hints = ttk.LabelFrame(side, text="Определения", padding=6)
        hints.pack(fill=tk.BOTH, expand=True)
        for hint in LABEL_HINTS_RU:
            ttk.Label(hints, text=hint, wraplength=320, justify=tk.LEFT).pack(
                anchor=tk.W, pady=1
            )

        btn_frame = ttk.Frame(self.root, padding=8)
        btn_frame.pack(fill=tk.X)
        # 2 rows of buttons to keep image large
        row1 = ttk.Frame(btn_frame)
        row1.pack(fill=tk.X)
        row2 = ttk.Frame(btn_frame)
        row2.pack(fill=tk.X, pady=(4, 0))
        for i, (key, label) in enumerate(BUTTON_KEYS):
            parent = row1 if i < 6 else row2
            ru = LABEL_RU[label]
            ttk.Button(
                parent,
                text=f"{key} {ru}",
                command=lambda l=label: self._on_label(l),
            ).pack(side=tk.LEFT, padx=2, pady=2, expand=True, fill=tk.X)

        nav = ttk.Frame(self.root, padding=8)
        nav.pack(fill=tk.X)
        ttk.Button(nav, text="← Предыдущая", command=self._on_prev).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(nav, text="Следующая →", command=self._on_next).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(nav, text="U — Отменить", command=self._on_undo).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(nav, text="Q — Сохранить и выйти", command=self._on_quit).pack(
            side=tk.RIGHT, padx=4
        )

        self.counts_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.counts_var, padding=8, wraplength=1080).pack(
            anchor=tk.W
        )

    def _bind_keys(self) -> None:
        for key in KEY_TO_LABEL:
            self.root.bind(key, lambda e, k=key: self._on_key(k))
        self.root.bind("<Left>", lambda e: self._on_prev())
        self.root.bind("<Right>", lambda e: self._on_next())
        self.root.bind("u", lambda e: self._on_undo())
        self.root.bind("U", lambda e: self._on_undo())
        self.root.bind("q", lambda e: self._on_quit())
        self.root.bind("Q", lambda e: self._on_quit())

    def _on_key(self, key: str) -> None:
        label = KEY_TO_LABEL.get(key)
        if label:
            self._on_label(label)

    def _on_label(self, label: str) -> None:
        row = self.session.current_row()
        if row.reviewed:
            self.session.relabel_current(label)
            self.refresh()
            return
        done = self.session.label_current_and_advance(label)
        if done:
            self._show_completion()
        self.refresh()

    def _on_prev(self) -> None:
        self.session.go_previous()
        self.refresh()

    def _on_next(self) -> None:
        self.session.go_next()
        self.refresh()

    def _on_undo(self) -> None:
        if self.session.undo_last():
            self.refresh()

    def _on_quit(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.root.destroy()

    def _show_completion(self) -> None:
        prog = self.session.progress()
        lines = ["Разметка завершена.", ""]
        for key in LABEL_TAXONOMY:
            lines.append(f"{LABEL_RU[key]}: {prog['counts'][key]}")
        messagebox.showinfo("Готово", "\n".join(lines))

    def refresh(self) -> None:
        prog = self.session.progress()
        pid = self.session.current_id
        idx = self.session.current_index + 1
        self.header_var.set(f"{pid}                         {idx} / {prog['total']}")
        self.progress_var.set(
            f"Reviewed: {prog['reviewed']} / {prog['total']}    "
            f"Remaining: {prog['remaining']}"
        )
        row = self.session.current_row()
        if row.reviewed and row.label:
            self.current_label_var.set(
                f"Current label: {row.label} ({LABEL_RU.get(row.label, row.label)})"
            )
        else:
            self.current_label_var.set("Current label: —")

        counts_parts = [
            f"{LABEL_RU[k]}: {prog['counts'][k]}" for k in LABEL_TAXONOMY
        ]
        self.counts_var.set("  |  ".join(counts_parts))

        self._render_image()

    def _render_image(self) -> None:
        self.canvas.delete("all")
        try:
            preview = load_display_preview(self.session.current_raw_path())
        except Exception as exc:  # noqa: BLE001
            self.canvas.create_text(
                20, 20, anchor=tk.NW, fill="white", text=f"Cannot load image: {exc}"
            )
            return

        cw = max(self.canvas.winfo_width(), 400)
        ch = max(self.canvas.winfo_height(), 400)
        iw, ih = preview.size
        scale = min(cw / iw, ch / ih, 1.0)
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        if (nw, nh) != (iw, ih):
            preview = preview.resize((nw, nh), Image.Resampling.LANCZOS)

        self._photo = ImageTk.PhotoImage(preview)
        x = cw // 2
        y = ch // 2
        self.canvas.create_image(x, y, image=self._photo, anchor=tk.CENTER)
        del preview

    def run(self) -> None:
        self.root.after(100, self.refresh)
        self.root.mainloop()


def run_labeling_gui(session: LabelingSession) -> None:
    app = LabelingApp(session)
    app.run()
