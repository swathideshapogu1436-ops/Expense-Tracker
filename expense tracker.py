import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import sqlite3
import csv
from pathlib import Path

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    Figure = None

DB_FILE = Path(__file__).with_name("expenses.db")

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1000x680")
        self.dark = True
        self.conn = sqlite3.connect(DB_FILE)
        self.create_table()
        self.build_ui()
        self.load_transactions()
        self.update_summary()

    def colors(self):
        return {
            "bg": "#202124" if self.dark else "#f5f5f5",
            "card": "#303134" if self.dark else "#ffffff",
            "input": "#3c4043" if self.dark else "#eeeeee",
            "text": "#ffffff" if self.dark else "#202124",
            "muted": "#bdc1c6" if self.dark else "#5f6368",
            "accent": "#8ab4f8" if self.dark else "#1a73e8",
            "danger": "#f28b82" if self.dark else "#d93025"
        }

    def create_table(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            note TEXT)""")
        self.conn.commit()

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        c = self.colors()
        self.root.configure(bg=c["bg"])

        header = tk.Frame(self.root, bg=c["bg"])
        header.pack(fill="x", padx=20, pady=15)
        tk.Label(header, text="💰 EXPENSE TRACKER", font=("Arial",20,"bold"),
                 bg=c["bg"], fg=c["text"]).pack(side="left")
        tk.Button(header, text="☀ Light" if self.dark else "🌙 Dark",
                  command=self.toggle_theme, bg=c["input"], fg=c["text"],
                  relief="flat").pack(side="right")

        cards = tk.Frame(self.root, bg=c["bg"])
        cards.pack(fill="x", padx=20)
        self.income = self.card(cards, "Total Income", 0)
        self.expense = self.card(cards, "Total Expense", 1)
        self.balance = self.card(cards, "Balance", 2)

        content = tk.Frame(self.root, bg=c["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=12)

        left = tk.Frame(content, bg=c["card"], padx=15, pady=15)
        left.pack(side="left", fill="y", padx=(0,10))
        tk.Label(left, text="Add Transaction", font=("Arial",15,"bold"),
                 bg=c["card"], fg=c["text"]).pack(anchor="w", pady=(0,12))

        self.type_var = tk.StringVar(value="Expense")
        self.cat_var = tk.StringVar(value="Food")
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.note_var = tk.StringVar()

        self.field(left, "Type", self.type_var, ["Expense","Income"])
        self.field(left, "Category", self.cat_var,
                   ["Food","Travel","Shopping","Bills","Education","Health",
                    "Entertainment","Salary","Other"])
        self.entry(left, "Amount", self.amount_var)
        self.entry(left, "Date (YYYY-MM-DD)", self.date_var)
        self.entry(left, "Note", self.note_var)

        tk.Button(left, text="Add Transaction", command=self.add_transaction,
                  bg=c["accent"], fg="#202124" if self.dark else "#fff",
                  relief="flat", pady=8).pack(fill="x", pady=15)
        tk.Button(left, text="Delete Selected", command=self.delete_selected,
                  bg=c["danger"], fg="#fff", relief="flat", pady=8).pack(fill="x", pady=3)
        tk.Button(left, text="Export CSV", command=self.export_csv,
                  bg=c["input"], fg=c["text"], relief="flat", pady=8).pack(fill="x", pady=3)

        right = tk.Frame(content, bg=c["card"], padx=12, pady=12)
        right.pack(side="left", fill="both", expand=True)

        bar = tk.Frame(right, bg=c["card"])
        bar.pack(fill="x")
        tk.Label(bar, text="Transactions", font=("Arial",15,"bold"),
                 bg=c["card"], fg=c["text"]).pack(side="left")
        self.search = tk.StringVar()
        e = tk.Entry(bar, textvariable=self.search, bg=c["input"], fg=c["text"],
                     insertbackground=c["text"], relief="flat")
        e.pack(side="right", ipady=5)
        e.bind("<KeyRelease>", lambda _: self.load_transactions())

        frame = tk.Frame(right, bg=c["card"])
        frame.pack(fill="both", expand=True, pady=10)
        cols = ("id","type","category","amount","date","note")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, width in zip(cols,[45,80,100,90,100,180]):
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        tk.Button(self.root, text="📊 View Expense Chart", command=self.show_chart,
                  bg=c["input"], fg=c["text"], relief="flat", pady=7).pack(
                  anchor="e", padx=20, pady=(0,15))

    def card(self, parent, title, col):
        c=self.colors()
        f=tk.Frame(parent,bg=c["card"],padx=18,pady=12)
        f.grid(row=0,column=col,sticky="ew",padx=5)
        parent.columnconfigure(col,weight=1)
        tk.Label(f,text=title,bg=c["card"],fg=c["muted"]).pack(anchor="w")
        lab=tk.Label(f,text="₹0.00",font=("Arial",18,"bold"),
                     bg=c["card"],fg=c["text"])
        lab.pack(anchor="w")
        return lab

    def field(self, parent, label, var, values):
        c=self.colors()
        tk.Label(parent,text=label,bg=c["card"],fg=c["text"]).pack(anchor="w",pady=(5,2))
        ttk.Combobox(parent,textvariable=var,values=values,state="readonly").pack(fill="x",ipady=5)

    def entry(self,parent,label,var):
        c=self.colors()
        tk.Label(parent,text=label,bg=c["card"],fg=c["text"]).pack(anchor="w",pady=(5,2))
        tk.Entry(parent,textvariable=var,bg=c["input"],fg=c["text"],
                 insertbackground=c["text"],relief="flat").pack(fill="x",ipady=6)

    def add_transaction(self):
        try:
            amount=float(self.amount_var.get())
            if amount<=0: raise ValueError
            date.fromisoformat(self.date_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input","Enter a positive amount and date as YYYY-MM-DD.")
            return
        self.conn.execute("""INSERT INTO transactions
            (transaction_type,category,amount,transaction_date,note)
            VALUES(?,?,?,?,?)""",
            (self.type_var.get(),self.cat_var.get(),amount,self.date_var.get(),self.note_var.get()))
        self.conn.commit()
        self.amount_var.set(""); self.note_var.set("")
        self.load_transactions(); self.update_summary()

    def load_transactions(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        s=self.search.get().strip()
        if s:
            rows=self.conn.execute("""SELECT id,transaction_type,category,amount,transaction_date,note
                FROM transactions WHERE category LIKE ? OR note LIKE ? OR transaction_type LIKE ?
                ORDER BY transaction_date DESC,id DESC""",(f"%{s}%",f"%{s}%",f"%{s}%")).fetchall()
        else:
            rows=self.conn.execute("""SELECT id,transaction_type,category,amount,transaction_date,note
                FROM transactions ORDER BY transaction_date DESC,id DESC""").fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r[0],r[1],r[2],f"₹{r[3]:.2f}",r[4],r[5] or ""))

    def update_summary(self):
        inc=self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='Income'").fetchone()[0]
        exp=self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='Expense'").fetchone()[0]
        self.income.config(text=f"₹{inc:,.2f}"); self.expense.config(text=f"₹{exp:,.2f}")
        self.balance.config(text=f"₹{inc-exp:,.2f}")

    def delete_selected(self):
        sel=self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection","Select a transaction first."); return
        tid=self.tree.item(sel[0],"values")[0]
        if messagebox.askyesno("Confirm Delete","Delete this transaction?"):
            self.conn.execute("DELETE FROM transactions WHERE id=?",(tid,))
            self.conn.commit(); self.load_transactions(); self.update_summary()

    def export_csv(self):
        rows=self.conn.execute("SELECT id,transaction_type,category,amount,transaction_date,note FROM transactions").fetchall()
        if not rows:
            messagebox.showinfo("Export","No transactions to export."); return
        path=Path(__file__).with_name("transactions.csv")
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["ID","Type","Category","Amount","Date","Note"]); w.writerows(rows)
        messagebox.showinfo("Export Complete",f"Saved as {path.name}")

    def show_chart(self):
        if Figure is None:
            messagebox.showerror("Missing Package","Run: pip install -r requirements.txt"); return
        rows=self.conn.execute("""SELECT category,SUM(amount) FROM transactions
            WHERE transaction_type='Expense' GROUP BY category""").fetchall()
        if not rows:
            messagebox.showinfo("Chart","Add an expense first."); return
        win=tk.Toplevel(self.root); win.title("Expense Chart"); win.geometry("700x500")
        fig=Figure(figsize=(7,5),dpi=100); ax=fig.add_subplot(111)
        ax.pie([r[1] for r in rows],labels=[r[0] for r in rows],autopct="%1.1f%%")
        ax.set_title("Expenses by Category")
        canvas=FigureCanvasTkAgg(fig,master=win); canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True)

    def toggle_theme(self):
        self.dark=not self.dark; self.build_ui(); self.load_transactions(); self.update_summary()

if __name__=="__main__":
    root=tk.Tk()
    app=ExpenseTracker(root)
    root.mainloop()
