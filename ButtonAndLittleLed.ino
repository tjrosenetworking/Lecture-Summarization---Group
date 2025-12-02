const int buttonPin = 12;
const int ledPin = 13;

bool isRecording = false;
bool lastButtonState = HIGH;
bool ledState = LOW;

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);

  Serial.begin(9600);
  delay(2000);
}

void loop() {

  bool buttonState = digitalRead(buttonPin);

  if (buttonState != lastButtonState) {
      delay(50); 
      buttonState = digitalRead(buttonPin);
  }  


  if (buttonState == LOW && lastButtonState == HIGH) {

    ledState = !ledState;
    digitalWrite(ledPin, ledState);

    if (!isRecording) {
      Serial.println("START");
      isRecording = true;
    }

    //delay(200); // debounce
  }

  // Detect release -> STOP recording
  if (buttonState == HIGH && isRecording) {
    Serial.println("STOP");
    isRecording = false;
    delay(50);
  }

  lastButtonState = buttonState;
}