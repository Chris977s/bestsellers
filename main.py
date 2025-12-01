# main.py — Modern Tkinter/ttk UI with Dark/Light themes, macOS-safe tab text & visible caret.
# This hopefully should work on windows/Linux
# I have not tested that. Programmed on/for MacOS via Python3+

import csv
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote_plus

FILE_NAME = "bestsellers.txt"
YEAR_MIN, YEAR_MAX = 1942, 2013

# ------------------------------------------
# Theme palettes for Light & Dark mode
# ------------------------------------------
PALETTES = {
    "dark": {
        "bg": "#0f1115",   # window background
        "panel": "#171a20",# card/panel background
        "accent": "#232833",# headers / tab strip
        "muted": "#3a414e",# borders
        "text": "#e7ebf3", # primary text
        "text_mute": "#aab4c3",
        "brand": "#6ea8fe",
        "row_alt": "#1b1f27",  # zebra
    },
    "light": {
        "bg": "#f7fafc",
        "panel": "#ffffff",
        "accent": "#e9edf3",
        "muted": "#cbd5e1",
        "text": "#0f172a",
        "text_mute": "#475569",
        "brand": "#2563eb",
        "row_alt": "#f2f5fa",
    },
}

def apply_modern_style(root: tk.Misc, mode: str = "dark"):
    """
    Apply a modern ttk theme that works on macOS/Windows/Linux and keeps:
      - Tab labels visible (we'll draw our own segmented tabbar)
      - Text caret visible in entries/text widgets
    """
    pal = PALETTES["dark"] if mode == "dark" else PALETTES["light"]

    style = ttk.Style(root)
    # Styleable base: 'alt' on macOS, 'clam' elsewhere.
    try:
        style.theme_use("alt" if sys.platform == "darwin" else "clam")
    except tk.TclError:
        pass

    # System font
    sysfont = (".AppleSystemUIFont", 12) if sys.platform == "darwin" else ("Segoe UI", 10)

    # Window bg
    try:
        root.configure(bg=pal["bg"])
    except tk.TclError:
        pass

    style.configure(".", font=sysfont)

    # --- Caret visibility (re-apply on every theme flip)  ---
    # Sidenote: This was the most annoying part of this entire program
    for opt in (
        "*insertBackground", "*Entry.insertBackground", "*TEntry*insertBackground",
        "*Spinbox.insertBackground", "*Text.insertBackground",
    ):
        root.option_add(opt, pal["text"])
    for opt in ("*insertWidth", "*Entry.insertWidth", "*TEntry*insertWidth"):
        root.option_add(opt, 2)

    # ---- Notebook container  ----
    style.configure(
        "TNotebook",
        background=pal["accent"],
        foreground=pal["text"],
        borderwidth=0,
        padding=0,
    )

    # ---- Segmented tabbar buttons (this is used as visible tabs) ----
    # Using ttk.Radiobutton with "Toolbutton" style
    style.configure(
        "Toolbutton",
        background=pal["accent"],
        foreground=pal["text"],
        padding=(14, 8),
        borderwidth=0,
        focusthickness=0,
        focuscolor=pal["accent"],
    )
    style.map(
        "Toolbutton",
        background=[("selected", pal["panel"]), ("active", pal["panel"])],
        foreground=[("selected", pal["text"]), ("!selected", pal["text"])],
        relief=[("selected", "flat"), ("!selected", "flat")],
    )

    # ---- Frames / labels ----
    style.configure("Modern.TFrame", background=pal["panel"])
    style.configure("Modern.TLabelframe", background=pal["panel"])
    style.configure("Modern.TLabelframe.Label", background=pal["panel"], foreground=pal["text"])
    style.configure("Modern.TLabel", background=pal["panel"], foreground=pal["text"])
    style.configure("Muted.TLabel", background=pal["panel"], foreground=pal["text_mute"])
    try:
        style.configure("TEntry", insertcolor=pal["text"])
        style.configure("Modern.TEntry", insertcolor=pal["text"])
        style.configure("TSpinbox", insertcolor=pal["text"])
    except tk.TclError:
        pass

    # ---- Entry ----
    style.configure(
        "Modern.TEntry",
        fieldbackground=pal["panel"],
        background=pal["panel"],
        foreground=pal["text"],
        bordercolor=pal["muted"],
        lightcolor=pal["brand"],
        darkcolor=pal["muted"],
        padding=8,
    )

    # ---- Button ----
    style.configure(
        "Modern.TButton",
        background=pal["panel"],
        foreground=pal["text"],
        padding=(12, 8),
        borderwidth=0,
    )
    style.map(
        "Modern.TButton",
        background=[("active", pal["accent"]), ("pressed", pal["accent"])],
        foreground=[("disabled", pal["text_mute"])],
        relief=[("pressed", "flat"), ("!pressed", "flat")],
    )

    # ---- Treeview ----
    style.configure(
        "Modern.Treeview",
        background=pal["panel"],
        fieldbackground=pal["panel"],
        foreground=pal["text"],
        bordercolor=pal["panel"],
        rowheight=26,
    )
    style.configure(
        "Modern.Treeview.Heading",
        background=pal["accent"],
        foreground=pal["text"],
        relief="flat",
        padding=(10, 8),
        font=(sysfont[0], 11, "bold"),
    )
    style.map("Modern.Treeview.Heading", background=[("active", pal["panel"])])

    # Misc
    style.configure("TSeparator", background=pal["muted"])
    style.configure("Vertical.TScrollbar", background=pal["accent"])
    style.configure("Horizontal.TScrollbar", background=pal["accent"])

