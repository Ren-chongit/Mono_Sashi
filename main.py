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
        # Virtual Screen Information for Multi-monitor support
        self.v_screen_left = win32api.GetSystemMetrics(76) # SM_XVIRTUALSCREEN
        self.v_screen_top = win32api.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        self.v_screen_width = win32api.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
        self.v_screen_height = win32api.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
        
        self.visual_window.overrideredirect(True)
        self.visual_window.geometry(f"{self.v_screen_width}x{self.v_screen_height}+{self.v_screen_left}+{self.v_screen_top}")
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
            width=self.v_screen_width,
            height=self.v_screen_height
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initial positions (Center of the primary screen, or center of virtual screen?)
        # Let's keep it simple and start at center of primary screen as before, 
        # but we need to make sure we have those values.
        # winfo_screenwidth/height return primary monitor size.
        primary_w = self.root.winfo_screenwidth()
        primary_h = self.root.winfo_screenheight()
        
        self.cx = primary_w // 2
        self.cy = primary_h // 2
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
        
        # Context Menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="次のモニターへ移動", command=self.move_to_next_monitor)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="終了", command=self.root.quit)
        
        self.root.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def get_all_monitors(self):
        return win32api.EnumDisplayMonitors()

    def get_current_monitor_rect(self):
        try:
            h_monitor = win32api.MonitorFromPoint((self.cx, self.cy), win32con.MONITOR_DEFAULTTONEAREST)
            monitor_info = win32api.GetMonitorInfo(h_monitor)
            return monitor_info['Monitor'] # (left, top, right, bottom)
        except:
            # Fallback to primary screen if something fails
            return (0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())

    def move_to_next_monitor(self):
        monitors = self.get_all_monitors()
        if not monitors:
            return
            
        current_h_monitor = win32api.MonitorFromPoint((self.cx, self.cy), win32con.MONITOR_DEFAULTTONEAREST)
        
        current_index = 0
        for i, (h_monitor, _, _) in enumerate(monitors):
            if h_monitor == current_h_monitor:
                current_index = i
                break
        
        next_index = (current_index + 1) % len(monitors)
        next_monitor = monitors[next_index]
        
        # next_monitor is (hMonitor, hdcMonitor, PyRECT)
        # PyRECT is (left, top, right, bottom)
        rect = next_monitor[2]
        left, top, right, bottom = rect
        
        # Move to center of new monitor
        self.cx = (left + right) // 2
        self.cy = (top + bottom) // 2
        
        self.update_handle_geometry()
        self.draw_rulers()

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
        
        # Get current monitor bounds to clip lines
        m_left, m_top, m_right, m_bottom = self.get_current_monitor_rect()
        
        # Coordinate transformation: Screen -> Canvas
        # canvas_x = screen_x - self.v_screen_left
        # canvas_y = screen_y - self.v_screen_top
        
        cx_canvas = self.cx - self.v_screen_left
        cy_canvas = self.cy - self.v_screen_top
        
        # Calculate start/end points clipped to monitor
        # Vertical ruler: x is constant (cx), y varies from m_top to m_bottom
        v_start_y = m_top - self.v_screen_top
        v_end_y = m_bottom - self.v_screen_top
        
        # Horizontal ruler: y is constant (cy), x varies from m_left to m_right
        h_start_x = m_left - self.v_screen_left
        h_end_x = m_right - self.v_screen_left
        
        # --- Vertical Ruler ---
        # Drawn to the LEFT of cx
        self.canvas.create_rectangle(
            cx_canvas - self.ruler_width, v_start_y,
            cx_canvas, v_end_y,
            fill=bg_color, outline="gray", tags="v_ruler"
        )
        
        # Ticks and Numbers
        # 0 is at cy. Up is negative, Down is positive.
        # We need to iterate from top of monitor to bottom of monitor relative to cy
        
        # range start/end relative to cy
        range_start_y = m_top - self.cy
        range_end_y = m_bottom - self.cy
        
        # Align to 10
        range_start_y = (range_start_y // 10) * 10
        
        for i in range(range_start_y, range_end_y, 10):
            y_pos = self.cy + i
            y_pos_canvas = y_pos - self.v_screen_top
            
            # Draw tick on the RIGHT edge of the vertical ruler (which is cx)
            right_edge_canvas = cx_canvas
            
            if i % 100 == 0:
                tick_len = self.ruler_width * 0.5
                # Text
                self.canvas.create_text(
                    right_edge_canvas - tick_len - 2, y_pos_canvas + 2, # Text to the left of tick
                    text=str(abs(i)), anchor="ne", fill=text_color, font=font_spec, tags="v_ruler"
                )
            elif i % 50 == 0:
                tick_len = self.ruler_width * 0.3
            else:
                tick_len = self.ruler_width * 0.15
            
            self.canvas.create_line(
                right_edge_canvas, y_pos_canvas, right_edge_canvas - tick_len, y_pos_canvas, # Line leftwards from right edge
                fill=line_color, tags="v_ruler"
            )

        # --- Horizontal Ruler ---
        # Drawn BELOW cy
        self.canvas.create_rectangle(
            h_start_x, cy_canvas,
            h_end_x, cy_canvas + self.ruler_width,
            fill=bg_color, outline="gray", tags="h_ruler"
        )
        
        range_start_x = m_left - self.cx
        range_end_x = m_right - self.cx
        
        # Align to 10
        range_start_x = (range_start_x // 10) * 10
        
        for i in range(range_start_x, range_end_x, 10):
            x_pos = self.cx + i
            x_pos_canvas = x_pos - self.v_screen_left
            
            # Draw tick on the TOP edge of the horizontal ruler (which is cy)
            top_edge_canvas = cy_canvas
            
            if i % 100 == 0:
                tick_len = self.ruler_width * 0.5
                self.canvas.create_text(
                    x_pos_canvas + 2, top_edge_canvas + tick_len + 2, # Text below tick
                    text=str(abs(i)), anchor="nw", fill=text_color, font=font_spec, tags="h_ruler"
                )
            elif i % 50 == 0:
                tick_len = self.ruler_width * 0.3
            else:
                tick_len = self.ruler_width * 0.15
            
            self.canvas.create_line(
                x_pos_canvas, top_edge_canvas, x_pos_canvas, top_edge_canvas + tick_len, # Line downwards from top
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
        # Move visual elements
        # Instead of moving, we redraw because the clipping rect might change 
        # if we drag near the edge (though user wants strict monitor clipping, 
        # so dragging between monitors might be tricky if we don't redraw).
        # But for smooth dragging within a monitor, moving is better.
        # However, since we are implementing "Move to Next Monitor" as the primary way to switch,
        # and dragging across might be ambiguous, let's just redraw to be safe and correct.
        # It ensures lines stay clipped to the monitor the center is on.
        self.draw_rulers()
        
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
