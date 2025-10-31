import serial
import time

ser = serial.Serial('/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0', 9600, timeout=1)
outfile = '/dev/shm/max.temp'

while True:
    line = ser.readline().decode('ascii', errors='ignore').strip()
    if line.startswith('T:'):
        try:
            temp = float(line.split('T:')[1].strip())
            with open(outfile, 'w') as f:
                f.write(f"{int(temp * 1000)}\n")  # millidegree format for Klipper
                f.flush()
        except ValueError:
            pass  # skip invalid readings
    time.sleep(0.1)
