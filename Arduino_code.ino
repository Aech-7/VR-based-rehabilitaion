int flexSensorPins[] = {A0, A1, A2, A3, A4}; 
int flexSensorValues[5]; 

void setup() {
  Serial.begin(9600); 
}

void loop() {
  for (int i = 0; i < 5; i++) {
    flexSensorValues[i] = analogRead(flexSensorPins[i]);
  }

  for (int i = 0; i < 5; i++) {
    Serial.print(flexSensorValues[i]);
    if (i < 4) {
      Serial.print(","); 
    }
  }
  Serial.println(); 

  delay(100); 
}
