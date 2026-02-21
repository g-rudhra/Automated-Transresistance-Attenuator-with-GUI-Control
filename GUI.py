import customtkinter as ctk
import serial
import threading
import time
import numpy as np

# ============ Arduino Serial Setup ============
try:
    arduino = serial.Serial('COM13', 9600, timeout=1)  # change port as needed
    time.sleep(2)
except Exception as e:  
    print("Arduino not connected:", e)
    arduino = None

# ============ Numeric Optimization Setup ============
# Physical / fixed params
Z_L = 4.7/4        # load impedance (ohm)
R2_fixed = 4.70    # fixed middle resistor (ohm)

LOWER_BOUND = 50.0
UPPER_BOUND = 10000.0

def gm_from_Rs(R1, R2, R3, Z_L):
    # returns gm = 1 / ((1 + (R3 + Z_L) / R2) * R1 + (R3 + Z_L))
    return 1.0 / ((1.0 + (R3 + Z_L) / R2) * R1 + (R3 + Z_L))

def optimize_resistors_numpy(G_dB, R2=R2_fixed,
                             R1_range=(LOWER_BOUND, UPPER_BOUND),
                             R3_range=(LOWER_BOUND, UPPER_BOUND),
                             n1=1000, n3=1000, coarse_refine=True):
    target_att = 10 ** (-G_dB / 10.0)  # target gm (attenuation ratio)

    R1_vals = np.linspace(R1_range[0], R1_range[1], n1)
    R3_vals = np.linspace(R3_range[0], R3_range[1], n3)

    R1_grid, R3_grid = np.meshgrid(R1_vals, R3_vals, indexing='xy')
    gm_grid = gm_from_Rs(R1_grid, R2, R3_grid, Z_L)
    abs_err = np.abs(gm_grid - target_att)

    idx_flat = np.argmin(abs_err.ravel())
    i_r3, i_r1 = np.unravel_index(idx_flat, abs_err.shape)
    best_R1 = R1_grid[i_r3, i_r1]
    best_R3 = R3_grid[i_r3, i_r1]
    best_gm = gm_grid[i_r3, i_r1]

    if coarse_refine:
        r1_lo = max(R1_range[0], best_R1 * 0.8)
        r1_hi = min(R1_range[1], best_R1 * 1.2)
        r3_lo = max(R3_range[0], best_R3 * 0.8)
        r3_hi = min(R3_range[1], best_R3 * 1.2)

        R1_vals_f = np.linspace(r1_lo, r1_hi, 500)
        R3_vals_f = np.linspace(r3_lo, r3_hi, 500)
        R1g_f, R3g_f = np.meshgrid(R1_vals_f, R3_vals_f, indexing='xy')
        gm_f = gm_from_Rs(R1g_f, R2, R3g_f, Z_L)
        err_f = np.abs(gm_f - target_att)
        idxf = np.argmin(err_f.ravel())
        ir3f, ir1f = np.unravel_index(idxf, err_f.shape)
        best_R1 = R1g_f[ir3f, ir1f]
        best_R3 = R3g_f[ir3f, ir1f]
        best_gm = gm_f[ir3f, ir1f]

    achieved_att_dB = -10.0 * np.log10(best_gm)
    return best_R1, R2, best_R3, achieved_att_dB

# ============ REVERSED motor mapping ============
def map_resistor_to_angle(R, lower=LOWER_BOUND, upper=UPPER_BOUND):
    # Reverse direction mapping
    R_clamped = max(lower, min(upper, R))
    return int((upper - R_clamped) / (upper - lower) * 270)

# ============ GUI Logic ============
def Simulate():
    try:
        G_dB = float(entry_dB.get())
    except ValueError:
        label_angles.configure(text="Invalid input")
        return

    def job():
        btn_simulate.configure(state="disabled", text="Optimizing...")
        best_r1, best_r2, best_r3, achieved_dB = optimize_resistors_numpy(G_dB)
        angle1 = map_resistor_to_angle(best_r1)
        angle3 = map_resistor_to_angle(best_r3)

        label_angles.configure(text=f"Mapped Angles:\nMotor 1: {angle1}°, Motor 2: {angle3}°")
        label_resistors.configure(text=(
            f"Resistor values:\nR1 = {best_r1:.2f} Ω\nR2 = {best_r2:.2f} Ω\nR3 = {best_r3:.2f} Ω\n"
            f"Achieved Attenuation = {achieved_dB:.3f} dB"
        ))

        if arduino:
            angle_str = f"{angle1},{angle3}\n"
            try:
                arduino.write(angle_str.encode())
                time.sleep(0.1)
                arduino.write(b'C')
            except Exception as e:
                print("Arduino write error:", e)

        btn_simulate.configure(state="normal", text="Simulate")

    threading.Thread(target=job, daemon=True).start()

led_on = False
def toggle_led():
    global led_on
    if arduino:
        try:
            arduino.write(b'L')
            led_on = not led_on
            btn_led.configure(text="Turn LED OFF" if led_on else "Turn LED ON")
        except Exception as e:
            print("Arduino write failed:", e)

# ============ GUI Setup ============
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Arduino Attenuator GUI")
app.geometry("500x600")

label_title = ctk.CTkLabel(app, text="Enter Attenuation (dB)", font=ctk.CTkFont(size=18))
label_title.pack(pady=15)

entry_dB = ctk.CTkEntry(app, placeholder_text="From 19 to 63", width=200)
entry_dB.pack(pady=10)

btn_simulate = ctk.CTkButton(app, text="Simulate", command=Simulate)
btn_simulate.pack(pady=15)

label_angles = ctk.CTkLabel(app, text="Mapped Angles: ---", font=ctk.CTkFont(size=14))
label_angles.pack(pady=10)

label_resistors = ctk.CTkLabel(app, text="Resistors: ---", font=ctk.CTkFont(size=13))
label_resistors.pack(pady=10)

btn_led = ctk.CTkButton(app, text="Turn LED ON", command=toggle_led)
btn_led.pack(pady=20)

app.mainloop()
