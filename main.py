import argparse
import os
import itertools
import PIL.Image
from cairosvg import svg2png
from typing import List
from string import Template


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    # Taken from itertools recipes
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def merge_2bits_lsb_first(bytes, mapping) -> int:
    result = 0
    # mapping = {0 : 0, 0b01: 0b10, 0b10: 0b01, 0b11: 0b11}
    for bit_group in reversed(bytes):
        result = (result << 2) + mapping[bit_group]
    return result


def input_data_to_byte_list(data, mapping) -> List[int]:
    result = []
    for byte_group in grouper(data, 4, 0):
        y = merge_2bits_lsb_first(byte_group, mapping)
        result.append(y)
    return result


def input_data_to_c_array(data, mapping) -> str:
    bytes = input_data_to_byte_list(data, mapping)
    return ', '.join(hex(x) for x in bytes)


def write_to_file(icon_name, image, mapping) -> None:
    width, height = image.size
    img_data = image.tobytes()
    arr_data = input_data_to_c_array(img_data, mapping)
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


def remove_alpha_channel(image: PIL.Image) -> PIL.Image:
    background = PIL.Image.new('RGBA', image.size, (255, 255, 255))
    return PIL.Image.alpha_composite(background, image)


def convert_svg(file_name: str) -> PIL.Image:
    temp_png_name = f"{file_name}_TEMP.png"
    svg2png(url=f"{file_name}.svg", write_to=temp_png_name, output_width=24, output_height=24)
    im = PIL.Image.open(temp_png_name)
    indexed_image = im.quantize(colors=4)
    os.remove(temp_png_name)
    return indexed_image


# How to map the paletted png colors to the .h file.
mappings = {
    # PIL.quantize puts alpha as 0, and then the "strongest" color as 1.
    "cairo_svg": {0: 0, 1: 3, 2: 2, 3: 1},
    "gimp_black_as_transparent": {0: 0, 0b01: 0b01, 0b10: 0b10, 0b11: 0b11},
    "gimp_white_as_transparent": {0: 0x03, 0b01: 0b10, 0b10: 0b01, 0b11: 0b00},

}


def main():
    parser = argparse.ArgumentParser(description="Convert an image into a .h file")
    parser.add_argument('output_name', type=str,
                        help="The variable name to be used for the Icon.")
    parser.add_argument("input_file", type=str,
                        help="The name of the image file: svg and png supported"
                             "For svg: It is assumed that the drawn area is black")
    # TODO: make this argument optional for svg:s
    parser.add_argument("-t ", "--transparent_color", type=str,
                        choices=["black", "white"],
                        help="What color to use as transparency."
                             "Only used for pngs. Options= black or white")

    args = parser.parse_args()
    file_name, file_type = os.path.splitext(args.input_file)
    if file_type == ".svg":
        indexed_image = convert_svg(file_name)
        mapping = mappings["cairo_svg"]
    elif not file_type == ".png":
        print("Error: Second argument has to be a .png or .svg file")
        return -1
    else:
        indexed_image = PIL.Image.open(args.input_file)
        indexed_image = indexed_image.quantize(colors=4)
        # Redoing the quantization makes sure that the colors are 0, 1, 2, 3
        if not args.transparent_color:
            print("Error: Have to specify transparency for PNGs.")
            return -1
        mapping = mappings["gimp_black_as_transparent"] if args.transparent_color == "black" else mappings[
            "gimp_white_as_transparent"]
    write_to_file(args.output_name, indexed_image, mapping)


if __name__ == '__main__':
    main()
