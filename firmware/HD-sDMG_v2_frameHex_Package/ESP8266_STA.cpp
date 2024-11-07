#include "ESP8266_STA.h"

//复位引脚
#define RST_Pin D2

ESP8266_STA::ESP8266_STA(HardwareSerial *espSerial, SerialBuffer *espBuf):
_espSerial(espSerial), _espBuf(espBuf)
{
  this->_flash.readPrefs(&this->_idSave, sizeof(this->_idSave));

  this->stateFlag = 0;

  pinMode(RST_Pin, OUTPUT);
  digitalWrite(RST_Pin, HIGH);
}


ESP8266_STA::ESP8266_STA(HardwareSerial *espSerial, SerialBuffer *espBuf, HardwareSerial *debugSerial, SerialBuffer *debugBuf):
_espSerial(espSerial), _espBuf(espBuf), _debugSerial(debugSerial), _debugBuf(debugBuf)
{
  this->_flash.readPrefs(&this->_idSave, sizeof(this->_idSave));

  this->stateFlag = 0;

  pinMode(RST_Pin, OUTPUT);
  digitalWrite(RST_Pin, HIGH);
}


ESP8266_STA::ESP8266_STA(HardwareSerial *espSerial, SerialBuffer *espBuf, HardwareSerial *debugSerial, SerialBuffer *debugBuf, char *id, char *pwd, char *ip, char *port):
_espSerial(espSerial), _espBuf(espBuf), _debugSerial(debugSerial), _debugBuf(debugBuf)
{
  strcpy(this->_idSave.id, id);
  strcpy(this->_idSave.pwd, pwd);
  strcpy(this->_idSave.ip, ip);
  strcpy(this->_idSave.port, port);
  // this->_flash.deletePrefs();          // 删除valid records
  this->_flash.garbageCollection();    //删除 dirty
  this->_flash.writePrefs(&this->_idSave, sizeof(this->_idSave));

  this->stateFlag = 0;

  pinMode(RST_Pin, OUTPUT);
  digitalWrite(RST_Pin, HIGH);
}


//命令和期望的回复
bool ESP8266_STA::SendCmd(const char *cmd, const char *res)
{
  uint8_t timeOut = 100;
  // this->_espBuf->Clear();
  this->_espSerial->print(cmd);
  while(timeOut--)
  {
    if(this->ReadESP() == true && strstr(this->_espBuf->GetString(),res) != NULL)
    {
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();      
      return true;
    }
    delay(10);
  }
  return false;
} 


//透传模式下发送字符串数据
void ESP8266_STA::SendData(const char *str) 
{
  this->_espSerial->print(str);
} 


//透传模式下发整形数据
void ESP8266_STA::SendData(int data) 
{
  this->_espSerial->print(data);
}


//透传模式下发送十六进制数据
void ESP8266_STA::SendData(const uint8_t data[], uint16_t len)
{
  for(int i = 0; i < len; i++)
  {
    this->_espSerial->write(data[i]);
  }
} 


//复位ESP8266、判断是否已经连接上wifi
bool ESP8266_STA::Reset(void)   
{
  uint16_t timeOut = 500;
  bool flag = false;
  // this->_espBuf->Clear(); 
  this->_debugSerial->println("Reset...");
  OLED_ShowString(0,8,"Reset...             ",8); 
  OLED_Refresh();

  // 硬件复位
  // digitalWrite(RST_Pin, LOW);
  // delay(1100);
  // digitalWrite(RST_Pin, HIGH);  

  // //软件复位
  this->_espSerial->print("AT+RST\r\n");

  while(timeOut--)
  {
    if(this->ReadESP() == true && strstr(this->_espBuf->GetString(),"ready") != NULL)
    {
      this->_debugSerial->println("Reset Succeed!");
      OLED_ShowString(0,16,"Reset Succeed!       ",8); 
      OLED_Refresh();
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();
      flag = true;
      break;
    }
    delay(10);
  }

  timeOut = 1000;   //秒
  while(timeOut--)
  {
    if(this->_espSerial->available())
    {
      this->_espBuf->AddByte(this->_espSerial->read());
      if(strstr(this->_espBuf->GetString(),"GOT IP") != NULL)
      {
        this->stateFlag = 1;
        this->_debugSerial->println("WLAN Connect Succeed!");
        OLED_ShowString(0,16,"WLAN Connect Succeed!",8); 
        OLED_Refresh();
        this->_espBuf->ResetFlag();
        this->_espBuf->Clear();
        break;        
      }
    }
    delay(10);
  }

  if(flag == false)
  {
    // this->stateFlag = 0;
    this->_debugSerial->println("Reset Failed!");
    OLED_ShowString(0,16,"Reset Failed!        ",8); 
    OLED_Refresh();
  }

  return flag;
}


