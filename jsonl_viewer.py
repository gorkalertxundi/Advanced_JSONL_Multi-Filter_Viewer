import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import re
import threading
import os

class JSONLViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced JSONL Multi-Filter Viewer")
        self.root.geometry("1400x850")
        
        self.all_records = []
        self.filtered_records = []
        self.current_directory = ""
        
        self.create_widgets()
        
        # Auto-load the current working directory to get started immediately
        self.load_directory(os.getcwd())

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
        
        match_mode_frame = ttk.Frame(filter_frame)
        match_mode_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(match_mode_frame, text="Match Mode:").pack(side=tk.LEFT, padx=2)
        self.match_mode = tk.StringVar(value="AND")
        ttk.Radiobutton(match_mode_frame, text="ALL Conditions (AND)", variable=self.match_mode, value="AND").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(match_mode_frame, text="ANY Condition (OR)", variable=self.match_mode, value="OR").pack(side=tk.LEFT, padx=10)
        
        self.help_btn = ttk.Button(match_mode_frame, text="❓ Path Help", width=12, command=self.show_syntax_help)
        self.help_btn.pack(side=tk.RIGHT)

        self.rows_container = ttk.Frame(filter_frame)
        self.rows_container.pack(fill=tk.X, pady=5)
        
        self.filter_rows = []
        self.add_filter_row("deviceSerialNumber", "511-0000988")
        self.add_filter_row("data.microtubes[*].reagentBarcode[*]", "031553340206")

        row_controls_frame = ttk.Frame(filter_frame)
        row_controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(row_controls_frame, text="➕ Add Condition Row", command=lambda: self.add_filter_row()).pack(side=tk.LEFT, padx=2)
        ttk.Button(row_controls_frame, text="Clear All Rows", command=self.clear_all_rows).pack(side=tk.LEFT, padx=2)
        
        self.reset_btn = ttk.Button(row_controls_frame, text="Reset & Show All", command=self.reset_filter)
        self.reset_btn.pack(side=tk.RIGHT, padx=2)
        self.filter_btn = ttk.Button(row_controls_frame, text="Apply Filter Matrix", command=self.apply_filter)
        self.filter_btn.pack(side=tk.RIGHT, padx=5)

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
        
        # Status Bar
        self.status_label = ttk.Label(self.root, text="Rows loaded: 0", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

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
            elif item.lower().endswith(('.jsonl', '.json')):
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

    def add_filter_row(self, initial_path="", initial_val=""):
        row_frame = ttk.Frame(self.rows_container)
        row_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(row_frame, text=f"Path:").pack(side=tk.LEFT, padx=2)
        path_ent = ttk.Entry(row_frame, width=35)
        path_ent.pack(side=tk.LEFT, padx=2)
        path_ent.insert(0, initial_path)
        
        ttk.Label(row_frame, text=f"Value contains:").pack(side=tk.LEFT, padx=5)
        val_ent = ttk.Entry(row_frame, width=35)
        val_ent.pack(side=tk.LEFT, padx=2)
        val_ent.insert(0, initial_val)
        
        del_btn = ttk.Button(row_frame, text="❌", width=3, command=lambda: self.delete_filter_row(row_frame))
        del_btn.pack(side=tk.LEFT, padx=5)
        
        self.filter_rows.append({"frame": row_frame, "path_entry": path_ent, "val_entry": val_ent})

    def delete_filter_row(self, row_frame):
        row_frame.destroy()
        self.filter_rows = [r for r in self.filter_rows if r["frame"] != row_frame]

    def clear_all_rows(self):
        for r in self.filter_rows:
            r["frame"].destroy()
        self.filter_rows = []

    def show_syntax_help(self):
        help_text = (
            "JSON Path Syntax Reference Guide\n"
            "=========================================\n\n"
            "1. MULTI-ARRAY CONCATENATION\n"
            "   If arrays are nested inside other arrays, chain wildcards together:\n"
            "   • Path: data.microtubes[*].reagentBarcode[*]\n\n"
            "2. STANDARD ARRAY WILD CARDS ([*])\n"
            "   • Path: data.microtubes[*].id\n\n"
            "3. EXPLICIT INDEXES / SLICES ([0] or [-1])\n"
            "   • First microtube: data.microtubes[0].id\n"
            "   • Last microtube:  data.microtubes[-1].id\n\n"
            "4. BLANK FUZZY SEARCH\n"
            "   Leave 'Path' blank to search for the value anywhere in that record."
        )
        messagebox.showinfo("JSON Path Query Guide", help_text)

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

    def apply_filter(self):
        active_rules = []
        for row in self.filter_rows:
            p = row["path_entry"].get().strip()
            v = row["val_entry"].get().strip().lower()
            if p or v:
                active_rules.append((p, v))
                
        if not active_rules:
            self.reset_filter()
            return
            
        self.filtered_records = []
        mode = self.match_mode.get()
        
        for rec in self.all_records:
            row_matches = [self.check_single_condition(rec, p, v) for p, v in active_rules]
            
            if mode == "AND" and all(row_matches):
                self.filtered_records.append(rec)
            elif mode == "OR" and any(row_matches):
                self.filtered_records.append(rec)
                
        self.update_listbox()

    def reset_filter(self):
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

if __name__ == "__main__":
    root = tk.Tk()
    app = JSONLViewer(root)
    root.mainloop()