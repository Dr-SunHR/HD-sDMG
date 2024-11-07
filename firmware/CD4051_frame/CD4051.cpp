#include "CD4051.h"

#define BUFLENGTH 1   //每一个通道缓存长度，<=255

/*------------------------------class CD4051_Chip------------------------------*/
CD4051_Chip::CD4051_Chip(uint8_t ssPin, uint8_t ioPin, uint8_t lineNum):
_ssPin(ssPin), _ioPin(ioPin), _lineNum(lineNum)
{
  pinMode(this->_ssPin, OUTPUT);
  digitalWrite(this->_ssPin, LOW);      //选中

  if(lineNum > 8)
    lineNum = 8;

  this->_data = new int*[this->_lineNum];       //通道数
  for(uint8_t i = 0; i < this->_lineNum; i++)
  {
    this->_data[i] = new int[BUFLENGTH];        //缓存长度
    memset(this->_data[i], 0, BUFLENGTH * 4);   //int是4字节
  }
}


CD4051_Chip::CD4051_Chip(uint8_t ioPin, uint8_t lineNum):
_ioPin(ioPin), _lineNum(lineNum)
{
  if(lineNum > 8)
    lineNum = 8;

  this->_data = new int*[this->_lineNum];       //通道数
  for(uint8_t i = 0; i < this->_lineNum; i++)
  {
    this->_data[i] = new int[BUFLENGTH];        //缓存长度
    memset(this->_data[i], 0, BUFLENGTH * 4);   //int是4字节
  }
}


uint8_t CD4051_Chip::GetLineNum(void)
{
  return this->_lineNum;
}


//片选
void CD4051_Chip::ChooseChip(bool ch)
{
  if(ch)
    digitalWrite(this->_ssPin, LOW);      //选中
  else
    digitalWrite(this->_ssPin, HIGH);      //不选中
}     


//读取某一通道上的值，编号从1开始
void CD4051_Chip::ReadLine(uint8_t line, uint8_t index)
{
  if(line < 1 || line > this->_lineNum)
    return;

  this->_data[line - 1][index] = analogRead(this->_ioPin);
}


//获取某一通道的数据
int CD4051_Chip::GetData(uint8_t line, uint8_t index)
{
  if(line < 1 || line > this->_lineNum)
    return -1;

  return this->_data[line - 1][index];
}


void CD4051_Chip::debug(void)
{
  for(uint8_t i = 0; i < this->_lineNum; i++)
  {
    for(uint8_t j = 0; j < BUFLENGTH; j++)
    {
      // this->_data[i][j] = i+j;
      Serial.print(this->_data[i][j]);
      Serial.print(" ");
    }
    Serial.print("\r\n");
  }

  // Serial.print("_ssPin = ");
  // Serial.println(this->_ssPin);
  // Serial.print("_ioPin = ");
  // Serial.println(this->_ioPin);
  // Serial.print("_lineNum = ");
  // Serial.println(this->_lineNum);
}


CD4051_Chip::~CD4051_Chip()
{
  for(uint8_t i = 0; i < this->_lineNum; i++)
  {
    delete[] this->_data[i];
    this->_data[i] = NULL;
  }

  delete[] this->_data;
  this->_data = NULL;
}






/*------------------------------class CD4051_Manager------------------------------*/
CD4051_Manager::CD4051_Manager(uint8_t addrAPin, uint8_t addrBPin, uint8_t addrCPin, uint8_t chipNum, CD4051_Chip chip[]):
_addrAPin(addrAPin), _addrBPin(addrBPin), _addrCPin(addrCPin), _chipNum(chipNum), _chip(chip)
{
  uint8_t temp;

  pinMode(this->_addrCPin, OUTPUT);
  pinMode(this->_addrBPin, OUTPUT);
  pinMode(this->_addrAPin, OUTPUT);

  digitalWrite(this->_addrCPin, LOW);   //默认0
  digitalWrite(this->_addrBPin, LOW);   //默认0
  digitalWrite(this->_addrAPin, LOW);   //默认0

  for(uint8_t i = 0; i < this->_chipNum; i++)       //获取通道组数
  {
    temp = this->_chip[i].GetLineNum();
    if(this->_groupNum < temp)
      this->_groupNum = temp;
  }

  this->_index = new uint8_t[this->_groupNum];    //同一个通道组共用一个索引，每一个索引值 0~BUFLENGTH
  memset(this->_index, 0, this->_groupNum);
}


