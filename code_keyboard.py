import time
import usb.core
import usb.util
import usb_hid
import adafruit_usb_host_descriptors
import supervisor

supervisor.runtime.autoreload = False

SCREEN_WIDTH = 3800
SCREEN_HEIGHT = 3800

HID_CLASS = 0x03
HID_SUBCLASS = 0x00
HID_PROTOCOL = 0x00

REPEAT_DELAY = 0.5
MEDIA_KEY_TIMEOUT = 0.3
DEBOUNCE_TIME = 0.05
MEDIA_KEY_DEBOUNCE = 0.5

TOUCH_ZONES = [
    (300, 300, 1175, 1175, 0x2F, "["),
    (1175, 300, 2050, 1175, 0x2D, "-"),
    (2050, 300, 2925, 1175, 0x36, "<"),
    (2925, 300, 3800, 1175, 0xCD, "Play/Pause"),
    (300, 1175, 1175, 2050, 0x30, "]"),
    (1175, 1175, 2050, 2050, 0x2E, "="),
    (2050, 1175, 2925, 2050, 0x37, ">"),
    (2925, 1175, 3800, 2050, 0x50, "Left Arrow"),
    (300, 2050, 1175, 2925, 0xB6, "Prev Song"),
    (1175, 2050, 2050, 2925, 0x4A, "Home"),
    (2050, 2050, 2925, 2925, 0x52, "Up Arrow"),
    (2925, 2050, 3800, 2925, 0x51, "Down Arrow"),
    (300, 2925, 1175, 3800, 0xB5, "Next Song"),
    (1175, 2925, 2050, 3800, 0x4D, "End"),
    (2050, 2925, 2925, 3800, 0x28, "Enter"),
    (2925, 2925, 3800, 3800, 0x4F, "Right Arrow"),
]

MEDIA_KEYS = {0xCD, 0xB6, 0xB5}

keyboard = None
consumer_control = None
last_touch_state = False
last_key = None
last_touch_time = 0
last_media_key_time = 0
last_state_change_time = 0
last_media_key_sent = None

def initialize_hid_devices():
    global keyboard, consumer_control
    print("Checking for HID devices...")
    print(f"Total HID devices available: {len(usb_hid.devices)}")
    
    for device in usb_hid.devices:
        print(f"Found USB HID device: usage_page={device.usage_page:02x}, usage={device.usage:02x}")
        if device.usage_page == 0x01 and device.usage == 0x06:
            keyboard = device
            print("Keyboard device found and initialized!")
        elif device.usage_page == 0x0C and device.usage == 0x01:
            consumer_control = device
            print("Consumer Control device found and initialized!")
    
    if not keyboard:
        print("ERROR: Keyboard device not found!")
    if not consumer_control:
        print("ERROR: Consumer Control device not found!")

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
                        print("  -> Found HID interface!")
                        touchscreen_interface = config_descriptor[i + 2]
                        
                elif descriptor_type == adafruit_usb_host_descriptors.DESC_ENDPOINT and touchscreen_interface is not None:
                    endpoint_address = config_descriptor[i + 2]
                    if endpoint_address & 0x80:
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

def send_key_press(keycode, key_name):
    if not keycode:
        print("ERROR: Cannot send key - keycode is None or 0")
        return

    if keycode in MEDIA_KEYS:
        _send_media_key(keycode, key_name)
    else:
        _send_keyboard_key(keycode, key_name)

def _send_media_key(keycode, key_name):
    if not consumer_control:
        print("ERROR: Cannot send media key - no consumer control device available")
        return
        
    print(f"Sending media key '{key_name}' (keycode: 0x{keycode:02x})...")
    try:
        report = bytearray(2)
        report[0] = 5
        
        if keycode == 0xCD:
            report[1] = 0x01
        else:
            print(f"Media key {key_name} not supported in minimal descriptor")
            return
        
        print(f"Sending report: ID={report[0]}, bits: 0x{report[1]:02x}")
        
        consumer_control.send_report(report)
        time.sleep(0.1)
        
        report[1] = 0
        consumer_control.send_report(report)
        time.sleep(0.05)
        
        print(f"Successfully sent media key '{key_name}'")
    except Exception as e:
        print(f"Error sending media key '{key_name}': {e}")

