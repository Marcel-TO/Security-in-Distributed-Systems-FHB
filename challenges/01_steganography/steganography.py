from PIL import Image
from typing import Iterator, Tuple, List
import logging


class SteganographyError(Exception):
    """Custom exception for steganography operations."""

    pass


class ImageSteganography:
    """
    LSB (Least Significant Bit) Steganography implementation.
    Hides text messages in images by modifying the least significant bits of pixel values.
    """

    def __init__(self, logger: logging.Logger | None = None):
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.BITS_PER_CHAR = 8

    def text_to_binary(self, text: str) -> List[str]:
        """
        Convert text to a list of 8-bit binary strings.

        :param str text:
            The text to convert

        :returns List[str]:
            List of binary strings, one per character

        Example:
            'Hi' -> ['01001000', '01101001']
        """
        binary = [format(ord(char), "08b") for char in text]
        self.logger.debug(f'Converted text "{text}" to binary: {binary}')
        return binary

    def make_even(self, value: int) -> int:
        """Make a number even by subtracting 1 if odd."""
        return value - 1 if value % 2 != 0 else value

    def make_odd(self, value: int) -> int:
        """Make a number odd by adjusting value."""
        if value % 2 == 0:
            return value + 1 if value < 255 else value - 1
        return value

    def encode_bit_in_value(self, value: int, bit: str) -> int:
        """
        Encode a single bit into a color value using LSB.

        :param int value:
            The color value (0-255)
        :param str bit:
            The bit to encode ('0' or '1')

        :returns int:
            Modified color value
        """
        if bit == "0":
            return self.make_even(value)
        else:  # bit == '1'
            return self.make_odd(value)

    def extract_bit_from_value(self, value: int) -> str:
        """Extract the LSB from a color value."""
        return "1" if value % 2 != 0 else "0"

    def modify_pixels_for_encoding(
        self, pixels: List[Tuple[int, ...]], text: str
    ) -> Iterator[Tuple[int, int, int]]:
        """
        Modify pixel values to encode the binary representation of text.
        Uses 3 pixels (9 color values) to encode each character:
        - 8 values for the 8 bits of the character
        - 1 value as a termination flag

        :param List[Tuple[int, ...]] pixels:
            List of pixel tuples (R, G, B)
        :param str text:
            The text to encode

        :yields Tuple[int, int, int]:
            Modified pixel tuples
        """
        binary_chars = self.text_to_binary(text)
        num_chars = len(binary_chars)
        pixel_iterator = iter(pixels)

        for char_index, binary_char in enumerate(binary_chars):
            try:
                # Get 3 pixels (9 color values)
                pixel1 = next(pixel_iterator)
                pixel2 = next(pixel_iterator)
                pixel3 = next(pixel_iterator)

                # Flatten to list of 9 color values
                color_values = list(pixel1[:3]) + list(pixel2[:3]) + list(pixel3[:3])

                # Encode 8 bits in first 8 color values
                for bit_index in range(self.BITS_PER_CHAR):
                    bit = binary_char[bit_index]
                    color_values[bit_index] = self.encode_bit_in_value(color_values[bit_index], bit)

                # Set termination flag in 9th value
                is_last_char = char_index == num_chars - 1
                if is_last_char:
                    color_values[8] = self.make_odd(color_values[8])
                else:
                    color_values[8] = self.make_even(color_values[8])

                # Yield the 3 modified pixels
                yield tuple(color_values[0:3])
                yield tuple(color_values[3:6])
                yield tuple(color_values[6:9])

            except StopIteration:
                raise SteganographyError(
                    f"Image too small to encode {len(text)} characters. "
                    f"Need at least {len(text) * 3} pixels."
                )

    def validate_image_capacity(self, image: Image.Image, text: str) -> None:
        """
        Check if the image has enough pixels to encode the text.

        :param Image.Image image:
            The PIL Image object
        :param str text:
            The text to encode

        :raises SteganographyError:
            If image is too small
        """
        total_pixels = image.size[0] * image.size[1]
        pixels_needed = len(text) * 3  # 3 pixels per character

        if total_pixels < pixels_needed:
            raise SteganographyError(
                f"Image too small! Has {total_pixels} pixels, "
                f"needs {pixels_needed} pixels for {len(text)} characters."
            )

    def encode(self, image_path: str, text: str, output_path: str) -> None:
        """
        Encode text into an image using LSB steganography.

        :param str image_path:
            Path to the input image
        :param str text:
            Text to hide in the image
        :param str output_path:
            Path where the encoded image will be saved

        :raises SteganographyError:
            If encoding fails
        """
        if not text:
            raise SteganographyError("Cannot encode empty text")

        try:
            image = Image.open(image_path)
        except Exception as e:
            raise SteganographyError(f"Failed to open image: {e}")

        # Validate capacity
        self.validate_image_capacity(image, text)

        # Create a copy to avoid modifying original
        encoded_image = image.copy()

        # Get all pixels and modify them
        pixels = list(encoded_image.getdata())
        self.logger.debug(f"Original pixels: {pixels[:10]}...")  # Log first 10 pixels
        modified_pixels = self.modify_pixels_for_encoding(pixels, text)

        # Write modified pixels back to image
        width = encoded_image.size[0]
        x, y = 0, 0

        for pixel in modified_pixels:
            encoded_image.putpixel((x, y), pixel)

            # Move to next position
            x += 1
            if x >= width:
                x = 0
                y += 1

        # Save the encoded image
        try:
            # Determine format from extension
            file_format = output_path.split(".")[-1].upper()
            if file_format == "JPG":
                file_format = "JPEG"

            encoded_image.save(output_path, format=file_format)
            print(f"✓ Successfully encoded {len(text)} characters into {output_path}")
        except Exception as e:
            raise SteganographyError(f"Failed to save image: {e}")

    def decode(self, image_path: str) -> str:
        """
        Decode hidden text from an image.

        :param str image_path:
            Path to the encoded image

        :returns str:
            The decoded text

        :raises SteganographyError:
            If decoding fails
        """
        try:
            image = Image.open(image_path)
        except Exception as e:
            raise SteganographyError(f"Failed to open image: {e}")

        pixel_iterator = iter(image.getdata())
        decoded_text = ""

        try:
            while True:
                # Read 3 pixels (9 color values)
                pixel1 = next(pixel_iterator)
                pixel2 = next(pixel_iterator)
                pixel3 = next(pixel_iterator)

                # Flatten to list of 9 color values
                color_values = list(pixel1[:3]) + list(pixel2[:3]) + list(pixel3[:3])

                # Extract 8 bits from first 8 color values
                binary_string = "".join(
                    [
                        self.extract_bit_from_value(color_values[i])
                        for i in range(self.BITS_PER_CHAR)
                    ]
                )

                # Convert binary to character
                char_code = int(binary_string, 2)
                decoded_text += chr(char_code)

                # Check termination flag (9th value)
                if color_values[8] % 2 != 0:  # Odd means stop
                    break

        except StopIteration:
            raise SteganographyError(
                "Unexpected end of image data - image may not contain encoded text"
            )
        except ValueError as e:
            raise SteganographyError(f"Invalid encoded data: {e}")

        return decoded_text


def main():
    """Interactive CLI for steganography operations."""
    print("=" * 50)
    print("  IMAGE STEGANOGRAPHY TOOL")
    print("  Hide text messages in images")
    print("=" * 50)
    print()
    print("1. Encode (hide text in image)")
    print("2. Decode (extract text from image)")
    print()

    choice = input("Enter your choice (1 or 2): ").strip()

    try:
        steg = ImageSteganography()

        if choice == "1":
            print("\n--- ENCODING MODE ---")
            image_path = input("Enter input image path (e.g., image.png): ").strip()
            text = input("Enter text to hide: ")
            output_path = input("Enter output image path (e.g., encoded.png): ").strip()

            steg.encode(image_path, text, output_path)

        elif choice == "2":
            print("\n--- DECODING MODE ---")
            image_path = input("Enter encoded image path: ").strip()

            decoded_text = steg.decode(image_path)
            print(f"\n✓ Decoded text: {decoded_text}")

        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    except SteganographyError as e:
        print(f"\n❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