//恢复出厂设置
bool ESP8266_STA::Restore(void)
{

}


//握手并关闭回传
bool ESP8266_STA::Hand(void) 
{
  uint8_t timeOut = 10;   //尝试10次
  bool flag = false;
    
  this->_debugSerial->println("AT...");  
  OLED_ShowString(0,8,"AT...                ",8); 
  OLED_Refresh();
  while(timeOut--)
  {
    if(this->SendCmd("AT\r\n", "OK") == true)
    {
      this->_debugSerial->println("AT OK");
      OLED_ShowString(0,16,"AT OK                ",8); 
      OLED_Refresh();      
      flag = true;
      break;
    }
  }

  timeOut = 10;
  this->_debugSerial->println("ATE0...");  
  OLED_ShowString(0,8,"ATE0...              ",8); 
  OLED_Refresh();      
  while(timeOut-- && flag == true)
  {
    if(this->SendCmd("ATE0\r\n", "OK") == true)
    {
      this->_debugSerial->println("ATE0 OK");
      this->_debugSerial->println("Handshake Succeed!");
      OLED_ShowString(0,16,"Handshake Succeed!   ",8); 
      OLED_Refresh();
      return true;      
    }
  }

  this->_debugSerial->println("Handshake Failed!");
  OLED_ShowString(0,16,"Handshake Failed!    ",8); 
  OLED_Refresh();
  return false;
}


//设置工作模式为STA模式
bool ESP8266_STA::SetMode(void)   
{
  uint8_t timeOut = 10;   //只尝试10次
    
  this->_debugSerial->println("Set Mode...");
  OLED_ShowString(0,8,"Set Mode...          ",8); 
  OLED_Refresh();
  while(timeOut-- )
  {
    if(this->SendCmd("AT+CWMODE_DEF=1\r\n", "OK") == true)
    {
      this->_debugSerial->println("Set Mode Succeed!");
      OLED_ShowString(0,16,"Set Mode Succeed!    ",8); 
      OLED_Refresh();
      return true;      
    }
  }

  this->_debugSerial->println("Set Mode Failed!");
  OLED_ShowString(0,16,"Set Mode Failed!     ",8); 
  OLED_Refresh();
  return false;
}


//设置WiFi并保存
bool ESP8266_STA::WLANConnect(void)
{
  uint16_t timeOut = 1000;      //等待10秒
  char temp[50];
  strcpy(temp, "AT+CWJAP_DEF=\"");
  strcat(temp, this->_idSave.id);
  strcat(temp, "\",\"");
  strcat(temp, this->_idSave.pwd);
  strcat(temp,"\"\r\n");

  this->_debugSerial->println("WLAN Connect...");
  OLED_ShowString(0,8,"WLAN Connect...      ",8); 
  OLED_Refresh();
  this->_espSerial->print(temp);
  while(timeOut--)
  {
    if(this->ReadESP() == true && strstr(this->_espBuf->GetString(),"GOT IP") != NULL)
    {
      this->stateFlag = 1;      
      this->_debugSerial->println("WLAN Connect Succeed!");
      OLED_ShowString(0,16,"WLAN Connect Succeed!",8); 
      OLED_Refresh();
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();
      return true;
    }
    delay(10);
  }

  this->stateFlag = 0;
  this->_debugSerial->println("WLAN Connect Failed!");
  OLED_ShowString(0,16,"WLAN Connect Failed! ",8); 
  OLED_Refresh();
  return false;
}


