import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import collections
from collections import deque
import math
import os
# Non-interactive Matplotlib backend initialization
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch  # 👈 ADD THIS LINE
import networkx as nx

from node import Node
from huffman import *

def _pick_font(preferred, fallback='Times-Roman'):
    """Return the first installed font family from a preference list."""
    try:
        available = set(tkfont.families())
    except Exception:
        return fallback
    for name in preferred:
        if name in available:
            return name
    return fallback


class HuffmanApp(tk.Tk):
    # Refined palette: warm ivory neutrals + a slate/terracotta accent duo,
    # tuned for softer contrast and a more polished, editorial feel.
    BG_LIGHT      = '#F7F4EF'  # Warm Ivory
    BG_SURFACE    = '#EEE7DC'  # Sand Tan
    PANEL_WHITE   = '#FFFFFF'  # Card White
    ACCENT_LIGHT  = '#E2D9CA'  # Warm Muted Border
    ACCENT_MED    = '#2E4A63'  # Deep Slate Blue (Internal Nodes)
    ACCENT_MED_LT = '#4A6B8A'  # Slate Blue, lighter (gradient/hover)
    LEAF_MUTED    = '#D9724F'  # Terracotta (Leaf Nodes)
    LEAF_MUTED_LT = '#E9946E'  # Terracotta, lighter (gradient/hover)
    DARK_MAIN     = '#1B1A17'  # Deep Charcoal
    TEXT_MUTED    = '#8A8072'  # Muted taupe for secondary text
    GLOW_ORANGE   = '#E0603E'  # Vibrant Accent Orange
    GLOW_TRAVERSE = '#2E7D4F'  # Fresh Green for Active Traversal Focus
    SHADOW        = '#D8CFC0'  # Soft ambient shadow tone
    FONT_UI = _pick_font([
               'Segoe UI',
             'Arial',
            'Calibri',
            'Verdana',
           'Tahoma'
            ], fallback='Segoe UI')
    FONT_MONO = _pick_font(['JetBrains Mono', 'Cascadia Code', 'Consolas', 'Courier New'])

    def __init__(self):
        super().__init__()
        self.title("Huffman Compressor and Visualization studio")
        self.geometry("1440x950")
        self.configure(bg=self.BG_LIGHT)
        
        try:
            self.tk.call('tk', 'scaling', 1.33)
        except Exception:
            pass
            
        self.tree_root = None
        self.pil_image = None
        self.img_meta = None
        self.anim_seq = []
        self._node_images = {}
        self._node_radius = {}
        self.anim_idx = 0
        self.after_id = None
        self._prev_node = None
        self.zoom_scale = 1.0
        
        self.mode_var = tk.StringVar(value='text')
        self.traversal_var = tk.StringVar(value='Pre-order')
        self.speed_var = tk.IntVar(value=450)
        
        self._set_style_hooks()
        self._build_layout_grid()

    def _set_style_hooks(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        F, FM = self.FONT_UI, self.FONT_MONO

        style.configure('.', background=self.BG_LIGHT, foreground=self.DARK_MAIN, font=(F, 11))
        style.configure('TFrame', background=self.BG_LIGHT)
        style.configure('Panel.TFrame', background=self.PANEL_WHITE)
        style.configure('Surface.TFrame', background=self.BG_SURFACE)

        style.configure('TNotebook', background=self.BG_LIGHT, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.BG_SURFACE, foreground=self.TEXT_MUTED,
                        padding=[26, 12], font=(F, 11, 'bold'), borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', self.DARK_MAIN)],
                                   foreground=[('selected', self.BG_LIGHT)])

        style.configure('TButton', background=self.BG_SURFACE, foreground=self.DARK_MAIN,
                        borderwidth=0, focuscolor='none', padding=11, font=(F, 11))
        style.map('TButton', background=[('active', self.ACCENT_LIGHT), ('pressed', self.ACCENT_LIGHT)],
                             foreground=[('active', self.DARK_MAIN)],
                             relief=[('pressed', 'flat'), ('!pressed', 'flat')])

        style.configure('Action.TButton', background=self.GLOW_ORANGE, foreground='#ffffff',
                        borderwidth=0, padding=15, font=(F, 11, 'bold'))
        style.map('Action.TButton', background=[('active', self.DARK_MAIN), ('pressed', self.DARK_MAIN)])

        style.configure('TRadiobutton', background=self.PANEL_WHITE, foreground=self.DARK_MAIN, focuscolor='none', font=(F, 11))
        style.map('TRadiobutton', background=[('active', self.PANEL_WHITE)], foreground=[('active', self.GLOW_ORANGE)])

        style.configure('TLabel', background=self.PANEL_WHITE, foreground=self.DARK_MAIN, font=(F, 11))
        style.configure('Heading.TLabel', background=self.PANEL_WHITE, foreground=self.TEXT_MUTED, font=(F, 9, 'bold'))
        style.configure('Value.TLabel', background=self.PANEL_WHITE, foreground=self.DARK_MAIN, font=(F, 15, 'bold'))

        style.configure('TCombobox', fieldbackground=self.BG_LIGHT, background=self.PANEL_WHITE,
                        foreground=self.DARK_MAIN, borderwidth=0, arrowsize=14, padding=8)
        style.map('TCombobox', fieldbackground=[('readonly', self.BG_LIGHT)])

        style.configure('TScale', background=self.PANEL_WHITE, troughcolor=self.BG_SURFACE, borderwidth=0)

        style.configure('Vertical.TScrollbar', background=self.BG_SURFACE, troughcolor=self.BG_LIGHT,
                        borderwidth=0, arrowsize=12, width=12)
        style.configure('Horizontal.TScrollbar', background=self.BG_SURFACE, troughcolor=self.BG_LIGHT,
                        borderwidth=0, arrowsize=12, width=12)

    def _build_layout_grid(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.tab_main = ttk.Frame(self.notebook)
        self.tab_visualizer = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_main, text=" Compression Dashboard ")
        self.notebook.add(self.tab_visualizer, text=" Graph & Traversal Engine ")
        
        self._build_main_tab_layout()
        self._build_visualizer_tab_layout()

    def _build_main_tab_layout(self):
        t = self.tab_main
        t.columnconfigure(1, weight=1)
        t.rowconfigure(0, weight=1)
        
        ctrl_panel = ttk.Frame(t, style='Panel.TFrame', width=380)
        ctrl_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 20))
        ctrl_panel.grid_propagate(False)
        
        tk.Label(ctrl_panel, text="HUFFMAN OPTIMIZATION", bg=self.PANEL_WHITE, fg=self.DARK_MAIN, 
                 font=(self.FONT_UI, 14, 'bold')).pack(anchor='w', padx=24, pady=(28, 20))
        
        mode_f = ttk.Frame(ctrl_panel, style='Panel.TFrame')
        mode_f.pack(fill='x', padx=24, pady=8)
        ttk.Radiobutton(mode_f, text="String Buffer", variable=self.mode_var, value='text').pack(side='left', padx=(0, 20))
        ttk.Radiobutton(mode_f, text="Image Matrices", variable=self.mode_var, value='image').pack(side='left')
        
        tk.Label(ctrl_panel, text="TEXT INPUT BUFFER", bg=self.PANEL_WHITE, fg=self.ACCENT_MED, font=(self.FONT_UI, 9, 'bold')).pack(anchor='w', padx=24, pady=(20, 6))
        self.text_widget = tk.Text(ctrl_panel, height=7, bg=self.BG_LIGHT, fg=self.DARK_MAIN, insertbackground=self.DARK_MAIN, 
                                   borderwidth=0, highlightthickness=1, highlightbackground=self.BG_SURFACE, 
                                   highlightcolor=self.GLOW_ORANGE, wrap='word', font=(self.FONT_UI, 11), padx=10, pady=10)
        self.text_widget.pack(fill='x', padx=24, pady=4)
        self.text_widget.insert('1.0', "the quick brown fox jumps over the lazy dog")
        ttk.Button(ctrl_panel, text="Import Text File", command=self.load_text_file).pack(fill='x', padx=24, pady=6)
        
        tk.Label(ctrl_panel, text="IMAGE STREAM STORAGE", bg=self.PANEL_WHITE, fg=self.ACCENT_MED, font=(self.FONT_UI, 9, 'bold')).pack(anchor='w', padx=24, pady=(20, 6))
        ttk.Button(ctrl_panel, text="Import Image Bitstream", command=self.load_image).pack(fill='x', padx=24, pady=6)
        
        ttk.Button(ctrl_panel, text="Clear Allocation Space", command=self.reset_all).pack(side='bottom', fill='x', padx=24, pady=(0, 28))
        ttk.Button(ctrl_panel, text="Execute Compression Pipeline", style='Action.TButton', command=self.generate_and_compress).pack(side='bottom', fill='x', padx=24, pady=(0, 16))

        display_space = ttk.Frame(t)
        display_space.grid(row=0, column=1, sticky='nsew')
        display_space.columnconfigure(0, weight=1)
        display_space.rowconfigure(0, weight=0) 
        display_space.rowconfigure(1, weight=1) 

        af = ttk.Frame(display_space, style='Panel.TFrame')
        af.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        self.analytics_vars = {k: tk.StringVar(value='—') for k in ['orig', 'comp', 'ratio', 'src_ent', 'avg_len', 'enc_ent', 'ok']}
        metrics = [
            ('Source Size', 'orig'), ('Compressed Size', 'comp'), ('Optimization Ratio', 'ratio'),
            ('Shannon Entropy H(X)', 'src_ent'), ('Avg Prefix Code Length', 'avg_len'),
            ('Bitstream Entropy State', 'enc_ent'), ('Structural Parity', 'ok')
        ]
        
        grid_wrapper = ttk.Frame(af, style='Panel.TFrame')
        grid_wrapper.pack(fill='x', padx=24, pady=15)
        cols_per_row = 4
        for c in range(cols_per_row):
            grid_wrapper.columnconfigure(c, weight=1)
        for i, (label, key) in enumerate(metrics):
            col = i % cols_per_row
            row_base = (i // cols_per_row) * 2
            top_pad = 0 if row_base == 0 else 22
            ttk.Label(grid_wrapper, text=label, style='Heading.TLabel').grid(
                row=row_base, column=col, sticky='w', padx=(10, 14), pady=(top_pad, 0))
            ttk.Label(grid_wrapper, textvariable=self.analytics_vars[key], style='Value.TLabel').grid(
                row=row_base + 1, column=col, sticky='w', padx=(10, 14), pady=(6, 0))

        # Horizontal Data Comparison Progress Bar Area
        self.bar_canvas = tk.Canvas(af, height=45, bg=self.PANEL_WHITE, highlightthickness=0)
        self.bar_canvas.pack(fill='x', padx=34, pady=(0, 15))
        self._draw_empty_comparison_bar()

        self.preview_panel = ttk.Frame(display_space, style='Panel.TFrame')
        self.preview_panel.grid(row=1, column=0, sticky='nsew')
        self.preview_panel.columnconfigure(0, weight=1)
        self.preview_panel.columnconfigure(1, weight=1)
        self.preview_panel.rowconfigure(0, weight=1)

        self.orig_label = tk.Label(self.preview_panel, text="[RAW SOURCE VIEWPORT]", bg=self.BG_LIGHT, fg=self.DARK_MAIN, font=(self.FONT_UI, 12, 'bold'))
        self.orig_label.grid(row=0, column=0, sticky='nsew', padx=24, pady=24)
        
        self.recon_label = tk.Label(self.preview_panel, text="[RECONSTRUCTED OUTPUT BITSTREAM]", bg=self.BG_LIGHT, fg=self.DARK_MAIN, font=(self.FONT_UI, 12, 'bold'))
        self.recon_label.grid(row=0, column=1, sticky='nsew', padx=(0, 24), pady=24)

    def _draw_empty_comparison_bar(self):
        self.bar_canvas.delete('all')
        self.bar_canvas.create_text(20, 22, text="Awaiting execution pipeline to calculate footprint scaling metrics...", fill=self.TEXT_MUTED, anchor='w', font=(self.FONT_UI, 11, 'italic'))

    def _update_comparison_bar(self, orig_bytes, comp_bytes):
        self.bar_canvas.delete('all')
        self.update_idletasks()
        w = self.bar_canvas.winfo_width() - 40
        if w < 100: w = 600
        
        h = 24
        x0, y0 = 20, 10
        
        self.bar_canvas.create_rectangle(x0, y0, x0 + w, y0 + h, fill='#E5DDD3', outline='', width=0)
        ratio = comp_bytes / orig_bytes if orig_bytes else 0
        comp_w = int(w * min(ratio, 1.0))
        
        # Fixed coordinate sequence here
        if comp_w > 0:
            self.bar_canvas.create_rectangle(x0, y0, x0 + comp_w, y0 + h, fill=self.ACCENT_MED, outline='', width=0)
            
        saved_pct = (1.0 - ratio) * 100
        self.bar_canvas.create_text(x0 + 12, y0 + 12, text=f"Compressed Frame Profile ({ratio*100:.1f}%)", fill='#ffffff', anchor='w', font=(self.FONT_UI, 10, 'bold'))
        self.bar_canvas.create_text(x0 + w - 12, y0 + 12, text=f"Data Saved: {saved_pct:.1f}%", fill=self.DARK_MAIN, anchor='e', font=(self.FONT_UI, 10, 'bold'))
    def _build_visualizer_tab_layout(self):
        v = self.tab_visualizer
        v.columnconfigure(0, weight=1)
        v.rowconfigure(0, weight=1)

        paned_window = tk.PanedWindow(v, orient='vertical', bd=0, sashwidth=6, bg=self.BG_SURFACE)
        paned_window.grid(row=0, column=0, sticky='nsew')

        f_canvas = ttk.Frame(paned_window)
        f_canvas.rowconfigure(0, weight=1)
        f_canvas.columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(f_canvas, bg=self.PANEL_WHITE, highlightthickness=1, highlightbackground=self.ACCENT_LIGHT)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        
        v_scroll = ttk.Scrollbar(f_canvas, orient='vertical', command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll = ttk.Scrollbar(f_canvas, orient='horizontal', command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.canvas.bind('<MouseWheel>', self._handle_scroll)
        self.canvas.bind('<Control-MouseWheel>', self._handle_zoom)
        
        paned_window.add(f_canvas, minsize=400, stretch='always')

        f_lower_deck = ttk.Frame(paned_window)
        f_lower_deck.columnconfigure(0, weight=1)
        f_lower_deck.columnconfigure(1, weight=2)
        f_lower_deck.rowconfigure(0, weight=1)

        t_ctrl = ttk.Frame(f_lower_deck, style='Panel.TFrame')
        t_ctrl.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=(10, 0))

        tk.Label(t_ctrl, text="GRAPH TRAVERSAL SIMULATOR", bg=self.PANEL_WHITE, fg=self.DARK_MAIN, font=(self.FONT_UI, 12, 'bold')).pack(anchor='w', padx=24, pady=(16, 6))
        
        self.traversal_cb = ttk.Combobox(t_ctrl, textvariable=self.traversal_var, state='readonly', values=['Pre-order', 'In-order', 'Post-order', 'Level-order'])
        self.traversal_cb.option_add('*TCombobox*Listbox.font', (self.FONT_UI, 11))
        self.traversal_cb.pack(fill='x', padx=24, pady=4)
        
        tk.Label(t_ctrl, text="ANIMATION STEP DELAY", bg=self.PANEL_WHITE, fg=self.DARK_MAIN, font=(self.FONT_UI, 9, 'bold')).pack(anchor='w', padx=24, pady=(12, 2))
        ttk.Scale(t_ctrl, from_=50, to=1200, variable=self.speed_var, orient='horizontal').pack(fill='x', padx=24, pady=4)
        
        ttk.Button(t_ctrl, text="Simulate Graph Traversal Pipeline", style='Action.TButton', command=self.animate_traversal).pack(fill='x', padx=24, pady=(16, 16))

        cf = ttk.Frame(f_lower_deck, style='Panel.TFrame')
        cf.grid(row=0, column=1, sticky='nsew', padx=(10, 0), pady=(10, 0))
        cf.rowconfigure(0, weight=1)
        cf.columnconfigure(0, weight=1)
        
        self.console = tk.Text(cf, bg=self.BG_LIGHT, fg=self.DARK_MAIN, font=('Courier New', 11), 
                               borderwidth=0, highlightthickness=0, state='disabled', wrap='none', padx=14, pady=14)
        self.console.grid(row=0, column=0, sticky='nsew')
        
        paned_window.add(f_lower_deck, minsize=180, stretch='never')

    def _handle_scroll(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), 'units')

    def _handle_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        new_zoom = self.zoom_scale * factor
        if 0.3 <= new_zoom <= 4.0:
            self.zoom_scale = new_zoom
            self.canvas.scale('all', event.x, event.y, factor, factor)
            bbox = self.canvas.bbox('all')
            if bbox:
                self.canvas.configure(scrollregion=(bbox[0]-50, bbox[1]-50, bbox[2]+50, bbox[3]+50))

    def load_text_file(self):
        path = filedialog.askopenfilename(filetypes=[('Text Blueprint', '*.txt'), ('All Files', '*.*')])
        if not path: return
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', content)
        self.mode_var.set('text')

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[('Image Bitstream', '*.png *.jpg *.jpeg *.bmp *.gif')])
        if not path: return
        img = Image.open(path).convert('RGB')
        self.pil_image = img
        
        self.update_idletasks()
        w = max(380, self.orig_label.winfo_width())
        h = max(300, self.orig_label.winfo_height())
        
        display_img = img.copy()
        display_img.thumbnail((w, h))
        self.orig_thumb = ImageTk.PhotoImage(display_img)
        self.orig_label.config(image=self.orig_thumb, text='')
        self.recon_label.config(image='', text='[AWAITING PIPELINE COMPRESSION]')
        self.mode_var.set('image')

    def count_leaves(self, node):
        if node is None: return 0
        if node.is_leaf(): return 1
        return self.count_leaves(node.left) + self.count_leaves(node.right)

    def get_max_depth(self, node):
        if node is None: return 0
        return 1 + max(self.get_max_depth(node.left), self.get_max_depth(node.right))

    def export_tree_visualization(self, target_dir):
        """Calculates explicit leaf-anchored non-overlapping spacing and uses the original palette."""
        if not self.tree_root: return
        
        num_leaves = self.count_leaves(self.tree_root)
        max_depth = self.get_max_depth(self.tree_root)
        
        # Dynamically scaled canvas boundaries to accommodate large structures comfortably
        fig_width = max(16, int(num_leaves * 0.55))
        fig_height = max(10, int(max_depth * 1.5))
        
        G = nx.DiGraph()
        labels = {}
        pos = {}
        node_colors = []

        # Palette matched to the live app UI for visual consistency between
        # the on-screen canvas and the exported PNG artifact.
        ORIG_INTERNAL_BLUE = self.ACCENT_MED    # Deep Slate Blue
        ORIG_LEAF_GREEN    = self.LEAF_MUTED    # Terracotta
        ORIG_BIT_RED       = self.GLOW_ORANGE   # Vivid Orange
        
        # Sequentially map leaf items to establish an absolute coordinate timeline spacing
        leaf_x_counter = [0]
        
        def calculate_mp_positions(node, depth=0):
            if node is None: return None
            
            node_id = id(node)
            if node.is_leaf():
                x = leaf_x_counter[0]
                leaf_x_counter[0] += 1
                pos[node_id] = (x, -depth)
                lbl = self.node_label(node)
                labels[node_id] = f"{lbl}\n({node.freq})"
                node_colors.append(ORIG_LEAF_GREEN)
            else:
                left_id = calculate_mp_positions(node.left, depth + 1)
                right_id = calculate_mp_positions(node.right, depth + 1)
                
                # Perfect alignment over actual child components eliminates structural shifting
                xs = []
                if node.left: xs.append(pos[id(node.left)][0])
                if node.right: xs.append(pos[id(node.right)][0])
                
                x = sum(xs) / len(xs) if xs else leaf_x_counter[0]
                pos[node_id] = (x, -depth)
                labels[node_id] = str(node.freq)
                node_colors.append(ORIG_INTERNAL_BLUE)
                
                if node.left: G.add_edge(node_id, left_id, bit='0')
                if node.right: G.add_edge(node_id, right_id, bit='1')
                
            return node_id

        calculate_mp_positions(self.tree_root)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor(self.BG_LIGHT)
        ax.set_facecolor(self.BG_LIGHT)

        mode_title = "Image Stream Matrix" if self.mode_var.get() == 'image' else "sample.txt"
        ax.set_title(f"Huffman Tree Topology Map [{mode_title}]", fontsize=16, fontweight='bold',
                     pad=32, color=self.DARK_MAIN, fontname=self.FONT_UI)
        ax.axis('off')

        dynamic_node_size = max(600, min(1500, int(45000 / (num_leaves + 5))))
        dynamic_font_size = max(6, min(10, int(220 / (max_depth + 10))))

        # Gently curved connectors (instead of rigid straight edges) read as
        # softer and more polished, and reduce visual clutter in dense trees.
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            arrow = FancyArrowPatch((x0, y0), (x1, y1), connectionstyle="arc3,rad=0.0",
                                     arrowstyle='-', color='#BDB2A0', linewidth=1.4,
                                     zorder=1, capstyle='round')
            ax.add_patch(arrow)

        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=dynamic_node_size, node_color=node_colors,
                               edgecolors=self.DARK_MAIN, linewidths=1.2, alpha=0.96)
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=dynamic_font_size,
                                font_color='#FFFFFF', font_weight='bold', font_family=self.FONT_UI)

        edge_labels = nx.get_edge_attributes(G, 'bit')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=dynamic_font_size + 3,
                                     font_color=ORIG_BIT_RED, font_weight='bold', font_family=self.FONT_UI, rotate=False,
                                     bbox=dict(facecolor=self.BG_LIGHT, edgecolor='none', alpha=0.9, pad=1))

        save_path = os.path.join(target_dir, "huffman_tree_topology.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.BG_LIGHT)
        plt.close()

    def write_traversal_audit_log(self, text_dir, codes):
        """Generates a tracking text file containing token bits mapped against every topological path strategy."""
        if not self.tree_root: return
        
        # Populate operational prefix string references onto all active nodes
        self.build_paths(self.tree_root)
        
        log_path = os.path.join(text_dir, "compressed_bitstream_dictionary.txt")
        with open(log_path, "w", encoding="utf-8") as audit_file:
            audit_file.write("=====================================================================\n")
            audit_file.write("            HUFFMAN TOPOLOGY PIPELINE TRAVERSAL AUDIT LOG            \n")
            audit_file.write("=====================================================================\n\n")
            
            # --- SECTION 1: GLOBAL BINARY RECOGNITION DICTIONARY ---
            audit_file.write("--- SECTION 1: VARIABLE-LENGTH PREFIX TOKENS DICTIONARY ---\n")
            audit_file.write(f"{'Value/Char':<15} | {'Frequency':<10} | {'Assigned Binary Bitstream String'}\n")
            audit_file.write("-" * 65 + "\n")
            
            # Extract list of all leaves sequentially
            raw_nodes = []
            self.collect_nodes(self.tree_root, raw_nodes)
            leaf_nodes = [n for n in raw_nodes if n.is_leaf()]
            # Sort for orderly scannability
            leaf_nodes.sort(key=lambda n: n.freq, reverse=True)
            
            for leaf in leaf_nodes:
                lbl = self.node_label(leaf)
                # Safeguard string wrapping visibility for plain whitespaces/returns
                if lbl == " ": lbl = "' '"
                elif lbl == "\n": lbl = "'\\n'"
                elif lbl == "\t": lbl = "'\\t'"
                
                bit_sequence = codes.get(leaf.val, leaf.path)
                audit_file.write(f"{lbl:<15} | {leaf.freq:<10} | {bit_sequence}\n")
            
            audit_file.write("\n" + "="*65 + "\n\n")
            
            # --- SECTION 2: THE 4 STRUCTURAL TRAVERSAL ARCHITECTURES ---
            audit_file.write("--- SECTION 2: TOPOLOGICAL TRAVERSAL STRUCTURAL MAPPING ---\n\n")
            
            traversal_modes = [
                ('Pre-order Traversal Sequence (Root -> Left -> Right)', 'pre'),
                ('In-order Traversal Sequence (Left -> Root -> Right)', 'in'),
                ('Post-order Traversal Sequence (Left -> Right -> Root)', 'post'),
                ('Level-order Traversal Sequence (Breadth-First Search)', 'level')
            ]
            
            for title, key in traversal_modes:
                audit_file.write(f"## {title}\n")
                audit_file.write("-" * 65 + "\n")
                audit_file.write(f"{'Index':<6} | {'Node Identity/Type':<22} | {'Weight (Freq)':<14} | {'Path Track Code'}\n")
                audit_file.write("-" * 65 + "\n")
                
                sequence = self.traversal_sequence(key)
                for index, node in enumerate(sequence):
                    is_leaf_node = node.is_leaf()
                    
                    if is_leaf_node:
                        lbl = f"Leaf ('{self.node_label(node)}')"
                        if "\\n" in lbl or "\\t" in lbl:
                            lbl = f"Leaf ({self.node_label(node)})"
                    else:
                        lbl = "Internal Node Structure"
                        
                    path_str = node.path if node.path else "ROOT"
                    audit_file.write(f"{index+1:<6} | {lbl:<22} | {node.freq:<14} | {path_str}\n")
                
                audit_file.write("\n" + "."*65 + "\n\n")

    def generate_and_compress(self):
        self._cancel_animation()
        mode = self.mode_var.get()
        
        base_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "huffman_exports")
        text_dir  = os.path.join(base_dir, "text_pipeline")
        image_dir = os.path.join(base_dir, "image_pipeline")
        
        os.makedirs(text_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)
        
        try:
            if mode == 'text':
                raw_text = self.text_widget.get('1.0', 'end-1c')
                data = raw_text.encode('utf-8')
                if not data:
                    messagebox.showwarning('Null Space Mapping', 'Text buffer frame holds no context.')
                    return
                self.img_meta = None
                target_dir = text_dir
                with open(os.path.join(text_dir, "uncompressed_source.txt"), "w", encoding="utf-8") as f:
                    f.write(raw_text)
            else:
                if self.pil_image is None:
                    messagebox.showwarning('Null Memory Address', 'No valid image object bound to register.')
                    return
                data = self.pil_image.tobytes()
                self.img_meta = (self.pil_image.mode, self.pil_image.size)
                target_dir = image_dir
                self.pil_image.save(os.path.join(image_dir, "uncompressed_source.png"))
                
            freqs = collections.Counter(data)
            self.tree_root = build_huffman(freqs)
            codes = gen_codes(self.tree_root)
            encoded, pad, bits = encode_bytes(data, codes)
            decoded = decode_bits(bits, self.tree_root)
            
            ok = (decoded == data)
            n = len(data)
            
            src_kb  = n / 1024.0
            comp_kb = len(encoded) / 1024.0
            
            ratio = 100 * (1 - len(encoded) / n) if n else 0
            src_ent = shannon_entropy(data)
            avg_len = sum(len(codes[b]) * c for b, c in freqs.items()) / n
            enc_ent = bit_entropy(bits)
            
            self.analytics_vars['orig'].set(f"{src_kb:.2f} KB")
            self.analytics_vars['comp'].set(f"{comp_kb:.2f} KB")
            self.analytics_vars['ratio'].set(f"{ratio:.1f}% Saved")
            self.analytics_vars['src_ent'].set(f"{src_ent:.3f} b/sym")
            self.analytics_vars['avg_len'].set(f"{avg_len:.3f} b/sym")
            self.analytics_vars['enc_ent'].set(f"{enc_ent:.3f}")
            self.analytics_vars['ok'].set("PASS" if ok else "FAIL")
            
            self._update_comparison_bar(n, len(encoded))
            
            self.zoom_scale = 1.0
            self.draw_tree()
            
            with open(os.path.join(target_dir, "compressed_payload.bin"), "wb") as f:
                f.write(encoded)
            
            self.export_tree_visualization(target_dir)
            
            if mode == 'text':
                with open(os.path.join(text_dir, "reconstructed_output.txt"), "w", encoding="utf-8") as f:
                    f.write(decoded.decode('utf-8', errors='replace'))
                
                # EXECUTE DYNAMIC AUDIT TRAVERSAL MAPPER FOR STRING MODE
                self.write_traversal_audit_log(text_dir, codes)
                
                self.orig_label.config(image='', text=f"[Text Buffer Mode Active]\nSource Size: {src_kb:.3f} KB")
                self.recon_label.config(image='', text=f"[Verification Output Match]\nCompressed Size: {comp_kb:.3f} KB")
            else:
                recon_img = Image.frombytes(self.img_meta[0], self.img_meta[1], decoded)
                recon_img.save(os.path.join(image_dir, "reconstructed_output.png"))
                
                self.update_idletasks()
                w = max(380, self.recon_label.winfo_width())
                h = max(300, self.recon_label.winfo_height())
                
                display_recon = recon_img.copy()
                display_recon.thumbnail((w, h))
                self.recon_thumb = ImageTk.PhotoImage(display_recon)
                self.recon_label.config(image=self.recon_thumb, text='')
                
            self._log_clear()
            self.console.config(state='normal')
            self.console.insert('end', f">> Pipeline execution success. Artifacts isolated cleanly inside:\n    {target_dir}\n")
            if mode == 'text':
                self.console.insert('end', f">> Audit trace saved: 'compressed_bitstream_dictionary.txt'\n")
            self.console.insert('end', f">> Clear non-overlapping layout created as 'huffman_tree_topology.png'\n")
            self.console.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror('Execution Fault', str(e))

    def reset_all(self):
        self._cancel_animation()
        self.tree_root = None
        self.pil_image = None
        self.zoom_scale = 1.0
        self.canvas.delete('all')
        self.text_widget.delete('1.0', 'end')
        self.orig_label.config(image='', text='[RAW SOURCE VIEWPORT]')
        self.recon_label.config(image='', text='[RECONSTRUCTED OUTPUT BITSTREAM]')
        for v in self.analytics_vars.values():
            v.set('—')
        self._draw_empty_comparison_bar()
        self._log_clear()

    def assign_positions(self, root):
        leaves = []
        def collect(n):
            if n.is_leaf(): leaves.append(n)
            else:
                if n.left: collect(n.left)
                if n.right: collect(n.right)
        collect(root)

        # Pick spacing first, then size nodes to comfortably fit inside that
        # spacing (with a gap) — this is what actually prevents circles from
        # visually overlapping, since the earlier fixed radius didn't scale
        # down for wide/leaf-heavy trees.
        spacing = max(72, min(150, int(6000 / (len(leaves) + 1))))
        self._render_radius = max(14, min(30, (spacing - 26) // 2))

        for i, leaf in enumerate(leaves):
            leaf.x = 80 + i * spacing

        level_gap = max(110, int(self._render_radius * 3.6))

        def set_pos(n, depth):
            n.depth = depth
            n.y = 100 + depth * level_gap
            if not n.is_leaf():
                if n.left: set_pos(n.left, depth + 1)
                if n.right: set_pos(n.right, depth + 1)
                xs = [ch.x for ch in (n.left, n.right) if ch]
                n.x = sum(xs) / len(xs)
        set_pos(root, 0)

    def collect_nodes(self, node, acc):
        if node is None: return
        acc.append(node)
        if node.left: self.collect_nodes(node.left, acc)
        if node.right: self.collect_nodes(node.right, acc)

    def node_label(self, node):
        v = node.val
        if self.mode_var.get() == 'text':
            try:
                ch = chr(v)
                return repr(ch)[1:-1] if not ch.isprintable() else ch
            except Exception:
                return str(v)
        return f"0x{v:02X}"

    # ---- Anti-aliased image helpers (supersample in PIL, downscale for crisp edges) ----

    def _make_node_image(self, radius, fill_hex, fill_hex_light, outline_hex, supersample=4):
        """Render a soft-shadowed, gradient-filled circle at high resolution then
        downsample for a crisp, smooth (anti-aliased) node — Tk ovals alone are jagged."""
        pad = 8
        size = (radius + pad) * 2
        big = size * supersample
        img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx = cy = big // 2
        r = radius * supersample
        shadow_off = 3 * supersample

        # Soft drop shadow
        shadow = Image.new('RGBA', (big, big), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.ellipse([cx - r + shadow_off, cy - r + shadow_off + 4 * supersample,
                       cx + r + shadow_off, cy + r + shadow_off + 4 * supersample],
                      fill=(0, 0, 0, 70))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6 * supersample // 4))
        img = Image.alpha_composite(img, shadow)
        draw = ImageDraw.Draw(img)

        # Subtle vertical gradient fill for depth
        grad = Image.new('L', (1, big), 0)
        for y in range(big):
            t = y / big
            grad.putpixel((0, y), int(255 * (0.15 + 0.85 * (1 - t * 0.5))))
        grad = grad.resize((big, big))
        top_rgb = tuple(int(c, 16) for c in (fill_hex_light[1:3], fill_hex_light[3:5], fill_hex_light[5:7]))
        bot_rgb = tuple(int(c, 16) for c in (fill_hex[1:3], fill_hex[3:5], fill_hex[5:7]))
        gradient_img = Image.new('RGBA', (big, big))
        for y in range(big):
            t = y / big
            rr = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
            gg = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
            bb = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
            for x in range(big):
                gradient_img.putpixel((x, y), (rr, gg, bb, 255))

        mask = Image.new('L', (big, big), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        img.paste(gradient_img, (0, 0), mask)

        draw = ImageDraw.Draw(img)
        outline_w = max(1, 2 * supersample)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=outline_hex, width=outline_w)

        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _make_pulse_image(self, radius, fill_hex, supersample=4):
        """A brighter, glowing variant used for the active traversal node."""
        top = self.GLOW_TRAVERSE
        return self._make_node_image(radius, fill_hex, '#57B87C', top, supersample=supersample)

    def draw_tree(self):
        c = self.canvas
        c.delete('all')
        root = self.tree_root
        if root is None: return

        self.assign_positions(root)
        self.node_list = []
        self.collect_nodes(root, self.node_list)
        self._node_images = {}  # keep PhotoImage refs alive
        self._node_radius = {}

        def draw_edges(n):
            if n.left:
                c.create_line(n.x, n.y, n.left.x, n.left.y, fill='#B9AF9E', width=2.2,
                              capstyle='round')
                c.create_text((n.x + n.left.x) / 2 - 12, (n.y + n.left.y) / 2,
                              text='0', fill=self.GLOW_ORANGE, font=(self.FONT_UI, 11, 'bold'))
                draw_edges(n.left)
            if n.right:
                c.create_line(n.x, n.y, n.right.x, n.right.y, fill='#B9AF9E', width=2.2,
                              capstyle='round')
                c.create_text((n.x + n.right.x) / 2 + 12, (n.y + n.right.y) / 2,
                              text='1', fill=self.GLOW_ORANGE, font=(self.FONT_UI, 11, 'bold'))
                draw_edges(n.right)

        draw_edges(root)

        r = getattr(self, '_render_radius', 30)
        for node in self.node_list:
            leaf = node.is_leaf()
            fill_color = self.LEAF_MUTED if leaf else self.ACCENT_MED
            fill_light = self.LEAF_MUTED_LT if leaf else self.ACCENT_MED_LT
            img = self._make_node_image(r, fill_color, fill_light, self.DARK_MAIN)
            self._node_images[id(node)] = img
            node.oid = c.create_image(node.x, node.y, image=img)
            self._node_radius[id(node)] = r

            if node is root:
                # Halo ring makes the root unmistakable even in a dense tree
                c.create_oval(node.x - r - 7, node.y - r - 7, node.x + r + 7, node.y + r + 7,
                              outline=self.GLOW_ORANGE, width=2.4)
                c.create_text(node.x, node.y - r - 20, text='ROOT', fill=self.GLOW_ORANGE,
                              font=(self.FONT_UI, 10, 'bold'))

            lbl = self.node_label(node) if leaf else str(node.freq)
            c.create_text(node.x, node.y, text=lbl, fill='#ffffff', font=(self.FONT_UI, 10, 'bold'))
            if leaf:
                c.create_text(node.x, node.y + r + 16, text=f"f:{node.freq}", fill=self.TEXT_MUTED, font=(self.FONT_UI, 9, 'italic'))

        bbox = c.bbox('all')
        if bbox:
            c.configure(scrollregion=(bbox[0]-80, bbox[1]-80, bbox[2]+80, bbox[3]+80))

    def build_paths(self, node, prefix=''):
        if node is None: return
        node.path = prefix
        if node.left: self.build_paths(node.left, prefix + '0')
        if node.right: self.build_paths(node.right, prefix + '1')

    def traversal_sequence(self, mode):
        root = self.tree_root
        seq = []
        if root is None: return seq
        
        if mode == 'pre':
            def rec(n):
                if n: seq.append(n); rec(n.left); rec(n.right)
            rec(root)
        elif mode == 'in':
            def rec(n):
                if n: rec(n.left); seq.append(n); rec(n.right)
            rec(root)
        elif mode == 'post':
            def rec(n):
                if n: rec(n.left); rec(n.right); seq.append(n)
            rec(root)
        else:
            q = deque([root])
            while q:
                n = q.popleft()
                seq.append(n)
                if n.left: q.append(n.left)
                if n.right: q.append(n.right)
        return seq

    def animate_traversal(self):
        if self.tree_root is None:
            messagebox.showwarning('Null Core Data Matrix', 'Generate compression dataset mapping inside Dashboard tab first.')
            return
        
        self.notebook.select(self.tab_visualizer)
        self._cancel_animation()
        self.build_paths(self.tree_root)
        mapping = {'Pre-order': 'pre', 'In-order': 'in', 'Post-order': 'post', 'Level-order': 'level'}
        self.anim_seq = self.traversal_sequence(mapping[self.traversal_var.get()])
        self.anim_idx = 0
        self._prev_node = None
        self._log_clear()
        self._animate_step()

    def _restore_node_image(self, node):
        """Swap a node's canvas image back to its resting-state render."""
        img = self._node_images.get(id(node))
        if img is not None:
            self.canvas.itemconfig(node.oid, image=img)

    def _activate_node_image(self, node):
        """Swap a node's canvas image to a glowing 'active' render for the traversal cursor."""
        r = self._node_radius.get(id(node), 30)
        active_img = self._make_pulse_image(r, self.GLOW_TRAVERSE)
        self._node_images[('active', id(node))] = active_img  # keep alive
        self.canvas.itemconfig(node.oid, image=active_img)

    def _animate_step(self):
        if self.anim_idx >= len(self.anim_seq):
            if self._prev_node:
                self._restore_node_image(self._prev_node)
            self.after_id = None
            return

        node = self.anim_seq[self.anim_idx]
        if self._prev_node:
            self._restore_node_image(self._prev_node)

        self._activate_node_image(node)

        lbl = self.node_label(node) if node.is_leaf() else f"internal({node.freq})"
        path_str = node.path if node.path else 'ROOT'
        log_line = f"[{self.anim_idx + 1:03d}] Node: {lbl!s:<14} Freq: {node.freq:<6} Bit Path Trace: {path_str}\n"
        
        self.console.config(state='normal')
        self.console.insert('end', log_line)
        self.console.see('end')
        self.console.config(state='disabled')
        
        self._prev_node = node
        self.anim_idx += 1
        self.after_id = self.after(self.speed_var.get(), self._animate_step)

    def _cancel_animation(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self._prev_node = None

    def _log_clear(self):
        self.console.config(state='normal')
        self.console.delete('1.0', 'end')
        self.console.config(state='disabled')

if __name__ == "__main__":
    app = HuffmanApp()
    app.mainloop()