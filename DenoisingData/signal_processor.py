import numpy as np
import pandas as pd
import pywt

class SignalProcessor:
    def load_data(self, filepath):
        """Load data from a CSV file."""
        data = pd.read_csv(filepath)
        signal = data['close'].values
        time = pd.to_datetime(data['time'])
        return signal, time

    def compute_snr(self, signal, noise):
        """Compute the Signal-to-Noise Ratio (SNR)."""
        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)
        snr = 10 * np.log10(signal_power / noise_power)
        return snr

    def wavelet_denoise(self, signal, wavelet, level, threshold, mode='soft'):
        """Perform wavelet denoising on the signal."""
        coeffs = pywt.wavedec(signal, wavelet, level=level)
        coeffs_thresholded = [pywt.threshold(c, threshold, mode=mode) for c in coeffs]
        denoised_signal = pywt.waverec(coeffs_thresholded, wavelet)
        return denoised_signal[:len(signal)]