import board
import busio
import time
from components import MyDigital


class MyRFID:
    def __init__(self):
        """
        Initialize the RFIDReader object.

        Parameters:
        - rx_pin: Pin for UART RX.
        - baudrate: Baud rate for the UART communication.
        - timeout: Timeout for reading data.
        - poll_interval: Time interval (in seconds) between polling attempts.
        """
        self.rx_pin=board.D9
        self.rst= MyDigital(board.D11, direction="output")
        self.baudrate = 9600
        self.timeout = 3
        self.poll_interval = 0.01
        self.rfid_uart = busio.UART(rx=self.rx_pin, tx=None, baudrate=self.baudrate, timeout=self.timeout)
        
    
    def reset(self):
        self.rst.write(True)
        time.sleep(10/1000)
        self.rst.write(False)
        print(self.rst.pin.value)

    def read_data_package(self):
        """
        Reads a data package from the RFID module.
        
        Returns:
        - A bytes object containing the data package or None if reading fails.
        """
        try:
            print("Waiting for a data package...")
            start_time = time.monotonic()  # Start the timer
            
            # Wait for the start byte (\x02)
            while True:
                if self.rfid_uart.in_waiting:
                    byte = self.rfid_uart.read(1)
                    if byte == b'\x02':  # Found the start byte
                        break
                elif time.monotonic() - start_time > self.timeout:
                    print("Timeout: No data received.")
                    return None
                time.sleep(self.poll_interval)

            # Start building the package
            package = byte
            start_time = time.monotonic()

            while True:
                if self.rfid_uart.in_waiting:
                    byte = self.rfid_uart.read(1)
                    package += byte
                    if byte == b'\x03':  # Found the end byte
                        break
                elif time.monotonic() - start_time > self.timeout:
                    print("Timeout: Incomplete data package.")
                    return None
                time.sleep(self.poll_interval)

            return package
        except Exception as e:
            print(f"Error reading data package: {e}")
            return None

    @staticmethod
    def interpret_data_package(data_package):
        """
        Interprets a data package from the RFID module.

        Parameters:
        - data_package: A bytes object containing the data package.

        Returns:
        - A dictionary with interpreted fields or None if the package is invalid.
        """
        if not data_package or len(data_package) < 29:
            print("Invalid package: Too short or empty.")
            return data_package
        if data_package[0] != 0x02 or data_package[-1] != 0x03:
            print("Invalid package: Missing header or end byte.")
            return data_package

        try:
            payload = data_package[1:-1]

            card_number_bytes = payload[:10]
            country_code_bytes = payload[10:14]
            data_flag = int(payload[14])
            animal_flag = int(payload[15])
            reserved = payload[16:20].decode('ascii')
            user_data = payload[20:26].decode('ascii')
            checksum = payload[26]
            checksum_invert = payload[27]

            card_number = int(''.join(reversed(card_number_bytes.decode('ascii'))), 16)
            country_code = int(''.join(reversed(country_code_bytes.decode('ascii'))), 16)

            calculated_checksum = 0
            for byte in payload[:-2]:
                calculated_checksum ^= byte
            if calculated_checksum != checksum:
                print(f"Checksum mismatch! Calculated: {calculated_checksum}, Received: {checksum}")
                return None

            return {
                "card_number": card_number,
                "country_code": country_code,
                "data_flag": data_flag,
                "animal_flag": animal_flag,
                "reserved": reserved,
                "user_data": user_data,
                "checksum": checksum,
                "checksum_invert": checksum_invert,
            }

        except Exception as e:
            print(f"Error interpreting data package: {e}")
            return None


# Example usage
if __name__ == "__main__":
    rfid_reader = MyRFID()
    rfid_reader.reset()
    time.sleep(1)
    x = rfid_reader.read_data_package()
        
