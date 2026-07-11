# Huffman Space Engine

A desktop GUI application (built with Tkinter) that demonstrates **Huffman coding** for lossless compression of both text and images. It visualizes the generated Huffman tree, animates tree traversals (pre-order, in-order, post-order, level-order), and reports compression statistics such as entropy and compression ratio.

## Features

- **Text & Image Compression** — Compress a text buffer or an imported image using a Huffman-coded binary tree built from byte frequencies.
- **Lossless Verification** — Decodes the compressed bitstream back to the original data and checks for an exact match (structural parity check).
- **Compression Analytics** — Displays source size, compressed size, compression ratio, Shannon entropy, average code length, and encoded bitstream entropy.
- **Interactive Tree Visualizer** — Renders the Huffman tree on a zoomable/scrollable canvas.
- **Traversal Animation** — Step-by-step animated walk of the tree (Pre-order, In-order, Post-order, Level-order) with an adjustable speed control and a live console log.
- **Exported Artifacts** — Each run writes the compressed payload, reconstructed output, a rendered tree topology image (via Matplotlib/NetworkX), and (for text) a full traversal/bitstream audit log.

## Project Structure

```
DSA project/
├── main.py                     # Entry point - launches the application
├── app.py                      # Tkinter GUI, visualization, and pipeline orchestration
├── huffman.py                  # Core Huffman coding algorithm (build, encode, decode, entropy)
├── node.py                     # Node class for the Huffman binary tree
├── sample pictures and txt/    # Sample input files for testing
└── huffman_exports/            # Auto-generated output artifacts (created on first run)
    ├── text_pipeline/
    │   ├── uncompressed_source.txt
    │   ├── reconstructed_output.txt
    │   ├── compressed_payload.bin
    │   ├── compressed_bitstream_dictionary.txt
    │   └── huffman_tree_topology.png
    └── image_pipeline/
        ├── uncompressed_source.png
        ├── reconstructed_output.png
        ├── compressed_payload.bin
        └── huffman_tree_topology.png
```

## Requirements

- Python 3.9+
- Tkinter (ships with most standard Python installations; on Linux you may need to install it separately, e.g. `sudo apt install python3-tk`)
- Dependencies listed in `requirements.txt`:
  - `Pillow` — image loading, thumbnails, and node rendering
  - `matplotlib` — tree topology export images
  - `networkx` — graph layout for the exported tree diagram

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd "DSA project"
   ```
2. (Optional but recommended) create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate    # on Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application from the project directory:

```bash
python main.py
```

**Compression Dashboard tab**
1. Choose input mode: **String Buffer** (text) or **Image Matrices** (image).
2. Type/paste text, or import a `.txt` file / image file.
3. Click **Execute Compression Pipeline** to build the Huffman tree, compress the data, verify lossless reconstruction, and view analytics.

**Graph & Traversal Engine tab**
1. After compressing, switch to this tab to see the rendered tree.
2. Select a traversal order and animation speed, then click **Simulate Graph Traversal Pipeline** to watch the traversal play out on the canvas with a live log.

All generated files (compressed payloads, reconstructed output, tree diagrams, and audit logs) are saved under `huffman_exports/`.

## How It Works

1. Input data (text or raw image bytes) is analyzed to compute byte-frequency counts.
2. A min-heap builds an optimal binary prefix-code tree (`build_huffman`).
3. Prefix codes are generated per byte via tree traversal (`gen_codes`).
4. Data is encoded into a packed bitstream (`encode_bytes`) and can be decoded back (`decode_bits`) to confirm correctness.
5. Shannon entropy and bitstream entropy are computed to compare theoretical vs. achieved compression.