# ---------------------------
# Data loading
# ---------------------------
def load_books(path: str):
    """
    Read a tab-separated file with columns:
      0: title  1: author  2: publisher  3: MM/DD/YYYY
    Return: list[dict]
    """
    books = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            title, author, publisher, date = parts[0], parts[1], parts[2], parts[3]
            try:
                mm, dd, yyyy = date.split("/")
                books.append({
                    "title": title.strip(),
                    "author": author.strip(),
                    "publisher": publisher.strip(),
                    "month": int(mm), "day": int(dd), "year": int(yyyy),
                })
            except Exception:
                continue
    return books


# ---------------------------
# Main App
# ---------------------------
class BestsellerApp(tk.Tk):
    def __init__(self, data_path=None, start_theme="dark"):
        super().__init__()
        self.title("Bestsellers Search")
        self.geometry("1080x720")
        self.minsize(980, 600)

        # Theme
        self.current_theme = start_theme
        apply_modern_style(self, mode=self.current_theme)

        # Data path
        self.data_path = data_path if (data_path and os.path.exists(data_path)) \
                         else (FILE_NAME if os.path.exists(FILE_NAME) else None)

        # Load data
        self.books_all = []
        if self.data_path:
            try:
                self.books_all = load_books(self.data_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{e}")
        self.books_display = list(self.books_all)

        # Layout grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # UI
        file_label = os.path.basename(self.data_path) if self.data_path else "(no file)"
        self._build_header(file_label)
        self._build_tabs()
        self._build_results()
        self._build_footer()
        self._refresh_tree(self.books_display)

    # ----- Header -----
    def _build_header(self, path_label: str):
        hdr = ttk.Frame(self, style="Modern.TFrame", padding=(14, 12))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        # Left meta
        meta = ttk.Frame(hdr, style="Modern.TFrame")
        meta.grid(row=0, column=0, sticky="w")
        ttk.Label(meta, text=f"Loaded {len(self.books_all)} books", style="Modern.TLabel").grid(row=0, column=0, sticky="w")

        # Live search
        ttk.Label(hdr, text="Live search:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.live_q = tk.StringVar()
        e = ttk.Entry(hdr, textvariable=self.live_q, width=46, style="Modern.TEntry")
        e.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(10, 0))
        e.bind("<KeyRelease>", self._on_live_search)

        # Right actions
        act = ttk.Frame(hdr, style="Modern.TFrame")
        act.grid(row=0, column=2, rowspan=2, sticky="e")
        self.theme_btn = ttk.Button(act, text="", style="Modern.TButton", command=self._toggle_theme)
        self._sync_theme_button()
        self.theme_btn.grid(row=0, column=0, padx=(0, 8))
        ttk.Button(act, text="Open…", style="Modern.TButton", command=self._open_file).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(act, text="Clear", style="Modern.TButton", command=self.clear_results).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(act, text="Export CSV", style="Modern.TButton", command=self.export_csv).grid(row=0, column=3)

        ttk.Label(hdr, text=path_label, style="Muted.TLabel").grid(row=0, column=1, sticky="e")

    # ----- Tabs -----
    def _build_tabs(self):
        wrapper = ttk.Frame(self, style="Modern.TFrame", padding=(14, 10))
        wrapper.grid(row=1, column=0, sticky="ew")
        wrapper.grid_columnconfigure(0, weight=1)

        nb = ttk.Notebook(wrapper)              # IMPORTANT: default style
        nb.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.nb = nb

        # Between Years
        t1 = ttk.Frame(nb, style="Modern.TFrame", padding=8)
        nb.add(t1, text="Between Years")
        ttk.Label(t1, text=f"Start year ({YEAR_MIN}-{YEAR_MAX})", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0,8), pady=(2,4))
        ttk.Label(t1, text=f"End year ({YEAR_MIN}-{YEAR_MAX})",   style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(0,8), pady=(2,4))
        self.start_year = tk.StringVar(); self.end_year = tk.StringVar()
        ttk.Entry(t1, textvariable=self.start_year, width=12, style="Modern.TEntry").grid(row=1, column=0, padx=(0,8), pady=(0,6))
        ttk.Entry(t1, textvariable=self.end_year,   width=12, style="Modern.TEntry").grid(row=1, column=1, padx=(0,8), pady=(0,6))
        ttk.Button(t1, text="Search", style="Modern.TButton", command=self.search_year_range).grid(row=1, column=2, padx=(4,0), pady=(0,6))
        t1.grid_columnconfigure(3, weight=1)

        # Month & Year
        t2 = ttk.Frame(nb, style="Modern.TFrame", padding=8)
        nb.add(t2, text="Month & Year")
        ttk.Label(t2, text="Month (1–12)", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0,8), pady=(2,4))
        ttk.Label(t2, text=f"Year ({YEAR_MIN}-{YEAR_MAX})", style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(0,8), pady=(2,4))
        self.month_val = tk.StringVar(); self.year_val  = tk.StringVar()
        ttk.Entry(t2, textvariable=self.month_val, width=12, style="Modern.TEntry").grid(row=1, column=0, padx=(0,8), pady=(0,6))
        ttk.Entry(t2, textvariable=self.year_val,  width=12, style="Modern.TEntry").grid(row=1, column=1, padx=(0,8), pady=(0,6))
        ttk.Button(t2, text="Search", style="Modern.TButton", command=self.search_month_year).grid(row=1, column=2, padx=(4,0), pady=(0,6))
        t2.grid_columnconfigure(3, weight=1)

        # Author
        t3 = ttk.Frame(nb, style="Modern.TFrame", padding=8)
        nb.add(t3, text="Author")
        ttk.Label(t3, text="Author contains", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0,8), pady=(2,4))
        self.author_q = tk.StringVar()
        ttk.Entry(t3, textvariable=self.author_q, width=42, style="Modern.TEntry").grid(row=1, column=0, padx=(0,8), pady=(0,6))
        ttk.Button(t3, text="Search", style="Modern.TButton", command=self.search_author).grid(row=1, column=1, padx=(4,0), pady=(0,6))
        t3.grid_columnconfigure(2, weight=1)

        # Title
        t4 = ttk.Frame(nb, style="Modern.TFrame", padding=8)
        nb.add(t4, text="Title")
        ttk.Label(t4, text="Title contains", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0,8), pady=(2,4))
        self.title_q = tk.StringVar()
        ttk.Entry(t4, textvariable=self.title_q, width=42, style="Modern.TEntry").grid(row=1, column=0, padx=(0,8), pady=(0,6))
        ttk.Button(t4, text="Search", style="Modern.TButton", command=self.search_title).grid(row=1, column=1, padx=(4,0), pady=(0,6))
        t4.grid_columnconfigure(2, weight=1)

    # ----- Results -----
    def _build_results(self):
        panel = ttk.Frame(self, style="Modern.TFrame", padding=(14, 10))
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        cols = ("title", "author", "publisher", "month", "day", "year")
        self.tree = ttk.Treeview(panel, columns=cols, show="headings", style="Modern.Treeview")
        for c in cols:
            self.tree.heading(c, text=c.title(), command=lambda col=c: self._sort_by(col, False))
            width = 340 if c in ("title", "author") else (240 if c == "publisher" else 80)
            self.tree.column(c, width=width, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_row_double_click)
        self._setup_tree_context_menu()

    # ----- Footer -----
    def _build_footer(self):
        ftr = ttk.Frame(self, style="Modern.TFrame", padding=(14, 10))
        ftr.grid(row=3, column=0, sticky="ew")
        ftr.grid_columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(ftr, textvariable=self.status_var, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(ftr, text="Quit", style="Modern.TButton", command=self.destroy).grid(row=0, column=1, sticky="e")

    # ----- Actions / helpers -----

    def _setup_tree_context_menu(self):
    #Right-click menu for the results table.
        self._tree_menu = tk.Menu(self, tearoff=0)
        self._tree_menu.add_command(label="Search Google: Title + Author", command=self._search_web_title_author)
        self._tree_menu.add_separator()
        self._tree_menu.add_command(label="Search Google: Title only", command=self._search_web_title_only)
        self._tree_menu.add_command(label="Search Google: Author only", command=self._search_web_author_only)

    # Right-click (Windows/Linux = Button-3; macOS also supports Control-Click and sometimes Button-2)
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        self.tree.bind("<Control-Button-1>", self._on_tree_right_click)   # Ctrl-click on mac
        self.tree.bind("<Button-2>", self._on_tree_right_click)           # safety for some mac configs

    def _on_tree_right_click(self, event):
    #Select the row under the cursor and show the menu
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
        try:
            self._tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._tree_menu.grab_release()

    def _get_selected_row_values(self):
    #Return (title, author, publisher, month, day, year) for the focused/selected row or None."""
        sel = self.tree.focus() or (self.tree.selection()[0] if self.tree.selection() else "")
        if not sel:
            return None
        vals = self.tree.item(sel, "values")
        return vals if vals else None

    def _search_web_title_author(self):
        vals = self._get_selected_row_values()
        if not vals:
            return
        title, author = vals[0], vals[1]
        q = quote_plus(f'{title} "{author}"')
        webbrowser.open_new_tab(f"https://www.google.com/search?q={q}")

    def _search_web_title_only(self):
        vals = self._get_selected_row_values()
        if not vals:
            return
        title = vals[0]
        q = quote_plus(title)
        webbrowser.open_new_tab(f"https://www.google.com/search?q={q}")

    def _search_web_author_only(self):
        vals = self._get_selected_row_values()
        if not vals:
            return
        author = vals[1]
        q = quote_plus(author)
        webbrowser.open_new_tab(f"https://www.google.com/search?q={q}")

    def _sync_theme_button(self):
        self.theme_btn.config(text=f"Theme: {self.current_theme.title()}")

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_modern_style(self, mode=self.current_theme)
        self._sync_theme_button()
        if hasattr(self, "tree"):
            self._apply_tree_stripes()  # update zebra colors

    def _open_file(self):
        sel = filedialog.askopenfilename(
            title="Select bestsellers.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not sel:
            return
        try:
            self.data_path = sel
            self.books_all = load_books(sel)
            self.clear_results()
            self._refresh_tree(self.books_all)
            self._relabel_header()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def _relabel_header(self):
        # Quick refresh of header with new filename/count
        for child in self.grid_slaves(row=0, column=0):
            child.destroy()
        file_label = os.path.basename(self.data_path) if self.data_path else "(no file)"
        self._build_header(file_label)

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _apply_tree_stripes(self):
        pal = PALETTES[self.current_theme]
        self.tree.tag_configure("even", background=pal["panel"])
        self.tree.tag_configure("odd",  background=pal["row_alt"])
        for i, iid in enumerate(self.tree.get_children("")):
            self.tree.item(iid, tags=("odd" if i % 2 else "even",))

    def _refresh_tree(self, items):
        self._clear_tree()
        for i, b in enumerate(items):
            tag = "odd" if i % 2 else "even"
            self.tree.insert(
                "", "end",
                values=(b["title"], b["author"], b["publisher"], b["month"], b["day"], b["year"]),
                tags=(tag,)
            )
        self._apply_tree_stripes()
        self.status_var.set(f"Showing {len(items)} result(s).")

    def _validated_int(self, s, name):
        try:
            return int(s)
        except Exception:
            messagebox.showwarning("Invalid input", f"{name} must be a number.")
            return None

    def _validate_year(self, y):
        if not (YEAR_MIN <= y <= YEAR_MAX):
            messagebox.showwarning("Invalid year", f"Year must be between {YEAR_MIN} and {YEAR_MAX}.")
            return False
        return True

    def _sort_by(self, col, descending):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        if col in ("month", "day", "year"):
            try:
                data = [(int(v), k) for v, k in data]
            except Exception:
                pass
        data.sort(reverse=descending)
        for index, (_, k) in enumerate(data):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda c=col: self._sort_by(c, not descending))

    def export_csv(self):
        if not getattr(self, "books_display", None):
            messagebox.showinfo("No data", "There are no results to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export results to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Author", "Publisher", "Month", "Day", "Year"])
                for b in self.books_display:
                    writer.writerow([
                        b.get("title", ""),
                        b.get("author", ""),
                        b.get("publisher", ""),
                        b.get("month", ""),
                        b.get("day", ""),
                        b.get("year", ""),
                    ])
            messagebox.showinfo("Export complete", f"Saved {len(self.books_display)} rows to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    # ----- Event handlers -----
    def _on_live_search(self, _event=None):
        q = self.live_q.get().strip().lower()
        if not q:
            self.books_display = list(self.books_all)
        else:
            def matches(b):
                return (q in b["title"].lower()
                        or q in b["author"].lower()
                        or q in b["publisher"].lower()
                        or q in str(b["year"])
                        or q in str(b["month"])
                        or q in str(b["day"]))
            self.books_display = [b for b in self.books_all if matches(b)]
        self._refresh_tree(self.books_display)

    def clear_results(self):
        self.live_q.set("")
        self.books_display = list(self.books_all)
        self._refresh_tree(self.books_display)

    def _on_row_double_click(self, _evt):
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")
        if not vals:
            return
        title, author, publisher, month, day, year = vals
        details = f"Title: {title}\nAuthor: {author}\nPublisher: {publisher}\nDate: {month}/{day}/{year}"
        messagebox.showinfo("Book Details", details)

    # ----- Searches -----
    def search_year_range(self):
        s = self._validated_int(self.start_year.get().strip(), "Start year")
        if s is None or not self._validate_year(s):
            return
        e = self._validated_int(self.end_year.get().strip(), "End year")
        if e is None or not self._validate_year(e):
            return
        if s > e:
            s, e = e, s
        results = [b for b in self.books_all if s <= b["year"] <= e]
        self.books_display = results
        self._refresh_tree(results)

    def search_month_year(self):
        m = self._validated_int(self.month_val.get().strip(), "Month")
        if m is None or not (1 <= m <= 12):
            messagebox.showwarning("Invalid month", "Month must be between 1 and 12.")
            return
        y = self._validated_int(self.year_val.get().strip(), "Year")
        if y is None or not self._validate_year(y):
            return
        results = [b for b in self.books_all if b["month"] == m and b["year"] == y]
        self.books_display = results
        self._refresh_tree(results)

    def search_author(self):
        q = self.author_q.get().strip().lower()
        if not q:
            messagebox.showinfo("Input needed", "Please enter an author query.")
            return
        results = [b for b in self.books_all if q in b["author"].lower()]
        self.books_display = results
        self._refresh_tree(results)

    def search_title(self):
        q = self.title_q.get().strip().lower()
        if not q:
            messagebox.showinfo("Input needed", "Please enter a title query.")
            return
        results = [b for b in self.books_all if q in b["title"].lower()]
        self.books_display = results
        self._refresh_tree(results)


# ---------------------------
# Entry point
# ---------------------------
def run_app(data_path=None, start_theme="dark"):
    app = BestsellerApp(data_path=data_path, start_theme=start_theme)
    app.mainloop()
    
if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_app(data_path=data_path, start_theme="dark")
    
    
