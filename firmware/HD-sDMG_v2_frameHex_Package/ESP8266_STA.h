#ifndef __ESP8266_STA_H
#define __ESP8266_STA_H

#include <Arduino.h>
#include <string.h>
#include <stdio.h>
#include <NanoBLEFlashPrefs.h>
#include "SerialBuffer.h"
#include "OLED091.h"
#include "CD4051.h"

typedef struct
{
  char id[20];
  char pwd[20];
  char ip[16];
  char port[6];
} flashPrefs;

class ESP8266_STA
{
private:
  HardwareSerial *_espSerial = NULL;
  SerialBuffer *_espBuf = NULL;
  HardwareSerial *_debugSerial = NULL;
  SerialBuffer *_debugBuf = NULL;
  NanoBLEFlashPrefs _flash;
  flashPrefs _idSave;

public:
  uint8_t stateFlag = 0;    //0：未联网，1：连接上了wifi，2：通过TCP连接到了服务端，3：可以透传，其它：什么都不做

  ESP8266_STA(HardwareSerial *espSerial,   SerialBuffer *espBuf);
  ESP8266_STA(HardwareSerial *espSerial,   SerialBuffer *espBuf,
              HardwareSerial *debugSerial, SerialBuffer *debugBuf);
  ESP8266_STA(HardwareSerial *espSerial,   SerialBuffer *espBuf,
              HardwareSerial *debugSerial, SerialBuffer *debugBuf,
              char *id, char *pwd, char *ip, char *port);

  bool SendCmd(const char *cmd, const char *res);       //命令和期望的回复
  void SendData(const char *str);                       //透传模式下发送字符串数据
  void SendData(int data);                              //透传模式下发送整形数据
  void SendData(const uint8_t data[], uint16_t len);    //透传模式下发送十六进制数据
 
  bool Reset(void);     //复位ESP8266
  bool Restore(void);   //恢复出厂设置
  bool Hand(void);      //握手并关闭回传
  bool SetMode(void);   //设置工作模式为STA模式
  bool WLANConnect(void);   //设置WiFi并保存
  bool TCPConnect(void);      //建立TCP连接
  bool TransparentON(void);    //开启透传模式
  bool TransparentOFF(void);   //关闭透传模式
  
  void ESPLoop(CD4051_Manager *cd);         //监测运行状态   
  void DebugLoop(CD4051_Manager *cd);       //查询是否有Debug指令  
  bool ReadESP(void);         //读取ESP串口数据
  bool ReadDebug(void);       //读取debug串口数据
  void ESPPassBack(void);     //回传ESP8266串口收到的数据
  void DebugPassBack(void);   //回传调试串口收到的数据

  ~ESP8266_STA();
};

#endif


