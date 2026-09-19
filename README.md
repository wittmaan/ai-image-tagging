# AI Image Tagging

This project uses a local vision-language model in LM Studio to generate exactly 10 English tags for every image in a directory. Image classification was removed; the result now contains tags only.

## How It Works

1. `classify_image.py` scans the selected directory for supported image files.
2. Each image is read and encoded as base64.
3. Each image is sent to LM Studio through its OpenAI-compatible API at `http://localhost:1234/v1`.
4. The configured vision model generates exactly 10 tags per image.
5. All results are written to one JSON file with this structure:

```json
[
  {
    "file": "example.png",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"]
  }
]
```

## Requirements

- Windows with Git Bash or another Bash-compatible terminal
- Miniconda or Anaconda
- Python environment named `py311`
- LM Studio with the local server enabled
- The `smolvlm2-2.2b-instruct` vision model loaded in LM Studio
- At least one `.bmp`, `.gif`, `.jpeg`, `.jpg`, `.png`, or `.webp` image in the input directory

## Installation

Create or use the Conda environment:

```bash
conda create -n py311 python=3.11
conda activate py311
```

Install the packages required by the tagging script:

```bash
pip install -r requirements.txt
```

## LM Studio Setup

1. Open LM Studio.
2. Load `smolvlm2-2.2b-instruct`.
3. Start the local server on port `1234`.
4. Confirm that the server is available at:

```text
http://localhost:1234/v1
```

## Run

From Git Bash in the project directory, process images in the current directory and write `tags.json`:

```bash
./run_classify_image.sh
```

To process a directory and write `tags.json` inside that same directory:

```bash
./run_classify_image.sh /e/images/01
```

To process another directory and choose a different output file:

```bash
./run_classify_image.sh path/to/images output.json
```

The output argument may also be an existing directory. In that case, the
script writes `tags.json` inside that directory:

```bash
./run_classify_image.sh data/ /e/images/01
```

When the output JSON already exists, the script checks its `file` entries and skips images that have already been tagged. This makes it safe to rerun the same command after adding new images; only the new images are sent to LM Studio.

The launcher discovers the active Conda installation automatically. To use a
specific installation, set `CONDA_ROOT` before running it:

```bash
CONDA_ROOT=/c/Users/your-user/miniconda3 ./run_classify_image.sh
```

You can also run the Python script directly. Its arguments are the input directory and output file:

```bash
python classify_image.py path/to/images output.json
```

## Output

The script prints progress for each image and the location of the generated JSON file:

```text
Tagging example.png...
Wrote tags for 3 images to /path/to/output.json
```

## Semantic Search

`semantic_search.py` searches the generated tags using a sentence-embedding model. It accepts a natural-language query and ranks the closest images by semantic similarity.

Search the results for folder `data`:

```bash
python semantic_search.py "a snowy traditional market" data/tags.json
```

The Bash wrapper provides the same search:

```bash
./search_images.sh "a snowy traditional market" data/tags.json
```

The default output shows the five closest matches. Use `--top-k` to change the number of results:

```bash
python semantic_search.py "historic town square" data/tags.json --top-k 10
```

The wrapper accepts the query, JSON file, and result count in that order:

```bash
./search_images.sh "historic town square" data/tags.json 10
```

The first run downloads the default `all-MiniLM-L6-v2` embedding model. Search is performed on the generated tags, not directly on image pixels.

## Troubleshooting

- **No supported images found:** Put supported image files in the selected input directory.
- **LM Studio connection error:** Start the LM Studio server and verify port `1234`.
- **Model error:** Load `smolvlm2-2.2b-instruct` in LM Studio.
- **Conda Python not found:** Set `CONDA_ROOT` to the directory containing your Conda installation.
