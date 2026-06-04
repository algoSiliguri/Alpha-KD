import dearpygui.dearpygui as dpg

def create_logger_console():
    with dpg.window(label="Telemetry Stream Logger", width=1200, height=200, pos=(0, 400), no_close=True, no_collapse=True):
        dpg.add_input_text(multiline=True, default_value="[System] UI Initialized.\n", width=-1, height=-1, readonly=True, tag="logger_text")

def log_message(msg: str):
    try:
        current = dpg.get_value("logger_text")
        lines = current.split('\n')
        if len(lines) > 50:
            lines = lines[-50:]
        new_text = "\n".join(lines) + msg + "\n"
        dpg.set_value("logger_text", new_text)
    except Exception:
        print(msg)
