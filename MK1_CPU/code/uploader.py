import warnings
import serial
import serial.tools.list_ports
import argparse
from tqdm import tqdm
from time import sleep

baud = 9600

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Binary uploader for MK1 computer.')
    parser.add_argument('-i', '--input', metavar='input', type=str, required = True,
                        help='input file name')
    parser.add_argument('-p', '--port', metavar='port', type=str,
                        help='Arduino serial property')

    args = parser.parse_args()

    arduino_ports = [
        p.device
        for p in serial.tools.list_ports.comports()
        if 'Arduino' in p.description or 'Serial' in p.description  # may need tweaking to match new arduinos
    ]

    if not arduino_ports:
        raise IOError("No Arduino found")
    if not args.port and len(arduino_ports) > 1:
        warnings.warn('Multiple Arduinos found - using the first')

    if not args.input.endswith('.bin'):
        warnings.warn('Input file may not be binary - continuing')

    ser = serial.Serial(args.port or arduino_ports[0], baud, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
    sleep(3)

    with open(args.input, 'rb') as f:
        byte = f.read(1)
        while byte:
            written = ser.write(byte)
            ser.flush()
            byte = f.read(1)
    ser.read()
    ser.close()
