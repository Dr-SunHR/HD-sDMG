#include "OLED091.h"
#include "OLED091_Font.h"

/*引脚配置（先将GPIOx全部替换为目标端口）*/
#define SCL_Pin D10	//SCL
#define SDA_Pin D6	//SDA

#define OLED_W_SCL(x)		digitalWrite(SCL_Pin, (PinStatus)(x))
#define OLED_W_SDA(x)		digitalWrite(SDA_Pin, (PinStatus)(x))

uint8_t OLED_GRAM[144][8];

/*---------------------------------------------I2C配置---------------------------------------------*/
/**
  * @brief  引脚初始化
  * @param  无
  * @retval 无
  */
void OLED_I2C_Init(void)
{
  pinMode(SCL_Pin, OUTPUT);
  pinMode(SDA_Pin, OUTPUT);

 	digitalWrite(SCL_Pin, HIGH);
 	digitalWrite(SDA_Pin, HIGH);
}

/**
  * @brief  I2C开始
  * @param  无
  * @retval 无
  */
void OLED_I2C_Start(void)
{
	OLED_W_SDA(1);
	OLED_W_SCL(1);
	// delayMicroseconds(2);
	OLED_W_SDA(0);
	// delayMicroseconds(2);
	OLED_W_SCL(0);
	// delayMicroseconds(2);
}

/**
  * @brief  I2C停止
  * @param  无
  * @retval 无
  */
void OLED_I2C_Stop(void)
{
	OLED_W_SDA(0);
	OLED_W_SCL(1);
	// delayMicroseconds(2);
	OLED_W_SDA(1);
}

/**
  * @brief  I2C等待信号响应
  * @param  无
  * @retval 无
  */
void OLED_I2C_WaitAck(void) //测数据信号的电平
{
	OLED_W_SDA(1);
	// delayMicroseconds(2);
	OLED_W_SCL(1);
	// delayMicroseconds(2);
	OLED_W_SCL(0);
	// delayMicroseconds(2);
}

/**
  * @brief  I2C写入一个字节
  * @param  Byte 要写入的一个字节
  * @retval 无
  */
void OLED_I2C_SendByte(uint8_t Byte)
{
	uint8_t i;
	for (i = 0; i < 8; i ++)
	{
		OLED_W_SDA(Byte & (0x80 >> i));	//按位与，取出相应位（0x80 == 1000 0000）
		OLED_W_SCL(1);
    // delayMicroseconds(2);
		OLED_W_SCL(0);	//数据放在SDA后，释放再拉低SCL，完成一次发送
    // delayMicroseconds(2);
	}
}


/*---------------------------------------------OLED函数---------------------------------------------*/
/**
  * @brief  OLED写入命令
  * @param  Cmd 要写入的命令
  * @retval 无
  */
void OLED_WR_Cmd(uint8_t Cmd)
{
	OLED_I2C_Start();
	OLED_I2C_SendByte(0x78);//从机地址
	OLED_I2C_WaitAck();
	OLED_I2C_SendByte(0x00);//写命令
	OLED_I2C_WaitAck();
	OLED_I2C_SendByte(Cmd);
	OLED_I2C_WaitAck();
	OLED_I2C_Stop();
}

/**
  * @brief  OLED写入数据
  * @param  dat 要写入的数据
  * @retval 无
  */
void OLED_WR_Data(uint8_t dat)
{
	OLED_I2C_Start();
	OLED_I2C_SendByte(0x78);//从机地址
	OLED_I2C_WaitAck();
	OLED_I2C_SendByte(0x40);//写数据
	OLED_I2C_WaitAck();
	OLED_I2C_SendByte(dat);
	OLED_I2C_WaitAck();
	OLED_I2C_Stop();
}

/**
  * @brief  更新显存到OLED	
  * @param  无
  * @retval 无
  */
void OLED_Refresh(void)
{
	uint8_t i,n;
	for(i=0;i<8;i++)
	{
		OLED_WR_Cmd(0xb0+i); //设置行起始地址
		OLED_WR_Cmd(0x00);   //设置低列起始地址
		OLED_WR_Cmd(0x10);   //设置高列起始地址
		OLED_I2C_Start();
		OLED_I2C_SendByte(0x78);
		OLED_I2C_WaitAck();
		OLED_I2C_SendByte(0x40);
		OLED_I2C_WaitAck();
		for(n=0;n<128;n++)
		{
			OLED_I2C_SendByte(OLED_GRAM[n][i]);
			OLED_I2C_WaitAck();
		}
		OLED_I2C_Stop();
  }
}

/**
  * @brief  OLED清屏
  * @param  无
  * @retval 无
  */
void OLED_Clear(void)
{
	uint8_t i,n;
	for(i=0;i<8;i++)
	{
	   for(n=0;n<128;n++)
		{
			OLED_GRAM[n][i]=0;//清除所有数据
		}
	}
	OLED_Refresh();//更新显示
}

/**
  * @brief  OLED画点
  * @param  x:0~127
  * @param  y:0~63
  * @param  mode:1 填充 0,清空
  * @retval 无
  */
