from api import OkexSpot
import time

# mock参数：交易模式，1为实盘，0为模拟盘
# symbol参数：交易对
# leverage参数：杠杆倍数
exchange = OkexSpot(
   mock= 1,
   symbol="SLP-USDT-SWAP",
   leverage = "75",
   access_key="0a67c0e9-ca45-48fd-8914-b847bf4393d8",
   secret_key="9EB6251F0C0776DAF0FE74FE78B54222",
   passphrase="Xyp123456789",
   host=None
)

# 默认交易开关，
switch = 1

# 价格格式，小数点位数
price_format = 5
# 基础张数
num = 1
#交易倍率multiple 
m = 1
# 设置概率决策数组
cha = [0,0,0]
# 存放决策结果：多还是少
choice = 0
#交易次数统计
count = 1


# 设置全仓持仓
exchange.set_position_mode()
# 设置杠杆倍数
exchange.set_leverage(mgnMode="cross")


# 如何开单
def buy(mode=None,sz="0"):
    if mode == 1:
        # 开多
        result, error = exchange.order(tdMode="cross", side="buy", posSide="long", ordType="market", sz=sz)
    else:
        # 开空
        result, error = exchange.order(tdMode="cross", side="sell", posSide="short", ordType="market", sz=sz)
    return result, error

# 如何止盈止损
def stop(pxHigh, tpOrdPx, pxLow, slOrdPx, mode=1, sz="0",):
    if mode == 1:
        # 开多
        result, error = exchange.order_algo(tdMode="cross", side="sell", posSide="long", ordType="oco", sz=sz, tpTriggerPx=pxHigh, tpOrdPx=tpOrdPx, slTriggerPx=pxLow, slOrdPx=slOrdPx)
    else:
        # 平空
        result, error = exchange.order_algo(tdMode="cross", side="buy", posSide="short", ordType="oco", sz=sz, tpTriggerPx=pxLow, tpOrdPx=tpOrdPx, slTriggerPx=pxHigh, slOrdPx=slOrdPx)
    return result, error

# 交易策略
def gray():
    global choice
    print("************** ",count," **************\n")
    k = 0
    for i in cha:
        k += i
    # 做多还是做空
    if k > 1 :
        choice = 1
        print("做多\n")
    else:
        choice = 0
        print("做空\n")
    result, error = buy(mode = choice, sz = str(num * m))
    # 获取订单ID
    ordId = result['data'][0]['ordId']
    # 转入止盈策略
    print("下单成功，转入止盈止损设置策略\n")
    return ordId

# 止盈止损策略
def gray_stop(ordId):
    avgPx = float(exchange.order_info(ordId=ordId)[0]['data'][0]['avgPx'])
    pxHigh = round(avgPx*1.01,price_format)
    pxLow = round(avgPx*0.99,price_format)
    result,error = stop(pxHigh = str(pxHigh), tpOrdPx = "-1", pxLow = str(pxLow), slOrdPx = "-1", mode = choice, sz = str(num * m))
    print("avg:",avgPx,"High:",pxHigh,"Low:",pxLow,"\n")
    return result, error

# 监视
def monitor(algoId):
    global cha
    global count
    global m 
    print("转入监控\n")

    while(1):
        time.sleep(0.1)
        algoData, error = exchange.orders_algo_pending(algoId=algoId)
        print(".", end="")
        if algoData == None:
            actualSide = exchange.orders_algo_history(algoId = algoId)[0]['data'][0]['actualSide']
            if actualSide == 'tp':
                count +=1
                m = 1
                cha.append(choice)
                del(cha[0])
                break
            elif actualSide == 'sl':
                count += 1
                m *= 2
                if choice == 0:
                    cha.append(1)
                else:
                    cha.append(0)
                del(cha[0])
            print("倍率:",m,"\n")
            print("收益情况:",actualSide,"\n")
            print("*********止盈:tp|止损:sl*********\n\n")
            return 0






#############################################
#@循环体
#############################################
while(switch):
    f =open("server.txt","r")
    content = f.read()
    f.close()
    if content == "0":
        break
    # 订单ID
    ordId = gray()
    # 转入设置止盈止损策略
    algoId = gray_stop(ordId)[0]['data'][0]['algoId']
    # 转入监控函数
    monitor(algoId)

# monitor("416495596915286022")



    