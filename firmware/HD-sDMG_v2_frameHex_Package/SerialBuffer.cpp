#include "SerialBuffer.h"


SerialBuffer::SerialBuffer()
{
  this->_buf = new uint8_t[this->_size];
  memset(this->_buf, '\0', this->_size);

  // //debug
  // Serial.print("size:");
  // Serial.print(this->_size); 
  // Serial.print("\n");     
}


SerialBuffer::SerialBuffer(uint16_t size)
{
  this->_size = size;
  this->_buf = new uint8_t[this->_size];
  memset(this->_buf, '\0', this->_size);

  // //debug
  // Serial.print("size:");
  // Serial.print(this->_size); 
  // Serial.print("\n");     
}


//清空缓存
void SerialBuffer::Clear(void)         
{
  memset(this->_buf, '\0', this->_len);
  this->_len = 0;
}


//获取数据包首地址
const uint8_t *SerialBuffer::GetBuf(void)    
{
  return this->_buf;
}


//将数据包返回为字符串
const char *SerialBuffer::GetString(void) 
{
  if(this->_len < this->_size)
    this->_buf[this->_len] = '\0';
  else
    this->_buf[this->_len - 1] = '\0';

  return (char *)this->_buf;
}


//设置索引
void SerialBuffer::SetIndex(uint16_t index)  
{
  if(index < 0)
    return;

  this->_len = index;
}


//按照索引读取数据
uint8_t SerialBuffer::ReadByIndex(uint16_t index)  
{
  if(index < 0)
    return 255;  

    return this->_buf[index];
}


//获取当前索引
uint16_t SerialBuffer::GetIndex(void)            
{
  return this->_len;
}


//存入数据
void SerialBuffer::AddByte(uint8_t data)  
{
  if(this->_len >= this->_size)
    this->_len = 0;

  this->_buf[this->_len++] = data;
}


//修改数据，默认修改当前位置
void SerialBuffer::ModByte(uint8_t data) 
{
  this->_buf[this->_len] = data;
}


//修改数据，指定当前位置
void SerialBuffer::ModByte(uint8_t data, uint16_t index) 
{
  if(index < 0)
    return;

  this->_buf[index] = data;
}


//获取完成标志位
bool SerialBuffer::GetFlag(void)       
{
  return this->_completeFlag;
}


//标志位设置为true
bool SerialBuffer::SetFlag(void)       
{
  this->_completeFlag = true;
  return true;
}


//志位设置为false
bool SerialBuffer::ResetFlag(void)     
{
  this->_completeFlag = false;
  return false;
}


//修改缓存大小
void SerialBuffer::ChangeSize(uint16_t size)    
{
  this->_size = size;  

  delete[] this->_buf;
  this->_buf = new uint8_t[this->_size];

  memset(this->_buf, '\0', this->_size);  
}


SerialBuffer::~SerialBuffer()
{
  delete[] this->_buf;
  this->_buf = NULL;

  // //debug
  // Serial.print("delete!\n");
}

