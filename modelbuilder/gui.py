"""Desktop GUI (Tkinter): pick a template, edit the numbers, preview, export .3mf."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import __version__
from .preview import draw_parts
from .templates import TEMPLATES
from .templates.base import BuildResult, Template
from .threemf import write_3mf


class App(ttk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, padding=8)
        self.root = root
        root.title(f"3D Model Builder {__version__}")
        root.geometry("1150x720")
        self.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.template: Template = TEMPLATES[0]
        self.vars: dict[str, tk.StringVar] = {}
        self.result: BuildResult | None = None
        self.view = tk.StringVar(value="assembled")

        # Left: form
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        ttk.Label(left, text="Template").grid(row=0, column=0, sticky="w")
        self.template_box = ttk.Combobox(
            left, state="readonly", values=[t.name for t in TEMPLATES], width=34
        )
        self.template_box.current(0)
        self.template_box.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.template_box.bind("<<ComboboxSelected>>", self._on_template)
        self.desc = ttk.Label(left, wraplength=300, foreground="#555")
        self.desc.grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.form = ttk.Frame(left)
        self.form.grid(row=3, column=0, sticky="nsew")

        btns = ttk.Frame(left)
        btns.grid(row=4, column=0, sticky="ew", pady=8)
        ttk.Button(btns, text="Update preview", command=self.rebuild).pack(side="left")
        ttk.Button(btns, text="Reset", command=self._reset).pack(side="left", padx=4)
        ttk.Button(btns, text="Export .3mf…", command=self.export).pack(side="right")

        views = ttk.Frame(left)
        views.grid(row=5, column=0, sticky="w")
        ttk.Radiobutton(views, text="Assembled", value="assembled", variable=self.view,
                        command=self.redraw).pack(side="left")
        ttk.Radiobutton(views, text="Print plate", value="plate", variable=self.view,
                        command=self.redraw).pack(side="left", padx=6)

        self.notes = tk.Text(left, height=9, width=42, wrap="word", relief="flat",
                             background=root.cget("background"))
        self.notes.grid(row=6, column=0, sticky="ew", pady=(8, 0))

        # Right: 3D preview
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.fig = Figure(figsize=(6, 6))
        self.ax = self.fig.add_subplot(projection="3d")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        tb_frame = ttk.Frame(right)
        tb_frame.grid(row=1, column=0, sticky="ew")
        NavigationToolbar2Tk(self.canvas, tb_frame)

        self._load_template()

    # ---- form
    def _load_template(self):
        for w in self.form.winfo_children():
            w.destroy()
        self.vars.clear()
        self.desc.config(text=self.template.description)
        for row, p in enumerate(self.template.params):
            label = ttk.Label(self.form, text=p.label)
            label.grid(row=row, column=0, sticky="w", pady=1)
            var = tk.StringVar(value=f"{p.default:g}")
            entry = ttk.Entry(self.form, textvariable=var, width=8, justify="right")
            entry.grid(row=row, column=1, padx=4)
            entry.bind("<Return>", lambda _e: self.rebuild())
            ttk.Label(self.form, text=p.unit).grid(row=row, column=2, sticky="w")
            if p.help:
                _Tooltip(label, p.help)
                _Tooltip(entry, p.help)
            self.vars[p.key] = var
        self.rebuild()

    def _on_template(self, _e=None):
        self.template = TEMPLATES[self.template_box.current()]
        self._load_template()

    def _reset(self):
        for p in self.template.params:
            self.vars[p.key].set(f"{p.default:g}")
        self.rebuild()

    def _values(self) -> dict[str, float] | None:
        values = {}
        for key, var in self.vars.items():
            try:
                values[key] = float(var.get())
            except ValueError:
                label = next(p.label for p in self.template.params if p.key == key)
                messagebox.showerror("Invalid number", f"{label}: '{var.get()}' is not a number")
                return None
        errors = self.template.validate(values)
        if errors:
            messagebox.showerror("Check your numbers", "\n".join(errors))
            return None
        return values

    # ---- build / draw / export
    def rebuild(self):
        values = self._values()
        if values is None:
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            self.result = self.template.build(values)
        except Exception as exc:  # geometry errors should not kill the app
            messagebox.showerror("Build failed", str(exc))
            return
        finally:
            self.root.config(cursor="")
        self.notes.delete("1.0", "end")
        self.notes.insert("end", "\n\n".join(self.result.notes))
        self.redraw()

    def redraw(self):
        if not self.result:
            return
        parts = self.result.assembled if self.view.get() == "assembled" else self.result.print_parts
        draw_parts(self.ax, parts, self.template.name)
        self.canvas.draw_idle()

    def export(self):
        self.rebuild()
        if not self.result:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".3mf",
            filetypes=[("3MF model", "*.3mf")],
            initialfile=self.template.name.lower().replace(" ", "_") + ".3mf",
        )
        if not path:
            return
        write_3mf(path, [p.to_mesh() for p in self.result.print_parts], title=self.template.name)
        messagebox.showinfo("Exported", f"Saved {path}\n\nOpen it in Bambu Studio (File > Import).")


class _Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip = widget, text, None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _e=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, background="#ffffe0", relief="solid",
                 borderwidth=1, wraplength=280, justify="left").pack()

    def hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def main() -> int:
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0
