import os
import time
import talib
import numpy as np
from binance.um_futures import UMFutures


'''交易参数'''
key = "AAEeskkUuek3sfrN8UhqkRmbzYymVqcRspHlcGkJXawuk49kiMGqBRurrYY47sNh"
secret = "clAyiHcsQBnNPbnUNEIXsVDo1tp753bCDC0jX99oMRItfUKIjgnO83oxsAnSYRfp"
symbol = 'ETHBUSD'
numFormat = 2
timeFrame = '5m'
bollPeriod = 7
bollMatype = 5
num = 0.005                   # 单次下单张数
maxTradeNum = 2               # 最大下单次数
minTradeAgainTime = 3600      # 最短再次下单间隔,单位为秒
avoidVolatilityTime = 300     # 避免波动的时间期限
avoidVolatilityRatio = 1/1000 # 避免波动的浮动比例

stopProfitRatio = 6/100       #未扛单止盈百分比
stopLossRatio = 6/100         #未扛单止损百分比
stopProfitRatio2 = 3/100      #扛单时止盈百分比
stopLossRatio2 = 3/100        #扛单时止损百分比

'''工具变量'''
side = 0
lastMakeTime = 0
openPrice = 0

# 创建交易所实例
exchange = UMFutures(key=key, secret=secret)

# 初始化函数
def tradeInit():
   print('量化交易开始!') 
   print("进程ID:",os.getpid())
   print("交易对:",symbol)
   print("单次下单张数:",num)
   print("最多下单次数:",maxTradeNum)
   print("再次下单最短间隔:",minTradeAgainTime,'\n')

# 获取布林带数据 bollPeriod
def getBoll():
   while 1:
      try:
         kData = exchange.klines(symbol=symbol,interval=timeFrame, limit=50)
         break
      except:
         print(time.strftime('%m-%d %H:%M:%S',time.localtime()),'获取行情出错！')
         continue
  
   close_price = np.array([float(i[4]) for i in kData])
   result = talib.BBANDS(close_price, bollPeriod, matype = bollMatype)
   return round(result[0][-1],numFormat), round(result[2][-1],numFormat), close_price[-1]

# 判断是否可以下单
def can_make():
   # 超过最大下单量
   if abs(side) >= maxTradeNum:
      return 0
   # 未开仓
   if side == 0:
      return 1
   # 加仓
   if abs(side) > 0 & abs(side) < maxTradeNum:
      if time.time() - lastMakeTime > minTradeAgainTime:
         return 1
   return 0

# 开单
def make(bollUb, bollLb, nowPrice):
   global side
   global lastMakeTime
   global openPrice

   # 做多
   if (nowPrice < bollLb) & (side >= 0) & (can_make() == 1):
      # exchange.createMarketBuyOrder(symbol,num,{
      # 'tdMode':'cross',
      # 'side': "buy",
      # 'posSide': "long",
      # 'ordType':"market",
      # })
      orderId = exchange.new_order_test(symbol=symbol, side='BUY',type='MARKET',positionSide='LONG', quantity=num)['orderId']
      side += 1
      lastMakeTime = time.time()
      openPrice = exchange.get_orders(symbol=symbol,orderId=orderId)['avgPrice']
      print(time.strftime('%m-%d %H:%M:%S',time.localtime()),
      "第",abs(side),"次做多入场！",
      "现价:",nowPrice,
      "开仓价:",openPrice,
      "下轨:",bollLb)
      return
 
   # 做空
   if (nowPrice > bollUb) & (side <= 0) & (can_make() == 1):
      # exchange.createMarketBuyOrder(symbol,num,{
      # 'tdMode':'cross',
      # 'side': "sell",
      # 'posSide': "short",
      # 'ordType':"market",
      # })
      orderId = exchange.new_order_test(symbol=symbol, side='SELL',type='MARKET',positionSide='SHORT', quantity=num)['orderId']
      side -= 1
      lastMakeTime = time.time()
      openPrice = exchange.get_orders(symbol=symbol,orderId=orderId)['avgPrice']
      print(time.strftime('%m-%d %H:%M:%S',time.localtime()),
      "第",abs(side),"次做空入场！",
      "现价:",nowPrice,
      "开仓价:",openPrice,
      "上轨:",bollUb)
      return     
   return

