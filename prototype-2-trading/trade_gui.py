import sys
import json
import threading
import queue
import tkinter as tk
from tkinter import ttk

import pika


TRADES_QUEUE = "trades"
RABBITMQ_USERNAME = "guest"
RABBITMQ_PASSWORD = "guest"


class TradeDashboardGUI:
    def __init__(self, root, host: str, port: int):
        self.root = root
        self.host = host
        self.port = port

        self.root.title("XYZ Corp Dashboard")
        self.root.geometry("1440x860")
        self.root.minsize(1180, 760)
        self.root.configure(bg="#111417")

        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.trade_history = []

        self.latest_price_var = tk.StringVar(value="$-.--")
        self.change_var = tk.StringVar(value="+0.00 (0.00%)")
        self.status_var = tk.StringVar(value=f"Connected target: {host}:{port}")
        self.market_status_var = tk.StringVar(value="Market Open")
        self.volume_var = tk.StringVar(value="4.2M")
        self.avg_vol_var = tk.StringVar(value="3.8M")

        self._build_styles()
        self._build_ui()
        self._start_consumer_thread()
        self._poll_messages()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_styles(self):
        self.colors = {
            "bg": "#111417",
            "panel": "#1d2023",
            "panel_alt": "#191c1f",
            "panel_high": "#272a2e",
            "text": "#e1e2e7",
            "muted": "#bacbb9",
            "accent": "#7dffa2",
            "accent_strong": "#05e777",
            "danger": "#ffb6b1",
            "primary": "#dfe3ff",
            "line": "#323538",
        }

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Dark.Treeview",
                        background=self.colors["panel"],
                        fieldbackground=self.colors["panel"],
                        foreground=self.colors["text"],
                        rowheight=34,
                        borderwidth=0,
                        relief="flat",
                        font=("Arial", 11))
        style.configure("Dark.Treeview.Heading",
                        background=self.colors["panel_high"],
                        foreground=self.colors["muted"],
                        font=("Arial", 10, "bold"),
                        relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", self.colors["panel_high"])],
                  foreground=[("selected", self.colors["text"])])

    def _card(self, parent, bg=None, padx=18, pady=18):
        return tk.Frame(
            parent,
            bg=bg or self.colors["panel"],
            highlightthickness=1,
            highlightbackground=self.colors["line"],
            bd=0,
            padx=padx,
            pady=pady
        )

    def _build_ui(self):
        self._build_top_nav()

        body = tk.Frame(self.root, bg=self.colors["bg"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_main_area(body)

    def _build_top_nav(self):
        nav = tk.Frame(self.root, bg="#14181c", height=56)
        nav.pack(fill="x", side="top")
        nav.pack_propagate(False)

        left = tk.Frame(nav, bg="#14181c")
        left.pack(side="left", padx=18)

        tk.Label(left, text="XYZ Corp",
                 bg="#14181c", fg=self.colors["primary"],
                 font=("Arial", 18, "bold")).pack(side="left", padx=(0, 24))

        for text, active in [("Dashboard", True), ("Markets", False), ("Portfolio", False), ("History", False)]:
            fg = self.colors["accent"] if active else self.colors["muted"]
            tk.Label(left, text=text,
                     bg="#14181c", fg=fg,
                     font=("Arial", 12, "bold" if active else "normal")
                     ).pack(side="left", padx=10)

        right = tk.Frame(nav, bg="#14181c")
        right.pack(side="right", padx=18)

        tk.Label(right, text="●", bg="#14181c", fg=self.colors["muted"], font=("Arial", 12)).pack(side="left", padx=8)
        tk.Label(right, text="⚙", bg="#14181c", fg=self.colors["muted"], font=("Arial", 12)).pack(side="left", padx=8)
        tk.Label(right, text="👤", bg="#14181c", fg=self.colors["text"], font=("Arial", 12)).pack(side="left", padx=8)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.colors["panel_alt"], width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        header = tk.Frame(sidebar, bg=self.colors["panel_alt"])
        header.pack(fill="x", padx=18, pady=(18, 12))

        tk.Label(header, text="● MARKETS",
                 bg=self.colors["panel_alt"], fg=self.colors["text"],
                 font=("Arial", 16, "bold")).pack(anchor="w")
        tk.Label(header, text="Global Liquidity",
                 bg=self.colors["panel_alt"], fg=self.colors["muted"],
                 font=("Arial", 10)).pack(anchor="w", pady=(4, 0))

        nav_items = [
            ("Equities", True),
            ("Crypto", False),
            ("Forex", False),
            ("Indices", False),
            ("Commodities", False),
        ]

        for name, active in nav_items:
            item_bg = self.colors["panel"] if active else self.colors["panel_alt"]
            fg = self.colors["accent"] if active else self.colors["muted"]
            row = tk.Frame(sidebar, bg=item_bg, height=48)
            row.pack(fill="x", padx=0, pady=1)
            row.pack_propagate(False)

            tk.Label(row, text=name, bg=item_bg, fg=fg,
                     font=("Arial", 12, "bold" if active else "normal")
                     ).pack(side="left", padx=18, pady=12)

            if active:
                tk.Frame(row, bg=self.colors["accent"], width=4).pack(side="right", fill="y")

        bottom = tk.Frame(sidebar, bg=self.colors["panel_alt"])
        bottom.pack(side="bottom", fill="x", padx=14, pady=18)

        tk.Button(bottom, text="Deposit Funds",
                  bg=self.colors["accent_strong"], fg="#00210b",
                  activebackground=self.colors["accent"],
                  activeforeground="#00210b",
                  relief="flat", bd=0,
                  font=("Arial", 12, "bold"), height=2).pack(fill="x", pady=(0, 14))

        tk.Label(bottom, text="Support", bg=self.colors["panel_alt"], fg=self.colors["muted"],
                 font=("Arial", 11)).pack(anchor="w", pady=5)
        tk.Label(bottom, text="API", bg=self.colors["panel_alt"], fg=self.colors["muted"],
                 font=("Arial", 11)).pack(anchor="w", pady=5)

    def _build_main_area(self, parent):
        main = tk.Frame(parent, bg=self.colors["bg"])
        main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        top_grid = tk.Frame(main, bg=self.colors["bg"])
        top_grid.pack(fill="x", pady=(0, 18))

        asset_card = self._card(top_grid, bg=self.colors["panel"], padx=24, pady=24)
        asset_card.pack(side="left", fill="both", expand=True, padx=(0, 14))

        self._build_asset_card(asset_card)

        status_card = self._card(top_grid, bg=self.colors["panel"], padx=20, pady=20)
        status_card.pack(side="left", fill="y")
        self._build_status_card(status_card)

        bottom_grid = tk.Frame(main, bg=self.colors["bg"])
        bottom_grid.pack(fill="both", expand=True)

        left_col = tk.Frame(bottom_grid, bg=self.colors["bg"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 14))

        right_col = tk.Frame(bottom_grid, bg=self.colors["bg"], width=300)
        right_col.pack(side="left", fill="y")
        right_col.pack_propagate(False)

        self._build_chart_placeholder(left_col)
        self._build_trades_table(left_col)
        self._build_side_panels(right_col)

    def _build_asset_card(self, parent):
        left = tk.Frame(parent, bg=self.colors["panel"])
        left.pack(side="left", fill="both", expand=True)

        title_row = tk.Frame(left, bg=self.colors["panel"])
        title_row.pack(anchor="w")

        tk.Label(title_row, text="XYZ Corp",
                 bg=self.colors["panel"], fg=self.colors["primary"],
                 font=("Arial", 24, "bold")).pack(side="left")
        tk.Label(title_row, text="NYSE: XYZ",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 9, "bold"), padx=8).pack(side="left", padx=10)

        tk.Label(left, text="Industrial Logistics & Tech Services",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 11)).pack(anchor="w", pady=(6, 0))

        right = tk.Frame(parent, bg=self.colors["panel"])
        right.pack(side="right", anchor="n")

        price_row = tk.Frame(right, bg=self.colors["panel"])
        price_row.pack(anchor="e")

        tk.Label(price_row, textvariable=self.latest_price_var,
                 bg=self.colors["panel"], fg=self.colors["primary"],
                 font=("Arial", 34, "bold")).pack(side="left")
        tk.Label(price_row, textvariable=self.change_var,
                 bg=self.colors["panel"], fg=self.colors["accent"],
                 font=("Arial", 16, "bold")).pack(side="left", padx=(12, 0))

        extra_row = tk.Frame(right, bg=self.colors["panel"])
        extra_row.pack(anchor="e", pady=(8, 0))

        tk.Label(extra_row, text="HIGH: --",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 10, "bold")).pack(side="left", padx=6)
        tk.Label(extra_row, text="LOW: --",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 10, "bold")).pack(side="left", padx=6)

    def _build_status_card(self, parent):
        tk.Label(parent, text="MARKET STATUS",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))

        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(anchor="w", pady=(0, 16))
        tk.Label(row, text="●", bg=self.colors["panel"], fg=self.colors["accent"],
                 font=("Arial", 12)).pack(side="left")
        tk.Label(row, textvariable=self.market_status_var,
                 bg=self.colors["panel"], fg=self.colors["text"],
                 font=("Arial", 16, "bold")).pack(side="left", padx=6)

        self._status_line(parent, "Volume", self.volume_var)
        self._status_line(parent, "Avg Vol", self.avg_vol_var)

    def _status_line(self, parent, label, variable):
        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(fill="x", pady=6)
        tk.Label(row, text=label,
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 11)).pack(side="left")
        tk.Label(row, textvariable=variable,
                 bg=self.colors["panel"], fg=self.colors["text"],
                 font=("Arial", 11, "bold")).pack(side="right")

    def _build_chart_placeholder(self, parent):
        card = self._card(parent, bg=self.colors["panel"], padx=20, pady=20)
        card.pack(fill="x", pady=(0, 18))

        top = tk.Frame(card, bg=self.colors["panel"])
        top.pack(fill="x", pady=(0, 14))

        for i, label in enumerate(["1H", "4H", "1D", "1W"]):
            active = (i == 0)
            bg = self.colors["panel_high"] if active else self.colors["panel"]
            fg = self.colors["accent"] if active else self.colors["muted"]
            tk.Label(top, text=label, bg=bg, fg=fg,
                     font=("Arial", 10, "bold"), padx=10, pady=4).pack(side="left", padx=3)

        chart = tk.Canvas(card, height=300, bg=self.colors["panel"], highlightthickness=0)
        chart.pack(fill="x")

        bar_data = [90, 130, 160, 145, 110, 190, 230, 260, 180, 290]
        sell_data = [60, 80, 40, 75, 50, 120, 115, 95, 140, 0]
        max_h = 290
        width = 760
        height = 280
        spacing = 8
        bar_w = 55

        chart.configure(width=width, height=height)

        x = 20
        baseline = 250
        for buy_h, sell_h in zip(bar_data, sell_data):
            if sell_h > 0:
                chart.create_rectangle(
                    x, baseline - sell_h, x + bar_w, baseline,
                    fill="#5a4749", outline=""
                )
            chart.create_rectangle(
                x, baseline - buy_h, x + bar_w, baseline,
                fill="#4f7d5d", outline=""
            )
            x += bar_w + spacing

        # guide line
        chart.create_line(390, 20, 390, baseline, fill="#7a8091", dash=(4, 4))
        chart.create_rectangle(360, 98, 420, 122, fill="#dfe3ff", outline="")
        chart.create_text(390, 110, text="Latest", fill="#002780", font=("Arial", 9, "bold"))

        footer = tk.Frame(card, bg=self.colors["panel"])
        footer.pack(fill="x", pady=(8, 0))
        for label in ["09:00", "11:00", "13:00", "15:00", "17:00"]:
            tk.Label(footer, text=label, bg=self.colors["panel"], fg=self.colors["muted"],
                     font=("Arial", 9, "bold")).pack(side="left", expand=True)

    def _build_trades_table(self, parent):
        card = self._card(parent, bg=self.colors["panel"], padx=0, pady=0)
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=self.colors["panel_high"], height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="LATEST TRADES: XYZ CORP",
                 bg=self.colors["panel_high"], fg=self.colors["text"],
                 font=("Arial", 12, "bold")).pack(side="left", padx=18, pady=12)

        tk.Label(header, text="VIEW ALL HISTORY",
                 bg=self.colors["panel_high"], fg=self.colors["accent"],
                 font=("Arial", 10, "bold")).pack(side="right", padx=18)

        columns = ("buyer", "seller", "quantity", "price", "time")
        self.trade_table = ttk.Treeview(card, columns=columns, show="headings", style="Dark.Treeview", height=9)

        headings = {
            "buyer": "BUYER",
            "seller": "SELLER",
            "quantity": "QUANTITY",
            "price": "PRICE",
            "time": "TIME",
        }

        widths = {
            "buyer": 180,
            "seller": 180,
            "quantity": 120,
            "price": 140,
            "time": 120,
        }

        for col in columns:
            self.trade_table.heading(col, text=headings[col])
            self.trade_table.column(col, width=widths[col], anchor="center")

        self.trade_table.pack(fill="both", expand=True, padx=10, pady=10)

    def _build_side_panels(self, parent):
        exec_card = self._card(parent, bg=self.colors["panel"], padx=20, pady=20)
        exec_card.pack(fill="x", pady=(0, 16))

        btn_row = tk.Frame(exec_card, bg=self.colors["panel"])
        btn_row.pack(fill="x", pady=(0, 16))

        tk.Label(
            btn_row,
            text="BUY / LONG",
            bg="#05e777",
            fg="#00210b",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Label(
            btn_row,
            text="SELL / SHORT",
            bg="#ffb6b1",
            fg="#68000c",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=8
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))


        self._side_field(exec_card, "Order Type", "Limit Order")
        self._side_field(exec_card, "Quantity", "100 XYZ")

        info = tk.Frame(exec_card, bg=self.colors["panel"])
        info.pack(fill="x", pady=(14, 10))

        self._info_line(info, "Available Margin", "$842,500.00")
        self._info_line(info, "Order Value", "Latest trade linked")

        tk.Label(
            exec_card,
            text="EXECUTE TRANSACTION",
            bg=self.colors["primary"],
            fg="#002780",
            font=("Arial", 14, "bold"),
            padx=6,
            pady=14,
            anchor="center",
            justify="center"
        ).pack(fill="x", pady=(8, 0))

        indicator_card = self._card(parent, bg=self.colors["panel"], padx=20, pady=20)
        indicator_card.pack(fill="x", pady=(0, 16))

        tk.Label(indicator_card, text="LATEST TRADE SUMMARY",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 12))

        self.summary_buyer = self._summary_box(indicator_card, "Buyer", "-")
        self.summary_seller = self._summary_box(indicator_card, "Seller", "-")
        self.summary_qty = self._summary_box(indicator_card, "Quantity", "-")
        self.summary_time = self._summary_box(indicator_card, "Time", "-")

        depth_card = self._card(parent, bg=self.colors["panel"], padx=20, pady=20)
        depth_card.pack(fill="x")

        tk.Label(depth_card, text="ORDER DEPTH",
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))

        self._depth_row(depth_card, "$1,249.00", "4,200", sell=True, fill_ratio=0.80)
        self._depth_row(depth_card, "$1,248.85", "2,150", sell=True, fill_ratio=0.45)
        tk.Label(depth_card, text=" $1,248.62 Mid ",
                 bg=self.colors["panel_high"], fg=self.colors["primary"],
                 font=("Arial", 11, "bold")).pack(fill="x", pady=8)
        self._depth_row(depth_card, "$1,248.40", "3,100", sell=False, fill_ratio=0.60)
        self._depth_row(depth_card, "$1,248.25", "5,800", sell=False, fill_ratio=0.90)

    def _side_field(self, parent, label, value):
        tk.Label(parent, text=label.upper(),
                 bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 9, "bold")).pack(anchor="w", pady=(6, 6))
        tk.Label(parent, text=value,
                 bg="#0b0e11", fg=self.colors["text"],
                 font=("Arial", 12, "bold"),
                 padx=12, pady=12).pack(fill="x")

    def _info_line(self, parent, left_text, right_text):
        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=left_text, bg=self.colors["panel"], fg=self.colors["muted"],
                 font=("Arial", 10)).pack(side="left")
        tk.Label(row, text=right_text, bg=self.colors["panel"], fg=self.colors["text"],
                 font=("Arial", 10, "bold")).pack(side="right")

    def _summary_box(self, parent, label, value):
        box = tk.Frame(parent, bg=self.colors["panel_high"], padx=12, pady=10)
        box.pack(fill="x", pady=6)

        tk.Label(box, text=label.upper(), bg=self.colors["panel_high"], fg=self.colors["muted"],
                 font=("Arial", 9, "bold")).pack(anchor="w")
        value_var = tk.StringVar(value=value)
        tk.Label(box, textvariable=value_var, bg=self.colors["panel_high"], fg=self.colors["accent"],
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(2, 0))
        return value_var

    def _depth_row(self, parent, price, amount, sell=True, fill_ratio=0.5):
        row = tk.Frame(parent, bg=self.colors["panel"], height=28)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        canvas = tk.Canvas(row, height=28, bg=self.colors["panel"], highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        w = 260
        fill_w = int(w * fill_ratio)
        if sell:
            canvas.create_rectangle(w - fill_w, 2, w, 26, fill="#4c393c", outline="")
            left_fg = self.colors["danger"]
        else:
            canvas.create_rectangle(0, 2, fill_w, 26, fill="#31523b", outline="")
            left_fg = self.colors["accent"]

        canvas.create_text(18, 14, text=price, fill=left_fg, anchor="w", font=("Arial", 10, "bold"))
        canvas.create_text(w - 10, 14, text=amount, fill=self.colors["muted"], anchor="e", font=("Arial", 10, "bold"))

    def _start_consumer_thread(self):
        thread = threading.Thread(target=self._consume_trades, daemon=True)
        thread.start()

    def _consume_trades(self):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )

            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=TRADES_QUEUE)

            def callback(ch, method, properties, body):
                if self.stop_event.is_set():
                    return
                try:
                    trade = json.loads(body.decode("utf-8"))
                    self.message_queue.put(trade)
                except Exception as err:
                    self.message_queue.put({"error": f"Invalid trade message: {err}"})

            channel.basic_consume(
                queue=TRADES_QUEUE,
                on_message_callback=callback,
                auto_ack=True
            )

            self.message_queue.put({"status": "Listening for trades..."})
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            self.message_queue.put({"error": "Failed to connect to RabbitMQ."})
        except Exception as err:
            self.message_queue.put({"error": f"Consumer error: {err}"})

    def _poll_messages(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()

            if "error" in message:
                self.status_var.set(message["error"])
            elif "status" in message:
                self.status_var.set(message["status"])
            else:
                self._update_trade_display(message)

        if not self.stop_event.is_set():
            self.root.after(200, self._poll_messages)

    def _update_trade_display(self, trade: dict):
        stock = trade.get("stock", "XYZ")
        price = trade.get("price", "-")
        buyer = trade.get("buyer", "-")
        seller = trade.get("seller", "-")
        quantity = trade.get("quantity", "-")
        timestamp = trade.get("timestamp", "-")

        self.root.title(f"{stock} Dashboard")

        try:
            price_value = float(price)
            self.latest_price_var.set(f"${price_value:,.2f}")
        except Exception:
            self.latest_price_var.set(str(price))

        self.change_var.set("+Latest trade")
        self.status_var.set("Latest trade received successfully.")

        self.summary_buyer.set(str(buyer))
        self.summary_seller.set(str(seller))
        self.summary_qty.set(str(quantity))
        self.summary_time.set(str(timestamp))

        # newest first
        self.trade_history.insert(0, {
            "buyer": str(buyer),
            "seller": str(seller),
            "quantity": str(quantity),
            "price": f"${float(price):,.2f}" if self._is_float(price) else str(price),
            "time": str(timestamp[-8:] if isinstance(timestamp, str) and len(timestamp) >= 8 else timestamp)
        })

        self.trade_history = self.trade_history[:8]
        self._refresh_trade_table()

    def _refresh_trade_table(self):
        for item in self.trade_table.get_children():
            self.trade_table.delete(item)

        for trade in self.trade_history:
            self.trade_table.insert(
                "",
                "end",
                values=(trade["buyer"], trade["seller"], trade["quantity"], trade["price"], trade["time"])
            )

    def _is_float(self, value):
        try:
            float(value)
            return True
        except Exception:
            return False

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()


def parse_endpoint(endpoint: str) -> tuple[str, int]:
    endpoint = endpoint.strip()
    if not endpoint:
        raise ValueError("endpoint cannot be empty")

    if ":" not in endpoint:
        raise ValueError("endpoint must be in the format host:port, e.g. localhost:5672")

    host, port_str = endpoint.split(":", 1)
    host = host.strip()
    if not host:
        raise ValueError("host cannot be empty")

    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError("port must be an integer") from exc

    if port <= 0 or port > 65535:
        raise ValueError("port must be between 1 and 65535")

    return host, port


def main():
    if len(sys.argv) != 2:
        print("Usage: python trade_gui.py <host:port>")
        print("Example: python trade_gui.py localhost:5672")
        sys.exit(1)

    try:
        host, port = parse_endpoint(sys.argv[1])

        root = tk.Tk()
        app = TradeDashboardGUI(root, host, port)
        root.mainloop()

    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()