//选中某个通道组
void CD4051_Manager::ChooseLine(uint8_t line)
{
  switch(line)
  {
    case 0:     //000
      digitalWrite(this->_addrCPin, LOW);
      digitalWrite(this->_addrBPin, LOW);
      digitalWrite(this->_addrAPin, LOW);
      break;
    case 1:     //001
      digitalWrite(this->_addrCPin, LOW);
      digitalWrite(this->_addrBPin, LOW);
      digitalWrite(this->_addrAPin, HIGH);
      break;
    case 2:     //010
      digitalWrite(this->_addrCPin, LOW);
      digitalWrite(this->_addrBPin, HIGH);
      digitalWrite(this->_addrAPin, LOW);
      break;
    case 3:     //011
      digitalWrite(this->_addrCPin, LOW);
      digitalWrite(this->_addrBPin, HIGH);
      digitalWrite(this->_addrAPin, HIGH);
      break;
    case 4:     //100
      digitalWrite(this->_addrCPin, HIGH);
      digitalWrite(this->_addrBPin, LOW);
      digitalWrite(this->_addrAPin, LOW);
      break;
    case 5:     //101
      digitalWrite(this->_addrCPin, HIGH);
      digitalWrite(this->_addrBPin, LOW);
      digitalWrite(this->_addrAPin, HIGH);
      break;
    case 6:     //110
      digitalWrite(this->_addrCPin, HIGH);
      digitalWrite(this->_addrBPin, HIGH);
      digitalWrite(this->_addrAPin, LOW);
      break;
    case 7:     //111
      digitalWrite(this->_addrCPin, HIGH);
      digitalWrite(this->_addrBPin, HIGH);
      digitalWrite(this->_addrAPin, HIGH);
      break;
    default:
      break;
  };
  delayMicroseconds(300);
}


//读取某一组通道数据，编号从1开始
void CD4051_Manager::ReadGroup(void)
{
  //选中通道
  this->ChooseLine(this->_group - 1);
  
  //读取每个芯片上的该通道数据
  for(uint8_t i = 0; i < this->_chipNum; i++)
  {
    this->_chip[i].ReadLine(this->_group, this->_index[this->_group - 1]);
  }
  
  //索引值调整
  this->_index[this->_group - 1]++;
  if(this->_index[this->_group - 1] >= BUFLENGTH)
    this->_index[this->_group - 1] = 0;

  this->_group++;
  if(this->_group > this->_groupNum)
    this->_group = 1;
}


//发送某一组通道数据，编号从1开始
void CD4051_Manager::SendGroup(void)
{
  uint8_t group;
  uint8_t index;
  uint8_t offset;
  int temp;

  //读上一组
  if(this->_group <= 1)
    group = this->_groupNum;
  else
    group = this->_group - 1;     

  //读上一个数据
  if(this->_index[group - 1] <= 0)
    index = BUFLENGTH - 1;
  else
    index = this->_index[group - 1] - 1;    

  offset = group;
  for(uint8_t i = 0; i < this->_chipNum; i++)
  {
    temp = this->_chip[i].GetData(group, index);
    if(temp >= 0)
    {
      Serial.print("L");
      Serial.print(offset);
      Serial.print(":");
      Serial.println(temp);
    }
    offset += this->_chip[i].GetLineNum();
  }
}


//读取并发送某一组通道数据，编号从1开始
void CD4051_Manager::Loop(void)
{
  //选中通道
  this->ChooseLine(this->_group - 1);
  
  //读取每个芯片上的该通道数据
  for(uint8_t i = 0; i < this->_chipNum; i++)
  { 
    //读取
    this->_chip[i].ReadLine(this->_group, this->_index[this->_group - 1]);
  }

  //读取完一帧数据（20个通道读完），可以发送数据了
  if(this->_group > this->_groupNum - 1)   
  {
    uint8_t offset = 1;
    uint16_t temp;
    uint8_t lineNum;

    for(uint8_t i = 0; i < this->_chipNum; i++)
    {
      lineNum = this->_chip[i].GetLineNum();
      for(uint8_t j = 1; j <= lineNum; j++)   //group-line
      {
        temp = this->_chip[i].GetData(j, this->_index[j - 1]);
        Serial.print("L");
        Serial.print(offset++);
        Serial.print(":");
        Serial.println(temp);
      }
    }
  }

  //索引值调整
  this->_index[this->_group - 1]++;
  if(this->_index[this->_group - 1] >= BUFLENGTH)
    this->_index[this->_group - 1] = 0;

  this->_group++;
  if(this->_group > this->_groupNum)
    this->_group = 1;
}            


void CD4051_Manager::debug(void)
{
  // Serial.print("_addrAPin = ");
  // Serial.println(this->_addrAPin);
  // Serial.print("_addrBPin = ");
  // Serial.println(this->_addrBPin);
  // Serial.print("_addrCPin = ");
  // Serial.println(this->_addrCPin);
  // Serial.print("_chipNum = ");
  // Serial.println(this->_chipNum);
  // Serial.print("_groupNum = ");
  // Serial.println(this->_groupNum);
  // Serial.print("_group = ");
  // Serial.println(this->_group);

  for(uint8_t i = 0; i < this->_chipNum; i++)
  {
    this->_chip[i].debug();
  }

  Serial.println("index:");
  for(uint8_t j = 0; j < this->_groupNum; j++)
  {
    Serial.print(this->_index[j]);
  }
  Serial.print("\r\n");
}


CD4051_Manager::~CD4051_Manager()
{
  this->_chip = NULL;

  delete[] this->_index;
  this->_index = NULL;
}

