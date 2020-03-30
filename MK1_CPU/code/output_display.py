digits = [0x7e, 0x30, 0x6d, 0x79, 0x33, 0x5b, 0x5f, 0x70, 0x7f, 0x7b]

def byte(value):
    return int.from_bytes((value).to_bytes(1, 'big', signed=True), 'big')

def write(address, data, out):
    out.seek(address)
    out.write(data.to_bytes(1, 'big'))

def main():
    with open('output_display.bin', 'wb') as out:
        print("Programming ones place")

        for value in range(256):
            write(value, digits[value % 10], out);

        print("Programming tens place")
        for value in range(256):
            write(value + 256, digits[(value // 10) % 10], out)

        print("Programming hundreds place")
        for value in range(256):
            write(value + 512, digits[(value // 100) % 10], out)

        print("Programming sign")
        for value in range(256):
            write(value + 768, 0, out)

        print("Programming ones place (twos complement)")
        for value in range(-128, 127):
            write(byte(value) + 1024, digits[abs(value) % 10], out)

        print("Programming tens place (twos complement)")
        for value in range(-128, 127):
            write(byte(value) + 1280, digits[abs(value // 10) % 10], out)

        print("Programming hundreds place (twos complement)")
        for value in range(-128, 127):
            write(byte(value) + 1536, digits[abs(value // 100) % 10], out)

        print("Programming sign (twos complement)")
        for value in range(-128, 127):
            if value < 0:
                write(byte(value) + 1792, 0x01, out)
            else:
                write(byte(value) + 1792, 0, out)

if __name__ == "__main__":
    main()
