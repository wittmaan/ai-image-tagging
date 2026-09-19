import argparse
import base64
from io import BytesIO
import json
import mimetypes
from pathlib import Path
from time import perf_counter

from PIL import Image
import requests
from openai import OpenAI

LMSTUDIO_URL = "http://localhost:1234/v1"
MODEL_NAME = "smolvlm2-2.2b-instruct"
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate tags for all images in a directory.")
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing the images (default: current directory).",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="tags.json",
        help="Output JSON file (default: tags.json).",
    )
    parser.add_argument(
        "--max-pixels",
        type=int,
        default=256*28*28,
        help="Maximum total pixels sent to the model (default: 256*28*28).",
    )
    return parser.parse_args()


def check_lmstudio():
    try:
        requests.get(LMSTUDIO_URL, timeout=3)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "LM Studio is not running or not listening on http://localhost:1234/v1. "
            f"Start the local server and load the {MODEL_NAME} model first."
        ) from exc


def encode_image(image_path, max_pixels):
    with Image.open(image_path) as image:
        if image.width * image.height <= max_pixels:
            with image_path.open("rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8"), (
                    mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
                )

        scale = (max_pixels / (image.width * image.height)) ** 0.5
        resized_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        image = image.convert("RGB")
        image.thumbnail(resized_size, Image.Resampling.BILINEAR)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=75, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8"), "image/jpeg"


def classify_image(image_path, client, max_pixels):
    base64_image, mime_type = encode_image(image_path, max_pixels)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Generate exactly 10 high-quality tags or keywords in English that best describe the content, mood, objects, and setting. "
                            "Return valid JSON with the structure: {'tags': ['tag1', 'tag2', ... , 'tag10']}. "
                            "Use lowercase words for the tags, separated as list entries, and do not include explanations, markdown, or extra text."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "image_tags",
                "schema": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 5,
                            "maxItems": 10,
                        },
                    },
                    "required": ["tags"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        max_tokens=200,
    )

    response_data = json.loads(response.choices[0].message.content)
    return response_data["tags"]


def load_existing_results(output_path):
    if not output_path.exists():
        return []

    existing_results = json.loads(output_path.read_text(encoding="utf-8"))
    if not isinstance(existing_results, list):
        raise ValueError(f"Expected a JSON list in output file: {output_path}")
    return existing_results


def main():
    arguments = parse_arguments()
    if arguments.max_pixels < 1:
        raise ValueError("--max-pixels must be at least 1")
    image_directory = Path(arguments.directory).resolve()
    output_path = Path(arguments.output).resolve()

    if not image_directory.is_dir():
        raise NotADirectoryError(f"Image directory not found: {image_directory}")

    image_paths = sorted(
        path for path in image_directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_paths:
        raise FileNotFoundError(f"No supported images found in: {image_directory}")

    results = load_existing_results(output_path)
    classified_files = {
        result["file"]
        for result in results
        if isinstance(result, dict) and "file" in result and "tags" in result
    }
    pending_images = [
        image_path
        for image_path in image_paths
        if str(image_path.relative_to(image_directory)) not in classified_files
    ]

    if not pending_images:
        print(f"All {len(image_paths)} images are already classified in {output_path}")
        return

    check_lmstudio()
    client = OpenAI(base_url=LMSTUDIO_URL, api_key="lm-studio")

    tagging_times = []
    for image_path in pending_images:
        print(f"Tagging {image_path.name}...")
        start_time = perf_counter()
        tags = classify_image(image_path, client, arguments.max_pixels)
        elapsed_time = perf_counter() - start_time
        tagging_times.append(elapsed_time)
        results.append(
            {
                "file": str(image_path.relative_to(image_directory)),
                "tags": tags,
            }
        )
        print(f"Completed in {elapsed_time:.3f} seconds")

    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote tags for {len(pending_images)} new images to {output_path}")
    print(f"Average tagging time: {sum(tagging_times) / len(tagging_times):.3f} seconds per image")


if __name__ == "__main__":
    main()