void OLED_DrawPoint(uint8_t x,uint8_t y,uint8_t mode)
{
	uint8_t i,m,n;
	i=y/8;
	m=y%8;
	n=1<<m;
	if(mode){OLED_GRAM[x][i]|=n;}
	else
	{
		OLED_GRAM[x][i]=~OLED_GRAM[x][i];
		OLED_GRAM[x][i]|=n;
		OLED_GRAM[x][i]=~OLED_GRAM[x][i];
	}
}

/**
  * @brief  OLED显示一个字符
  * @param  x:0~127，y:0~63
  * @param  chr:字符
  * @param  Size:选择字体 6x8/6x12/8x16/12x24
  * @retval 无
  */
void OLED_ShowChar(uint8_t x,uint8_t y,uint8_t chr,uint8_t Size)
{
	uint8_t i,m,temp,Size1,chr1;
	uint8_t x0=x,y0=y;
	if(Size==8)Size1=6;
	else Size1=(Size/8+((Size%8)?1:0))*(Size/2);  //得到字体一个字符对应点阵集所占的字节数
	chr1=chr-' ';  //计算偏移后的值
	for(i=0;i<Size1;i++)
	{
		if(Size==8)
				{temp=OLED_F6x8[chr1][i];} //调用0806字体
		// else if(Size==12)
		// 		{temp=OLED_F6x12[chr1][i];} //调用1206字体
		// else if(Size==16)
		// 		{temp=OLED_F8x16[chr1][i];} //调用1608字体
		// else if(Size==24)
		// 		{temp=OLED_F12x24[chr1][i];} //调用2412字体
		else return;
		for(m=0;m<8;m++)
		{
			if(temp&0x01)OLED_DrawPoint(x,y,1);
			else OLED_DrawPoint(x,y,0);			
			temp>>=1;
			y++;
		}
		x++;
		if((Size!=8)&&((x-x0)==Size/2))
		{x=x0;y0=y0+8;}
		y=y0;
  }
}

/**
  * @brief  OLED显示字符串
  * @param  x:0~127，y:0~63,起点坐标
  * @param  chr:字符串
  * @param  Size:选择字体 6x8/6x12/8x16/12x24
  * @retval 无
  */
void OLED_ShowString(uint8_t x,uint8_t y,char *chr,uint8_t Size)
{
	while((*chr>=' ')&&(*chr<='~'))//判断是不是非法字符
	{
		OLED_ShowChar(x,y,*chr,Size);
		if(Size==8)x+=6;
		else x+=Size/2;
		chr++;
  }
}

/**
  * @brief  OLED次方函数
  * @retval 返回值等于m的n次方
  */
uint32_t OLED_Pow(uint8_t m,uint8_t n)
{
	uint32_t result=1;
	while(n--)
	{
	  result*=m;
	}
	return result;
}

/**
  * @brief  OLED显示数字（十进制正数）
  * @param  x:0~127，y:0~63,起点坐标
  * @param  num :要显示的数字，范围：0~4294967295
  * @param  len :数字的位数
  * @param  Size:字体大小
  * @retval 无
  */
void OLED_ShowNum(uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t Size)
{
	uint8_t t,temp,m=0;
	if(Size==8)m=2;
	for(t=0;t<len;t++)
	{
		temp=(num/OLED_Pow(10,len-t-1))%10;
		OLED_ShowChar(x+(Size/2+m)*t,y,temp+'0',Size);
	}
}

/**
  * @brief  OLED显示数字（十进制，带符号）
  * @param  x:0~127，y:0~63,起点坐标
  * @param  num :要显示的数字，范围：-2147483648~2147483647
  * @param  len :数字的位数
  * @param  Size:字体大小
  * @retval 无
  */
// void OLED_ShowSignedNum(uint8_t x,uint8_t y,int32_t num,uint8_t len,uint8_t Size)
// {
// 	uint8_t t,temp,m=0;
// 	uint32_t num1;
// 	if(Size==8)m=2;
// 	if(num>=0)
// 	{
// 		OLED_ShowChar(x,y,'+',Size);
// 		num1=num;
// 	}
// 	else
// 	{
// 		OLED_ShowChar(x,y,'-',Size);
// 		num1=-num;
// 	}
// 	for(t=0;t<len;t++)
// 	{
// 		temp=(num1/OLED_Pow(10,len-t-1))%10;
// 		OLED_ShowChar(x+(Size/2+m)*t+(Size/2),y,temp+'0',Size);
// 	}
// }

/**
  * @brief  OLED显示数字（十六进制，正数）
  * @param  x:0~127，y:0~63,起点坐标
  * @param  num :要显示的数字，范围：0~0xFFFFFFFF
  * @param  len :数字的位数
  * @param  Size:字体大小
  * @retval 无
  */
// void OLED_ShowHexNum(uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t Size)
// {
// 	uint8_t t,temp,m=0;
// 	if(Size==8)m=2;
// 	for(t=0;t<len;t++)
// 	{
// 		temp=(num/OLED_Pow(16,len-t-1))%16;
// 		if(temp<10)	OLED_ShowChar(x+(Size/2+m)*t,y,temp+'0',Size);
// 		else			OLED_ShowChar(x+(Size/2+m)*t,y,temp-10+'A',Size);
// 	}
// }

