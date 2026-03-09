import threading
import time
from datetime import datetime
import csv
import os

# -----------------------------
# Configuration
# -----------------------------
MAX_TACHO = 3000        # Max tachometer value (can vary)
LOG_INTERVAL = 3.0      # Seconds between logs (can vary)

# Build a timestamped CSV filename at startup (local time)
start_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOGFILE = f"tachometer_log_{start_ts}.csv"

# Shared state
pwm_value = 0.0         # initial PWM
tachometer_value = 0.0  # initial tachometer

# Synchronization
lock = threading.Lock()
stop_event = threading.Event()


def _ensure_csv_with_header(path: str):
    """
    Create the CSV file with a header if it doesn't exist or is empty.
    """
    needs_header = (not os.path.exists(path)) or os.path.getsize(path) == 0
    if needs_header:
        with open(path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "tachometer", "pwm", "status"])


# -----------------------------
# Tachometer logging function
# -----------------------------
def tachometer_logger():
    global pwm_value, tachometer_value

    _ensure_csv_with_header(LOGFILE)

    while not stop_event.is_set():
        # Sleep in small increments to react quickly to stop_event
        end_time = time.time() + LOG_INTERVAL
        while time.time() < end_time:
            if stop_event.is_set():
                return
            time.sleep(0.05)

        with lock:
            # Tachometer is % of MAX_TACHO, but capped [0, MAX_TACHO]
            raw_tacho = (pwm_value / 100.0) * MAX_TACHO
            tachometer_value = max(0.0, min(MAX_TACHO, raw_tacho))

            # Determine pass/fail
            status = "PASS" if pwm_value <= 100 else "FAIL"

            # Timestamp (local time)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append a row to the CSV
            with open(LOGFILE, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, f"{tachometer_value:.2f}", f"{pwm_value:.2f}", status])

            # Also print to console
            print(f"{timestamp}, tachometer={tachometer_value:.2f}, pwm={pwm_value:.2f}, status={status}")


# -----------------------------
# PWM Input Function
# -----------------------------
def pwm_input():
    global pwm_value
    print("Type a number ANYTIME into the ongoing LOG to set PWM (can be >100). Type 'q' or 'quit' to exit.")

    while not stop_event.is_set():
        try:
            user = input("Enter PWM (or 'q' to quit): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            # Graceful shutdown if input stream closes or Ctrl+C
            stop_event.set()
            break

        if user in ("q", "quit"):
            stop_event.set()
            break

        # Attempt to parse numeric PWM
        try:
            new_pwm = float(user)
            with lock:
                pwm_value = new_pwm  # Any number allowed; tachometer is capped separately
        except ValueError:
            print("Invalid input. Please enter a numeric PWM value, or 'q' to quit.")


# -----------------------------
# Main Program
# -----------------------------
if __name__ == "__main__":
    print("Starting parallel Tachometer Logger and PWM Input...")
    print(f"Logging every {LOG_INTERVAL} second(s) to {LOGFILE}")
    print(f"Max Tachometer = {MAX_TACHO}")
    print("----------------------------------------------")

    # Create threads
    t_logger = threading.Thread(target=tachometer_logger, name="TachoLogger", daemon=True)
    t_input = threading.Thread(target=pwm_input, name="PWMInput", daemon=False)

    # Start threads
    t_logger.start()
    t_input.start()

    # Wait for input thread to finish (when user quits)
    t_input.join()

    # Signal stop and allow logger to exit
    stop_event.set()
    t_logger.join(timeout=2.0)

    print("\nShutdown complete. Goodbye!")