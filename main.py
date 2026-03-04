from tkinter import Tk, Frame
from tkinter import ttk

def main():
    root = Tk()
    root.geometry("800x600")
    root.title("HedgehogFund")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    tab_1 = Frame(notebook, bg="white")
    tab_2 = Frame(notebook, bg="white")
    tab_3 = Frame(notebook, bg="white")

    notebook.add(tab_1, text="Tab 1")
    notebook.add(tab_2, text="Tab 2")
    notebook.add(tab_3, text="Tab 3")








    root.mainloop()

if __name__ == "__main__":
    main()
