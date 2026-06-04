import dearpygui.dearpygui as dpg

def create_equity_chart():
    with dpg.window(label="Equity Curve Canvas", width=800, height=400, pos=(0, 0), no_close=True, no_collapse=True):
        with dpg.plot(label="Capital Evolution", height=-1, width=-1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Ticks")
            with dpg.plot_axis(dpg.mvYAxis, label="Allocated Capital"):
                dpg.add_line_series([], [], label="Capital", tag="series_capital")