# 止盈止损
def stopProfitOrLoss():
   global maxPrice
   global minPrice
   # 开多情况下
   if side > 0:
      # 未扛单
      if side == 1:
         if (nowPrice >= openPrice * (1 + stopProfitRatio)) | (nowPrice <= openPrice * (1 - stopLossRatio)):
            print(time.strftime('%m-%d %H:%M:%S',time.localtime()),"触发止盈止损")
            return 1
      # 扛单
      else:
         if (nowPrice >= openPrice * (1 + stopProfitRatio2)) | (nowPrice <= openPrice * (1 - stopLossRatio2)):
            print(time.strftime('%m-%d %H:%M:%S',time.localtime()),"扛单时触发止盈止损")
            return 1
   elif side < 0:
      # 未扛单
      if side == -1:
         if (nowPrice <= openPrice * (1 - stopProfitRatio)) | (nowPrice >= openPrice * (1 + stopLossRatio)):
            print(time.strftime('%m-%d %H:%M:%S',time.localtime()),"触发止盈止损")
            return 1
      # 扛单
      else:
         if (nowPrice <= openPrice * (1 - stopProfitRatio2)) | (nowPrice >= openPrice * (1 + stopLossRatio2)):
            print(time.strftime('%m-%d %H:%M:%S',time.localtime()),"扛单时触发止盈止损")
            return 1
   return 0

# 避免微小波动造成平仓
def avoidVolatility():
   if (time.time() - lastMakeTime < avoidVolatilityTime) & (abs(nowPrice - openPrice) < openPrice * avoidVolatilityRatio):
      return 0
   else:
      return 1

# 平仓
def sell(bollUb, bollLb, nowPrice):
   global side
   global openPrice
   # 平多
   if side > 0:
      if ((nowPrice >= bollUb) & avoidVolatility()) | stopProfitOrLoss():
         # exchange.createMarketSellOrder(symbol,abs(side) * num,{
         # 'tdMode':'cross',
         # 'side': "sell",
         # 'posSide': "long",
         # 'ordType':"market",
         # })
         exchange.new_order_test(symbol=symbol, side='SELL',type='MARKET',positionSide='LONG',quantity=abs(side) * num)
         print(time.strftime('%m-%d %H:%M:%S',time.localtime()),
         "平多:", abs(side) * num ,"张",
         "现价:",nowPrice,
         "上轨:",bollUb,
         "\n******************************************************************")
         side = 0
         openPrice = 0
         return

   # 平空
   if side < 0:
      if ((nowPrice <= bollLb) & avoidVolatility()) | stopProfitOrLoss():
         # exchange.createMarketSellOrder(symbol,abs(side) * num,{
         # 'tdMode':'cross',
         # 'side': "buy",
         # 'posSide': "short",
         # 'ordType':"market",
         # })
         exchange.new_order_test(symbol=symbol, side='BUY',type='MARKET',positionSide='SHORT',quantity=abs(side) * num)
         print(time.strftime('%m-%d %H:%M:%S',time.localtime()),
         "平空:", abs(side) * num,"张",
         "现价:",nowPrice,
         "下轨:",bollLb,
         "\n******************************************************************")
         side = 0
         openPrice = 0
         return
   return
   

tradeInit()
while 1:

   bollUb, bollLb, nowPrice = getBoll()
   if side != 0:
      sell(bollUb, bollLb, nowPrice)

   bollUb, bollLb, nowPrice = getBoll()
   if abs(side) < maxTradeNum:
      make(bollUb, bollLb, nowPrice)


