import numpy as np
import pandas as pd
from signal_processor import SignalProcessor
from performance_evaluator import PerformanceEvaluator
from signal_plotter import SignalPlotter
from parameter_tuner import ParameterTuner

if __name__ == "__main__":
    # Create instances of the classes
    processor = SignalProcessor()
    evaluator = PerformanceEvaluator()
    plotter = SignalPlotter()
    tuner = ParameterTuner()

    # Load the data
    filepath = "../Upstox_Data/Fixed_Time_Bars/NIFTYBEES_day.csv"
    signal, time = processor.load_data(filepath)

    # Define parameters to tune
    wavelets = ["db1", "sym5", "coif5", "haar"]
    levels = range(1, 6)
    thresholds = np.linspace(0.1, 1.0, 10)

    # Default wavelet and level
    default_wavelet = "db1"
    default_level = 4
    default_threshold = 0.4

    # Tune parameters
    best_threshold, best_mse_threshold, best_snr_threshold = tuner.tune_threshold(
        signal, default_wavelet, default_level, thresholds
    )
    print(
        f"Best Threshold: {best_threshold}, MSE: {best_mse_threshold}, SNR: {best_snr_threshold}"
    )

    best_wavelet, best_mse_wavelet, best_snr_wavelet = tuner.tune_wavelet(
        signal, wavelets, default_level, default_threshold
    )
    print(
        f"Best Wavelet: {best_wavelet}, MSE: {best_mse_wavelet}, SNR: {best_snr_wavelet}"
    )

    best_level, best_mse_level, best_snr_level = tuner.tune_level(
        signal, default_wavelet, levels, default_threshold
    )
    print(
        f"Best Decomposition Level: {best_level}, MSE: {best_mse_level}, SNR: {best_snr_level}"
    )

    best_mode, best_mse_mode, best_snr_mode = tuner.tune_thresholding_method(
        signal, default_wavelet, default_level, default_threshold
    )
    print(
        f"Best Thresholding Mode: {best_mode}, MSE: {best_mse_mode}, SNR: {best_snr_mode}"
    )

    # Final denoised signal with the best parameters
    final_denoised_signal = processor.wavelet_denoise(
        signal, best_wavelet, best_level, best_threshold, best_mode
    )

    truncated_denoised_signal = final_denoised_signal[: len(time)]
    df_denoised = pd.DataFrame(
        {"time": time, "denoised_signal": truncated_denoised_signal}
    )

    # Save the DataFrame to a CSV file
    df_denoised.to_csv("../DenoisingData/final_denoised_signal.csv", index=False)

    print("Denoised signal saved to 'final_denoised_signal.csv'")
    residual = signal[: len(final_denoised_signal)] - final_denoised_signal

    # Plot signals
    plotter.plot_signals(time, signal, final_denoised_signal, residual)
