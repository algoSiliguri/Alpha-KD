from sklearn.metrics import mean_squared_error
from signal_processor import SignalProcessor

class PerformanceEvaluator:
  def __init__(self):
      self.snr_calculator = SignalProcessor()

  def evaluate_performance(self, original_signal, denoised_signal):
      """Evaluate performance using MSE and SNR."""
      mse = mean_squared_error(original_signal[:len(denoised_signal)], denoised_signal)
      residual = original_signal[:len(denoised_signal)] - denoised_signal
      snr = self.snr_calculator.compute_snr(original_signal[:len(denoised_signal)], residual)
      return mse, snr