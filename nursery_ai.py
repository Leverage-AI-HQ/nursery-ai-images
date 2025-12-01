#!/usr/bin/env python3
"""
Script to generate images from CSV prompts using OpenAI's GPT-Image-1 API.
Images are then extended to 16:9 aspect ratio using Flux Fill Pro.
Each line in the CSV should contain an image prompt.
Generated images are saved with filenames matching their line numbers.
"""

import os
import csv
import requests
import io
import base64
import replicate
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
replicate_client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

def create_extended_canvas_and_mask(image, aspect_ratio="16:9"):
    """
    Extend image canvas to target aspect ratio.
    Create a mask where white = areas to fill, black = original image area.
    Use blurred edges from the original image as the background.

    Args:
        image: PIL Image object (1536x1024 for 16:9, or 1024x1536 for 9:16)
        aspect_ratio: Target aspect ratio - "16:9" for horizontal, "9:16" for vertical

    Returns:
        tuple: (extended_image, mask_image)
    """
    from PIL import ImageFilter

    original_width, original_height = image.size

    # Determine target dimensions based on aspect ratio
    if aspect_ratio == "16:9":
        # Horizontal extension: 1536x1024 -> 1824x1024
        target_width = 1824
        target_height = original_height
        extension = (target_width - original_width) // 2
        paste_position = (extension, 0)
        target_size = (target_width, target_height)
    elif aspect_ratio == "9:16":
        # Vertical extension: 1024x1536 -> 1024x1824
        target_width = original_width
        target_height = 1824
        extension = (target_height - original_height) // 2
        paste_position = (0, extension)
        target_size = (target_width, target_height)
    else:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")

    # Create blurred version of the image to use as background
    blurred = image.filter(ImageFilter.GaussianBlur(radius=20))

    # Create new canvas by stretching the blurred image
    extended_canvas = blurred.resize(target_size)

    # Paste original image in the center (this will be preserved)
    extended_canvas.paste(image, paste_position)

    # Create mask: white for areas to fill, black for original image
    mask = Image.new('L', target_size, color='white')
    black_box = Image.new('L', (original_width, original_height), color='black')
    mask.paste(black_box, paste_position)

    return extended_canvas, mask

def extend_with_flux_fill(extended_canvas, mask, prompt):
    """
    Use Flux Fill Dev to fill the masked areas of the extended canvas.

    Args:
        extended_canvas: PIL Image with extended canvas
        mask: PIL Image mask (white = fill, black = preserve)
        prompt: Text prompt for filling

    Returns:
        PIL Image: Final image with filled areas
    """
    # Save images to bytes for upload
    canvas_bytes = io.BytesIO()
    extended_canvas.save(canvas_bytes, format='PNG')
    canvas_bytes.seek(0)

    mask_bytes = io.BytesIO()
    mask.save(mask_bytes, format='PNG')
    mask_bytes.seek(0)

    # Call Flux Fill Pro
    # Use empty prompt with low guidance so the image context guides the fill
    output = replicate_client.run(
        "black-forest-labs/flux-fill-pro",
        input={
            "prompt": "",
            "image": canvas_bytes,
            "mask": mask_bytes,
            "steps": 50,
            "guidance": 2.5,
            "output_format": "png",
            "safety_tolerance": 5
        }
    )

    # Download the result
    result_response = requests.get(output)
    result_response.raise_for_status()
    result_image = Image.open(io.BytesIO(result_response.content))

    return result_image

def generate_images_from_csv(csv_file_path, output_dir='generated_images', max_lines=None, aspect_ratio="16:9"):
    """
    Read prompts from CSV and generate images using GPT-Image-1 + Flux Fill Pro.

    Args:
        csv_file_path: Path to the CSV file containing prompts
        output_dir: Directory where generated images will be saved
        max_lines: Maximum number of lines to process (None = process all)
        aspect_ratio: Target aspect ratio - "16:9" (landscape) or "9:16" (portrait)
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Track number of processed images
    processed_count = 0

    # Read CSV and process each prompt
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)

        for line_number, row in enumerate(csv_reader, start=1):
            # Check if we've reached the limit
            if max_lines is not None and processed_count >= max_lines:
                print(f"\nReached limit of {max_lines} images. Stopping.")
                break

            # Skip empty rows
            if not row or not row[0].strip():
                print(f"Skipping empty line {line_number}")
                continue

            prompt = row[0].strip()
            print(f"\nProcessing line {line_number}: {prompt[:60]}...")

            try:
                # Determine image size based on aspect ratio
                if aspect_ratio == "16:9":
                    image_size = "1536x1024"  # Landscape
                elif aspect_ratio == "9:16":
                    image_size = "1024x1536"  # Portrait
                else:
                    raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")

                # Step 1: Generate image using GPT-Image-1
                print(f"  [1/3] Generating base image with GPT-Image-1 ({image_size})...")
                response = openai_client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size=image_size,
                    quality="high",
                    n=1
                )

                # Decode base64 image data
                image_base64 = response.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)
                base_image = Image.open(io.BytesIO(image_bytes))

                print(f"  [2/3] Extending canvas to {aspect_ratio} and creating mask...")
                # Step 2: Extend canvas and create mask
                extended_canvas, mask = create_extended_canvas_and_mask(base_image, aspect_ratio=aspect_ratio)

                # Debug: Save canvas and mask for inspection
                debug_dir = Path(output_dir) / 'debug'
                debug_dir.mkdir(exist_ok=True)
                extended_canvas.save(debug_dir / f"{line_number}_canvas.png")
                mask.save(debug_dir / f"{line_number}_mask.png")

                print(f"  [3/3] Filling edges with Flux Fill Pro...")
                # Step 3: Use Flux Fill Pro to fill the edges
                final_image = extend_with_flux_fill(extended_canvas, mask, prompt)

                # Save the final image
                image_path = Path(output_dir) / f"{line_number}.png"
                final_image.save(image_path, format='PNG')

                print(f"✓ Saved {aspect_ratio} image {line_number} to {image_path}")
                processed_count += 1

            except Exception as e:
                print(f"✗ Error processing line {line_number}: {str(e)}")
                continue

if __name__ == "__main__":
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Generate images from CSV prompts using GPT-Image-1 and Flux Fill Pro'
    )
    parser.add_argument(
        'csv_file',
        nargs='?',
        default='input.csv',
        help='Path to CSV file containing prompts (default: input.csv)'
    )
    parser.add_argument(
        '--aspect-ratio',
        type=str,
        choices=['16:9', '9:16'],
        default='16:9',
        help='Aspect ratio for generated images: 16:9 (landscape) or 9:16 (portrait) (default: 16:9)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of images to generate (default: process all lines)'
    )

    args = parser.parse_args()

    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found")
        parser.print_help()
        exit(1)

    # Print start message
    aspect_ratio = args.aspect_ratio
    print(f"Starting {aspect_ratio} image generation from {args.csv_file}")
    if args.limit:
        print(f"Limiting to {args.limit} image(s)")

    # Determine sizes for display message
    if aspect_ratio == "16:9":
        base_size = "1536x1024"
        final_size = "1824x1024"
    else:  # 9:16
        base_size = "1024x1536"
        final_size = "1024x1824"

    print(f"Process: GPT-Image-1 ({base_size}) → Canvas Extension → Flux Fill Pro → {aspect_ratio} Output ({final_size})\n")

    # Generate images
    generate_images_from_csv(args.csv_file, max_lines=args.limit, aspect_ratio=aspect_ratio)
    print("\nImage generation complete!")