def _send_keyboard_key(keycode, key_name):
    if not keyboard:
        print("ERROR: Cannot send key - no keyboard device available")
        return

    print(f"Sending key '{key_name}' (keycode: 0x{keycode:02x})...")
    try:
        report = bytearray(8)
        report[0] = 0
        report[1] = 0
        report[2] = keycode
        
        keyboard.send_report(report)
        time.sleep(0.05)
        
        report = bytearray(8)
        keyboard.send_report(report)
        time.sleep(0.01)
        
        print(f"Successfully sent key '{key_name}'")
    except Exception as e:
        print(f"Error sending key '{key_name}': {e}")

def parse_touchscreen_report(data):
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
    for zone in TOUCH_ZONES:
        x1, y1, x2, y2, keycode, key_name = zone
        if x1 <= x < x2 and y1 <= y < y2:
            return keycode, key_name
    return None, None

def process_touch_report(data):
    global last_touch_state, last_key, last_touch_time, last_media_key_time, last_state_change_time, last_media_key_sent
    
    touched, x, y = parse_touchscreen_report(data)
    current_time = time.monotonic()
    
    if touched != last_touch_state:
        if current_time - last_state_change_time < DEBOUNCE_TIME:
            return last_touch_state
        last_state_change_time = current_time
    
    if touched:
        keycode, key_name = find_touch_zone(x, y)
        if keycode:
            if keycode in MEDIA_KEYS:
                if (touched and not last_touch_state and 
                    (last_media_key_sent != keycode or 
                     current_time - last_media_key_time >= MEDIA_KEY_DEBOUNCE)):
                    print(f"Touch detected at ({x}, {y}) -> Sending media key '{key_name}'")
                    send_key_press(keycode, key_name)
                    last_key = keycode
                    last_touch_time = current_time
                    last_media_key_time = current_time
                    last_media_key_sent = keycode
            else:
                if (not last_touch_state or 
                    keycode != last_key or 
                    current_time - last_touch_time >= REPEAT_DELAY):
                    print(f"Touch detected at ({x}, {y}) -> Sending key '{key_name}'")
                    send_key_press(keycode, key_name)
                    last_key = keycode
                    last_touch_time = current_time
        else:
            print(f"Touch detected at ({x}, {y}) -> No zone mapped")
    
    if not touched and last_touch_state:
        last_media_key_sent = None
    
    last_touch_state = touched
    return touched

def display_touch_zones():
    print("Touch zones configured:")
    for i, zone in enumerate(TOUCH_ZONES):
        x1, y1, x2, y2, keycode, key_name = zone
        print(f"  Zone {i+1}: ({x1},{y1}) to ({x2},{y2}) -> {key_name} (0x{keycode:02x})")

def run_touch_event_loop(touchscreen_device, endpoint_addr, max_packet_size):
    try:
        touchscreen_device.set_configuration()
        print("Reading touch events... Touch the screen to trigger key presses")
        
        while True:
            try:
                buffer = bytearray(max_packet_size or 8)
                bytes_read = touchscreen_device.read(endpoint_addr, buffer, timeout=1000)
                if bytes_read > 0:
                    process_touch_report(buffer[:bytes_read])
                else:
                    print("Read returned 0 bytes")
                    
            except usb.core.USBTimeoutError:
                print(".", end="")
                continue
            except Exception as e:
                print(f"Read error: {e}")
                break
                
    except Exception as e:
        print(f"Error configuring touchscreen: {e}")

def main():
    initialize_hid_devices()
    print("Looking for USB touchscreen...")
    display_touch_zones()
    
    while True:
        touchscreen_device, endpoint_addr, max_packet_size = find_touchscreen_and_endpoint()
        
        if touchscreen_device and endpoint_addr:
            print(f"Found touchscreen: {touchscreen_device.product}")
            run_touch_event_loop(touchscreen_device, endpoint_addr, max_packet_size)
        else:
            print("No touchscreen found, retrying...")

if __name__ == "__main__":
    main()