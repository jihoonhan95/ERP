import tkinter as tk
from modules.sales_manager import SalesManager
from modules.ui import SalesUI


def main():
    root = tk.Tk()
    root.title("매출 관리 프로그램")
    root.geometry("1100x700")
    root.resizable(True, True)

    manager = SalesManager()
    app = SalesUI(root, manager)

    root.mainloop()


if __name__ == "__main__":
    main()
