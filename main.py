import tkinter as tk
import win32gui
import win32con
import win32api

class RulerApp:
    def __init__(self):
        self.root = tk.Tk()
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        self.setup_visual_window()
        self.setup_handle_window()
        self.draw_rulers()
        
    def setup_visual_window(self):
        # --- Visual Window (The lines) ---
        self.visual_window = tk.Toplevel(self.root)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        self.visual_window.overrideredirect(True)
        self.visual_window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.visual_window.wm_attributes("-topmost", True)
        
        # Transparent background
        self.TRANS_COLOR = "#000001"
        self.visual_window.wm_attributes("-transparentcolor", self.TRANS_COLOR)
        # Semi-transparent window (0.6 opacity)
        self.visual_window.wm_attributes("-alpha", 0.6)
        self.visual_window.configure(bg=self.TRANS_COLOR)
        
        # Canvas
        self.canvas = tk.Canvas(
            self.visual_window,
            bg=self.TRANS_COLOR,
            highlightthickness=0,
            width=self.screen_width,
            height=self.screen_height
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initial positions
        self.cx = self.screen_width // 2
        self.cy = self.screen_height // 2
        self.ruler_width = 40 # Width of the ruler strip
        
        # Make Visual Window Click-Through using Win32 API
        # We need to wait for the window to be drawn to get its HWND
        self.visual_window.update()
        hwnd = win32gui.GetParent(self.visual_window.winfo_id())
        
        # Get current style
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        # Add WS_EX_TRANSPARENT (makes it ignore mouse events) and WS_EX_LAYERED (needed for transparency)
        style = style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)

    def setup_handle_window(self):
        # --- Handle Window (The intersection controller) ---
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # Make handle window invisible but clickable
        # We use a normal color but set alpha to near zero.
        # Note: Do NOT set transparentcolor, as that makes it click-through.
        self.root.configure(bg="white")
        self.root.wm_attributes("-alpha", 0.01)
        
        self.handle_size = 40 
        
        self.update_handle_geometry()
        
        # Bind events
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Keyboard movement
        self.root.bind("<Up>", lambda e: self.move_by_key(0, -1))
        self.root.bind("<Down>", lambda e: self.move_by_key(0, 1))
        self.root.bind("<Left>", lambda e: self.move_by_key(-1, 0))
        self.root.bind("<Right>", lambda e: self.move_by_key(1, 0))
        # Shift + Arrow for faster movement
        self.root.bind("<Shift-Up>", lambda e: self.move_by_key(0, -10))
        self.root.bind("<Shift-Down>", lambda e: self.move_by_key(0, 10))
        self.root.bind("<Shift-Left>", lambda e: self.move_by_key(-10, 0))
        self.root.bind("<Shift-Right>", lambda e: self.move_by_key(10, 0))
        
        # Ensure focus to receive key events
        self.root.focus_force()

    def move_by_key(self, dx, dy):
        self.cx += dx
        self.cy += dy
        self.update_handle_geometry()
        self.draw_rulers()

    def update_handle_geometry(self):
        # Position handle at the intersection (The red square area)
        # 0 point is at (cx, cy).
        # Vertical ruler is to the left of cx.
        # Horizontal ruler is below cy.
        
        x = self.cx - self.handle_size
        y = self.cy
        self.root.geometry(f"{self.handle_size}x{self.handle_size}+{x}+{y}")

    def draw_rulers(self):
        self.canvas.delete("all")
        
        # Colors and Fonts
        bg_color = "#F0F0F0" # Light gray like a physical ruler
        line_color = "black"
        text_color = "black"
        font_spec = ("Arial", 8)
        
        # Length to draw (enough to cover screen even if moved)
        length_v = self.screen_height * 3
        length_h = self.screen_width * 3
        
        # --- Vertical Ruler ---
        # Drawn to the LEFT of cx
        self.canvas.create_rectangle(
            self.cx - self.ruler_width, self.cy - length_v//2,
            self.cx, self.cy + length_v//2,
            fill=bg_color, outline="gray", tags="v_ruler"
        )
        
        # Ticks and Numbers
        # 0 is at cy. Up is negative, Down is positive.
        start_y = - (length_v // 2)
        end_y = length_v // 2
        
        for i in range(start_y, end_y, 10):
            y_pos = self.cy + i
            
            # Draw tick on the RIGHT edge of the vertical ruler (which is cx)
            right_edge = self.cx
            
            if i % 100 == 0:
                tick_len = self.ruler_width * 0.5
                # Text
                self.canvas.create_text(
                    right_edge - tick_len - 2, y_pos + 2, # Text to the left of tick
                    text=str(abs(i)), anchor="ne", fill=text_color, font=font_spec, tags="v_ruler"
                )
            elif i % 50 == 0:
                tick_len = self.ruler_width * 0.3
            else:
                tick_len = self.ruler_width * 0.15
            
            self.canvas.create_line(
                right_edge, y_pos, right_edge - tick_len, y_pos, # Line leftwards from right edge
                fill=line_color, tags="v_ruler"
            )

        # --- Horizontal Ruler ---
        # Drawn BELOW cy
        self.canvas.create_rectangle(
            self.cx - length_h//2, self.cy,
            self.cx + length_h//2, self.cy + self.ruler_width,
            fill=bg_color, outline="gray", tags="h_ruler"
        )
        
        start_x = - (length_h // 2)
        end_x = length_h // 2
        
        for i in range(start_x, end_x, 10):
            x_pos = self.cx + i
            
            # Draw tick on the TOP edge of the horizontal ruler (which is cy)
            top_edge = self.cy
            
            if i % 100 == 0:
                tick_len = self.ruler_width * 0.5
                self.canvas.create_text(
                    x_pos + 2, top_edge + tick_len + 2, # Text below tick
                    text=str(abs(i)), anchor="nw", fill=text_color, font=font_spec, tags="h_ruler"
                )
            elif i % 50 == 0:
                tick_len = self.ruler_width * 0.3
            else:
                tick_len = self.ruler_width * 0.15
            
            self.canvas.create_line(
                x_pos, top_edge, x_pos, top_edge + tick_len, # Line downwards from top
                fill=line_color, tags="h_ruler"
            )

    def start_drag(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

    def on_drag(self, event):
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        # Move handle window
        self.cx += dx
        self.cy += dy
        self.update_handle_geometry()
        
        # Move visual elements
        self.canvas.move("v_ruler", dx, dy)
        self.canvas.move("h_ruler", dx, dy)
        
        # Update drag start for next event (relative movement)
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = RulerApp()
        app.run()
    except Exception as e:
        with open("error.log", "w") as f:
            f.write(str(e))
