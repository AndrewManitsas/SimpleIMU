import serial
import tkinter as tk
from tkinter import ttk
import datetime
import threading
from collections import deque

def parse_imu_data(data):
    """
    Parses the IMU data string and returns the acceleration and gyro values.

    Args:
        data (str): The IMU data string in the format "S0.05/0.11/1.01/-1.38/0.44/0.31E".

    Returns:
        tuple: A tuple containing (acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z).
               Returns None if the data string is invalid.
    """
    if not data.startswith("S") or not data.endswith("E"):
        return None  # Invalid data format

    try:
        values = data[1:-1].split("/")  # Remove 'S' and 'E', then split by '/'
        if len(values) != 6:
            return None  # Incorrect number of values

        # Convert the string values to floats.
        acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = map(float, values)
        return acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
    except ValueError:
        return None  # Error converting values to float

def moving_average_filter(data_queue, new_value, window_size=10):
    """
    Applies a moving average filter to the data.

    Args:
        data_queue (deque): A deque containing the previous data points.
        new_value (float): The new data point to add to the filter.
        window_size (int): The number of data points to average.

    Returns:
        float: The filtered data value.
    """
    data_queue.append(new_value)
    if len(data_queue) > window_size:
        data_queue.popleft()
    return sum(data_queue) / len(data_queue)

class IMUApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live IMU Data")
        self.root.geometry("400x400")  # Adjust size as needed

        # --- Serial Connection ---
        self.ser = None
        self.port = 'COM4'  # You may need to change this
        self.baudrate = 115200
        self.timeout = 1

        # --- UI Elements ---
        # Connection Info Label
        self.connection_info_label = ttk.Label(root, text="", font=("Arial", 10))
        self.connection_info_label.place(x=10, y=0)

        # Status Label and Label Frame
        self.status_label_frame = ttk.Frame(root)
        self.status_label_frame.place(x=5, y=40, relwidth=1)
        self.status_label_text = ttk.Label(self.status_label_frame, text="Connection Status: ", font=("Arial", 10))
        self.status_label_text.pack(side="left")
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.status_label_frame, textvariable=self.status_var, font=("Arial", 10, "italic"))
        self.status_label.pack(side="left")

        # Label for non-data messages
        self.non_data_label = ttk.Label(root, text="Non-Data Messages:")
        self.non_data_label.place(x=10, y=20)
        self.non_data_msg_var = tk.StringVar()
        self.non_data_msg_label = ttk.Label(root, textvariable=self.non_data_msg_var, font=("Arial", 10, "italic"))
        self.non_data_msg_label.place(x=150, y=20)

        # Separator
        ttk.Separator(root, orient='horizontal').place(x=5, y=70, relwidth=1)

        # Labels for the data values
        self.acc_label = ttk.Label(root, text="Acceleration (m/s^2)")
        self.acc_label.place(x=10, y=80)
        self.gyro_label = ttk.Label(root, text="Gyroscope (rad/s)")
        self.gyro_label.place(x=200, y=80)

        # Labels for the RAW data  VERTICAL display
        self.raw_label = ttk.Label(root, text="Raw Data", font=("Arial", 10, "bold"))
        self.raw_label.place(x=10, y=95) # Adjusted y-position

        self.acc_x_label_text = ttk.Label(root, text="Acc X:")
        self.acc_x_label_text.place(x=10, y=115)
        self.acc_x_var = tk.StringVar()
        self.acc_x_label = ttk.Label(root, textvariable=self.acc_x_var)
        self.acc_x_label.place(x=60, y=115)

        self.acc_y_label_text = ttk.Label(root, text="Acc Y:")
        self.acc_y_label_text.place(x=10, y=135)
        self.acc_y_var = tk.StringVar()
        self.acc_y_label = ttk.Label(root, textvariable=self.acc_y_var)
        self.acc_y_label.place(x=60, y=135)

        self.acc_z_label_text = ttk.Label(root, text="Acc Z:")
        self.acc_z_label_text.place(x=10, y=155)
        self.acc_z_var = tk.StringVar()
        self.acc_z_label = ttk.Label(root, textvariable=self.acc_z_var)
        self.acc_z_label.place(x=60, y=155)

        self.gyro_x_label_text = ttk.Label(root, text="Gyro X:")
        self.gyro_x_label_text.place(x=200, y=115)
        self.gyro_x_var = tk.StringVar()
        self.gyro_x_label = ttk.Label(root, textvariable=self.gyro_x_var)
        self.gyro_x_label.place(x=250, y=115)

        self.gyro_y_label_text = ttk.Label(root, text="Gyro Y:")
        self.gyro_y_label_text.place(x=200, y=135)
        self.gyro_y_var = tk.StringVar()
        self.gyro_y_label = ttk.Label(root, textvariable=self.gyro_y_var)
        self.gyro_y_label.place(x=250, y=135)

        self.gyro_z_label_text = ttk.Label(root, text="Gyro Z:")  # Added Gyro Z label
        self.gyro_z_label_text.place(x=200, y=155)
        self.gyro_z_var = tk.StringVar()
        self.gyro_z_label = ttk.Label(root, textvariable=self.gyro_z_var)
        self.gyro_z_label.place(x=250, y=155)

        # Labels for the FILTERED data  VERTICAL display
        self.filtered_label = ttk.Label(root, text=f"Filtered Data (Moving Average, Window Size={moving_average_filter.__defaults__[0]})", font=("Arial", 10, "bold"))
        self.filtered_label.place(x=10, y=175) # Adjusted y-position

        self.acc_x_filtered_label_text = ttk.Label(root, text="Acc X:")
        self.acc_x_filtered_label_text.place(x=10, y=195)
        self.acc_x_filtered_var = tk.StringVar()
        self.acc_x_filtered_label = ttk.Label(root, textvariable=self.acc_x_filtered_var)
        self.acc_x_filtered_label.place(x=60, y=195)

        self.acc_y_filtered_label_text = ttk.Label(root, text="Acc Y:")
        self.acc_y_filtered_label_text.place(x=10, y=215)
        self.acc_y_filtered_var = tk.StringVar()
        self.acc_y_filtered_label = ttk.Label(root, textvariable=self.acc_y_filtered_var)
        self.acc_y_filtered_label.place(x=60, y=215)

        self.acc_z_filtered_label_text = ttk.Label(root, text="Acc Z:")
        self.acc_z_filtered_label_text.place(x=10, y=235)
        self.acc_z_filtered_var = tk.StringVar()
        self.acc_z_filtered_label = ttk.Label(root, textvariable=self.acc_z_filtered_var)
        self.acc_z_filtered_label.place(x=60, y=235)

        self.gyro_x_filtered_label_text = ttk.Label(root, text="Gyro X:")
        self.gyro_x_filtered_label_text.place(x=200, y=195)
        self.gyro_x_filtered_var = tk.StringVar()
        self.gyro_x_filtered_label = ttk.Label(root, textvariable=self.gyro_x_filtered_var)
        self.gyro_x_filtered_label.place(x=250, y=195)

        self.gyro_y_filtered_label_text = ttk.Label(root, text="Gyro Y:")
        self.gyro_y_filtered_label_text.place(x=200, y=215)
        self.gyro_y_filtered_var = tk.StringVar()
        self.gyro_y_filtered_label = ttk.Label(root, textvariable=self.gyro_y_filtered_var)
        self.gyro_y_filtered_label.place(x=250, y=215)

        self.gyro_z_filtered_label_text = ttk.Label(root, text="Gyro Z:") # Added Gyro Z label
        self.gyro_z_filtered_text = ttk.Label(root, text="Gyro Z:")
        self.gyro_z_filtered_text.place(x=200, y=235)
        self.gyro_z_filtered_var = tk.StringVar()
        self.gyro_z_filtered_label = ttk.Label(root, textvariable=self.gyro_z_filtered_var)
        self.gyro_z_filtered_label.place(x=250, y=235)

        # --- Exit Button ---
        self.exit_button = ttk.Button(root, text="Exit", command=self.on_close)
        self.exit_button.place(x=150, y=300, relwidth=0.2)

        # --- Initialize Data Variables ---
        self.acc_x_var.set("0.00")
        self.acc_y_var.set("0.00")
        self.acc_z_var.set("0.00")
        self.gyro_x_var.set("0.00")
        self.gyro_y_var.set("0.00")
        self.gyro_z_var.set("0.00")

        self.acc_x_filtered_var.set("0.00")
        self.acc_y_filtered_var.set("0.00")
        self.acc_z_filtered_var.set("0.00")
        self.gyro_x_filtered_var.set("0.00")
        self.gyro_y_filtered_var.set("0.00")
        self.gyro_z_filtered_var.set("0.00")

        self.status_var.set("Connecting...")
        self.connection_info_label.config(text=f"Port: {self.port}, Baudrate: {self.baudrate}, Timeout: {self.timeout}")

        # --- Initialize filter data structures ---
        self.acc_x_queue = deque()
        self.acc_y_queue = deque()
        self.acc_z_queue = deque()
        self.gyro_x_queue = deque()
        self.gyro_y_queue = deque()
        self.gyro_z_queue = deque()

        # --- Start Serial Connection and Data Reading ---
        self.connect_serial()
        self.start_reading()

    def connect_serial(self):
        """
        Establishes the serial connection.
        """
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            self.status_var.set(f"Connected to {self.port}")
        except serial.SerialException as e:
            self.status_var.set(f"Error: {e}")
            self.ser = None  # Ensure self.ser is None on failure
            print(f"Error connecting to serial port: {e}")

    def start_reading(self):
        """
        Starts a thread to continuously read data from the serial port.
        """
        if self.ser is None:
            print("Serial port not connected.  Cannot start reading.")
            return

        self.reading_thread = threading.Thread(target=self.read_serial_data)
        self.reading_thread.daemon = True  # Allow the program to exit even if this thread is running
        self.reading_thread.start()

    def read_serial_data(self):
        """
        Reads data from the serial port, parses it, and updates the GUI.
        This function runs in a separate thread.
        """
        try:
            while True:
                data = self.ser.readline()
                if data:
                    data_str = data.decode('utf-8').strip()
                    imu_data = parse_imu_data(data_str)
                    if imu_data:
                        acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = imu_data
                        # Apply the moving average filter to each data stream
                        acc_x_filtered = moving_average_filter(self.acc_x_queue, acc_x)
                        acc_y_filtered = moving_average_filter(self.acc_y_queue, acc_y)
                        acc_z_filtered = moving_average_filter(self.acc_z_queue, acc_z)
                        gyro_x_filtered = moving_average_filter(self.gyro_x_queue, gyro_x)
                        gyro_y_filtered = moving_average_filter(self.gyro_y_queue, gyro_y)
                        gyro_z_filtered = moving_average_filter(self.gyro_z_queue, gyro_z)

                        # Update the GUI variables.  This must be done in the main thread.
                        self.root.after(0, self.update_gui, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z,
                                         acc_x_filtered, acc_y_filtered, acc_z_filtered, gyro_x_filtered, gyro_y_filtered, gyro_z_filtered)
                    else:
                        self.root.after(0, self.non_data_msg_var.set, data_str)
        except serial.SerialException as e:
            print(f"Error reading from serial port: {e}")
            self.root.after(0, self.status_var.set, f"Error: {e}")  # use root.after to update
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.root.after(0, self.connect_serial)  # attempt to reconnect
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.root.after(0, self.status_var.set, f"Error: {e}")
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.root.after(0, self.connect_serial)  # attempt to reconnect

    def update_gui(self, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z,
                   acc_x_filtered, acc_y_filtered, acc_z_filtered, gyro_x_filtered, gyro_y_filtered, gyro_z_filtered):
        """
        Updates the GUI labels with the latest IMU data.
        This function is called from the read_serial_data thread using root.after().
        """
        # RAW Data
        self.acc_x_var.set(f"{acc_x:.2f}")
        self.acc_y_var.set(f"{acc_y:.2f}")
        self.acc_z_var.set(f"{acc_z:.2f}")
        self.gyro_x_var.set(f"{gyro_x:.2f}")
        self.gyro_y_var.set(f"{gyro_y:.2f}")
        self.gyro_z_var.set(f"{gyro_z:.2f}")

        # Filtered Data
        self.acc_x_filtered_var.set(f"{acc_x_filtered:.2f}")
        self.acc_y_filtered_var.set(f"{acc_y_filtered:.2f}")
        self.acc_z_filtered_var.set(f"{acc_z_filtered:.2f}")
        self.gyro_x_filtered_var.set(f"{gyro_x_filtered:.2f}")
        self.gyro_y_filtered_var.set(f"{gyro_y_filtered:.2f}")
        self.gyro_z_filtered_var.set(f"{gyro_z_filtered:.2f}")

        self.status_var.set("Receiving Data")

    def on_close(self):
        """
        Closes the serial port when the application is closed.
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed.")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = IMUApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)  # Handle window close event
    root.mainloop()