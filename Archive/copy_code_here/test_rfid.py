import board
import busio
import time

def read_data_package(rfid_uart, poll_interval=0.01):
    try:
        print("Waiting for a data package...")
        start_time = time.monotonic()  # Start the timer
        # Wait for the start byte (\x02)
        while True:
            if rfid_uart.in_waiting:  # Check if there is data in the buffer
                byte = rfid_uart.read(1)  # Read one byte
                if byte == b'\x02':  # Found the start byte
                    break
            elif time.monotonic() - start_time > timeout:  # Timeout reached
                print("Timeout: No data received.")
                return None
            time.sleep(poll_interval)  # Pause briefly before polling again

        # Start building the package
        package = byte  # Include the header byte
        start_time = time.monotonic()  # Reset the timer for reading the package

        while True:
            if rfid_uart.in_waiting:  # Check if there is data in the buffer
                byte = rfid_uart.read(1)  # Read the next byte
                package += byte
                if byte == b'\x03':  # Found the end byte
                    break
            elif time.monotonic() - start_time > timeout:  # Timeout reached
                print("Timeout: Incomplete data package.")
                return None
            time.sleep(poll_interval)  # Pause briefly before polling again
        return package
    except Exception as e:
        print(f"Error reading data package: {e}")
        return None
    

def interpret_data_package(data_package):
    """
    Interprets a data package from the WL-134 module.

    Parameters:
    - data_package: A bytes object containing the data package, starting with \x02 and ending with \x03.

    Returns:
    - A dictionary with interpreted fields (card number, country code, flags, etc.),
      or None if the package is invalid.
    """
    # Validate package
    if not data_package or len(data_package) < 26:
        print("Invalid package: Too short or empty.")
        return None
    if data_package[0] != 0x02 or data_package[-1] != 0x03:
        print("Invalid package: Missing header or end byte.")
        return None

    try:
        # Strip header (\x02) and tail (\x03)
        payload = data_package[1:-1]

        # Extract fields
        card_number_bytes = payload[:10]  # First 10 bytes
        country_code_bytes = payload[10:14]  # Next 4 bytes
        data_flag = int(payload[14])  # Data flag (1 byte)
        animal_flag = int(payload[15])  # Animal flag (1 byte)
        reserved = payload[16:20].decode('ascii')  # Reserved (4 bytes)
        user_data = payload[20:26].decode('ascii')  # User data (6 bytes)
        checksum = payload[26]  # Checksum (1 byte)
        checksum_invert = payload[27]  # Checksum bitwise invert (1 byte)

        # Convert card number and country code (LSB first)
        card_number = int(''.join(reversed(card_number_bytes.decode('ascii'))), 16)
        country_code = int(''.join(reversed(country_code_bytes.decode('ascii'))), 16)

        # Verify checksum
        calculated_checksum = 0
        for byte in payload[:-2]:  # Exclude checksum and checksum_invert
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
    rx = board.D9
    baudrate = 9600
    timeout = 3
    rfid_uart = busio.UART(rx=rx, tx=None, baudrate=baudrate, timeout=timeout)
    while True:
        data_package = read_data_package(rfid_uart)
        if data_package:
            print(f"Received Data Package: {data_package}")
            r = interpret_data_package(data_package)
            print(r)
        else:
            print("Failed to receive a valid data package.")
