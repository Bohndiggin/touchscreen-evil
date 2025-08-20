import time
import usb_hid

# Find our custom joystick device
custom_joystick = None
for device in usb_hid.devices:
    if device.usage_page == 0x01 and device.usage == 0x04:  # Generic Desktop, Joystick
        custom_joystick = device
        print("Custom joystick device found!")
        break

if not custom_joystick:
    print("ERROR: Custom joystick device not found!")
    exit()

def test_button(button_num):
    """Test a specific button"""
    print(f"Testing button {button_num}...")
    
    # Create joystick report: Report ID + X + Y + 16 buttons
    report = bytearray(5)
    report[0] = 4    # Report ID
    report[1] = 0x80 # X axis center (128)
    report[2] = 0x80 # Y axis center (128)
    
    if button_num <= 8:
        # Buttons 1-8 in third byte
        report[3] = 1 << (button_num - 1)
        report[4] = 0
        print(f"Button {button_num}: report[3]=0x{report[3]:02x}, report[4]=0x{report[4]:02x}")
    elif button_num <= 16:
        # Buttons 9-16 in fourth byte  
        report[3] = 0
        report[4] = 1 << (button_num - 9)
        print(f"Button {button_num}: report[3]=0x{report[3]:02x}, report[4]=0x{report[4]:02x}")
    else:
        print(f"ERROR: Invalid button number {button_num}")
        return
    
    try:
        # Send button press
        custom_joystick.send_report(report)
        print(f"Sent button {button_num} press")
        time.sleep(0.1)
        
        # Send button release
        report[3] = 0
        report[4] = 0
        custom_joystick.send_report(report)
        print(f"Sent button {button_num} release")
        time.sleep(0.1)
        
    except Exception as e:
        print(f"Error sending button {button_num}: {e}")

# Test all buttons
for i in range(1, 17):
    test_button(i)
    time.sleep(0.5)

print("Button test complete")