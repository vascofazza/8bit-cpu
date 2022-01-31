#digits = [0x7e, 0x30, 0x6d, 0x79, 0x33, 0x5b, 0x5f, 0x70, 0x7f, 0x7b]
digits = [0x7e, 0x30, 0x6d, 0x79, 0x33, 0x5b, 0x5f, 0x70, 0x7f, 0x7b, 0x77, 0x1f, 0x4e, 0x3d, 0x4f, 0x47]
lower = [0x7D, 0x1F, 0x0D, 0x3D, 0x6f, 0x47, 0x7B, 0x17, 0x10, 0x38, 0x17, 0x06, 0x55, 0x15, 0x1D, 0x67, 0x73, 0x05, 0x5B, 0x0F, 0x1C, 0x23, 0x2B, 0x25, 0x33, 0x6D]
upper = [0x77, 0x7F, 0x4E, 0x7E, 0x4F, 0x47, 0x5E, 0x37, 0x30, 0x3C, 0x37, 0x0E, 0x55, 0x15, 0x7E, 0x67, 0x73, 0x77, 0x5B, 0x46, 0x3E, 0x27, 0x3F, 0x25, 0x3B, 0x6D]
space = 0x00

def byte(value):
    return int.from_bytes((value).to_bytes(1, 'big', signed=True), 'big')

def write(address, data, out):
    out.seek(address)
    out.write(data.to_bytes(1, 'big'))

def main():
    with open('output_display_extended.bin', 'wb') as out:
        print("Programming ones place")

        for value in range(256):
            write(value, digits[value % 10], out)

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

        #Begin extended characters

        print("Programming ones place (HEX)")
        for value in range(256):
            write(value + 2048, digits[value % 16], out)
  
        print("Programming tens place (HEX)")
        for value in range(256):
            write(value + 2048 + 256, digits[(value // 16) % 16], out)
        
        print("Programming hundreds place (HEX)")
        for value in range(256):
            write(value + 2048 + 512, 0, out)

        print("Programming sign (HEX)")
        for value in range(256):
            write(value + 2048 + 768, 0, out)


        print("Programming ones place (ASCII)")
        
        pattern = 0
        
        for value in range(256):
            if (chr(value) >= '0' and chr(value) <= '9'):
                pattern = digits[value - ord('0')]

            elif (chr(value) >= 'A' and chr(value) <= 'Z'):
                pattern = upper[value - ord('A')]

            elif (chr(value) >= 'a' and chr(value) <= 'z'):
                pattern = lower[value - ord('a')]
            
            elif (value == ' '):
                pattern = space
            
            write(value + 4096, pattern, out)

        print("Programming tens place (ASCII)")
        for value in range(256):
            write(value + 4096 + 256, 0, out)

        print("Programming hundreds place (ASCII)")
        for value in range(256):
            write(value + 4096 + 512, 0, out)

        print("Programming sign (ASCII)")
        for value in range(256):
            write(value + 4096 + 768, 0, out)

if __name__ == "__main__":
    main()
