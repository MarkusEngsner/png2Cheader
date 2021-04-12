import argparse
import os
from io import BytesIO
from string import Template

import PIL.Image
import PIL.ImageOps
import numpy as np
from cairosvg import svg2png


def numpy_concat(image: PIL.Image) -> np.ndarray:
    arr = np.array(image)
    trans_arr = np.array([0, 2, 4, 6])  # Defines the bit shifts for the pixel merging.
    rows = arr.size // 4
    arr = arr.reshape(rows, 4)
    # Note: the input image stores the pixels from right to left,
    # this flips the pixels within each bytes so that:
    # 1 2 3 4 5 6 7 8  (with each number being the index)
    # turns into:
    # 4 3 2 1 8 7 6 5
    # which is the way they are stored in the library.
    # It does this by changing the values of the pixels, not by physically swapping them.
    shifted = (arr << trans_arr)
    return shifted.sum(axis=1)


def np_bytes_to_c_array_str(pixel_data: np.ndarray) -> str:
    return ', '.join(hex(x) for x in pixel_data)


def write_to_file(icon_name: str, image: PIL.Image) -> None:
    width, height = image.size
    arr_as_str = np_bytes_to_c_array_str(numpy_concat(image))
    header_text = f"{icon_name.upper()}_H"
    replacements = {
        "ICON_TEMPLATE_H": header_text,
        "IMAGE_DATA": arr_as_str,
        "WIDTH": width,
        "HEIGHT": height,
        "ICON_NAME": icon_name,
    }
    with open('icon_template.h', 'r') as template:
        src = Template(template.read())
        result = src.substitute(replacements)
        with open(icon_name + ".h", 'w') as out:
            out.write(result)


# Removing the alpha channel isn't strictly necessary, but results in the data from the svg not having
# to be remapped (ie 0 = transparent, 0x3 = "strongest" color)
def remove_alpha_channel(image: PIL.Image) -> PIL.Image:
    background = PIL.Image.new('RGBA', image.size, (255, 255, 255))
    return PIL.Image.alpha_composite(background, image)


def cleanup_input_file(image: PIL.Image) -> PIL.Image:
    # converting to grayscale ('L') only works without alpha channel: it therefore has to be removed
    im_no_alpha = remove_alpha_channel(image) if image.mode == 'RGBA' else image
    iml = im_no_alpha.convert('L')
    # redo quantization. This ensures that the palette always turn out the same way:
    # 0 = white (transparent)
    # 3 = black (100% opacity)
    # with 1 and 2 as colors in-between
    return iml.quantize(colors=4)


def convert_svg(file_name: str, width: int, height: int) -> PIL.Image:
    temp_png = BytesIO()
    svg2png(url=f"{file_name}.svg", write_to=temp_png, output_width=width, output_height=height)
    im = PIL.Image.open(temp_png)
    iml = cleanup_input_file(im)
    return iml


def main():
    parser = argparse.ArgumentParser(description="Convert an image into a .h file")
    parser.add_argument('output_name', type=str,
                        help="The variable name to be used for the Icon.")
    parser.add_argument("input_file", type=str,
                        help="The name of the image file: svg and png supported")
    parser.add_argument("-iw", "--width", type=int, required=False,
                        help="(Only for svg): the width of the Icon.")
    parser.add_argument("-ih", "--height", type=int, required=False,
                        help="(Only for svg): the height of the Icon.")

    args = parser.parse_args()
    file_name, file_type = os.path.splitext(args.input_file)
    if file_type == ".svg":
        if not args.width or not args.height:
            print("Error: svg requires --height and --width")
            return -1
        indexed_image = convert_svg(file_name, args.width, args.height)
    elif not file_type == ".png":
        print("Error: Input file has to be .png or .svg")
        return -1
    else:
        input_image = PIL.Image.open(args.input_file)
        indexed_image = cleanup_input_file(input_image)
    write_to_file(args.output_name, indexed_image)


if __name__ == '__main__':
    main()