//建立TCP连接
bool ESP8266_STA::TCPConnect(void)  
{
  uint16_t timeOut = 1000;      //等待10秒
  char temp[50];
  strcpy(temp, "AT+CIPSTART=\"TCP\",\"");
  strcat(temp, this->_idSave.ip);
  strcat(temp, "\",");
  strcat(temp, this->_idSave.port);
  strcat(temp,"\r\n");

  this->_debugSerial->println("TCP Connect...");
  OLED_ShowString(0,8,"TCP Connect...       ",8); 
  OLED_Refresh();
  this->_espSerial->print(temp);  
  while(timeOut-- )
  {
    if(this->ReadESP() == true)
    {
      if(strstr(this->_espBuf->GetString(),"OK") != NULL)
      {
        this->stateFlag = 2;      
        this->_debugSerial->println("TCP Connect Succeed!");
        OLED_ShowString(0,16,"TCP Connect Succeed! ",8); 
        OLED_Refresh();
        this->_espBuf->ResetFlag();
        this->_espBuf->Clear();
        return true;      
      }
      else if(strstr(this->_espBuf->GetString(),"no ip") != NULL)
      {
        this->stateFlag = 0;      
        this->_debugSerial->println("WLAN is disconnected thus TCP cannot connect!");        
        OLED_ShowString(0,16,"WLAN is disconnected ",8);  
        OLED_Refresh();
        this->_espBuf->ResetFlag();
        this->_espBuf->Clear();
        return false;      
      }
    }
    delay(10);
  }

  this->stateFlag = 1;
  this->_debugSerial->println("TCP Connect Failed!");
  OLED_ShowString(0,16,"TCP Connect Failed!  ",8);  
  OLED_Refresh();
  return false;
}  


//开启透传模式
bool ESP8266_STA::TransparentON(void) 
{
  uint8_t timeOut = 10;   //只尝试10次
  uint8_t timeOut2;
  // uint8_t temp;
  bool flag = false;
    
  this->_debugSerial->println("Enabling the transparent transmission mode...");     
  this->_debugSerial->println("AT+CIPMODE=1...");  
  OLED_ShowString(0,8,"AT+CIPMODE=1...      ",8);  
  OLED_Refresh();
  while(timeOut--)
  {
    if(this->SendCmd("AT+CIPMODE=1\r\n", "OK") == true)
    {
      this->_debugSerial->println("AT+CIPMODE=1 OK");
      OLED_ShowString(0,16,"AT+CIPMODE=1 OK      ",8);  
      OLED_Refresh();
      flag = true;
      break;
    }
  }

  timeOut = 10;
  this->_debugSerial->println("AT+CIPSEND...");
  OLED_ShowString(0,8,"AT+CIPSEND...        ",8); 
  OLED_Refresh();
  while(timeOut-- && flag == true)
  {
    this->_espSerial->print("AT+CIPSEND\r\n");
    timeOut2 = 100;
    while(timeOut2--)
    {
      if(this->_espSerial->available() && this->_espSerial->read() == '>')
      {
        this->stateFlag = 3;
        this->_debugSerial->println("The transparent transmission mode is enabled!");
        OLED_ShowString(0,16,"Transmission enabled!",8);  
        OLED_Refresh();
        this->_espBuf->ResetFlag();
        this->_espBuf->Clear();
        return true;        
      }
      delay(10);
    }
  }
  
  this->stateFlag = 1;
  this->_debugSerial->println("Failed to enable the transparent transmission mode!");
  OLED_ShowString(0,16,"Transmission failed! ",8);  
  OLED_Refresh();
  return false;
}   


//关闭透传模式
bool ESP8266_STA::TransparentOFF(void)  
{
  uint8_t timeOut = 10;   //只尝试10次
  this->_debugSerial->println("Exit the transparent transmission mode...");
  OLED_ShowString(0,8,"Exit transmission... ",8);  
  OLED_Refresh();
  
  delay(1100);

  this->_espSerial->write("+++");

  delay(1100);

  while(timeOut--)
  {
    if(this->SendCmd("AT\r\n", "OK") == true)
    {
      this->stateFlag = 255;   //暂时写255   
      this->_debugSerial->println("AT OK");
      this->_debugSerial->println("Succeed to exit!");    
      OLED_ShowString(0,16,"Succeed to exit!     ",8);  
      OLED_Refresh();
      return true;      
    }
  }

  this->stateFlag = 3;
  this->_debugSerial->println("Failed to exit!");
  OLED_ShowString(0,16,"Failed to exit!      ",8);  
  OLED_Refresh();
  return false;
} 


