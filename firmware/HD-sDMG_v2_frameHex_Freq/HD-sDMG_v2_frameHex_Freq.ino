#include "SerialBuffer.h"
#include "ESP8266_STA.h"
#include "OLED091.h"
#include "CD4051.h"

//ESP8266
SerialBuffer rx0(50);
SerialBuffer rx1;
ESP8266_STA esp(&Serial1, &rx1, &Serial, &rx0);

//CD4051B
CD4051_Chip cdChip[3]={
  CD4051_Chip(A2, 7),
  CD4051_Chip(A1, 7),
  CD4051_Chip(A0, 6)};
CD4051_Manager cdManage(A5, A4, A3, 3, cdChip);

uint8_t lastState = esp.stateFlag;

void setup() 
{
  delay(1000);

  //调试串口
  Serial.begin(115200);

  //通信串口
  Serial1.begin(115200);

  // analogReference(AR_INTERNAL1V2);   //内部1.2V参考电压  
  analogReference(AR_INTERNAL2V4);   //内部2.4V参考电压  
  analogReadResolution(16);

  OLED_Init();
  OLED_ShowString(0, 0,"State:",8);  
  // OLED_ShowString(0,24,"Frame:",8);  
  OLED_ShowNum(36,0,esp.stateFlag,3,8);  
  OLED_Refresh();
  
  esp.Reset();
  esp.Hand();
}


void loop() 
{
  esp.ESPLoop(&cdManage);
  esp.DebugLoop(&cdManage);

  if(lastState != esp.stateFlag)
  {
    lastState = esp.stateFlag;
    // Serial.println(esp.stateFlag);
    OLED_ShowNum(36,0,esp.stateFlag,3,8);  
    OLED_Refresh();
  }

  // delay(500);
}




