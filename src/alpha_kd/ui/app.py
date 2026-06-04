import os
import sys
import argparse
import multiprocessing.shared_memory as shm
import dearpygui.dearpygui as dpg

from alpha_kd.ui.render_loop import NativeUIReader
from alpha_kd.ui.views.charts import create_equity_chart
from alpha_kd.ui.views.metrics import create_metrics_grid
from alpha_kd.ui.views.logger import create_logger_console, log_message

def run_ui():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()
    
    session_id = args.session_id
    ring_name = f"ring_{session_id}"
    snap_name = f"snap_{session_id}"
    
    dpg.create_context()
    
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 20, 20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
            dpg.add_theme_color(dpg.mvThemeCol_PlotLines, (50, 205, 50, 255), category=dpg.mvThemeCat_Plots)
    
    dpg.bind_theme(global_theme)
    
    dpg.create_viewport(title=f"Alpha-KD Observability | Session: {session_id}", width=1200, height=600)
    dpg.setup_dearpygui()
    
    create_equity_chart()
    create_metrics_grid()
    create_logger_console()
    
    dpg.show_viewport()
    log_message(f"[System] Booting UI for session {session_id}")
    
    try:
        ring_shm = shm.SharedMemory(name=ring_name)
        snap_shm = shm.SharedMemory(name=snap_name)
        reader = NativeUIReader(ring_shm.buf, snap_shm.buf)
        log_message("[System] Successfully mapped telemetry buffers.")
    except Exception as e:
        log_message(f"[Error] Failed to attach shared memory: {e}")
        reader = None

    while dpg.is_dearpygui_running():
        if reader:
            reader.render_tick()
        dpg.render_dearpygui_frame()
        
    dpg.destroy_context()

if __name__ == "__main__":
    run_ui()
