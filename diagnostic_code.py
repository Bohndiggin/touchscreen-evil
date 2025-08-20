import time
import usb.core
import usb.util
import adafruit_usb_host_descriptors
import supervisor
supervisor.runtime.autoreload = False

def find_touchscreen_and_endpoint():
    print("Scanning for USB devices...")
    device_count = 0
    
    for device in usb.core.find(find_all=True):
        device_count += 1
        try:
            print(f"Device {device_count}: VID:{device.idVendor:04x} PID:{device.idProduct:04x}")
            if hasattr(device, 'product') and device.product:
                print(f"  Product: {device.product}")
            
            config_descriptor = adafruit_usb_host_descriptors.get_configuration_descriptor(device, 0)
            i = 0
            touchscreen_interface = None
            endpoint_addr = None
            
            while i < len(config_descriptor):
                descriptor_len = config_descriptor[i]
                descriptor_type = config_descriptor[i + 1]
                
                if descriptor_type == adafruit_usb_host_descriptors.DESC_INTERFACE:
                    interface_class = config_descriptor[i + 5]
                    interface_subclass = config_descriptor[i + 6]
                    interface_protocol = config_descriptor[i + 7]
                    print(f"  Interface: Class={interface_class:02x} Sub={interface_subclass:02x} Proto={interface_protocol:02x}")
                    
                    if interface_class == 0x03:  # HID_CLASS
                        print(f"  -> Found HID interface!")
                        touchscreen_interface = config_descriptor[i + 2]
                        
                elif descriptor_type == adafruit_usb_host_descriptors.DESC_ENDPOINT and touchscreen_interface is not None:
                    endpoint_address = config_descriptor[i + 2]
                    if endpoint_address & 0x80:  # Input endpoint
                        endpoint_addr = endpoint_address
                        max_packet_size = config_descriptor[i + 4]
                        print(f"  -> Found input endpoint: {endpoint_addr:02x}, packet size: {max_packet_size}")
                        return device, endpoint_addr, max_packet_size
                        
                i += descriptor_len
        except Exception as e:
            print(f"Error checking device {device_count}: {e}")
            continue
    
    print(f"Scanned {device_count} devices, no suitable touchscreen found")
    return None, None, None

def parse_touchscreen_report(data):
    """Parse touchscreen HID report and show multiple interpretations"""
    if len(data) < 6:
        return False, 0, 0, ""
    
    # Show raw bytes
    raw_hex = " ".join([f"{b:02x}" for b in data])
    
    # Try different parsing methods
    touch_state = data[1] > 0
    
    # Method 1: Current assumption (little endian, bytes 2-3 = X, 4-5 = Y)
    x1 = data[2] | (data[3] << 8)
    y1 = data[4] | (data[5] << 8)
    
    # Method 2: Big endian
    x2 = data[3] | (data[2] << 8)
    y2 = data[5] | (data[4] << 8)
    
    # Method 3: Different byte positions
    x3 = data[0] | (data[1] << 8) if len(data) > 1 else 0
    y3 = data[2] | (data[3] << 8) if len(data) > 3 else 0
    
    # Method 4: Try bytes 1-2, 3-4
    x4 = data[1] | (data[2] << 8) if len(data) > 2 else 0
    y4 = data[3] | (data[4] << 8) if len(data) > 4 else 0
    
    interpretations = f"Raw: {raw_hex} | LE_2345: ({x1},{y1}) | BE_2345: ({x2},{y2}) | LE_0123: ({x3},{y3}) | LE_1234: ({x4},{y4})"
    
    return bool(touch_state), x1, y1, interpretations

def log_touch_event(x, y, interpretations):
    """Log touch coordinates to console"""
    current_time = time.monotonic()
    print(f"=== TOUCH EVENT ===")
    print(f"Time: {current_time:.2f}s")
    print(f"Primary coordinates: ({x}, {y})")
    print(f"All interpretations: {interpretations}")
    print(f"===================")

print("=== TouchScreen Coordinate Diagnostic ===")
print("Instructions: Touch corners in this order:")
print("1. Top-Left")
print("2. Top-Right") 
print("3. Bottom-Left")
print("4. Bottom-Right")
print("==========================================")

print("Looking for USB touchscreen...")

# Global variables for touch state tracking
last_touch_state = False
last_touch_time = 0
TOUCH_DELAY = 0.3  # Minimum time between logged touches

while True:
    touchscreen_device, endpoint_addr, max_packet_size = find_touchscreen_and_endpoint()
    
    if touchscreen_device and endpoint_addr:
        print(f"Found touchscreen: {touchscreen_device.product}")
        try:
            touchscreen_device.set_configuration()
            print("Reading touch events... Touch corners now!")
            
            while True:
                try:
                    buffer = bytearray(max_packet_size or 8)
                    bytes_read = touchscreen_device.read(endpoint_addr, buffer, timeout=1000)
                    if bytes_read > 0:
                        touched, x, y, interpretations = parse_touchscreen_report(buffer[:bytes_read])
                        current_time = time.monotonic()
                        
                        if touched and (not last_touch_state or current_time - last_touch_time >= TOUCH_DELAY):
                            log_touch_event(x, y, interpretations)
                            last_touch_time = current_time
                        
                        last_touch_state = touched
                    else:
                        print(".", end="")
                        
                except usb.core.USBTimeoutError:
                    print(".", end="")
                    continue
                except Exception as e:
                    print(f"Read error: {e}")
                    break
                    
        except Exception as e:
            print(f"Error configuring touchscreen: {e}")
    else:
        print("No touchscreen found, retrying...")
    
    time.sleep(2)