import usb_hid

# Define a custom joystick HID descriptor with 16 buttons
JOYSTICK_REPORT_DESCRIPTOR = bytes((
    0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
    0x09, 0x04,        # Usage (Joystick)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x04,        #   Report ID (4)
    
    # X and Y axes (dummy - we'll send 0x80 for center)
    0x05, 0x01,        #   Usage Page (Generic Desktop Ctrls)
    0x09, 0x30,        #   Usage (X)
    0x09, 0x31,        #   Usage (Y)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x02,        #   Report Count (2)
    0x81, 0x02,        #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    
    # 16 buttons
    0x05, 0x09,        #   Usage Page (Button)
    0x19, 0x01,        #   Usage Minimum (0x01) - Start from button 1
    0x29, 0x10,        #   Usage Maximum (0x10) - End at button 16
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x10,        #   Report Count (16)
    0x81, 0x02,        #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    
    0xC0,              # End Collection
))

# Define a minimal Consumer Control HID descriptor - just Play/Pause
CONSUMER_CONTROL_REPORT_DESCRIPTOR = bytes((
    0x05, 0x0C,        # Usage Page (Consumer)
    0x09, 0x01,        # Usage (Consumer Control)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x05,        #   Report ID (5)
    
    # Single Play/Pause button
    0x09, 0xCD,        #   Usage (Play/Pause)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    # Padding (7 bits to complete the byte)
    0x75, 0x07,        #   Report Size (7)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x01,        #   Input (Const,Array,Abs)
    
    0xC0,              # End Collection
))

# Create the custom HID devices
custom_joystick = usb_hid.Device(
    report_descriptor=JOYSTICK_REPORT_DESCRIPTOR,
    usage_page=0x01,           # Generic Desktop Control
    usage=0x04,                # Joystick
    report_ids=(4,),           # Descriptor uses report ID 4
    in_report_lengths=(5,),    # X(1) + Y(1) + buttons(2) + report_id = 5 bytes
    out_report_lengths=(0,),   # No output reports
)

consumer_control = usb_hid.Device(
    report_descriptor=CONSUMER_CONTROL_REPORT_DESCRIPTOR,
    usage_page=0x0C,           # Consumer
    usage=0x01,                # Consumer Control
    report_ids=(5,),           # Descriptor uses report ID 5
    in_report_lengths=(2,),    # Report ID + 1 byte for 1 bit + 7 padding
    out_report_lengths=(0,),   # No output reports
)

# Enable the custom HID devices along with default keyboard and mouse
usb_hid.enable((custom_joystick, consumer_control, usb_hid.Device.KEYBOARD, usb_hid.Device.MOUSE))