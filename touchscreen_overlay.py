#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import colorsys

class TouchscreenOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Touchscreen Zone Overlay")
        self.fullscreen = False
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Set fixed size to 1024x768
        self.root.geometry("1024x768")
        self.root.resizable(True, True)  # Allow resizing but start at fixed size
        
        self.canvas = tk.Canvas(self.root, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind resize event to recalculate zones
        self.root.bind('<Configure>', self.on_resize)
        
        # Initialize after a short delay to ensure canvas is sized
        self.root.after(100, self.initialize_overlay)
        
    def initialize_overlay(self):
        """Initialize overlay after canvas is properly sized"""
        self.calculate_touch_zones()
        self.draw_zones()
        self.add_coordinates_display()
        
    def calculate_touch_zones(self):
        """Calculate 16 touch zones in 4x4 grid based on current canvas size"""
        self.root.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Fallback to 1024x768 if canvas not ready
        if canvas_width <= 1:
            canvas_width = 1024
        if canvas_height <= 1:
            canvas_height = 768
        
        zone_width = canvas_width // 4
        zone_height = canvas_height // 4
        
        self.touch_zones = []
        # Mirror the layout horizontally to match physical touchscreen
        # Button layout: 1 5 9 13 / 2 6 10 14 / 3 7 11 15 / 4 8 12 16
        buttons = ['Button1', 'Button5', 'Button9', 'Button13', 'Button2', 'Button6', 'Button10', 'Button14', 
                  'Button3', 'Button7', 'Button11', 'Button15', 'Button4', 'Button8', 'Button12', 'Button16']
        button_nums = [1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15, 4, 8, 12, 16]
        
        for row in range(4):
            for col in range(4):
                x1 = col * zone_width
                y1 = row * zone_height
                x2 = x1 + zone_width
                y2 = y1 + zone_height
                
                idx = row * 4 + col
                self.touch_zones.append((x1, y1, x2, y2, button_nums[idx], buttons[idx]))
    
    def on_resize(self, event=None):
        """Handle window resize events"""
        if event and event.widget == self.root:
            # Delay redraw to avoid too frequent updates
            if hasattr(self, '_resize_timer'):
                self.root.after_cancel(self._resize_timer)
            self._resize_timer = self.root.after(100, self.redraw_overlay)
    
    def redraw_overlay(self):
        """Redraw the overlay after resize"""
        self.calculate_touch_zones()
        self.canvas.delete("all")
        self.draw_zones()
        self.add_coordinates_display()
        
    def generate_colors(self, num_colors):
        """Generate visually distinct colors"""
        colors = []
        for i in range(num_colors):
            hue = i / num_colors
            saturation = 0.7
            lightness = 0.6
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        return colors
        
    def draw_zones(self):
        """Draw all touch zones as colored rectangles with labels"""
        if not hasattr(self, 'touch_zones') or not self.touch_zones:
            return
            
        colors = self.generate_colors(len(self.touch_zones))
        
        for i, (x1, y1, x2, y2, button_num, button_name) in enumerate(self.touch_zones):
            color = colors[i]
            
            # Draw rectangle
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline='white',
                width=2,
                tags=f"zone_{i}"
            )
            
            # Calculate center for text
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Calculate font size based on zone size
            zone_width = x2 - x1
            zone_height = y2 - y1
            font_size = min(zone_width, zone_height) // 10
            font_size = max(12, min(font_size, 24))  # Clamp between 12 and 24
            
            # Draw button name
            self.canvas.create_text(
                center_x, center_y - font_size,
                text=f"{button_name}",
                fill='white',
                font=('Arial', font_size, 'bold'),
                tags=f"zone_{i}"
            )
            
            # Draw coordinates (smaller font)
            coord_font_size = max(8, font_size - 4)
            self.canvas.create_text(
                center_x, center_y,
                text=f"({x1},{y1})",
                fill='white',
                font=('Arial', coord_font_size),
                tags=f"zone_{i}"
            )
            
            self.canvas.create_text(
                center_x, center_y + coord_font_size + 2,
                text=f"({x2},{y2})",
                fill='white',
                font=('Arial', coord_font_size),
                tags=f"zone_{i}"
            )
            
            # Draw button number
            self.canvas.create_text(
                center_x, center_y + font_size,
                text=f"Button #{button_num}",
                fill='white',
                font=('Arial', coord_font_size),
                tags=f"zone_{i}"
            )
    
    def add_coordinates_display(self):
        """Add mouse coordinates display"""
        self.coord_label = tk.Label(
            self.root,
            text="Mouse: (0, 0)",
            bg='yellow',
            fg='black',
            font=('Arial', 12, 'bold')
        )
        self.coord_label.place(x=10, y=10)
        
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<Button-1>', self.on_click)
        
    def on_mouse_move(self, event):
        """Update coordinate display on mouse movement"""
        self.coord_label.config(text=f"Mouse: ({event.x}, {event.y})")
        
    def on_click(self, event):
        """Handle mouse clicks to show which zone was clicked"""
        x, y = event.x, event.y
        if hasattr(self, 'touch_zones'):
            for i, (x1, y1, x2, y2, button_num, button_name) in enumerate(self.touch_zones):
                if x1 <= x <= x2 and y1 <= y <= y2:
                    print(f"Clicked zone {i+1}: {button_name} at ({x}, {y})")
                    # Briefly highlight the clicked zone
                    self.highlight_zone(i)
                    break
            else:
                print(f"Clicked outside zones at ({x}, {y})")
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode with F11"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        if self.fullscreen:
            self.root.configure(cursor='none')
        else:
            self.root.configure(cursor='')
        
        # Recalculate zones after fullscreen toggle
        self.root.after(100, self.redraw_overlay)
    
    def highlight_zone(self, zone_index):
        """Briefly highlight a zone when clicked"""
        # Flash the zone border
        zone_items = self.canvas.find_withtag(f"zone_{zone_index}")
        for item in zone_items:
            if self.canvas.type(item) == 'rectangle':
                original_outline = self.canvas.itemcget(item, 'outline')
                self.canvas.itemconfig(item, outline='red', width=4)
                self.root.after(200, lambda: self.canvas.itemconfig(item, outline=original_outline, width=2))
    
    def run(self):
        """Start the GUI"""
        print("Touchscreen Zone Overlay")
        print("- Move mouse to see coordinates")
        print("- Click zones to test detection")
        print("- Press F11 to toggle fullscreen")
        print("- Press Escape to exit")
        self.root.mainloop()

if __name__ == "__main__":
    overlay = TouchscreenOverlay()
    overlay.run()