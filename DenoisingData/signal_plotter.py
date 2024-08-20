import matplotlib.pyplot as plt

class SignalPlotter:
  def plot_signals(self, time, original_signal, denoised_signal, residual):
      """Plot the original, denoised, and residual signals."""
      plt.figure(figsize=(12, 6))
      plt.plot(time, original_signal, label='Original Signal', alpha=0.75)
      plt.plot(time[:len(denoised_signal)], denoised_signal, label='Denoised Signal', alpha=0.75)
      plt.title('Original vs Denoised Signal')
      plt.legend()
      plt.show()

      plt.figure(figsize=(12, 6))
      plt.plot(time[:len(residual)], residual, label='Residual (Original - Denoised)')
      plt.title('Residual Plot')
      plt.legend()
      plt.show()