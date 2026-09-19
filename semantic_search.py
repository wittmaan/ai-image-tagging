import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from sentence_transformers import SentenceTransformer, util


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find images by semantic similarity to a natural-language query."
    )
    parser.add_argument(
        "query",
        help="Natural-language description to search for.",
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        default="tags.json",
        help="JSON file containing image tags (default: tags.json).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of results to display (default: 5).",
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Sentence-transformers model to use for embeddings.",
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    if arguments.top_k < 1:
        raise ValueError("--top-k must be at least 1")

    json_path = Path(arguments.json_file)
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in: {json_path}")

    valid_entries = [
        entry
        for entry in data
        if isinstance(entry, dict)
        and isinstance(entry.get("file"), str)
        and isinstance(entry.get("tags"), list)
    ]
    if not valid_entries:
        raise ValueError(f"No image entries with tags found in: {json_path}")

    model = SentenceTransformer(arguments.model)
    documents = [" ".join(str(tag) for tag in entry["tags"]) for entry in valid_entries]
    query_embedding = model.encode(arguments.query, convert_to_tensor=True)
    document_embeddings = model.encode(documents, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, document_embeddings)[0]

    result_count = min(arguments.top_k, len(valid_entries))
    print(f"Search results for: {arguments.query}\n")
    for index in scores.argsort(descending=True)[:result_count]:
        result = valid_entries[int(index)]
        print(f"{float(scores[index]):.3f}  {result['file']}")
        print(f"       {', '.join(result['tags'])}")


if __name__ == "__main__":
    main()
