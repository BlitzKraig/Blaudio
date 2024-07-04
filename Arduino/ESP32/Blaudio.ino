const int KNOB_COUNT = 5;
const int analogInputs[KNOB_COUNT] = {A0, A1, A2, A3, A4};
const int resetButtonPin = 2;

int knobValues[KNOB_COUNT];

// Variables for heartbeat
const String heartbeatMessage = "BLAUDIO_HEARTBEAT";
unsigned long lastHeartbeatTime = 0;
const unsigned long heartbeatTimeout = 15000; // 15 seconds

void setup()
{
  for (int i = 0; i < KNOB_COUNT; i++)
  {
    pinMode(analogInputs[i], INPUT);
  }
  pinMode(resetButtonPin, INPUT_PULLUP);

  analogReadResolution(10);

  Serial.begin(9600);
}

void loop()
{
  checkResetButton();
  checkHeartbeat();
  pushKnobValues();
  delay(10);
}

void checkResetButton()
{
  int buttonState = digitalRead(resetButtonPin);

  if (buttonState == LOW)
  {
    // Button is pressed
    ESP.restart();
  }
}

void checkHeartbeat()
{
  if (Serial.available() > 0)
  {
    String incomingString = Serial.readStringUntil('\n');
    if (incomingString == heartbeatMessage)
    {
      // Reset the timer when the heartbeat message is received
      lastHeartbeatTime = millis();
    }
  }
  // Check if the heartbeat timeout has been exceeded
  if (millis() - lastHeartbeatTime > heartbeatTimeout)
  {
    ESP.restart();
  }
}

void pushKnobValues()
{
  String serialKnobString = String("");

  for (int i = 0; i < KNOB_COUNT; i++)
  {
    knobValues[i] = analogRead(analogInputs[i]);
    
    serialKnobString += analogRead(analogInputs[i]);

    if (i < KNOB_COUNT - 1)
    {
      serialKnobString += String("|");
    }
  }

  Serial.println(serialKnobString);
}
