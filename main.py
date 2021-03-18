import argparse
import itertools
import functools
import PIL.Image
from typing import List, Dict
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


def write_to_file(icon_name, input_file, mapping) -> None:
    im = PIL.Image.open(input_file)
    width, height = im.size
    img_data = im.tobytes()
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


def build_mapping(transparent_byte) -> Dict[int, int]:
    if transparent_byte == 0x00:
        return {0: 0, 0b01: 0b01, 0b10: 0b10, 0b11: 0b11}
    elif transparent_byte == 0x03:
        return {0: 0x03, 0b01: 0b10, 0b10: 0b01, 0b11: 0b00}


def main():
    parser = argparse.ArgumentParser(description="Convert an image into a .h file")
    parser.add_argument('output_name', type=str,
                        help="The variable name to be used for the Icon.")
    parser.add_argument("input_file", type=str,
                        help="The name of the image file")
    # partial(int, base=0) allows for any base to be entered (hex, binary, decimal etc)
    parser.add_argument("transparent_byte", type=functools.partial(int, base=0),
                        help="The encoding of the color that is supposed to be "
                             "turned transparent (encoded as 0 in the .h file). black=0x00, white=0x03")
    args = parser.parse_args()
    mapping = build_mapping(args.transparent_byte)
    if not args.input_file.endswith(".png"):
        print("Error: Second argument has to be a .png file")
        return -1
    write_to_file(args.output_name, args.input_file, mapping)


if __name__ == '__main__':
    main()
