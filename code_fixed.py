import time
import usb.core
import usb.util
import usb_hid
import adafruit_usb_host_descriptors
import supervisor
supervisor.runtime.autoreload = False

# Find our custom joystick device
custom_joystick = None
available_device = None
print("Checking for custom joystick device...")
print(f"Total HID devices available: {len(usb_hid.devices)}")

for device in usb_hid.devices:
    print(f"Found USB HID device: usage_page={device.usage_page:02x}, usage={device.usage:02x}")
    # Save the first available device as fallback
    if not available_device:
        available_device = device
    # Look for our custom joystick
    if device.usage_page == 0x01 and device.usage == 0x04:  # Generic Desktop, Joystick
        custom_joystick = device
        print("Custom joystick device found and initialized!")
        break

if not custom_joystick:
    print("ERROR: Custom joystick device not found!")
    print("This means boot.py is not configured or device needs reset.")
    if available_device:
        print(f"Using fallback device: usage_page={available_device.usage_page:02x}, usage={available_device.usage:02x}")
        custom_joystick = available_device
    else:
        print("No HID devices available at all!")

# Touch zone mappings: (x1, y1, x2, y2, button_num, button_name)
# 16 buttons for gamepad compatibility
# 16 evenly spaced sections using actual coordinate ranges (300-3800)
# Grid: 4x4 layout, each section is 875x875 pixels
TOUCH_ZONES = [
    (300, 300, 1175, 1175, 1, "Button1"),     # Row 1, Col 1
    (1175, 300, 2050, 1175, 2, "Button2"),    # Row 1, Col 2
    (2050, 300, 2925, 1175, 3, "Button3"),    # Row 1, Col 3
    (2925, 300, 3800, 1175, 4, "Button4"),    # Row 1, Col 4
    (300, 1175, 1175, 2050, 5, "Button5"),    # Row 2, Col 1
    (1175, 1175, 2050, 2050, 6, "Button6"),   # Row 2, Col 2
    (2050, 1175, 2925, 2050, 7, "Button7"),   # Row 2, Col 3
    (2925, 1175, 3800, 2050, 8, "Button8"),   # Row 2, Col 4
    (300, 2050, 1175, 2925, 9, "Button9"),    # Row 3, Col 1
    (1175, 2050, 2050, 2925, 10, "Button10"), # Row 3, Col 2
    (2050, 2050, 2925, 2925, 11, "Button11"), # Row 3, Col 3
    (2925, 2050, 3800, 2925, 12, "Button12"), # Row 3, Col 4
    (300, 2925, 1175, 3800, 13, "Button13"),  # Row 4, Col 1
    (1175, 2925, 2050, 3800, 14, "Button14"), # Row 4, Col 2
    (2050, 2925, 2925, 3800, 15, "Button15"), # Row 4, Col 3
    (2925, 2925, 3800, 3800, 16, "Button16"), # Row 4, Col 4
]

# Touchscreen resolution (updated to actual coordinate range)
SCREEN_WIDTH = 3800
SCREEN_HEIGHT = 3800

# HID class constants
HID_CLASS = 0x03
HID_SUBCLASS = 0x00
HID_PROTOCOL = 0x00

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
                    
                    if interface_class == HID_CLASS:
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

