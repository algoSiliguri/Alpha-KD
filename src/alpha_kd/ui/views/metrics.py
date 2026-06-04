import dearpygui.dearpygui as dpg

def create_metrics_grid():
    with dpg.window(label="Strategy Metrics Grid", width=400, height=400, pos=(800, 0), no_close=True, no_collapse=True):
        with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True):
            dpg.add_table_column()
            dpg.add_table_column()
            
            with dpg.table_row():
                dpg.add_text("Sequence ID")
                dpg.add_text("0", tag="metric_sequence_id")
            with dpg.table_row():
                dpg.add_text("Unrealized PnL")
                dpg.add_text("0.00", tag="metric_upnl")
            with dpg.table_row():
                dpg.add_text("Allocated Capital")
                dpg.add_text("0.00", tag="metric_capital")
