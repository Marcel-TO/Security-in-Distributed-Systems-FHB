#!/usr/bin/env python3
"""
Main entry point for the steganography tool.
Handles command-line arguments and calls the appropriate encoding/decoding functions.
"""

import argparse
import sys
from pathlib import Path
from steganography import SteganographyError, ImageSteganography
import logging

logger = logging.getLogger(__name__)


def validate_file_exists(filepath: str) -> Path:
    """
    Validate that a file exists.

    :param str filepath:
        Path to the file

    :returns Path:
        Path object

    :raises argparse.ArgumentTypeError:
        If file doesn't exist
    """
    path = Path(filepath)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"File not found: {filepath}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Not a file: {filepath}")
    return path


def validate_output_path(filepath: str) -> Path:
    """
    Validates whether the given output is usable.

    :param str filepath:
        Path to the output file

    :returns Path:
        Path object

    :raises argparse.ArgumentTypeError:
        If the output path is invalid
    """
    path = Path(filepath)

    # Check if parent directory exists
    if not path.parent.exists():
        raise argparse.ArgumentTypeError(f"Parent directory does not exist: {path.parent}")

    # Check if it has a valid image extension
    valid_extensions = {".png", ".bmp", ".tiff", ".tif"}
    if path.suffix.lower() not in valid_extensions:
        raise argparse.ArgumentTypeError(
            f"Output file must have one of these extensions: {', '.join(valid_extensions)}\n"
            f"(Note: JPG/JPEG is not recommended due to lossy compression)"
        )

    return path


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    :returns argparse.ArgumentParser:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="LSB Steganography Tool - Hide text messages in images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Encode text into an image:
    %(prog)s encode input.png -t "Secret message" -o output.png
    %(prog)s encode input.png --text "Hello World" --output encoded.png

  Decode text from an image:
    %(prog)s decode encoded.png
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)

    # Encode subcommand
    encode_parser = subparsers.add_parser("encode", help="Encode text into an image")
    encode_parser.add_argument(
        "input_image", type=validate_file_exists, help="Path to the input image file"
    )
    encode_parser.add_argument(
        "-t", "--text", type=str, required=True, help="Text to hide in the image"
    )
    encode_parser.add_argument(
        "-o",
        "--output",
        type=validate_output_path,
        required=True,
        help="Path for the output image (recommended: PNG, BMP, TIFF)",
    )
    encode_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")

    # Decode subcommand
    decode_parser = subparsers.add_parser("decode", help="Decode text from an image")
    decode_parser.add_argument(
        "input_image", type=validate_file_exists, help="Path to the encoded image file"
    )
    decode_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")

    return parser


def handle_encode(args: argparse.Namespace) -> int:
    """
    Handle the encode command.

    :param argparse.Namespace args:
        Parsed command-line arguments

    :returns int:
        Exit code (0 for success, 1 for failure)
    """
    try:
        input_path = str(args.input_image)
        output_path = str(args.output)
        debug = args.debug
        text = args.text

        if not text.strip():
            print("❌ Error: Text cannot be empty or whitespace only", file=sys.stderr)
            return 1

        print(f"Encoding {len(text)} characters into {args.input_image.name}...")
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.debug("Debug mode enabled.")
        stego = ImageSteganography(logger=logger)
        stego.encode(input_path, text, output_path)
        return 0

    except SteganographyError as e:
        print(f"❌ Encoding failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def handle_decode(args: argparse.Namespace) -> int:
    """
    Handle the decode command.

    :param argparse.Namespace args:
        Parsed command-line arguments

    :returns int:
        Exit code (0 for success, 1 for failure)
    """
    try:
        input_path = str(args.input_image)
        debug = args.debug
        print(f"Decoding text from {args.input_image.name}...")
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.debug("Debug mode enabled.")
        stego = ImageSteganography(logger=logger)
        decoded_text = stego.decode(input_path)

        print("\n" + "=" * 50)
        print("Decoded message:")
        print("=" * 50)
        print(decoded_text)
        print("=" * 50)

        return 0

    except SteganographyError as e:
        print(f"❌ Decoding failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for the application.

    :returns int:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "encode":
        return handle_encode(args)
    elif args.command == "decode":
        return handle_decode(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    main()