//监测运行状态  
void ESP8266_STA::ESPLoop(CD4051_Manager *cd)  
{
  char ch = 'a';
  char *temp = NULL;

  switch (this->stateFlag)
  {
    case 0:
      this->WLANConnect();
      break;
    case 1:
      this->TCPConnect();
      break;
    case 2:
      this->TransparentON();
      break;
    case 3:
      cd->Loop();
      break;      
    default:
      break;
  }

  if(this->ReadESP() == true)
  {
    temp = strstr(this->_espBuf->GetString(),"freq");
    if(temp != NULL)
    {
      temp += 5;
      cd->setFreq(atoi(temp));
      this->_debugSerial->print("Now the frequency is:");
      this->_debugSerial->print(atoi(temp));
      this->_debugSerial->println("Hz");      
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();
      return;
    }

    //透传模式下停止或继续发送数据
    else if(strstr(this->_espBuf->GetString(),"hold") != NULL)
    {
      if(this->stateFlag == 3)
      {
        this->stateFlag = 253;
        this->_debugSerial->println("hold on...");
        OLED_ShowString(0,16,"hold on...           ",8);  
        OLED_Refresh();
      }
      else if(this->stateFlag == 253)
      {
        this->stateFlag = 3;
        this->_debugSerial->println("Continue data transmission!");        
        OLED_ShowString(0,16,"Continue transmission",8);  
        OLED_Refresh();
      }
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();
      return;
    }

    else if(strstr(this->_espBuf->GetString(),"CLOSED") != NULL)
    {
      // this->TransparentOFF();    
      // this->stateFlag = 255;      //说明客户端关闭了
      this->_debugSerial->println("TCP disconnected");
      OLED_ShowString(0,16,"TCP disconnected     ",8);  
      OLED_Refresh();
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();  
    }

    else if(strstr(this->_espBuf->GetString(),"WIFI DISCONNECT") != NULL)
    {
      this->TransparentOFF();
      this->stateFlag = 0;      //说明断开了WiFi连接
      this->_debugSerial->println("WLAN disconnected");
      OLED_ShowString(0,16,"WLAN disconnected    ",8);  
      OLED_Refresh();
      this->_espBuf->ResetFlag();
      this->_espBuf->Clear();  
    }
  }
}


//查询是否有Debug指令  
void ESP8266_STA::DebugLoop(CD4051_Manager *cd)  
{
  char ch = 'a';
  char *temp = NULL;

  if(this->ReadDebug() == true)
  {
    temp = strstr(this->_debugBuf->GetString(),"set");
    if(temp != NULL)
    {
      temp += 5;
      ch = *temp;
      temp = strstr(this->_debugBuf->GetString(),"=");
      if(temp != NULL)
      {
        temp ++;
        switch(ch)
        {
          case 'd':
            strcpy(this->_idSave.id, temp);
            this->_debugSerial->print("Now the id is:");
            this->_debugSerial->println(this->_idSave.id);
            break;
          case 'w':
            strcpy(this->_idSave.pwd, temp);
            this->_debugSerial->print("Now the pwd is:");
            this->_debugSerial->println(this->_idSave.pwd);
            break;
          case 'p':
            strcpy(this->_idSave.ip, temp);
            this->_debugSerial->print("Now the ip is:");
            this->_debugSerial->println(this->_idSave.ip);
            break;
          case 'o':
            strcpy(this->_idSave.port, temp);
            this->_debugSerial->print("Now the port is:");
            this->_debugSerial->println(this->_idSave.port);
            break;
          case 'r':
            cd->setFreq(atoi(temp));
            this->_debugSerial->print("Now the frequency is:");
            this->_debugSerial->print(atoi(temp));
            this->_debugSerial->println("Hz");
            break;            
          default:
            break;        
        }
      }
      this->_debugBuf->ResetFlag();
      this->_debugBuf->Clear();        
      return;      
    }

    else if(strstr(this->_debugBuf->GetString(),"save") != NULL)
    {
      // this->_flash.deletePrefs();          // 删除valid records
      this->_flash.garbageCollection();    //删除 dirty
      this->_flash.writePrefs(&this->_idSave, sizeof(this->_idSave));
      int rc = this->_flash.readPrefs(&this->_idSave, sizeof(this->_idSave));
      this->_debugSerial->println(this->_flash.errorString(rc));
      this->_debugBuf->ResetFlag();
      this->_debugBuf->Clear();
      return;
    }

    else if(strstr(this->_debugBuf->GetString(),"go ahead") != NULL)
    {
      this->TransparentOFF();
      this->stateFlag = 0;
      this->_debugBuf->ResetFlag();
      this->_debugBuf->Clear();
      return;
    }

    //退出或开启透传
    else if(strstr(this->_debugBuf->GetString(),"quit") != NULL)
    {
      if(this->stateFlag == 3)
      {
        this->TransparentOFF();
        this->stateFlag = 254;
        this->_debugSerial->println("Quit transparent and keep silence...");
      }
      else if(this->stateFlag == 254)
      {
        this->stateFlag = 2;   
        this->_debugSerial->println("Enabling transparent...");
      }

      this->_debugBuf->ResetFlag();
      this->_debugBuf->Clear();
      return;
    }

    //透传模式下停止或继续发送数据
    else if(strstr(this->_debugBuf->GetString(),"hold") != NULL)
    {
      if(this->stateFlag == 3)
      {
        this->stateFlag = 253;
        this->_debugSerial->println("hold on...");
      }
      else if(this->stateFlag == 253)
      {
        this->stateFlag = 3;
        this->_debugSerial->println("Continue data transmission!");        
      }

      this->_debugBuf->ResetFlag();
      this->_debugBuf->Clear();
      return;
    }

    //停止连接WiFi或者TCP
    else if(strstr(this->_debugBuf->GetString(),"stop") != NULL)
    {
      if(this->stateFlag == 0 ||this->stateFlag == 1)
      {
        this->stateFlag = 252;
        this->_debugSerial->println("stop...");
      }

      this->_debugBuf->ResetFlag();
      this->_debugBuf->Clear();
      return;
    }

    this->_debugSerial->println("Your input is incorrect!");
    this->_debugSerial->println("Please input \"set id/pwd/ip/port=xxx\", \"go ahead\", \"quit\" or \"hold\"");
    this->_debugBuf->ResetFlag();
    this->_debugBuf->Clear();
  }
}


