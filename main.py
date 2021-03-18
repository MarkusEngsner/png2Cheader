import argparse
import os
import PIL.Image, PIL.ImageOps
import numpy as np
from io import BytesIO
from cairosvg import svg2png
from string import Template


def numpy_concat(image):
    arr = np.array(image)
    rows = arr.size // 4
    arr = arr.reshape(rows, 4)
    arr = np.flip(arr, axis=1)
    flat = arr.reshape(arr.size, 1)
    shifted = flat << 6
    bits_og = np.unpackbits(shifted, axis=1, count=2)
    rows = arr.size // 4  # 4 pixels per uint8_t
    bits = bits_og.reshape(bits_og.size // 8, 8)
    bytes = np.packbits(bits)
    np.set_printoptions(formatter={'int': hex})
    return bytes.flatten()


def np_bytes_to_c_array_str(bytes):
    return ', '.join(hex(x) for x in bytes)


def write_to_file(icon_name, image) -> None:
    width, height = image.size
    arr_data = np_bytes_to_c_array_str(numpy_concat(image))
    with open('icon_template.h', 'r') as template:
        header_text = f"{icon_name.upper()}_H"
        replacements = {
            "ICON_TEMPLATE_H": header_text,
            "IMAGE_DATA": arr_data,
            "WIDTH": width,
            "HEIGHT": height,
            "ICON_NAME": icon_name,
        }
        src = Template(template.read())
        result = src.substitute(replacements)
        with open(icon_name + ".h", 'w') as out:
            out.write(result)
        return result


# Removing the alpha channel isn't strictly necessary, but results in the data from the svg not having
# to be remapped (ie 0 = transparent, 0x3 = "strongest" color
# Should perhaps be done for PNGs too
def remove_alpha_channel(image: PIL.Image) -> PIL.Image:
    background = PIL.Image.new('RGBA', image.size, (255, 255, 255))
    return PIL.Image.alpha_composite(background, image)


def cleanup_input_file(image: PIL.Image) -> PIL.Image:
    # converting to grayscale ('L') only works without alpha channel
    im_no_alpha = remove_alpha_channel(image) if image.mode == 'RGBA' else image
    iml = im_no_alpha.convert('L')
    # redo quantization. This ensures that the palette always turn out the same way:
    # 0 = white (transparent)
    # 3 = black (100% opacity)
    # with 1 and 2 as colors in-between
    iml = iml.quantize(colors=4)
    return iml


def convert_svg(file_name: str) -> PIL.Image:
    temp_png = BytesIO()
    # TODO: add support for choosing size
    svg2png(url=f"{file_name}.svg", write_to=temp_png, output_width=24, output_height=24)
    im = PIL.Image.open(temp_png)
    iml = cleanup_input_file(im)
    return iml


def main():
    parser = argparse.ArgumentParser(description="Convert an image into a .h file")
    parser.add_argument('output_name', type=str,
                        help="The variable name to be used for the Icon.")
    parser.add_argument("input_file", type=str,
                        help="The name of the image file: svg and png supported"
                             "For svg: It is assumed that the drawn area is black")

    args = parser.parse_args()
    file_name, file_type = os.path.splitext(args.input_file)
    if file_type == ".svg":
        indexed_image = convert_svg(file_name)
    elif not file_type == ".png":
        print("Error: Second argument has to be a .png or .svg file")
        return -1
    else:
        indexed_image = PIL.Image.open(args.input_file)
        indexed_image = cleanup_input_file(indexed_image)
    write_to_file(args.output_name, indexed_image)


if __name__ == '__main__':
    main()
