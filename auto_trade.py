import json
import os
import pyupbit
import requests

from dotenv import load_dotenv
from openai import OpenAI
from ta.utils import dropna

from capture_chart import run_capture
from indicators import (
    add_indicators,
    get_etherium_news,
    get_fear_and_greed_index
)


load_dotenv()

def ai_trade():

    upbit_access_key = os.getenv('UPBIT_ACCESS_KEY')
    upbit_secret_key = os.getenv('UPBIT_SECRET_KEY')
    upbit_client = pyupbit.Upbit(upbit_access_key, upbit_secret_key)

    ####################################################################################################################
    # 1. 업비트 데이터 가져오기 (30일 일봉 데이터, 24시간 ohlcv 데이터, 오더북, balance)
    ####################################################################################################################

    # Get upbit balance
    all_balances = upbit_client.get_balances()
    # filtered_balances_dict = {balance['currency']:balance for balance in all_balances if balance['currency'] in ['ETH', 'KRW']}
    filtered_balances = [balance for balance in all_balances if balance['currency'] in ['ETH', 'KRW']]

    # Orderbook(현재 호가) 데이터 조회
    order_book = pyupbit.get_orderbook("KRW-ETH")

    # 30일 기준 일봉 데이터 조회
    df_daily = pyupbit.get_ohlcv("KRW-ETH", interval="day", count=30)
    df_daily = dropna(df_daily)
    df_daily = add_indicators(df=df_daily)

    # 1일 기준 시간봉 데이터 조회
    df_hourly = pyupbit.get_ohlcv("KRW-ETH", interval="minute60", count=24)
    df_hourly = dropna(df_hourly)
    df_hourly = add_indicators(df=df_hourly)

    # 공포 탐욕 지수 가져오기
    fear_greed_index = get_fear_and_greed_index()

    # 뉴스 헤드라인 가져오기
    news_headlines = get_etherium_news()

    # 차트 이미지 캡처 후 가져오기
    chart_image, saved_file_path = run_capture()

    ####################################################################################################################
    # 2. AI에게 데이터를 제공하고 판단 받기
    ####################################################################################################################
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages = [
            {
                "role": "system",
                "content": """
                    You are an expert in Bitcoin investing. Analyze the provided data including technical indicators and tell me whether to buy, sell, or hold at the moment. Consider the following indicators in your analysis:
                        - Bollinger Bands (bb_bbm, bb_bbh, bb_bbl)
                        - RSI (rsi)
                        - MACD (macd, macd_signal, macd_diff)
                        - Moving Averages (sma_20, ema_12)
                        
                        Response in json format.   
                        
                        Response Example:
                        {"decision": "BUY", "reason": "some technical reason"}
                        {"decision": "SELL", "reason": "some technical reason"}
                        {"decision": "HOLD", "reason": "some technical reason"}"""
            },
            {
                "role": "user",
                "content":[
                    {
                        "type": "text",
                        "content": f"""
                            Current investment status: {json.dumps(filtered_balances)}
                            Orderbook: {json.dumps(order_book)}
                            Daily OHLCV with indicators (30 days): {df_daily.to_json()}
                            Hourly OHLCV with indicators (24 Hours): {df_hourly.to_json()}
                            Fear and Greed index: {json.dumps(fear_greed_index)}
                            Recent news headlines : {json.dumps(news_headlines)}
                        """
                     },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{chart_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300,
        response_format={
            "type": "json_object"
        }
    )
    ai_decision = response.choices[0].message.content

    ####################################################################################################################
    # 3. AI의 판단에 따라 실제로 자동매매 진행하기
    ####################################################################################################################
    upbit_access_key = os.getenv('UPBIT_ACCESS_KEY')
    upbit_secret_key = os.getenv('UPBIT_SECRET_KEY')
    upbit_client = pyupbit.Upbit(upbit_access_key, upbit_secret_key)

    trade_decision = json.loads(ai_decision)

    print(f"### AI Decision : {trade_decision['decision'].upper()} ###")
    print(f"### Reason : {trade_decision['reason']} ###")

    if trade_decision['decision'].upper() == 'BUY':
        print(f">> Buy order executed")
        my_krw = upbit_client.get_balance("KRW")
        trading_quantity = my_krw * 0.99  # 수수료를 제외한 나머지 금액으로 매수한다.
        if trading_quantity > 5000:  # Upbit 매수 최소 금액 5,000원 확인
            # print(upbit_client.buy_market_order("KRW-ETH", upbit_client.get_balance("KRW") * 0.99))
            pass
        else:
            print("[Warning] 매수 최소 금액 미충족 (원화 잔액이 5,000원 이하)")

    elif trade_decision['decision'].upper() == 'SELL':
        print(f">> Sell order executed")
        my_eth = upbit_client.get_balance("ETH")
        current_price = pyupbit.get_orderbook(ticker="KRW-ETH")['orderbhook_units'][0]['ask_price']  # 현재 매도 호가 조회
        if my_eth * current_price > 5000:
            # print(upbit_client.sell_market_order("KRW-ETH", upbit_client.get_balance("KRW-ETH")))
            pass
        else:
            print("[Warning] 매도 최소 금액 미충족 (5,000원 미만)")

    elif trade_decision['decision'].upper() == 'HOLD':
        print(f">> HOLD Position")


if __name__ == "__main__":
    ai_trade()