//读取ESP8266串口数据
bool ESP8266_STA::ReadESP(void)    
{
  static uint8_t state = 0;   //状态机变量
  uint8_t temp;               //暂存数据
  while(this->_espSerial->available()) 
  {
    temp = this->_espSerial->read();
    if(state == 0)
    { 
      // if(temp != '\r' && this->_espBuf->GetFlag() == false)
      if(temp == '\r')
      {
        state = 1;
      }
      else
      {
        this->_espBuf->AddByte(temp); //存入数据        
      }
    }
    else if(state == 1)
    {
      if(temp == '\n')  //收到包尾"\r\n"，该位不用存
      {
        state = 0;      //状态变量清零
        this->_espBuf->SetFlag();   //接收数据标志位置1
      }
    }
  }
  return this->_espBuf->GetFlag();
} 


//读取debug串口数据
bool ESP8266_STA::ReadDebug(void)   
{
  static uint8_t state = 0;   //状态机变量
  uint8_t temp;               //暂存数据
  while(this->_debugSerial->available()) 
  {
    temp = this->_debugSerial->read();
    if(state == 0)
    { 
      // if(temp != '\r' && this->_debugBuf->GetFlag() == false)
      if(temp == '\r')
      {
        state = 1;
      }
      else
      {
        this->_debugBuf->AddByte(temp); //存入数据        
      }
    }
    else if(state == 1)
    {
      if(temp == '\n')  //收到包尾"\r\n"，该位不用存
      {
        state = 0;      //状态变量清零
        this->_debugBuf->SetFlag();   //接收数据标志位置1
      }      
    }
  }
  return this->_debugBuf->GetFlag();
}


//回传ESP8266串口收到的数据
void ESP8266_STA::ESPPassBack(void)
{
  if(this->ReadESP() == true)
  {
    this->_espSerial->print(this->_espBuf->GetString());
    this->_espBuf->ResetFlag();
    this->_espBuf->Clear();
  }
  // this->ReadESP();
}


//回传调试串口收到的数据
void ESP8266_STA::DebugPassBack(void)
{
  if(this->ReadDebug() == true)
  {
    this->_debugSerial->print(this->_debugBuf->GetString());
    this->_debugBuf->ResetFlag();
    this->_debugBuf->Clear();
  }
  // this->ReadDebug();
}        


ESP8266_STA::~ESP8266_STA()
{
  this->_espSerial = NULL;
  this->_espBuf = NULL;
  this->_debugSerial = NULL;
  this->_debugBuf = NULL;
}

