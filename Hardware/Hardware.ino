#include <Stepper.h>

const int ledPin = 13;
bool ledState = false;

const int stepsPerRevolution = 2048;  // 28BYJ-48 full revolution

// Motor pins (adjust to your wiring)
Stepper motor1(stepsPerRevolution, 6, 8, 7, 9);
Stepper motor2(stepsPerRevolution, 2, 4, 3, 5);

// Track current angle positions (degrees)
float currentAngle1 = 0;
float currentAngle2 = 0;

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  Serial.println("Ready");

  motor1.setSpeed(10);  // RPM
  motor2.setSpeed(10);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() == 0) return;

    if (input == "L") {
      // Toggle LED
      ledState = !ledState;
      digitalWrite(ledPin, ledState ? HIGH : LOW);
      Serial.print("LED is now ");
      Serial.println(ledState ? "ON" : "OFF");
    } else {
      // Expect input as "angle1,angle2"
      float angle1, angle2;
      if (parseAngles(input, angle1, angle2)) {
        rotateToAngle(angle1, angle2);
      } else {
        Serial.println("Invalid input format. Use angle1,angle2");
      }
    }
  }
}

bool parseAngles(String s, float &a1, float &a2) {
  int commaIndex = s.indexOf(',');
  if (commaIndex == -1) return false;

  String part1 = s.substring(0, commaIndex);
  String part2 = s.substring(commaIndex + 1);

  a1 = part1.toFloat();
  a2 = part2.toFloat();

  if (a1 < 0 || a1 > 360 || a2 < 0 || a2 > 360) return false;

  return true;
}

void rotateToAngle(float targetAngle1, float targetAngle2) {
  targetAngle1 = constrain(targetAngle1, 0, 360);
  targetAngle2 = constrain(targetAngle2, 0, 360);

  // Calculate step difference for motor 1
  long targetSteps1 = degreesToSteps(targetAngle1);
  long currentSteps1 = degreesToSteps(currentAngle1);
  long stepDiff1 = targetSteps1 - currentSteps1;

  // Calculate step difference for motor 2
  long targetSteps2 = degreesToSteps(targetAngle2);
  long currentSteps2 = degreesToSteps(currentAngle2);
  long stepDiff2 = targetSteps2 - currentSteps2;

  Serial.print("Motor1 steps: "); Serial.println(stepDiff1);
  Serial.print("Motor2 steps: "); Serial.println(stepDiff2);

  motor1.step(stepDiff1);
  motor2.step(stepDiff2);

  currentAngle1 = targetAngle1;
  currentAngle2 = targetAngle2;

  Serial.println("Rotation complete");
}

long degreesToSteps(float degrees) {
  return (long)((degrees / 360.0) * stepsPerRevolution + 0.5);
}
