import tkinter as tk
from tkinter import ttk
from datetime import datetime
import masterref
import widgets as w
import converters as conv


class Product:
    def __init__(self, name, done_datetime):
        self.name = name
        self.done_datetime = done_datetime


class State:
    def __init__(self):
        self.products_done_datetime = datetime.now()
        self.products: list[Product] = []


class App(ttk.Frame):
    def __init__(self, state: State, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        
        self.products_done_row = w.Row(self)
        self.products_done_entry = w.Entry(self.products_done_row, conv.TimeToNextDatetimeConverter("%#I:%M %p"), width=10)  # 1:30 PM
        self.products_done_entry.listen(self.on_products_done_changed)
        self.products_done_display_label = w.Label(self.products_done_row)
        self.products_done_row.add("All products done @", self.products_done_entry, self.products_done_display_label)
        
        self.products_table = w.Table(self, ["product", "time"])
        self.add_product_row()
        
        self.timeline_table = w.Table(self)  # TODO: perhaps a Column is more appropriate
        
        self.products_done_row.grid(row=0, sticky=tk.W)
        self.products_table.grid(row=1, sticky=tk.W)
    
    def add_product_row(self):
        product_entry = w.Entry(self.products_table, width=20)
        time_entry = w.Entry(self.products_table, conv.TimeToNextDatetimeConverter("%#I:%M %p"), width=10)  # 1:30 PM
        self.products_table.add(product=product_entry, time=time_entry)
        
    
    def on_products_done_changed(self, d: datetime, error: str | None):
        if d is None:
            if error:
                self.products_done_entry.config(foreground='red')
                self.products_done_display_label.set(error)
            return
        self.products_done_entry.config(foreground='black')
        self.products_done_display_label.set(d.strftime("%a, %#I:%M %p"))  # Sun, 1:30 PM
        
        # update all times of products to the new default if they matched the previous default value
        for row in self.products_table:
            if entry := self.products_table.get_widget(row, "time"):  # type: w.Entry
                custom_dt = entry.get()
                if custom_dt is None or custom_dt == self.state.products_done_datetime:
                    entry.set(d)
                    
        self.state.products_done_datetime = d
        


app = App(State())
app.grid(sticky=tk.NSEW, padx=10, pady=10)

masterref.root.mainloop()
