import PIL.Image
import sys
from typing import List
from itertools import zip_longest


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    # Taken from itertools recipes
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def merge_2bits_lsb_first(bytes, mapping):
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


def write_to_file(icon_name, input_file, mapping):
    im = PIL.Image.open(input_file)
    width, height = im.size
    img_data = im.tobytes()
    arr_data = input_data_to_c_array(img_data, mapping)
    with open('icon_template.h', 'r') as template:
        t_str = template.read()
        header_text = f"{icon_name.upper()}_H"
        result = t_str.replace("%ICON_TEMPLATE_H%", header_text)
        result = result.replace("%IMAGE_DATA%", arr_data)
        result = result.replace("%WIDTH%", f"{width}").replace("%HEIGHT%", f"{height}")
        result = result.replace("%ICON_NAME%", icon_name)
        with open(icon_name + ".h", 'w') as out:
            out.write(result)
        return result

def build_mapping(transparent_byte):
    if transparent_byte == 0x00:
        return {0: 0, 0b01: 0b01, 0b10: 0b10, 0b11: 0b11}
    elif transparent_byte == 0x03:
        return {0: 0x03, 0b01: 0b10, 0b10: 0b01, 0b11: 0b00}


def main(argv):
    if len(argv) != 4:
        print("Wrong argument count. Usage: python3 png2c.py <OUTPUT_VARIABLE_NAME> <INPUT.PNG> <TRANSPARENT_BYTE>")
        print("<TRANSPARENT_BYTE>: If white should be transparent, use 0x03. If black, use 0x00 (currently has to be hex)")
        return -1
    output_name = argv[1]
    input_file = argv[2]
    transparent_byte = int(argv[3], base=16)
    mapping = build_mapping(transparent_byte)
    if not input_file.endswith(".png"):
        print("Error: Second argument has to be a .png file")
        return -1
    write_to_file(output_name, input_file, mapping)



if __name__ == '__main__':
    main(sys.argv)


