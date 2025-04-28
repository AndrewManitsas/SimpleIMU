import serial

ser = serial.Serial(port='COM4', baudrate=115200, timeout=1)

if ser.is_open:
    print(f"Serial port {ser.port} is open.")

try:
    while True:
        data = ser.readline()
        if data:
            try:
                print("Received:", data.decode('utf-8').strip())
            except UnicodeDecodeError:
                print("Received (raw):", data)
except KeyboardInterrupt:
    print("Stopping reading...")

finally:
    ser.close()
    print("Serial port closed.")
