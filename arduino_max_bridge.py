# -*- coding: utf-8 -*-
#!/opt/bin/python3
import serial
import time
import os
import sys

SERIAL_PATH = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
OUTFILE = '/dev/shm/max.temp'
TIMEOUT_SEC = 3.0     # total allowed time without valid reading before writing impossible value
SER_TIMEOUT = 0.2      # per-read timeout
READ_CHUNK = 64

def open_serial(max_time=TIMEOUT_SEC):
    """Try to open serial for up to max_time seconds, then fail."""
    start = time.monotonic()
    while time.monotonic() - start < max_time:
        try:
            ser = serial.Serial(SERIAL_PATH, 9600, timeout=SER_TIMEOUT)
            print(f"[bridge] Connected to {SERIAL_PATH}")
            return ser
        except serial.SerialException as e:
            sys.stderr.write(f"[bridge] Serial open failed: {e}. Retrying...\n")
            time.sleep(0.5)
    # Give up after max_time
    return None

def write_temp(temp_c):
    try:
        with open(OUTFILE, 'w') as f:
            f.write(f"{int(temp_c * 1000)}\n")
    except Exception as e:
        sys.stderr.write(f"[bridge] Write error: {e}\n")

def write_impossible():
    try:
        with open(OUTFILE, 'w') as f:
            f.write("-150000\n")  # impossible value for Klipper fault
    except Exception:
        pass

def main():
    ser = open_serial()
    last_good = time.monotonic()
    buffer = ""

    while True:
        if ser is None:
            sys.stderr.write(f"[bridge] Could not reconnect for {TIMEOUT_SEC}s. Writing impossible value.\n")
            write_impossible()
            ser = open_serial()
            last_good = time.monotonic()
            continue

        try:
            chunk = ser.read(READ_CHUNK).decode('ascii', errors='ignore')
            if chunk:
                buffer += chunk
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

            # Timeout: no valid data for too long
            if time.monotonic() - last_good > TIMEOUT_SEC:
                sys.stderr.write(f"[bridge] No valid data for {TIMEOUT_SEC}s. Writing impossible value.\n")
                write_impossible()
                try:
                    ser.close()
                except Exception:
                    pass
                ser = open_serial()
                last_good = time.monotonic()
                buffer = ""

        except serial.SerialException as e:
            sys.stderr.write(f"[bridge] SerialException: {e}\n")
            try:
                ser.close()
            except Exception:
                pass
            ser = open_serial()
            if ser is None:
                sys.stderr.write(f"[bridge] Reconnect failed for {TIMEOUT_SEC}s. Writing impossible value.\n")
                write_impossible()
                ser = open_serial()
            last_good = time.monotonic()
            buffer = ""

        except Exception as e:
            sys.stderr.write(f"[bridge] Unexpected error: {e}\n")
            time.sleep(0.1)

        time.sleep(0.05)

if __name__ == "__main__":
    main()
