# Arduino Dual-Stepper Attenuator Controller (GUI + Optimization)

This project implements a **PC GUI-controlled attenuator** using:
- **Python (CustomTkinter)** for the user interface
- **NumPy-based numeric optimization** to compute resistor values for a target attenuation (dB)
- **Arduino + 2× 28BYJ-48 stepper motors** to mechanically set the attenuator (via mapped angles)
- A simple **serial protocol** (`angle1,angle2` and `L`) to command motors and toggle an onboard LED

---

## Features

- Enter desired **attenuation in dB** (e.g., 19 to 63)
- Computes **best-fit resistor values**: `R1`, `R2 (fixed)`, `R3`
- Maps computed resistors → **stepper angles** (0–270°)
- Sends angles to Arduino over serial as:  
  `angle1,angle2\n`
- Arduino rotates both motors to the requested angles and prints debug info to Serial Monitor
- GUI button to **toggle Arduino LED (pin 13)** by sending `L`

---

## System Overview

### 1) Optimization Model (Python)
The attenuator gain model is:

\[
gm = \frac{1}{\left(1 + \frac{R3 + Z_L}{R2}\right)R1 + (R3 + Z_L)}
\]

Target attenuation is converted to the target gain:

\[
gm_{target} = 10^{-G_{dB}/10}
\]

The script searches over bounded ranges of `R1` and `R3` and selects values minimizing:

\[
|gm - gm_{target}|
\]

A coarse grid search is followed by a local refine search for better accuracy.

### 2) Angle Mapping (Reversed)
Resistor values are mapped to a 0–270° shaft rotation (reverse direction):

- `R = LOWER_BOUND` → 270°
- `R = UPPER_BOUND` → 0°

### 3) Arduino Motion Control
Arduino receives either:
- `"L"` → toggle LED on pin 13
- `"angle1,angle2"` → rotate Motor 1 and Motor 2 to those absolute angles (0–360 constraint in code)

Angles are converted to steps using:
- **28BYJ-48**: `2048 steps/revolution`

---

## Hardware Requirements

- Arduino (Uno / Nano / Mega etc.)
- 2 × **28BYJ-48 stepper motors**
- 2 × **ULN2003 stepper driver boards**
- External 5V supply recommended for motors (common GND with Arduino)
- USB cable for Arduino serial connection

---

## Software Requirements

### Python
- Python 3.9+
- Packages:
  - `customtkinter`
  - `pyserial`
  - `numpy`

Install dependencies:
```bash
pip install customtkinter pyserial numpy