/**
  * @brief  OLED显示数字（二进制正数）
  * @param  x:0~127，y:0~63,起点坐标
  * @param  num :要显示的数字，范围：0~1111 1111 1111 1111，C语言不支持直接写二进制数，所以要用十六进制代替
  * @param  len :数字的位数
  * @param  Size:字体大小
  * @retval 无
  */
// void OLED_ShowBinNum(uint8_t x,uint8_t y,uint32_t num,uint8_t len,uint8_t Size)
// {
// 	uint8_t t,temp,m=0;
// 	if(Size==8)m=2;
// 	for(t=0;t<len;t++)
// 	{
// 		temp=(num/OLED_Pow(2,len-t-1))%2;
// 		OLED_ShowChar(x+(Size/2+m)*t,y,temp+'0',Size);
// 	}
// }

/**
  * @brief  OLED显示汉字
  * @param  x:0~127，y:0~63,起点坐标
  * @param  num :汉字对应的序号
  * @param  Size:字体大小,16、24、32、64
  * @retval 无
  */
// void OLED_ShowChinese(uint8_t x,uint8_t y,uint8_t num,uint8_t Size)
// {
// 	uint8_t m,temp;
// 	uint8_t x0=x,y0=y;
// 	uint16_t i,Size3=(Size/8+((Size%8)?1:0))*Size;  //得到字体一个字符对应点阵集所占的字节数
// 	for(i=0;i<Size3;i++)
// 	{
// 		if(Size==16)
// 				{temp=Chara1[num][i];}//调用16*16字体
// 		else if(Size==24)
// 				{temp=Chara2[num][i];}//调用24*24字体
// 		else if(Size==32)       
// 				{temp=Chara3[num][i];}//调用32*32字体
// 		// else if(Size==64)
// 		// 		{temp=Chara4[num][i];}//调用64*64字体
// 		else return;
// 		for(m=0;m<8;m++)
// 		{
// 			if(temp&0x01)OLED_DrawPoint(x,y,1);
// 			else OLED_DrawPoint(x,y,0);
// 			temp>>=1;
// 			y++;
// 		}
// 		x++;
// 		if((x-x0)==Size)
// 		{x=x0;y0=y0+8;}
// 		y=y0;
// 	}
// }


/**
  * @brief  OLED显示BMP图片
  * @param  x:0~127，y:0~63,起点坐标
  * @param  Sizex,Sizey,图片长宽
  * @param  BMP：要写入的图片数组
  * @retval 无
  */
// void OLED_ShowPicture(uint8_t x,uint8_t y,uint8_t Sizex,uint8_t Sizey,const uint8_t *BMP)
// {
// 	uint16_t j=0;
// 	uint8_t i,n,temp,m;
// 	uint8_t x0=x,y0=y;
// 	Sizey=Sizey/8+((Sizey%8)?1:0);
// 	for(n=0;n<Sizey;n++)
// 	{
// 		 for(i=0;i<Sizex;i++)
// 		 {
// 				temp=BMP[j];
// 				j++;
// 				for(m=0;m<8;m++)
// 				{
// 					if(temp&0x01)OLED_DrawPoint(x,y,1);
// 					else OLED_DrawPoint(x,y,0);
// 					temp>>=1;
// 					y++;
// 				}
// 				x++;
// 				if((x-x0)==Sizex)
// 				{
// 					x=x0;
// 					y0=y0+8;
// 				}
// 				y=y0;
// 		}
// 	 }
// }

/**
  * @brief  OLED初始化
  * @param  无
  * @retval 无
  */
void OLED_Init(void)
{
	// uint32_t i, j;
	// for(i=0;i<1000;i++)	//上电延时
	// {
	// 	for(j=0;j<1000;j++);
	// }	
	OLED_I2C_Init();//端口初始化

	OLED_WR_Cmd (0xAE);//关闭显示

	OLED_WR_Cmd(0x40);//---set low column address
	OLED_WR_Cmd(0xB0);//---set high column address

	OLED_WR_Cmd(0xC8);//-not offset

	OLED_WR_Cmd(0x81);//设置对比度
	OLED_WR_Cmd(0xff);

	OLED_WR_Cmd(0xa1);//段重定向设置

	OLED_WR_Cmd(0xa6);

	OLED_WR_Cmd(0xa8);//设置驱动路数
	OLED_WR_Cmd(0x1f);

	OLED_WR_Cmd(0xd3);
	OLED_WR_Cmd(0x00);

	OLED_WR_Cmd(0xd5);
	OLED_WR_Cmd(0xf0);

	OLED_WR_Cmd(0xd9);
	OLED_WR_Cmd(0x22);

	OLED_WR_Cmd(0xda);
	OLED_WR_Cmd(0x02);

	OLED_WR_Cmd(0xdb);
	OLED_WR_Cmd(0x49);

	OLED_WR_Cmd(0x8d);
	OLED_WR_Cmd(0x14);

	OLED_WR_Cmd(0xaf);
	OLED_Clear();
}

