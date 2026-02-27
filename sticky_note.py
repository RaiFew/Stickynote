import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

class StickyNoteApp:
    DATA_FILE = "sticky_note_data.txt"
    FONT_SETTING_FILE = "sticky_note_font.txt"
    AUTOSAVE_INTERVAL_MS = 5000 
    
    COLOR_MAP = {
        "Yellow": "#FFFFCC", "Green": "#CCFFCC", "Blue": "#CCE5FF",
        "Pink": "#FFCCCC", "White": "#FFFFFF", "Black": "#000000" 
    }
    
    DEFAULT_FONT_FAMILY = "Arial"
    FONT_CHOICES = sorted(["Arial", "Courier New", "Tahoma", "Times New Roman", "Verdana", "Leelawadee UI"])

    def __init__(self, master):
        self.master = master
        master.title("Sticky Note")
        master.attributes('-topmost', True)
        
        self.load_settings()
        self.note_font = tkfont.Font(family=self.current_font_family, size=self.current_font_size)
        
        # --- UI ส่วนควบคุม ---
        self.control_frame = tk.Frame(master, bg='#f0f0f0')
        self.control_frame.pack(fill='x')
        
        # BG Color
        tk.Label(self.control_frame, text="BG:", bg='#f0f0f0').pack(side='left', padx=(5,0))
        self.bg_color_var = tk.StringVar(master, value=self.current_bg_color_name)
        self.bg_color_var.trace_add("write", lambda *args: self.change_color_handler("bg", self.bg_color_var.get()))
        tk.OptionMenu(self.control_frame, self.bg_color_var, *self.COLOR_MAP.keys()).pack(side='left', padx=2)

        # FG Color
        tk.Label(self.control_frame, text="FG:", bg='#f0f0f0').pack(side='left', padx=(5,0))
        self.fg_color_var = tk.StringVar(master, value=self.current_fg_color_name)
        self.fg_color_var.trace_add("write", lambda *args: self.change_color_handler("fg", self.fg_color_var.get()))
        tk.OptionMenu(self.control_frame, self.fg_color_var, *self.COLOR_MAP.keys()).pack(side='left', padx=2)

        # Font/Size/Align
        self.font_var = tk.StringVar(master, value=self.current_font_family)
        self.font_var.trace_add("write", self.change_font_family_handler)
        tk.OptionMenu(self.control_frame, self.font_var, *self.FONT_CHOICES).pack(side='left', padx=5)
        
        tk.Button(self.control_frame, text="A+", command=self.increase_font_size, width=2).pack(side='left', padx=1)
        tk.Button(self.control_frame, text="A-", command=self.decrease_font_size, width=2).pack(side='left', padx=1)
        
        for align in [("L", "left"), ("C", "center"), ("R", "right")]:
            tk.Button(self.control_frame, text=align[0], command=lambda a=align[1]: self.set_alignment(a), width=1).pack(side='left', padx=1)
        
        tk.Button(self.control_frame, text="ปิด", command=self.on_closing).pack(side='right', padx=2)

        # --- UI ส่วน Text Area ---
        self.text_area = tk.Text(master, wrap='word', font=self.note_font, 
                                 bg=self.COLOR_MAP[self.current_bg_color_name], 
                                 fg=self.COLOR_MAP[self.current_fg_color_name], 
                                 undo=True, # เพิ่มระบบ Undo/Redo พื้นฐาน
                                 padx=5, pady=5)
        self.text_area.pack(expand=True, fill='both')
        
        self.text_area.tag_configure("center", justify='center')
        self.text_area.tag_configure("right", justify='right')
        
        # --- ผูกคำสั่งคีย์ลัด (Shortcuts) ---
        self.bind_shortcuts()
        
        self.load_note()
        self.set_alignment(self.current_alignment)
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.auto_save_loop()

    def bind_shortcuts(self):
        """กำหนดคีย์ลัดมาตรฐาน"""
        self.text_area.bind("<Control-a>", self.select_all)
        self.text_area.bind("<Control-A>", self.select_all)
        # ปกติ Ctrl+C/V จะทำงานเองในหลายระบบ แต่ถ้าไม่ได้ เราสามารถสั่ง manual ได้:
        self.text_area.bind("<Control-c>", lambda e: self.text_area.event_generate("<<Copy>>"))
        self.text_area.bind("<Control-v>", lambda e: self.text_area.event_generate("<<Paste>>"))
        self.text_area.bind("<Control-x>", lambda e: self.text_area.event_generate("<<Cut>>"))
        self.text_area.bind("<Control-z>", lambda e: self.text_area.event_generate("<<Undo>>"))

    def select_all(self, event=None):
        """เลือกข้อความทั้งหมด"""
        self.text_area.tag_add("sel", "1.0", "end")
        return "break" # ป้องกันการทำงานซ้ำซ้อนของระบบ

    # --- ส่วนจัดการการบันทึกและโหลด (คงเดิมแต่ปรับให้เสถียรขึ้น) ---
    def load_settings(self):
        self.current_font_family, self.current_font_size = self.DEFAULT_FONT_FAMILY, 14
        self.current_alignment, self.current_bg_color_name, self.current_fg_color_name = "left", "Yellow", "Black"
        try:
            with open(self.FONT_SETTING_FILE, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines()]
                if len(lines) >= 5:
                    self.current_font_family, self.current_font_size = lines[0], int(lines[1])
                    self.current_alignment, self.current_bg_color_name, self.current_fg_color_name = lines[2], lines[3], lines[4]
        except: pass

    def save_settings(self):
        try:
            with open(self.FONT_SETTING_FILE, 'w', encoding='utf-8') as f:
                f.write(f"{self.current_font_family}\n{self.current_font_size}\n{self.current_alignment}\n{self.current_bg_color_name}\n{self.current_fg_color_name}")
        except: pass

    def change_color_handler(self, color_type, color_name):
        if color_name in self.COLOR_MAP:
            if color_type == "bg": self.text_area.config(bg=self.COLOR_MAP[color_name]); self.current_bg_color_name = color_name
            else: self.text_area.config(fg=self.COLOR_MAP[color_name]); self.current_fg_color_name = color_name
            self.save_settings()

    def change_font_family_handler(self, *args):
        self.current_font_family = self.font_var.get()
        self.note_font.config(family=self.current_font_family)
        self.save_settings()

    def increase_font_size(self):
        self.current_font_size += 2; self.note_font.config(size=self.current_font_size); self.save_settings()
        
    def decrease_font_size(self):
        if self.current_font_size > 6: self.current_font_size -= 2; self.note_font.config(size=self.current_font_size); self.save_settings()
            
    def set_alignment(self, align_type):
        self.text_area.tag_remove("center", "1.0", tk.END); self.text_area.tag_remove("right", "1.0", tk.END)
        if align_type != "left": self.text_area.tag_add(align_type, "1.0", tk.END)
        self.current_alignment = align_type
        self.save_settings()
        
    def load_note(self):
        try:
            with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert('1.0', f.read())
        except: self.text_area.insert('1.0', "ใส่โน้ตของคุณที่นี่...")
            
    def save_note(self):
        try:
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(self.text_area.get('1.0', tk.END).strip())
        except: pass
            
    def on_closing(self):
        self.save_note(); self.save_settings(); self.master.destroy()

    def auto_save_loop(self):
        self.save_note(); self.save_settings()
        self.master.after(self.AUTOSAVE_INTERVAL_MS, self.auto_save_loop)

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("500x300") 
    app = StickyNoteApp(root)
    root.mainloop()