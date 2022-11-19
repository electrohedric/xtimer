import tkinter as tk
from tkinter import ttk
from typing import Callable
import converters as conv
from typing import Generic, TypeVar


T = TypeVar('T')
SupportsWidget = ttk.Widget|str


class BaseFrame(ttk.Frame):
    def as_widget(self, x: SupportsWidget):
        if isinstance(x, str):
            return ttk.Label(self, text=x)
        return x


class Row(BaseFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.widgets: list[ttk.Widget] = []
    
    def add(self, *widgets: SupportsWidget, pad=5):
        for widget in widgets:
            widget = self.as_widget(widget)
            widget.pack(side=tk.LEFT, padx=pad)
            self.widgets.append(widget)


ColumnKey = int|str

class Table(BaseFrame):
    def __init__(self, master, key_order: list[str] = None, fixed=False, **kwargs):
        super().__init__(master, **kwargs)
        self.widgets: list[dict[ColumnKey, ttk.Widget]] = []
        self.key_order: list[str] = key_order or []
        self.fixed = fixed
    
    def get_column(self, key: ColumnKey):
        if isinstance(key, int):
            return key
        return self.key_order.index(key)
    
    def row_exists(self, row: int):
        return -len(self.widgets) <= row < len(self.widgets)

    def get_widget(self, row: int, key: ColumnKey):
        if self.row_exists(row):
            return self.widgets[row].get(key)
        return None
    
    def set_widget(self, row: int, key: ColumnKey, widget: SupportsWidget):
        if not self.row_exists(row):
            return False
        widget = self.as_widget(widget)
        self.remove(row, key)  # remove destination just in case
        widget.grid(row=row, column=self.get_column(key))
        self.widgets[row][key] = widget
    
    @staticmethod
    def _iter(*i, **k):
        for index, value in enumerate(i):
            yield index, value
        for key, value in k.items():
            yield key, value
    
    def columns(self, *iwidths: int, **kwidths: int):
        for k, width in self._iter(*iwidths, **kwidths):
            c = self.get_column(k)
            if self.fixed:
                self.grid_columnconfigure(c, minsize=width)
            else:
                self.grid_columnconfigure(c, weight=width)
    
    def add(self, *iwidgets: SupportsWidget, **kwidgets: SupportsWidget):
        row = {}
        next_row = len(self.widgets)
        for k, widget in self._iter(*iwidgets, **kwidgets):
            widget = self.as_widget(widget)
            widget.grid(row=next_row, column=self.get_column(k))
            row[k] = widget
        self.widgets.append(row)
    
    def remove(self, row: int, key: ColumnKey):
        if w := self.get_widget(row, key):
            w.grid_remove()
            del self.widgets[row][key]
            return w
        return None
    
    def move(self, from_row: int, from_key: ColumnKey, row: int|None = None, key: ColumnKey|None = None):
        widget = self.remove(from_row, from_key)
        if not widget:
            return
        if key is None:
            key = from_key
        if row is None:
            row = from_row
        self.set_widget(row, key, widget)
    
    def __iter__(self):
        for r in range(len(self.widgets)):
            yield r


class Entry(ttk.Entry, Generic[T]):
    def __init__(self, master, converter: conv.Converter[T] = conv.StringConverter, **kwargs):
        super().__init__(master, **kwargs)
        self.var = tk.StringVar()
        self.config(textvariable=self.var)
        self.converter = converter
        
    def get(self) -> T:
        return self.converter.to_value(self.var.get())
    
    def set(self, value: T):
        self.var.set(self.converter.to_string(value))

    def listen(self, callback: Callable[[T, str | None], None]):
        def wrapper(*_):
            callback(self.get(), self.converter.error)
    
        self.var.trace_add('write', wrapper)


class Label(ttk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.var = tk.StringVar()
        self.config(textvariable=self.var)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value):
        self.var.set(str(value).strip())

