import argparse
from io import BytesIO
import sys

def byte(value):
    return (value).to_bytes(1, 'big', signed=False)

def write(address, data, out):
    out.seek(address)
    data = data & 255
    out.write(data.to_bytes(1, 'big'))

def assemble_binary(files):
    b = bytes()
    buffer = BytesIO(b)
    #Program data bytes
    print("Generating binary...")

    #address-out locations
    for i in range(512):
        buffer.write(byte(i // 2))

    current_bank = 1
    for file in files:
        curr_address = 0
        with open(file, 'rb') as f:
            data = 1
            while data:
                data = f.read(1)
                if curr_address > 0xFF:
                    buffer.seek(current_bank * 512 + (curr_address - 0x100) * 2 + 1)
                    buffer.write(data)
                else:
                    buffer.seek(current_bank * 512 + curr_address * 2)
                    buffer.write(data)
                curr_address += 1
        current_bank += 1

    print("done")
    return buffer.getvalue()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Flash memory composer for Start9 Programming Interface.')
    parser.add_argument('-i', '--input', metavar='input', type=str, nargs='+',
                        required=True, help='input files name')

    args = parser.parse_args()

    if len(args.input) > 14:
        print("max number of programs reached: %d. Skipping last %d." % (len(args.input), len(args.input) - 14))

    binary = assemble_binary(args.input)

    out_file_name = "start9.bin"

    with open(out_file_name, 'wb') as out:
        out.write(binary)

    with open("start9.txt", "w") as f:
        for idx, file in enumerate(args.input):
            f.write("%d\t%s\n" % (idx + 1, file[file.rfind("/") + 1:]))

    print("%s generated (%d bytes)."%(out_file_name, len(binary)))
