#include "CD4051.h"

// CD4051_Chip chip1(D5, A3, 7);
// CD4051_Chip cdChip[3]={
//               {D5, A3, 7},
//               {D4, A4, 7},
//               {D3, A5, 6}};
CD4051_Chip cdChip[3]={
  CD4051_Chip(A2, 7),
  CD4051_Chip(A1, 7),
  CD4051_Chip(A0, 6)};

CD4051_Manager cdManage(A5, A4, A3, 3, cdChip);

int temp = 0;

void setup() 
{
  delay(1000);
  
  Serial.begin(115200);
  // analogReference(AR_INTERNAL1V2);   //内部1.2V参考电压  
  analogReference(AR_INTERNAL2V4);   //内部2.4V参考电压  
  analogReadResolution(16);

  // pinMode(D5, OUTPUT);
  // pinMode(D4, OUTPUT);
  // pinMode(D3, OUTPUT);
  // pinMode(A2, OUTPUT);
  // pinMode(A1, OUTPUT);
  // pinMode(A0, OUTPUT);

  // digitalWrite(D5, LOW);
  // digitalWrite(D4, LOW);
  // digitalWrite(D3, LOW);
  // digitalWrite(A2, LOW);
  // digitalWrite(A1, LOW);
  // digitalWrite(A0, LOW);

  delay(2000);
  // chip1.debug();
  // cdChip[0].debug();
  // cdChip[1].debug();
  // cdChip[2].debug();
  // cdManage.debug();
  // cdManage.ChooseLine(0);
}

void loop() 
{
  // cdManage.ChooseLine(0);
  // temp = analogRead(A2);
  // Serial.println(temp);

  // cdManage.ChooseLine(1);
  // temp = analogRead(A1);
  // Serial.println(temp);

  // cdManage.ChooseLine(2);
  // temp = analogRead(A0);
  // Serial.println(temp);

  // cdManage.ReadGroup();
  // cdManage.SendGroup();
  cdManage.Loop();
  // cdManage.debug();
  delay(50);
}


