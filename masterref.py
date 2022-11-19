import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("XTimer")
root.geometry("800x600")
style = ttk.Style(root)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
