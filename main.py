# main.py
import tkinter as tk
from npo_ui import NPOApp

if __name__ == "__main__":
    root = tk.Tk()
    app = NPOApp(root)
    root.mainloop()