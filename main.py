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

def merge_2bits_lsb_first(bytes):
    result = 0
    for bit_group in reversed(bytes):
        result = (result << 2) + bit_group
    return result


def input_data_to_byte_list(data) -> List[int]:
    result = []
    for byte_group in grouper(data, 4, 0):
        y = merge_2bits_lsb_first(byte_group)
        result.append(y)
    return result

def input_data_to_c_arr(data) -> str:
    bytes = input_data_to_byte_list(data)
    return ', '.join(hex(x) for x in bytes)


def write_to_file(icon_name, input_file):
    im = PIL.Image.open(input_file)
    width, height = im.size
    img_data = im.tobytes()
    arr_data = input_data_to_c_arr(img_data)
    with open('icon_template.h', 'r') as template:
        t_str = template.read()
        header_text = f"{icon_name.upper()}_H"
        result = t_str.replace("%ICON_TEMPLATE_H%", header_text)
        result = result.replace("%IMAGE_DATA%", arr_data)
        result = result.replace("%WIDTH%", f"{width}").replace("%HEIGHT%", f"{height}")
        result = result.replace("%ICON_NAME%", icon_name)
        # TODO: check if file already exists
        with open(icon_name + ".h", 'w') as out:
            out.write(result)
        return result


def main(argv):
    if len(argv) != 3:
        print("Wrong argument count. Usage: python3 png2c.py <OUTPUT_VARIABLE_NAME> <INPUT.PNG>")
        return -1
    output_name = argv[1]
    input_file = argv[2]
    if not input_file.endswith(".png"):
        print("Error: Second argument has to be a .png file")
        return -1
    write_to_file(output_name, input_file)



if __name__ == '__main__':
    main(sys.argv)


