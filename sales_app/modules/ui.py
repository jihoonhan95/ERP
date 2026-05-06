import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from .sales_manager import SalesManager


class SalesUI:
    def __init__(self, root: tk.Tk, manager: SalesManager):
        self.root = root
        self.manager = manager
        self._build_layout()
        self._refresh_table()
        self._refresh_summary()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_toolbar(self.root)
        self._build_table(self.root)
        self._build_summary(self.root)

    def _build_toolbar(self, parent):
        bar = ttk.Frame(parent, padding=8)
        bar.grid(row=0, column=0, sticky="ew")

        ttk.Label(bar, text="기간:").pack(side="left")
        self.start_var = tk.StringVar(value=f"{date.today().year}-01-01")
        self.end_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(bar, textvariable=self.start_var, width=12).pack(side="left", padx=2)
        ttk.Label(bar, text="~").pack(side="left")
        ttk.Entry(bar, textvariable=self.end_var, width=12).pack(side="left", padx=2)

        ttk.Label(bar, text="  카테고리:").pack(side="left")
        self.cat_var = tk.StringVar(value="")
        self.cat_combo = ttk.Combobox(bar, textvariable=self.cat_var, width=12, state="readonly")
        self.cat_combo.pack(side="left", padx=2)

        ttk.Button(bar, text="조회", command=self._on_search).pack(side="left", padx=4)
        ttk.Button(bar, text="전체보기", command=self._on_show_all).pack(side="left")

        ttk.Button(bar, text="+ 매출 추가", command=self._open_add_dialog).pack(side="right", padx=4)
        ttk.Button(bar, text="수정", command=self._on_edit).pack(side="right", padx=2)
        ttk.Button(bar, text="삭제", command=self._on_delete).pack(side="right", padx=2)

    def _build_table(self, parent):
        frame = ttk.Frame(parent)
        frame.grid(row=1, column=0, sticky="nsew", padx=8)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("date", "category", "item", "quantity", "price", "total")
        headers = {"date": "날짜", "category": "카테고리", "item": "품목", "quantity": "수량", "price": "단가", "total": "합계"}

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        widths = {"date": 110, "category": 110, "item": 200, "quantity": 70, "price": 100, "total": 110}
        for col in cols:
            self.tree.heading(col, text=headers[col], command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=widths[col], anchor="center" if col != "item" else "w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._sort_col = "date"
        self._sort_asc = False

    def _build_summary(self, parent):
        bar = ttk.Frame(parent, padding=8)
        bar.grid(row=2, column=0, sticky="ew")

        self.lbl_count = ttk.Label(bar, text="건수: 0")
        self.lbl_qty = ttk.Label(bar, text="총수량: 0")
        self.lbl_revenue = ttk.Label(bar, text="총매출: 0원")
        self.lbl_avg = ttk.Label(bar, text="평균: 0원")

        for lbl in (self.lbl_count, self.lbl_qty, self.lbl_revenue, self.lbl_avg):
            lbl.pack(side="left", padx=16)

    # ── Table helpers ────────────────────────────────────────────────────────

    def _refresh_table(self, records=None):
        if records is None:
            records = self.manager.get_all()
        self.tree.delete(*self.tree.get_children())
        self._row_ids = {}
        for r in records:
            iid = self.tree.insert(
                "", "end",
                values=(
                    r["date"],
                    r.get("category", ""),
                    r["item"],
                    f"{r['quantity']:,}",
                    f"{r['price']:,}",
                    f"{r['total']:,}",
                ),
            )
            self._row_ids[iid] = r["id"]
        self._refresh_categories()

    def _refresh_summary(self, records=None):
        if records is None:
            records = self.manager.get_all()
        s = self.manager.summary(records)
        self.lbl_count.config(text=f"건수: {s['count']:,}")
        self.lbl_qty.config(text=f"총수량: {s['total_quantity']:,}")
        self.lbl_revenue.config(text=f"총매출: {s['total_revenue']:,}원")
        self.lbl_avg.config(text=f"평균: {s['average']:,}원")

    def _refresh_categories(self):
        cats = [""] + self.manager.get_categories()
        self.cat_combo["values"] = cats

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key_map = {"date": "date", "category": "category", "item": "item",
                   "quantity": "quantity", "price": "price", "total": "total"}
        records = sorted(self.manager.get_all(), key=lambda r: r.get(key_map[col], ""), reverse=not self._sort_asc)
        self._refresh_table(records)

    # ── Events ───────────────────────────────────────────────────────────────

    def _on_search(self):
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        cat = self.cat_var.get().strip()
        records = self.manager.filter_by_period(start, end)
        if cat:
            records = [r for r in records if r.get("category") == cat]
        self._refresh_table(records)
        self._refresh_summary(records)

    def _on_show_all(self):
        self.cat_var.set("")
        records = self.manager.get_all()
        self._refresh_table(records)
        self._refresh_summary(records)

    def _selected_record_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self._row_ids.get(sel[0])

    def _on_delete(self):
        rid = self._selected_record_id()
        if rid is None:
            messagebox.showwarning("선택 없음", "삭제할 항목을 선택하세요.")
            return
        if messagebox.askyesno("삭제 확인", "선택한 항목을 삭제하시겠습니까?"):
            self.manager.delete_sale(rid)
            self._on_show_all()

    def _on_edit(self):
        rid = self._selected_record_id()
        if rid is None:
            messagebox.showwarning("선택 없음", "수정할 항목을 선택하세요.")
            return
        record = next((r for r in self.manager.data if r["id"] == rid), None)
        if record:
            self._open_add_dialog(record)

    # ── Add / Edit Dialog ────────────────────────────────────────────────────

    def _open_add_dialog(self, record=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("매출 수정" if record else "매출 추가")
        dlg.grab_set()
        dlg.resizable(False, False)

        fields = [("날짜 (YYYY-MM-DD)", "date"), ("카테고리", "category"),
                  ("품목명", "item"), ("수량", "quantity"), ("단가 (원)", "price")]
        vars_ = {}

        for i, (label, key) in enumerate(fields):
            ttk.Label(dlg, text=label).grid(row=i, column=0, padx=12, pady=6, sticky="e")
            v = tk.StringVar(value=str(record.get(key, "")) if record else
                             (str(date.today()) if key == "date" else ""))
            ttk.Entry(dlg, textvariable=v, width=22).grid(row=i, column=1, padx=12, pady=6)
            vars_[key] = v

        def _submit():
            try:
                d = vars_["date"].get().strip()
                datetime.strptime(d, "%Y-%m-%d")
                item = vars_["item"].get().strip()
                if not item:
                    raise ValueError("품목명을 입력하세요.")
                qty = int(vars_["quantity"].get())
                price = int(vars_["price"].get())
                cat = vars_["category"].get().strip()
                if qty <= 0 or price <= 0:
                    raise ValueError("수량과 단가는 1 이상이어야 합니다.")
            except ValueError as e:
                messagebox.showerror("입력 오류", str(e), parent=dlg)
                return

            if record:
                self.manager.update_sale(record["id"], date=d, item=item,
                                         quantity=qty, price=price, category=cat)
            else:
                self.manager.add_sale(d, item, qty, price, cat)

            dlg.destroy()
            self._on_show_all()

        ttk.Button(dlg, text="저장", command=_submit).grid(row=len(fields), column=0, columnspan=2, pady=10)
