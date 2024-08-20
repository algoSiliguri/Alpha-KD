from signal_processor import SignalProcessor
from performance_evaluator import PerformanceEvaluator


class ParameterTuner:
    def __init__(self):
        self.denoiser = SignalProcessor()
        self.evaluator = PerformanceEvaluator()

    def tune_threshold(self, signal, wavelet, level, thresholds, mode="soft"):
        """Tune the threshold parameter."""
        best_threshold = None
        best_mse = float("inf")
        best_snr = None

        for t in thresholds:
            denoised_signal = self.denoiser.wavelet_denoise(
                signal, wavelet, level, t, mode
            )
            mse, snr = self.evaluator.evaluate_performance(signal, denoised_signal)
            if mse < best_mse:
                best_mse = mse
                best_snr = snr
                best_threshold = t

        return best_threshold, best_mse, best_snr

    def tune_wavelet(self, signal, wavelets, level, threshold, mode="soft"):
        """Tune the wavelet type."""
        best_wavelet = None
        best_mse = float("inf")
        best_snr = None

        for wavelet in wavelets:
            denoised_signal = self.denoiser.wavelet_denoise(
                signal, wavelet, level, threshold, mode
            )
            mse, snr = self.evaluator.evaluate_performance(signal, denoised_signal)
            if mse < best_mse:
                best_mse = mse
                best_snr = snr
                best_wavelet = wavelet

        return best_wavelet, best_mse, best_snr

    def tune_level(self, signal, wavelet, levels, threshold, mode="soft"):
        """Tune the decomposition level."""
        best_level = None
        best_mse = float("inf")
        best_snr = None

        for level in levels:
            denoised_signal = self.denoiser.wavelet_denoise(
                signal, wavelet, level, threshold, mode
            )
            mse, snr = self.evaluator.evaluate_performance(signal, denoised_signal)
            if mse < best_mse:
                best_mse = mse
                best_snr = snr
                best_level = level

        return best_level, best_mse, best_snr

    def tune_thresholding_method(self, signal, wavelet, level, threshold):
        """Tune the thresholding method (soft/hard)."""
        best_mode = None
        best_mse = float("inf")
        best_snr = None

        for mode in ["soft", "hard"]:
            denoised_signal = self.denoiser.wavelet_denoise(
                signal, wavelet, level, threshold, mode
            )
            mse, snr = self.evaluator.evaluate_performance(signal, denoised_signal)
            if mse < best_mse:
                best_mse = mse
                best_snr = snr
                best_mode = mode

        return best_mode, best_mse, best_snr
