#!/opt/bin/python3
import serial
import time
import os
import sys

SERIAL_PATH = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
OUTFILE = '/dev/shm/max.temp'
TIMEOUT_SEC = 3.0  # error threshold
SER_TIMEOUT = 0.2  # serial read polling period

def open_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PATH, 9600, timeout=SER_TIMEOUT)
            print(f"[bridge] Connected to {SERIAL_PATH}")
            return ser
        except serial.SerialException as e:
            print(f"[bridge] Serial open failed: {e}. Retrying...")
            time.sleep(2)

def write_temp(temp_c):
    try:
        with open(OUTFILE, 'w') as f:
            f.write(f"{int(temp_c * 1000)}\n")
    except Exception as e:
        sys.stderr.write(f"[bridge] Write error: {e}\n")

def write_impossible():
    try:
        with open(OUTFILE, 'w') as f:
            f.write("-150000\n")
    except Exception:
        pass

def main():
    ser = open_serial()
    last_good = time.monotonic()
    buffer = ""

    while True:
        try:
            # Non-blocking read
            chunk = ser.read(64).decode('ascii', errors='ignore')
            if chunk:
                buffer += chunk
                # Process each line
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line.startswith('T:'):
                        try:
                            temp = float(line.split('T:')[1].strip())
                            write_temp(temp)
                            last_good = time.monotonic()
                        except ValueError:
                            pass

            # Timeout handling
            if time.monotonic() - last_good > TIMEOUT_SEC:
                sys.stderr.write(f"[bridge] ERROR: No data for {TIMEOUT_SEC}s, writing impossible value\n")
                write_impossible()
                ser.close()
                time.sleep(2)
                ser = open_serial()
                buffer = ""
                last_good = time.monotonic()

        except serial.SerialException as e:
            sys.stderr.write(f"[bridge] Serial error: {e}, writing impossible value\n")
            write_impossible()
            time.sleep(2)
            ser = open_serial()
            buffer = ""
            last_good = time.monotonic()

        except Exception as e:
            sys.stderr.write(f"[bridge] Unexpected: {e}\n")
            time.sleep(0.5)

        time.sleep(0.05)

if __name__ == "__main__":
    main()
