// OUTDATED!!! ========================

const int KNOB_COUNT = 5;
const int analogInputs[KNOB_COUNT] = {A0,A1,A2,A3,A4};
const int BUTTON_COUNT = 1;
const int digitalInputs[BUTTON_COUNT]= {2};

int knobValues[KNOB_COUNT];
int buttonValues[BUTTON_COUNT];

// Variables for heartbeat
const String heartbeatMessage = "BLAUDIO_HEARTBEAT";
unsigned long lastHeartbeatTime = 0;
const unsigned long heartbeatTimeout = 15000; // 15 seconds

String serialString = "";

void setup()
{
  for (int i = 0; i < KNOB_COUNT; i++)
  {
    pinMode(analogInputs[i], INPUT);
  }
  
  for (int i = 0; i < BUTTON_COUNT; i++)
  {
    pinMode(digitalInputs[i], INPUT_PULLUP);
  }

  analogReadResolution(10);

  Serial.begin(9600);
}

void loop()
{
  checkHeartbeat();
  checkButtons();
  checkKnobValues();
  pushSerial();
  delay(10);
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
    // Serial.end();
    // delay(100);
    // Serial.begin(9600);
    // lastHeartbeatTime = millis();
    ESP.restart();
  }
}

void checkButtons()
{
  for (int i = 0; i < BUTTON_COUNT; i++)
  {
    buttonValues[i] = digitalRead(digitalInputs[i]);
  }
}

void checkKnobValues()
{
  for (int i = 0; i < KNOB_COUNT; i++)
  {
    knobValues[i] = analogRead(analogInputs[i]);
  }
}

void pushSerial()
{
  serialString = String("");
  if(BUTTON_COUNT > 0)
  {
    serialString += String("BTN");
  }
  for (int i = 0; i < BUTTON_COUNT; i++)
  {
    serialString += buttonValues[i];
    if (i < BUTTON_COUNT - 1)
    {
      serialString += String("|");
    }
  }
  if(KNOB_COUNT > 0)
  {
    serialString += String("KNOB");
  }
  for (int i = 0; i < KNOB_COUNT; i++)
  {
    serialString += knobValues[i];
    if (i < KNOB_COUNT - 1)
    {
      serialString += String("|");
    }
  }
  
  Serial.println(serialString);
}
