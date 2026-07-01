import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import re
import threading
import os
import webbrowser

class JSONLViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced JSONL Multi-Filter Viewer")
        self.root.geometry("1400x850")
        
        self.all_records = []
        self.filtered_records = []
        self.current_directory = ""
        self.expression_history = []
        
        self.create_widgets()
        
        # Auto-load the user's home directory to get started immediately
        self.load_directory(os.path.expanduser("~"))

    def create_widgets(self):
        # --- Top Control Panel ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        self.load_dir_btn = ttk.Button(control_frame, text="📁 Open Folder", command=self.choose_directory)
        self.load_dir_btn.pack(side=tk.LEFT, padx=5)
        
        self.file_label = ttk.Label(control_frame, text="No file loaded", font=("Arial", 10, "italic"))
        self.file_label.pack(side=tk.LEFT, padx=10)

        self.progress_bar = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, length=150, mode='determinate')
        self.progress_lbl = ttk.Label(control_frame, text="", font=("Arial", 9))

        # --- Advanced Filter Matrix Panel ---
        filter_frame = ttk.LabelFrame(self.root, text=" Filter Criteria Matrix ", padding="10")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        expr_frame = ttk.Frame(filter_frame)
        expr_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(expr_frame, text="Expression:").pack(anchor=tk.W, padx=2)

        expr_text_frame = ttk.Frame(expr_frame)
        expr_text_frame.pack(fill=tk.X, expand=True, padx=2, pady=(2, 0))
        self.expression_text = tk.Text(
            expr_text_frame,
            height=8,
            wrap=tk.NONE,
            font=("Consolas", 10),
            background="#FFFFFF",
            foreground="#000000",
            insertbackground="#000000"
        )
        self.expression_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        expr_scroll_y = ttk.Scrollbar(expr_text_frame, orient=tk.VERTICAL, command=self.expression_text.yview)
        expr_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        expr_scroll_x = ttk.Scrollbar(expr_frame, orient=tk.HORIZONTAL, command=self.expression_text.xview)
        expr_scroll_x.pack(fill=tk.X, padx=2, pady=(2, 0))
        self.expression_text.config(yscrollcommand=expr_scroll_y.set, xscrollcommand=expr_scroll_x.set)

        self.expression_text.bind("<ButtonPress-1>", self.on_expression_border_press)
        self.expression_text.bind("<B1-Motion>", self.on_expression_border_drag)
        self.expression_text.bind("<ButtonRelease-1>", self.on_expression_border_release)
        self.expression_text.bind("<Motion>", self.on_expression_border_motion)

        self.expression_text.tag_config("expr_keyword", foreground="#0000CC")
        self.expression_text.tag_config("expr_paren", foreground="#CC6600")
        self.expression_text.tag_config("expr_operator", foreground="#CC0000")
        self.expression_text.tag_config("expr_string", foreground="#008000")
        self.expression_text.tag_config("expr_comment", foreground="#0A8F3D")
        self.expression_text.bind("<KeyRelease>", self.on_expression_text_change)

        row_controls_frame = ttk.Frame(filter_frame)
        row_controls_frame.pack(fill=tk.X, pady=(5, 0))

        self.reset_btn = ttk.Button(row_controls_frame, text="Reset & Show All", command=self.reset_filter)
        self.reset_btn.pack(side=tk.RIGHT, padx=2)
        self.filter_btn = self.create_rounded_button(
            row_controls_frame,
            text="Apply Expression",
            command=self.apply_filter,
            width=120,
            height=22,
            radius=3,
            bg="#9AB1FD",
            hover_bg="#97AEFC",
            press_bg="#97AEFC",
            fg="#000000"
        )
        self.filter_btn.pack(side=tk.RIGHT, padx=5)
        self.help_btn = ttk.Button(row_controls_frame, text="❓ Expression Help", width=18, command=self.show_syntax_help)
        self.help_btn.pack(side=tk.LEFT, padx=2)
        self.history_btn = ttk.Button(row_controls_frame, text="🕘 Expression History", width=20, command=self.show_expression_history)
        self.history_btn.pack(side=tk.LEFT, padx=2)

        # --- Main Viewport Nested Splitter ---
        # Outer PanedWindow splits: [File Tree] | [The rest of the UI]
        self.outer_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.outer_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel: File Explorer Sidebar
        tree_frame = ttk.Frame(self.outer_paned)
        self.outer_paned.add(tree_frame, weight=1)
        
        self.dir_lbl = ttk.Label(tree_frame, text="Folder Workspace:", font=("Arial", 9, "bold"))
        self.dir_lbl.pack(anchor=tk.W, pady=(0,2))
        
        self.file_tree = ttk.Treeview(tree_frame, selectmode="browse", show="tree")
        self.file_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_tree_select)
        self.file_tree.bind("<<TreeviewOpen>>", self.on_tree_node_expand)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.config(yscrollcommand=tree_scroll.set)
        
        # Inner PanedWindow splits: [Records List] | [Detailed Inspection Text]
        self.inner_paned = ttk.PanedWindow(self.outer_paned, orient=tk.HORIZONTAL)
        self.outer_paned.add(self.inner_paned, weight=4)
        
        # Middle Panel: List of Rows
        list_frame = ttk.Frame(self.inner_paned)
        self.inner_paned.add(list_frame, weight=1)
        ttk.Label(list_frame, text="Records List:").pack(anchor=tk.W)
        
        self.record_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, font=("Courier", 10))
        self.record_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.record_listbox.bind('<<ListboxSelect>>', self.on_record_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.record_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.record_listbox.config(yscrollcommand=scrollbar.set)
        
        # Right Panel: Notepad++ Style Text Inspector
        details_frame = ttk.Frame(self.inner_paned)
        self.inner_paned.add(details_frame, weight=2)
        
        details_header_frame = ttk.Frame(details_frame)
        details_header_frame.pack(fill=tk.X)
        ttk.Label(details_header_frame, text="Detailed Inspection (Notepad++ Style JSON):").pack(side=tk.LEFT, anchor=tk.W)
        
        self.copy_btn = ttk.Button(details_header_frame, text="📋 Copy JSON", command=self.copy_to_clipboard)
        self.copy_btn.pack(side=tk.RIGHT, padx=2, pady=2)
        
        self.details_text = tk.Text(details_frame, wrap=tk.NONE, font=("Consolas", 10), background="#FFFFFF", foreground="#000000", insertbackground="black")
        self.details_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.details_text.tag_config("json_key", foreground="#0000FF")      
        self.details_text.tag_config("json_string", foreground="#808080")   
        self.details_text.tag_config("json_number", foreground="#FF0000")   
        self.details_text.tag_config("json_boolean", foreground="#008080")  
        self.details_text.tag_config("json_null", foreground="#FF00FF")     
        
        det_scroll_y = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        det_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        det_scroll_x = ttk.Scrollbar(details_frame, orient=tk.HORIZONTAL, command=self.details_text.xview)
        det_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.details_text.config(yscrollcommand=det_scroll_y.set, xscrollcommand=det_scroll_x.set)
        
        # Status Bar with Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(footer_frame, text="Rows loaded: 0", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        creator_frame = ttk.Frame(footer_frame)
        creator_frame.pack(side=tk.RIGHT, padx=5, pady=2)
        
        ttk.Label(creator_frame, text="Created by Gorka Lertxundi", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        github_btn = ttk.Button(creator_frame, text="🐙 GitHub", command=self.open_github_repo)
        github_btn.pack(side=tk.LEFT, padx=2)

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, color):
        body = []
        body.append(canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=color, outline=color))
        body.append(canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=color, outline=color))
        body.append(canvas.create_oval(x1, y1, x1 + 2 * radius, y1 + 2 * radius, fill=color, outline=color))
        body.append(canvas.create_oval(x2 - 2 * radius, y1, x2, y1 + 2 * radius, fill=color, outline=color))
        body.append(canvas.create_oval(x1, y2 - 2 * radius, x1 + 2 * radius, y2, fill=color, outline=color))
        body.append(canvas.create_oval(x2 - 2 * radius, y2 - 2 * radius, x2, y2, fill=color, outline=color))
        return body

    def _set_canvas_items_color(self, canvas, items, color):
        for item in items:
            canvas.itemconfig(item, fill=color, outline=color)

    def create_rounded_button(self, parent, text, command, width, height, radius, bg, hover_bg, press_bg, fg):
        canvas_bg = self.root.cget("bg")
        canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0, bg=canvas_bg)
        shape_items = self._draw_rounded_rect(canvas, 1, 1, width - 1, height - 1, radius, bg)
        label_item = canvas.create_text(width // 2, height // 2, text=text, fill=fg, font=("Segoe UI", 9))

        def on_enter(_event):
            self._set_canvas_items_color(canvas, shape_items, hover_bg)

        def on_leave(_event):
            self._set_canvas_items_color(canvas, shape_items, bg)

        def on_press(_event):
            self._set_canvas_items_color(canvas, shape_items, press_bg)

        def on_release(_event):
            self._set_canvas_items_color(canvas, shape_items, hover_bg)
            command()

        for item in [*shape_items, label_item]:
            canvas.tag_bind(item, "<Enter>", on_enter)
            canvas.tag_bind(item, "<Leave>", on_leave)
            canvas.tag_bind(item, "<ButtonPress-1>", on_press)
            canvas.tag_bind(item, "<ButtonRelease-1>", on_release)

        return canvas

    # --- Directory Tree Utilities ---
    def choose_directory(self):
        """Opens a folder dialogue selection box."""
        chosen_dir = filedialog.askdirectory(initialdir=self.current_directory or os.getcwd())
        if chosen_dir:
            self.load_directory(chosen_dir)

    def load_directory(self, path):
        """Resets and Populates the baseline root items in the tree view sidebar."""
        self.current_directory = path
        self.dir_lbl.config(text=f"Folder: {os.path.basename(path) or path}")
        
        # Clear old items
        for node in self.file_tree.get_children():
            self.file_tree.delete(node)
            
        # Insert Root folder entry
        root_node = self.file_tree.insert("", "end", text=path, open=True, values=(path, "dir"))
        self.populate_tree_node(root_node, path)

    def populate_tree_node(self, parent_node, path):
        """Scans directories and maps contents out to the treeview structure layout safely."""
        try:
            items = os.listdir(path)
        except PermissionError:
            return

        # Separate files vs directories to sort nicely
        dirs = []
        json_files = []
        
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
            elif item.lower().endswith(('.jsonl')):
                json_files.append(item)
                
        dirs.sort(key=str.lower)
        json_files.sort(key=str.lower)
        
        # Append subdirectories (add dummy item so it's expandable)
        for d in dirs:
            full_p = os.path.join(path, d)
            node = self.file_tree.insert(parent_node, "end", text=f"📁 {d}", values=(full_p, "dir"))
            self.file_tree.insert(node, "end", text="dummy") # Placeholders resolved on expansion trigger
            
        # Append compatible target JSON data payloads
        for f in json_files:
            full_p = os.path.join(path, f)
            self.file_tree.insert(parent_node, "end", text=f"📄 {f}", values=(full_p, "file"))

    def on_tree_node_expand(self, event):
        """Lazy evaluation loader triggered only when an unread subdirectory gets expanded."""
        selected_node = self.file_tree.focus()
        node_data = self.file_tree.item(selected_node)
        
        if not node_data["values"]:
            return
            
        full_path, node_type = node_data["values"]
        if node_type == "dir":
            # Clear placeholder children structures safely
            children = self.file_tree.get_children(selected_node)
            if len(children) == 1 and self.file_tree.item(children[0], "text") == "dummy":
                self.file_tree.delete(children[0])
                self.populate_tree_node(selected_node, full_path)

    def on_file_tree_select(self, event):
        """Fires whenever a file item in the sidebar explorer tree is clicked."""
        selected_node = self.file_tree.focus()
        node_data = self.file_tree.item(selected_node)
        
        if not node_data["values"]:
            return
            
        full_path, node_type = node_data["values"]
        if node_type == "file":
            # Direct file read processing sequences initiated inside a helper function
            self.start_file_load(full_path)

    # --- Core Loading & Query Engine Routing ---
    def start_file_load(self, file_path):
        """Initializes progress indicators and starts a safe multi-threaded background read operation."""
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        self.progress_lbl.pack(side=tk.LEFT)
        self.load_dir_btn.config(state=tk.DISABLED)
        
        threading.Thread(target=self.load_file_worker, args=(file_path,), daemon=True).start()

    def load_file_worker(self, file_path):
        self.all_records = []
        try:
            total_bytes = os.path.getsize(file_path)
            bytes_processed = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    bytes_processed += len(line.encode('utf-8'))
                    line_str = line.strip()
                    if line_str:
                        try:
                            self.all_records.append(json.loads(line_str))
                        except json.JSONDecodeError:
                            pass
                    if line_num % 100 == 0 or bytes_processed == total_bytes:
                        percentage = (bytes_processed / total_bytes) * 100
                        self.root.after(0, self.update_progress, percentage, f"Reading: {int(percentage)}%")
            self.root.after(0, self.load_complete_callback, file_path, None)
        except Exception as e:
            self.root.after(0, self.load_complete_callback, file_path, str(e))

    def update_progress(self, percent_val, label_text):
        self.progress_bar['value'] = percent_val
        self.progress_lbl.config(text=label_text)

    def load_complete_callback(self, file_path, error_msg):
        self.progress_bar.pack_forget()
        self.progress_lbl.pack_forget()
        self.load_dir_btn.config(state=tk.NORMAL)
        if error_msg:
            messagebox.showerror("Error", f"Could not read file:\n{error_msg}")
            return
        self.file_label.config(text=os.path.basename(file_path))
        self.reset_filter()

    def show_syntax_help(self):
        if hasattr(self, "help_window") and self.help_window.winfo_exists():
            self.help_window.lift()
            self.help_window.focus_force()
            return

        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("Expression Help")
        self.help_window.geometry("940x680")
        self.help_window.minsize(760, 520)
        self.help_window.transient(self.root)

        container = ttk.Frame(self.help_window, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        title_lbl = ttk.Label(
            container,
            text="Expression Syntax Reference",
            font=("Segoe UI", 16, "bold")
        )
        title_lbl.pack(anchor=tk.W, pady=(0, 8))

        subtitle_lbl = ttk.Label(
            container,
            text="Use logical operators, parentheses, and LIKE patterns to filter JSON records.",
            font=("Segoe UI", 10)
        )
        subtitle_lbl.pack(anchor=tk.W, pady=(0, 10))

        text_frame = ttk.Frame(container)
        text_frame.pack(fill=tk.BOTH, expand=True)

        help_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#FFFFFF",
            foreground="#1f2937",
            spacing1=2,
            spacing3=3,
            padx=10,
            pady=10,
            borderwidth=1,
            relief=tk.SOLID
        )
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        help_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=help_text.yview)
        help_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        help_text.config(yscrollcommand=help_scroll.set)

        help_text.tag_config("h1", font=("Segoe UI", 12, "bold"), foreground="#111827", spacing1=8, spacing3=6)
        help_text.tag_config("h2", font=("Segoe UI", 10, "bold"), foreground="#1d4ed8", spacing1=6, spacing3=2)
        help_text.tag_config("body", font=("Consolas", 10), foreground="#1f2937")
        help_text.tag_config("code", font=("Consolas", 10, "bold"), foreground="#065f46")
        help_text.tag_config("note", font=("Consolas", 10), foreground="#7c2d12")

        help_text.insert(tk.END, "Expression Filter\n", "h1")
        help_text.insert(tk.END, "Supports AND, OR, parentheses, =, != and LIKE.\n\n", "body")

        help_text.insert(tk.END, "Single-line example\n", "h2")
        help_text.insert(tk.END, "customerId = 'C-1024' AND (region = 'EU' OR orderState != 'Shipped')\n\n", "code")

        help_text.insert(tk.END, "Multi-line example\n", "h2")
        help_text.insert(tk.END, "customerId = 'C-1024'\nAND (region = 'EU' OR orderState LIKE '%Pending%')\n\n", "code")

        help_text.insert(tk.END, "Cheat-sheet\n", "h2")
        help_text.insert(tk.END, "field = 'value'\n", "code")
        help_text.insert(tk.END, "field != 'value'\n", "code")
        help_text.insert(tk.END, "field LIKE '%text%'\n", "code")
        help_text.insert(tk.END, "field LIKE '%text'\n", "code")
        help_text.insert(tk.END, "field LIKE 'text%'\n", "code")
        help_text.insert(tk.END, "-- this is a comment line\n", "code")
        help_text.insert(tk.END, "Use AND/OR and (...)\n\n", "body")

        help_text.insert(tk.END, "LIKE patterns\n", "h2")
        help_text.insert(tk.END, "productName LIKE '%Pro%'      -> contains\n", "code")
        help_text.insert(tk.END, "city LIKE '%ville'            -> ends with\n", "code")
        help_text.insert(tk.END, "category LIKE 'Electro%'      -> starts with\n\n", "code")

        help_text.insert(tk.END, "Comments\n", "h2")
        help_text.insert(tk.END, "Lines starting with '--' are ignored by the filter parser.\n", "body")
        help_text.insert(tk.END, "Example:\n", "body")
        help_text.insert(tk.END, "-- Narrow down to EU pending orders\n", "code")
        help_text.insert(tk.END, "region = 'EU' AND orderState LIKE '%Pending%'\n\n", "code")

        help_text.insert(tk.END, "JSON path notes\n", "h2")
        help_text.insert(tk.END, "data.test[*].sample[*]        -> nested arrays\n", "code")
        help_text.insert(tk.END, "data.test[*].id               -> wildcard over array\n", "code")
        help_text.insert(tk.END, "data.test[0].id / data.test[-1].id -> first / last item\n\n", "code")

        help_text.insert(tk.END, "Tip: leave path blank in row-style search to do a global fuzzy match.\n", "note")
        help_text.config(state=tk.DISABLED)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(actions, text="Close", command=self.help_window.destroy).pack(side=tk.RIGHT)

    def _is_near_expression_bottom_border(self, event):
        widget_height = self.expression_text.winfo_height()
        return event.y >= widget_height - 8

    def on_expression_border_press(self, event):
        if self._is_near_expression_bottom_border(event):
            self._expr_resize_active = True
            self._expr_resize_start_y = event.y_root
            self._expr_resize_start_height = int(self.expression_text.cget("height"))
            return "break"
        self._expr_resize_active = False

    def on_expression_border_drag(self, event):
        if not getattr(self, "_expr_resize_active", False):
            return
        delta_pixels = event.y_root - self._expr_resize_start_y
        delta_lines = int(delta_pixels / 16)
        new_height = max(3, min(30, self._expr_resize_start_height + delta_lines))
        self.expression_text.config(height=new_height)
        return "break"

    def on_expression_border_release(self, _event):
        self._expr_resize_active = False

    def on_expression_border_motion(self, event):
        if self._is_near_expression_bottom_border(event) or getattr(self, "_expr_resize_active", False):
            self.expression_text.config(cursor="sb_v_double_arrow")
        else:
            self.expression_text.config(cursor="xterm")

    def strip_expression_comments(self, expression_text):
        lines = expression_text.splitlines()
        kept_lines = []
        for line in lines:
            if re.match(r"^\s*--", line):
                continue
            kept_lines.append(line)
        return "\n".join(kept_lines)

    def add_expression_to_history(self, expression_text):
        cleaned = expression_text.strip()
        if not cleaned:
            return

        if cleaned in self.expression_history:
            self.expression_history.remove(cleaned)

        self.expression_history.append(cleaned)

        if len(self.expression_history) > 50:
            self.expression_history.pop(0)

        if hasattr(self, "history_window") and self.history_window.winfo_exists():
            self.refresh_expression_history_list()

    def refresh_expression_history_list(self):
        if not hasattr(self, "history_listbox"):
            return

        self.history_listbox.delete(0, tk.END)
        self._history_display_to_value = list(reversed(self.expression_history))

        for idx, expr in enumerate(self._history_display_to_value, 1):
            first_line = expr.splitlines()[0].strip()
            preview = first_line[:70] + ("..." if len(first_line) > 70 else "")
            self.history_listbox.insert(tk.END, f"{idx:02d}. {preview}")

        if self._history_display_to_value:
            self.history_listbox.selection_set(0)
            self.on_history_select()
        else:
            self.history_preview.config(state=tk.NORMAL)
            self.history_preview.delete("1.0", tk.END)
            self.history_preview.insert(tk.END, "No expressions applied yet in this session.")
            self.history_preview.config(state=tk.DISABLED)

    def get_selected_history_expression(self):
        if not hasattr(self, "history_listbox"):
            return None
        sel = self.history_listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if idx >= len(self._history_display_to_value):
            return None
        return self._history_display_to_value[idx]

    def on_history_select(self, event=None):
        selected_expr = self.get_selected_history_expression()
        self.history_preview.config(state=tk.NORMAL)
        self.history_preview.delete("1.0", tk.END)
        if selected_expr:
            self.history_preview.insert(tk.END, selected_expr)
            self.colorize_expression_widget(self.history_preview)
        self.history_preview.config(state=tk.DISABLED)

    def copy_selected_history_expression(self):
        selected_expr = self.get_selected_history_expression()
        if not selected_expr:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(selected_expr)

    def insert_selected_history_expression(self):
        selected_expr = self.get_selected_history_expression()
        if not selected_expr:
            return
        self.expression_text.delete("1.0", tk.END)
        self.expression_text.insert(tk.END, selected_expr)
        self.colorize_expression_text()
        self.expression_text.focus_set()

    def show_expression_history(self):
        if hasattr(self, "history_window") and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_force()
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Expression History")
        self.history_window.geometry("900x520")
        self.history_window.minsize(700, 420)
        self.history_window.transient(self.root)

        container = ttk.Frame(self.history_window, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Recent Expressions (session only)", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))

        main = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        main.add(left, weight=1)

        self.history_listbox = tk.Listbox(left, font=("Consolas", 10))
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)
        self.history_listbox.bind("<Double-Button-1>", lambda _e: self.insert_selected_history_expression())

        left_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.history_listbox.yview)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=left_scroll.set)

        right = ttk.Frame(main, padding=(10, 0, 0, 0))
        main.add(right, weight=1)

        ttk.Label(right, text="Preview:").pack(anchor=tk.W)
        self.history_preview = tk.Text(right, wrap=tk.WORD, font=("Consolas", 10), background="#FFFFFF", foreground="#000000", height=14)
        self.history_preview.pack(fill=tk.BOTH, expand=True)
        self.history_preview.tag_config("expr_keyword", foreground="#0000CC")
        self.history_preview.tag_config("expr_paren", foreground="#CC6600")
        self.history_preview.tag_config("expr_operator", foreground="#CC0000")
        self.history_preview.tag_config("expr_string", foreground="#008000")
        self.history_preview.tag_config("expr_comment", foreground="#0A8F3D")
        self.history_preview.config(state=tk.DISABLED)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(actions, text="Insert in Editor", command=self.insert_selected_history_expression).pack(side=tk.LEFT)
        ttk.Button(actions, text="Copy", command=self.copy_selected_history_expression).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Close", command=self.history_window.destroy).pack(side=tk.RIGHT)

        self.refresh_expression_history_list()

    def parse_path_string(self, path_str):
        raw_segments = path_str.split('.')
        refined_segments = []
        for seg in raw_segments:
            match = re.match(r"([^\[]+)(.*)", seg)
            if match:
                refined_segments.append(match.group(1)) 
                brackets = re.findall(r"\[[^\]]+\]", match.group(2)) 
                refined_segments.extend(brackets)
        return refined_segments

    def get_values_by_path(self, data, segments):
        if not segments:
            return [data]
        
        current_token = segments[0]
        remaining_tokens = segments[1:]
        
        if current_token.startswith('[') and current_token.endswith(']'):
            index_val = current_token[1:-1]
            if not isinstance(data, list):
                return []
                
            if index_val == '*':  
                results = []
                for item in data:
                    results.extend(self.get_values_by_path(item, remaining_tokens))
                return results
            else:  
                try:
                    idx = int(index_val)
                    if -len(data) <= idx < len(data):
                        return self.get_values_by_path(data[idx], remaining_tokens)
                except ValueError:
                    pass
                return []
                
        elif isinstance(data, dict) and current_token in data:
            return self.get_values_by_path(data[current_token], remaining_tokens)
            
        return []

    def global_fuzzy_search(self, data, target_val):
        t_val = str(target_val).strip().lower()
        if isinstance(data, dict):
            return any(self.global_fuzzy_search(v, target_val) for v in data.values())
        elif isinstance(data, list):
            return any(self.global_fuzzy_search(item, target_val) for item in data)
        return t_val in str(data).strip().lower()

    def check_single_condition(self, record, path_query, val_query):
        if not path_query:
            return self.global_fuzzy_search(record, val_query)
        
        tokens = self.parse_path_string(path_query)
        found_values = self.get_values_by_path(record, tokens)
        
        flattened_strings = []
        def flatten(v):
            if isinstance(v, list):
                for item in v: flatten(item)
            else:
                flattened_strings.append(str(v).lower())
                
        for v in found_values: 
            flatten(v)
            
        return any(val_query in s for s in flattened_strings)

    def tokenize_expression(self, expression_text):
        token_pattern = re.compile(
            r"\s*(?:(?P<LPAREN>\()|(?P<RPAREN>\))|(?P<NEQ>!=)|(?P<EQ>=)|"
            r"(?P<AND>AND\b)|(?P<OR>OR\b)|(?P<LIKE>LIKE\b)|"
            r"(?P<STRING>'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")|"
            r"(?P<IDENT>[A-Za-z_][A-Za-z0-9_\.\[\]\-\*]*)|(?P<MISMATCH>.))",
            flags=re.IGNORECASE
        )

        tokens = []
        position = 0
        while position < len(expression_text):
            match = token_pattern.match(expression_text, position)
            if not match:
                raise ValueError(f"Invalid token near position {position + 1}")

            kind = match.lastgroup
            value = match.group(kind)
            position = match.end()

            if kind == "MISMATCH":
                raise ValueError(f"Unexpected token '{value}' at position {position}")

            if kind in {"AND", "OR", "LIKE"}:
                value = value.upper()

            tokens.append((kind, value))

        return tokens

    def _current_token(self, tokens, idx):
        if idx < len(tokens):
            return tokens[idx]
        return None

    def _consume_token(self, tokens, idx, expected_kind=None):
        tok = self._current_token(tokens, idx)
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if expected_kind and tok[0] != expected_kind:
            raise ValueError(f"Expected {expected_kind}, found {tok[1]}")
        return tok, idx + 1

    def _unescape_string_token(self, raw):
        quote = raw[0]
        content = raw[1:-1]
        if quote == "'":
            return content.replace("\\'", "'").replace('\\\\', '\\')
        return content.replace('\\\"', '"').replace('\\\\', '\\')

    def _convert_ident_literal(self, ident_value):
        lowered = ident_value.lower()
        if lowered == "true":
            return ("LITERAL", True)
        if lowered == "false":
            return ("LITERAL", False)
        if lowered == "null":
            return ("LITERAL", None)
        if re.fullmatch(r"-?\d+", ident_value):
            return ("LITERAL", int(ident_value))
        if re.fullmatch(r"-?\d+\.\d+", ident_value):
            return ("LITERAL", float(ident_value))
        return ("LITERAL", ident_value)

    def _parse_value_token(self, tokens, idx):
        tok = self._current_token(tokens, idx)
        if tok is None:
            raise ValueError("Missing value in condition")

        if tok[0] == "STRING":
            _, idx = self._consume_token(tokens, idx, "STRING")
            return ("STRING", self._unescape_string_token(tok[1])), idx

        if tok[0] == "IDENT":
            _, idx = self._consume_token(tokens, idx, "IDENT")
            return self._convert_ident_literal(tok[1]), idx

        raise ValueError(f"Expected value, found {tok[1]}")

    def _parse_condition_token(self, tokens, idx):
        path_tok, idx = self._consume_token(tokens, idx, "IDENT")
        op_tok = self._current_token(tokens, idx)
        if op_tok is None or op_tok[0] not in {"EQ", "NEQ", "LIKE"}:
            raise ValueError("Condition must use '=', '!=', or 'LIKE'")
        _, idx = self._consume_token(tokens, idx, op_tok[0])
        value, idx = self._parse_value_token(tokens, idx)
        return ("COND", path_tok[1], op_tok[1], value), idx

    def _parse_factor(self, tokens, idx):
        tok = self._current_token(tokens, idx)
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if tok[0] == "LPAREN":
            _, idx = self._consume_token(tokens, idx, "LPAREN")
            node, idx = self._parse_or_expression(tokens, idx)
            _, idx = self._consume_token(tokens, idx, "RPAREN")
            return node, idx
        return self._parse_condition_token(tokens, idx)

    def _parse_and_expression(self, tokens, idx):
        node, idx = self._parse_factor(tokens, idx)
        while True:
            tok = self._current_token(tokens, idx)
            if tok is None or tok[0] != "AND":
                break
            _, idx = self._consume_token(tokens, idx, "AND")
            right, idx = self._parse_factor(tokens, idx)
            node = ("AND", node, right)
        return node, idx

    def _parse_or_expression(self, tokens, idx):
        node, idx = self._parse_and_expression(tokens, idx)
        while True:
            tok = self._current_token(tokens, idx)
            if tok is None or tok[0] != "OR":
                break
            _, idx = self._consume_token(tokens, idx, "OR")
            right, idx = self._parse_and_expression(tokens, idx)
            node = ("OR", node, right)
        return node, idx

    def parse_expression(self, expression_text):
        tokens = self.tokenize_expression(expression_text)
        if not tokens:
            raise ValueError("Expression is empty")

        ast, idx = self._parse_or_expression(tokens, 0)
        if idx != len(tokens):
            raise ValueError(f"Unexpected token '{tokens[idx][1]}'")
        return ast

    def flatten_record_values(self, value):
        if isinstance(value, list):
            flattened = []
            for item in value:
                flattened.extend(self.flatten_record_values(item))
            return flattened
        return [value]

    def evaluate_expression_condition(self, record, path_query, operator, value_info):
        path_tokens = self.parse_path_string(path_query)
        found_values = self.get_values_by_path(record, path_tokens)
        candidates = []
        for val in found_values:
            candidates.extend(self.flatten_record_values(val))

        if not candidates:
            return operator == "!="

        value_type, expected_value = value_info

        def values_like(candidate):
            pattern = str(expected_value)
            candidate_text = str(candidate)
            if pattern.startswith('%') and pattern.endswith('%') and len(pattern) >= 2:
                return pattern[1:-1].lower() in candidate_text.lower()
            if pattern.startswith('%'):
                return candidate_text.lower().endswith(pattern[1:].lower())
            if pattern.endswith('%'):
                return candidate_text.lower().startswith(pattern[:-1].lower())
            return candidate_text.lower() == pattern.lower()

        def values_equal(candidate):
            if value_type == "STRING":
                return str(candidate) == expected_value

            if isinstance(expected_value, (int, float)) and isinstance(candidate, (int, float)):
                return candidate == expected_value

            if isinstance(expected_value, bool) and isinstance(candidate, bool):
                return candidate == expected_value

            if expected_value is None:
                return candidate is None or str(candidate).lower() == "null"

            return str(candidate) == str(expected_value)

        if operator == "LIKE":
            return any(values_like(c) for c in candidates)

        if operator == "=":
            return any(values_equal(c) for c in candidates)

        return all(not values_equal(c) for c in candidates)

    def evaluate_expression_ast(self, record, node):
        node_type = node[0]
        if node_type == "COND":
            _, path_query, operator, value_info = node
            return self.evaluate_expression_condition(record, path_query, operator, value_info)
        if node_type == "AND":
            return self.evaluate_expression_ast(record, node[1]) and self.evaluate_expression_ast(record, node[2])
        if node_type == "OR":
            return self.evaluate_expression_ast(record, node[1]) or self.evaluate_expression_ast(record, node[2])
        return False

    def apply_expression_filter(self, expression_text):
        ast = self.parse_expression(expression_text)
        self.filtered_records = [rec for rec in self.all_records if self.evaluate_expression_ast(rec, ast)]
        self.update_listbox()

    def colorize_expression_text(self):
        self.colorize_expression_widget(self.expression_text)

    def colorize_expression_widget(self, text_widget):
        full_text = text_widget.get("1.0", tk.END)

        for tag in ("expr_keyword", "expr_paren", "expr_operator", "expr_string", "expr_comment"):
            text_widget.tag_remove(tag, "1.0", tk.END)

        keyword_pattern = r"\b(AND|OR|LIKE)\b"
        paren_pattern = r"[()]"
        operator_pattern = r"!=|="
        string_pattern = r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\""

        for match in re.finditer(string_pattern, full_text, flags=re.IGNORECASE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add("expr_string", start, end)

        for match in re.finditer(keyword_pattern, full_text, flags=re.IGNORECASE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add("expr_keyword", start, end)

        for match in re.finditer(paren_pattern, full_text):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add("expr_paren", start, end)

        for match in re.finditer(operator_pattern, full_text):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add("expr_operator", start, end)

        comment_pattern = r"^\s*--.*$"
        for match in re.finditer(comment_pattern, full_text, flags=re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add("expr_comment", start, end)

    def on_expression_text_change(self, event=None):
        self.colorize_expression_text()

    def apply_filter(self):
        raw_expression_text = self.expression_text.get("1.0", tk.END).strip()
        if not raw_expression_text:
            self.reset_filter()
            return

        expression_text = self.strip_expression_comments(raw_expression_text).strip()
        if not expression_text:
            self.reset_filter()
            return

        try:
            self.apply_expression_filter(expression_text)
            self.add_expression_to_history(raw_expression_text)
        except ValueError as err:
            messagebox.showerror("Expression Error", str(err))

    def reset_filter(self):
        self.expression_text.delete("1.0", tk.END)
        self.colorize_expression_text()
        self.filtered_records = list(self.all_records)
        self.update_listbox()

    def update_listbox(self):
        self.record_listbox.delete(0, tk.END)
        for i, rec in enumerate(self.filtered_records):
            msg_type = rec.get("msgType", "Unknown")
            dev_sn = rec.get("deviceSerialNumber", "N/A")
            sample = rec.get("data", {}).get("sampleHash", "N/A")[:10] if isinstance(rec.get("data"), dict) else "N/A"
            
            display_text = f"[{i+1:03d}] Type: {msg_type} | SN: {dev_sn} | Sample: {sample}..."
            self.record_listbox.insert(tk.END, display_text)
            
        self.status_label.config(text=f"Showing {len(self.filtered_records)} of {len(self.all_records)} total rows.")
        self.details_text.delete('1.0', tk.END)

    def colorize_json_text(self, plain_text):
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, plain_text)
        
        key_pattern = r'("[^"\\]*(?:\\.[^"\\]*)*")\s*:'
        string_pattern = r':\s*("[^"\\]*(?:\\.[^"\\]*)*")'
        number_pattern = r'\b(-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)\b'
        bool_pattern = r'\b(true|false)\b'
        null_pattern = r'\b(null)\b'
        
        lines = plain_text.split('\n')
        for idx, line in enumerate(lines, 1):
            for match in re.finditer(key_pattern, line):
                start, end = match.span(1)
                self.details_text.tag_add("json_key", f"{idx}.{start}", f"{idx}.{end}")
            for match in re.finditer(string_pattern, line):
                start, end = match.span(1)
                self.details_text.tag_add("json_string", f"{idx}.{start}", f"{idx}.{end}")
            for match in re.finditer(number_pattern, line):
                start, end = match.span(1)
                current_tags = self.details_text.tag_names(f"{idx}.{start}")
                if "json_key" not in current_tags and "json_string" not in current_tags:
                    self.details_text.tag_add("json_number", f"{idx}.{start}", f"{idx}.{end}")
            for match in re.finditer(bool_pattern, line):
                start, end = match.span(1)
                if "json_key" not in self.details_text.tag_names(f"{idx}.{start}"):
                    self.details_text.tag_add("json_boolean", f"{idx}.{start}", f"{idx}.{end}")
            for match in re.finditer(null_pattern, line):
                start, end = match.span(1)
                if "json_key" not in self.details_text.tag_names(f"{idx}.{start}"):
                    self.details_text.tag_add("json_null", f"{idx}.{start}", f"{idx}.{end}")

    def on_record_select(self, event):
        selection = self.record_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        selected_record = self.filtered_records[index]
        pretty_json = json.dumps(selected_record, indent=4, ensure_ascii=False)
        self.colorize_json_text(pretty_json)

    def copy_to_clipboard(self):
        text_content = self.details_text.get('1.0', tk.END).strip()
        if text_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_content)
            messagebox.showinfo("Success", "JSON copied to clipboard successfully!")

    def open_github_repo(self):
        """Opens the GitHub repository in the default web browser."""
        webbrowser.open("https://github.com/gorkalertxundi/Advanced_JSONL_Multi-Filter_Viewer")

if __name__ == "__main__":
    root = tk.Tk()
    app = JSONLViewer(root)
    root.mainloop()