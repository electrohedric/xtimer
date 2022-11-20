import tkinter as tk
from tkinter import ttk
from datetime import datetime

import masterref
import widgets as w
import converters as conv
import pickle
import os


class Product:
    def __init__(self, pid: int, name, done_datetime):
        self.id = pid
        self.name = name
        self.done_datetime = done_datetime
    
    def is_empty(self):
        return not self.name and self.done_datetime is None


class State:
    perist_file = "state.pickle"
    
    def __init__(self):
        self.products_done_datetime: datetime | None = None
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
                    print("Backup file was corrupted. Defaulting to primary file")
        if os.path.exists(file):
            with open(file, 'rb') as f:
                return pickle.load(f)
        print("Primary file was missing")
        return State()


class App(ttk.Frame):
    def __init__(self, state: State, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.persistence = False  # Do not persist anything until the state is fully loaded
        
        self.products_done_stack = w.HStack(self)
        self.products_done_entry = w.Entry(self.products_done_stack, conv.TimeToNextDatetimeConverter("%#I:%M %p"), width=10)  # 1:30 PM
        self.products_done_entry.set(self.state.products_done_datetime)
        self.products_done_entry.listen(self.on_products_done_changed)
        self.products_done_display_label = w.Label(self.products_done_stack)
        self.products_done_stack.add("All products done @", self.products_done_entry, self.products_done_display_label)
        
        self.products_table = w.Table(self, ["product", "time", "display"])
        self.products = {x.id: x for x in self.state.products}
        for product in self.state.products:
            self.add_product(product)
        self.add_new_product()
        
        self.timeline_stack = w.VStack(self)
        
        self.products_done_stack.grid(row=0, sticky=tk.W, pady=5)
        self.products_table.grid(row=1, sticky=tk.W, pady=5)
        self.timeline_stack.grid(row=2, sticky=tk.W, pady=5)
        self.persistence = True  # Done loading the state, and will now be persisted
    
    def persist(self):
        if self.persistence:
            self.state.save()
    
    def add_new_product(self):
        prod = Product(self.state.next_product_id, None, None)
        self.state.products.append(prod)
        self.state.next_product_id += 1
        self.products[prod.id] = prod
        self.add_product(prod)
        
    def add_product(self, product: Product):
        product_entry = w.Entry(self.products_table, width=20)
        time_entry = w.Entry(self.products_table, conv.TimeToNextDatetimeConverter("%#I:%M %p"), width=10)  # 1:30 PM
        display_label = w.Label(self.products_table)
        row = self.products_table.add(product=product_entry, time=time_entry, display=display_label)
    
        def on_product_name_change(s: str, _err):
            product.name = s
            self.persist()
    
        def on_product_done_changed(d: datetime | None, error: str | None):
            if d is None:
                if error:
                    product_entry.config(foreground='red')
                    display_label.set(error)
                return
            product_entry.config(foreground='black')
            display_label.set(d.strftime("%a, %#I:%M %p"))  # Sun, 1:30 PM
            product.done_datetime = d
            self.persist()
    
        product_entry.listen(on_product_name_change)
        time_entry.listen(on_product_done_changed)
        product_entry.set(product.name)
        time_entry.set(product.done_datetime)
        
    
    def on_products_done_changed(self, d: datetime | None, error: str | None):
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
        self.persist()


app = App(State.load())
app.grid(sticky=tk.NSEW, padx=10, pady=10)

masterref.root.mainloop()
