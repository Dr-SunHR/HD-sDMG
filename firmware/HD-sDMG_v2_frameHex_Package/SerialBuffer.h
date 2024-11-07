#ifndef __SERIALBUFFER_H
#define __SERIALBUFFER_H

#include <Arduino.h>
#include <stdarg.h>
#include <string.h>
#include <stdio.h>

class SerialBuffer
{
private:
  uint8_t *_buf = NULL;        //数据包指针  
  uint16_t _size = 128;       //数据包最大长度，默认128Bytes，<=65535
  uint16_t _len = 0;          //存入的数据长度，<=_size
  bool _completeFlag = false;
public:
  SerialBuffer();
  SerialBuffer(uint16_t size);

  void Clear(void);                     //清空缓存

  const uint8_t *GetBuf(void);          //获取数据包首地址
  const char *GetString(void);          //将数据包返回为字符串

  void SetIndex(uint16_t index);        //设置索引
  uint8_t ReadByIndex(uint16_t index);  //按照索引读取数据
  uint16_t GetIndex(void);              //获取当前索引

  void AddByte(uint8_t data);                 //存入数据
  void ModByte(uint8_t data);                 //修改数据，默认修改当前位置
  void ModByte(uint8_t data, uint16_t index); //修改数据，指定当前位置

  bool GetFlag(void);       //获取完成标志位
  bool SetFlag(void);       //标志位设置为true
  bool ResetFlag(void);     //志位设置为false

  void ChangeSize(uint16_t size);    //修改缓存大小

  ~SerialBuffer();
};




#endif


