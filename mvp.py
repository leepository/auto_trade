import json
import os
import pyupbit

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def trade_mvp():
    #1. 업비트 차트 데이터 가져오기 (30일 일봉 데이터)
    df = pyupbit.get_ohlcv("KRW-ETH", count=30, interval="day")

    #2. AI에게 데이터를 제공하고 판단 받기
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages = [
            {
                "role": "system",
                 "content": [
                     {
                         "type": "text",
                         "text": """
                            You are an expert in Bitcoin investing. 
                            Tell me whether to buy, sell, or hole at the moment based on the chart data provided. 
                            Response is json format.
                            
                            Response Example:
                            {"decision": "buy", "reason": "some technical reason"}
                            {"decision": "sell", "reason": "some technical reason"}
                            {"decision": "hold", "reason": "some techinal reason"}
                         """
                     }
                 ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": df.to_json()
                    }
                ]
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    ai_decision = response.choices[0].message.content

    # 3. AI의 판단에 따라 실제로 자동매매 진행하기
    upbit_access_key = os.getenv('UPBIT_ACCESS_KEY')
    upbit_secret_key = os.getenv('UPBIT_SECRET_KEY')
    upbit_client = pyupbit.Upbit(upbit_access_key, upbit_secret_key)

    trade_decision = json.loads(ai_decision)

    print(f"### AI Decision : {trade_decision['decision'].upper()} ###")
    print(f"### Reason : {trade_decision['reason']} ###")

    if trade_decision['decision'].upper() == 'BUY':
        print(f"buy : {trade_decision['reason']}")
        my_krw = upbit_client.get_balance("KRW")
        trading_quantity = my_krw * 0.99 # 수수료를 제외한 나머지 금액으로 매수한다.
        if trading_quantity > 5000: # Upbit 매수 최소 금액 5,000원 확인
            # print(upbit_client.buy_market_order("KRW-ETH", upbit_client.get_balance("KRW") * 0.99))
            pass
        else:
            print("[Warning] 매수 최소 금액 미충족 (원화 잔액이 5,000원 이하)")

    elif trade_decision['decision'].upper() == 'SELL':
        print(f"Sell : {trade_decision['reason']}")
        my_eth = upbit_client.get_balance("ETH")
        current_price = pyupbit.get_orderbook(ticker="KRW-ETH")['orderbhook_units'][0]['ask_price'] # 현재 매도 호가 조회
        if my_eth * current_price > 5000:
            # print(upbit_client.sell_market_order("KRW-ETH", upbit_client.get_balance("KRW-ETH")))
            pass
        else:
            print("[Warning] 매도 최소 금액 미충족 (5,000원 미만)")

    elif trade_decision['decision'].upper() == 'HOLD':
        print(f"Hold : {trade_decision['reason']}")


if __name__ == "__main__":
    trade_mvp()
