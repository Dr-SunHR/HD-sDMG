#ifndef __OLED091_H
#define __OLED091_H 

#include <Arduino.h>
// #include "OLED091_BMP.h"

void OLED_Refresh(void);
// void OLED_DrawPoint(uint8_t x,uint8_t y,uint8_t mode);
void OLED_ShowChar(uint8_t x,uint8_t y,uint8_t chr,uint8_t size);
void OLED_ShowString(uint8_t x,uint8_t y,char *chr,uint8_t size);
void OLED_ShowNum(uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t size);
// void OLED_ShowSignedNum(uint8_t x,uint8_t y,int32_t num,uint8_t len,uint8_t Size);
// void OLED_ShowHexNum(uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t Size);
// void OLED_ShowBinNum(uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t Size);
// void OLED_ShowChinese(uint8_t x,uint8_t y,uint8_t num,uint8_t size1);
// void OLED_ShowPicture(uint8_t x,uint8_t y,uint8_t Sizex,uint8_t Sizey,const uint8_t *BMP);
void OLED_Clear(void);
void OLED_Init(void);

#endif