def send_button_press(button_num):
    """Send a button press through custom joystick or fallback to keyboard"""
    if not button_num:
        print("ERROR: Cannot send button - button_num is None or 0")
        return
        
    if not custom_joystick:
        print("ERROR: Cannot send button - no HID device available")
        return

    # Check if this is our custom joystick (usage 0x04) or fallback keyboard (usage 0x06)
    if custom_joystick.usage == 0x04:
        # Custom joystick mode
        print(f"Sending joystick button {button_num}...")
        try:
            # Create joystick report: Report ID + X + Y + 16 buttons
            report = bytearray(5)
            report[0] = 4    # Report ID
            report[1] = 0x80 # X axis center (128)
            report[2] = 0x80 # Y axis center (128)
            
            if button_num <= 8:
                # Buttons 1-8 in third byte
                report[3] = 1 << (button_num - 1)
                report[4] = 0
            elif button_num <= 16:
                # Buttons 9-16 in fourth byte  
                report[3] = 0
                report[4] = 1 << (button_num - 9)
            else:
                print(f"ERROR: Invalid button number {button_num}, must be 1-16")
                return
            
            # Send button press
            custom_joystick.send_report(report)
            time.sleep(0.05)
            
            # Send button release
            report[3] = 0
            report[4] = 0
            custom_joystick.send_report(report)
            time.sleep(0.01)
            
            print(f"Successfully sent joystick button {button_num}")
        except Exception as e:
            print(f"Error sending joystick button {button_num}: {e}")
    else:
        # Fallback keyboard mode - map buttons to keys A-P
        print(f"Sending button {button_num} as keyboard key...")
        try:
            keycode = button_num + 3  # Button 1 = keycode 4 (A), Button 16 = keycode 19 (P)
            
            # Key press
            report = bytearray(8)
            report[2] = keycode
            custom_joystick.send_report(report)
            time.sleep(0.01)
            
            # Key release
            report[2] = 0
            custom_joystick.send_report(report)
            time.sleep(0.01)
            print(f"Successfully sent button {button_num} as key {chr(ord('A') + button_num - 1)}")
        except Exception as e:
            print(f"Error sending button {button_num}: {e}")

def parse_touchscreen_report(data):
    """Parse touchscreen HID report to extract touch state and coordinates"""
    if len(data) < 6:
        return False, 0, 0
    
    touch_state = data[1] > 0
    x = data[2] | (data[3] << 8)
    y = data[4] | (data[5] << 8)
    
    scaled_x = x
    scaled_y = y
    
    if scaled_x > SCREEN_WIDTH:
        scaled_x = int((x / 4096.0) * SCREEN_WIDTH)
    if scaled_y > SCREEN_HEIGHT:
        scaled_y = int((y / 3072.0) * SCREEN_HEIGHT)
    return bool(touch_state), scaled_x, scaled_y

def find_touch_zone(x, y):
    """Check if coordinates fall within any defined touch zone"""
    for zone in TOUCH_ZONES:
        x1, y1, x2, y2, button_num, button_name = zone
        if x1 <= x < x2 and y1 <= y < y2:
            return button_num, button_name
    return None, None

# Global variables for touch state tracking
last_touch_state = False
last_button = None
last_touch_time = 0
REPEAT_DELAY = 0.5  # Time between repeated button presses in seconds

def process_touch_report(data):
    """Process touchscreen report and send appropriate button press"""
    global last_touch_state, last_button, last_touch_time
    
    touched, x, y = parse_touchscreen_report(data)
    current_time = time.monotonic()
    
    if touched:
        button_num, button_name = find_touch_zone(x, y)
        if button_num:
            # Send button on initial touch or after repeat delay
            if (not last_touch_state or 
                button_num != last_button or 
                current_time - last_touch_time >= REPEAT_DELAY):
                print(f"Touch detected at ({x}, {y}) -> Sending button '{button_name}'")
                send_button_press(button_num)
                last_button = button_num
                last_touch_time = current_time
        else:
            print(f"Touch detected at ({x}, {y}) -> No zone mapped")
    
    last_touch_state = touched
    return touched


print("Looking for USB touchscreen...")
print("Touch zones configured:")
for i, zone in enumerate(TOUCH_ZONES):
    x1, y1, x2, y2, button_num, button_name = zone
    print(f"  Zone {i+1}: ({x1},{y1}) to ({x2},{y2}) -> {button_name}")

while True:
    touchscreen_device, endpoint_addr, max_packet_size = find_touchscreen_and_endpoint()
    
    if touchscreen_device and endpoint_addr:
        print(f"Found touchscreen: {touchscreen_device.product}")
        try:
            touchscreen_device.set_configuration()
            print("Reading touch events... Touch the screen to trigger button presses")
            
            while True:
                try:
                    buffer = bytearray(max_packet_size or 8)
                    bytes_read = touchscreen_device.read(endpoint_addr, buffer, timeout=1000)
                    if bytes_read > 0:
                        process_touch_report(buffer[:bytes_read])
                    else:
                        print("Read returned 0 bytes")
                        
                except usb.core.USBTimeoutError:
                    print(".", end="")  # Show we're still alive
                    continue
                except Exception as e:
                    print(f"Read error: {e}")
                    break
                    
        except Exception as e:
            print(f"Error configuring touchscreen: {e}")
    else:
        print("No touchscreen found, retrying...")
    
    time.sleep(2)