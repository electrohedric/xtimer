import tkinter as tk
from tkinter import ttk
from datetime import datetime

import masterref
import widgets as w
import converters as conv
import pickle
import os


class Product:
    def __init__(self, pid: int | None, name: str | None, done_datetime: datetime | None):
        self.id = pid
        self.name = name
        self.done_datetime = done_datetime
    

class State:
    perist_file = "state.pickle"
    
    def __init__(self):
        self.all_done_datetime: datetime | None = None
        self.products: list[Product] = []
        self.next_product_id = 1
    
    def save(self, file=None):
        file = file or State.perist_file
        backup_file = "." + file
        
        # 3-stage commit:
        # 1. write to backup
        # 2. write to main file
        # 3. remove backup
        # -----
        # if crash before step 1: nothing is written, [old state] is preserved in main file
        # if crash during step 1: backup is corrupted, [old state] is preserved in main file
        # if crash between step 1 and 2: [new state] is preserved in backup, old state is preserved in main file
        # if crash during step 2: main file is corrupted, [new state] is preserved in backup
        # if crash between step 2 and 3: [new state] is preserved in both the backup and main file
        # if crash during step 3: backup is corrupted, [new state] is preserved in main file
        # if crash after step 3: backup is deleted, [new state] is preserved in main file
        # -----
        with open(backup_file, 'wb') as f:
            pickle.dump(self, f)
        with open(file, 'wb') as f:
            pickle.dump(self, f)
        os.remove(backup_file)
        print("Saved successfully to " + file)
    
    @staticmethod
    def load(file=None):
        file = file or State.perist_file
        backup_file = "." + file
        
        # because of the way the file is saved, checking for the backup first produces a more recent copy
        if os.path.exists(backup_file):
            with open(backup_file, 'rb') as f:
                try:
                    return pickle.load(f)
                except (EOFError, ValueError, TypeError):
                    print("New state file was corrupted. Loading from previous state.")
        if os.path.exists(file):
            with open(file, 'rb') as f:
                try:
                    return pickle.load(f)
                except (EOFError, ValueError, TypeError):
                    print("State file was corrupted. This should never happen.")
        print("All state files are missing or corrupted.")  # bad!
        return State()


class App(ttk.Frame):
    def __init__(self, state: State, **kwargs):
        super().__init__(**kwargs)
        self.state: State = state
        self.init = True  # Do not persist anything until the state is fully loaded
        
        self.all_done_stack = w.HStack(self)
        self.all_done_entry = w.Entry(self.all_done_stack, conv.TimeToNextDatetimeConverter("%#I:%M %p"), width=10)  # 1:30 PM
        self.all_done_entry.set(self.state.all_done_datetime)
        self.all_done_entry.listen(self.on_all_done_changed)
        self.all_done_display_label = w.Label(self.all_done_stack)
        self.all_done_stack.add("All products done @", self.all_done_entry, self.all_done_display_label)
        
        self.products_table = w.Table(self, ["product", "time", "display"])
        self.products = {}
        for product in self.state.products:
            self.products[product.id] = product
            self.render_product(product)
        self.ensure_one_blank_product()
        
        self.timeline_stack = w.VStack(self)
        
        self.all_done_stack.grid(row=0, sticky=tk.W, pady=5)
        self.products_table.grid(row=1, sticky=tk.W, pady=5)
        self.timeline_stack.grid(row=2, sticky=tk.W, pady=5)
        self.init = False  # Done loading the state, and will now be persisted
    
    def persist(self):
        if self.init:
            return
        self.state.save()
    
    def ensure_one_blank_product(self):
        if self.init:
            return
        empty = 0
        last_index = len(self.state.products) - 1
        for i in range(last_index, -1, -1):
            product = self.state.products[i]
            if product.name:
                break
            else:
                empty += 1
        if empty == 0:
            self.add_phantom_product()
        else:
            for j in range(last_index, last_index - empty + 1, -1):
                rm_product = self.state.products[j]
                self.products_table.delete_row(j)
                del self.products[rm_product.id]
                del self.state.products[j]
    
    def register_new_product(self, product: Product):
        if product.id is None:
            product.id = self.state.next_product_id
            self.state.next_product_id += 1
            self.products[product.id] = product
            self.state.products.append(product)
    
    def add_phantom_product(self):
        product = Product(None, None, None)
        self.render_product(product)
        
    def render_product(self, product: Product):
        product_entry = w.Entry(self.products_table, width=20)
        time_entry = w.Entry(self.products_table, conv.TimeToNextDatetimeConverter("%#I:%M %p"), width=10)  # 1:30 PM
        display_label = w.Label(self.products_table)
        row = self.products_table.add(product=product_entry, time=time_entry, display=display_label)
    
        def on_name_change(s: str, _err):
            product.name = s
            self.register_new_product(product)
            if s:
                if product.done_datetime is None:
                    self.products_table.get_widget(row, "time").set(self.state.all_done_datetime)
                    
            self.ensure_one_blank_product()
            self.persist()
    
        def on_done_changed(d: datetime | None, error: str | None):
            product.done_datetime = d
            self.register_new_product(product)
            if d is None:
                product_entry.config(foreground='red')
                display_label.set(error or "")
            else:
                product_entry.config(foreground='black')
                display_label.set(d.strftime("%a, %#I:%M %p"))  # Sun, 1:30 PM

            self.persist()
    
        product_entry.listen(on_name_change)
        time_entry.listen(on_done_changed)
        product_entry.set(product.name)
        time_entry.set(product.done_datetime)
        
    
    def on_all_done_changed(self, d: datetime | None, error: str | None):
        if d is None:
            self.all_done_entry.config(foreground='red')
            self.all_done_display_label.set(error or "")
        else:
            self.all_done_entry.config(foreground='black')
            self.all_done_display_label.set(d.strftime("%a, %#I:%M %p"))  # Sun, 1:30 PM
        
        # update all times of products to the new default if they matched the previous default value
        for row, product in enumerate(self.state.products):
            if not product.name:
                continue
            dt = product.done_datetime
            if dt is None or dt == self.state.all_done_datetime:
                self.products_table.get_widget(row, "time").set(d)
                    
        self.state.all_done_datetime = d
        self.persist()


app = App(State.load())
app.grid(sticky=tk.NSEW, padx=10, pady=10)

masterref.root.mainloop()
