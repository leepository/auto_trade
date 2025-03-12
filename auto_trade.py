import json
import logging
import os
import pyupbit
import time

from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from ta.utils import dropna

from analytics_resource.indicators import (
    add_indicators,
    get_fear_and_greed_index
)
from analytics_resource.news_data import get_etherium_news
from analytics_resource.capture_chart import run_capture
from analytics_resource.youtube_script import get_combined_transcript
from mongodb_connector import get_mongodb_client

# Logger 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정 파일 Load
load_dotenv()

# Structured Output : https://platform.openai.com/docs/guides/structured-outputs
# OpenAI Playground : https://platform.openai.com/playground/chat?models=gpt-4o
class TradingDecision(BaseModel):
    decision: str
    percentage: int
    reason: str


def ai_trade():
    print("##### [START] AutoTrade ######")

    upbit_access_key = os.getenv('UPBIT_ACCESS_KEY')
    upbit_secret_key = os.getenv('UPBIT_SECRET_KEY')
    upbit_client = pyupbit.Upbit(upbit_access_key, upbit_secret_key)

    ####################################################################################################################
    # 1. 업비트 데이터 가져오기 (30일 일봉 데이터, 24시간 ohlcv 데이터, 오더북, balance)
    ####################################################################################################################

    print(">> Get Upbit data : Balance")
    # Get upbit balance
    all_balances = upbit_client.get_balances()
    # filtered_balances_dict = {balance['currency']:balance for balance in all_balances if balance['currency'] in ['ETH', 'KRW']}
    filtered_balances = [balance for balance in all_balances if balance['currency'] in ['ETH', 'KRW']]

    print(">> Get Upbit orderbook data")
    # Orderbook(현재 호가) 데이터 조회
    order_book = pyupbit.get_orderbook("KRW-ETH")

    print(">> Get Upbit daily OHLCV")
    # 30일 기준 일봉 데이터 조회
    df_daily = pyupbit.get_ohlcv("KRW-ETH", interval="day", count=30)
    df_daily = dropna(df_daily)
    df_daily = add_indicators(df=df_daily)

    print(">> Get Upbit 24Hours OHLCV")
    # 1일 기준 시간봉 데이터 조회
    df_hourly = pyupbit.get_ohlcv("KRW-ETH", interval="minute60", count=24)
    df_hourly = dropna(df_hourly)
    df_hourly = add_indicators(df=df_hourly)

    print(">> Get fear and greed index")
    # 공포 탐욕 지수 가져오기
    fear_greed_index = get_fear_and_greed_index()

    print(">> Get news headline")
    # 뉴스 헤드라인 가져오기
    news_headlines = get_etherium_news()

    # 차트 이미지 캡처 후 가져오기
    # chart_image, saved_file_path = run_capture()

    print(">> Get Youtube script")
    # YouTube script 가져오기
    youtube_transcript = get_combined_transcript(video_id="3XbtEX3jUv4")

    ####################################################################################################################
    # 2. AI에게 데이터를 제공하고 판단 받기
    ####################################################################################################################
    print(">> Make AI Decision")
    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": f"""You are an expert in Cryptocurrency investing. Analyze the provided data including technical indicators and tell me whether to buy, sell, or hold at the moment. Consider the following indicators in your analysis. Translate the reason in the message's content into Korean:
                    - Technical indicators and market data
                    - The Fear and Greed index and its implications
                    - Recent news headlines and their potential impact on Ethereum price
                    - Insight from the YouTube video transcript

                    Particularly important is to always refer to the trading method of 'Wonyyotti', a legendary Korean investor, to access the current situation and make trading decision. Wonyyotti's trading method is as follows: 
                    {youtube_transcript}
                    
                    Based on this trading method, analyze the current market situation and make a judgement by synthesizing it with the provided data.
                    
                    Response format:
                    1. A decision (buy, sell, or hold)
                    2. If the decision is 'buy', provide a percentage (1-100) of available KRW to use for buying.
                    If the decision is 'sell', provide a percentabe (1-100) of held ETH to sell.
                    If the decision is 'hold', set the percentage to 0.
                    3. A reason for your deicision
                    
                    Ensure that the percentage is an integer between 1 and 100 for buy/sell decision, and exactly 0 for hold decisions.
                    Your percentage should reflect the strength of your conviction in the decision based on. the analyzed data.
            """
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""
                        Current investment status: {json.dumps(filtered_balances)}
                        Orderbook: {json.dumps(order_book)}
                        Daily OHLCV with indicators (30 days): {df_daily.to_json()}
                        Hourly OHLCV with indicators (24 Hours): {df_hourly.to_json()}
                        Fear and Greed index: {json.dumps(fear_greed_index)}
                        Recent news headlines : {json.dumps(news_headlines)}
                    """
                },
                # {
                #     "type": "image_url",
                #     "image_url": {
                #         "url": f"data:image/png;base64,{chart_image}"
                #     }
                # }
            ]
        }
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "trading_decision",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "decision": {
                        "type": "string",
                        "enum": ["buy", "sell", "hold"]
                    },
                    "percentage": {
                        "type": "integer"
                    },
                    "reason": {
                        "type": "string"
                    }
                },
                "required": ["decision", "percentage",  "reason"],
                "additionalProperties": False
            }
        }
    }
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=response_format,
        max_tokens=4095
    )
    # ai_decision = response.choices[0].message.content
    trade_decision = TradingDecision.model_validate_json(response.choices[0].message.content)


    ####################################################################################################################
    # 3. AI의 판단에 따라 실제로 자동매매 진행하기
    ####################################################################################################################
    print(">> Execution trading")
    # Setup upbit client
    upbit_access_key = os.getenv('UPBIT_ACCESS_KEY')
    upbit_secret_key = os.getenv('UPBIT_SECRET_KEY')
    upbit_client = pyupbit.Upbit(upbit_access_key, upbit_secret_key)



    print(f"> AI Decision : {trade_decision.decision.upper()} ###")
    print(f"> Reason : {trade_decision.reason} ###")

    if trade_decision.decision.upper() == 'BUY':
        my_krw = upbit_client.get_balance("KRW")
        # trading_quantity = my_krw * 0.99  # 수수료를 제외한 나머지 금액으로 매수한다.
        trading_quantity = my_krw * (trade_decision.percentage / 100) * 0.99
        if trading_quantity > 5000:  # Upbit 매수 최소 금액 5,000원 확인
            print(f">> Buy order executed : {trade_decision.percentage}% of available KRW")
            # print(upbit_client.buy_market_order("KRW-ETH", trading_quantity))
            pass
        else:
            print("[Warning] 매수 최소 금액 미충족 (원화 잔액이 5,000원 이하)")

    elif trade_decision.decision.upper() == 'SELL':
        my_eth = upbit_client.get_balance("ETH")
        trading_quantity = my_eth * (trade_decision.percentage / 100)
        current_price = pyupbit.get_orderbook(ticker="KRW-ETH")['orderbook_units'][0]['ask_price']  # 현재 매도 호가 조회
        if trading_quantity * current_price > 5000:
            print(f">> Sell order executed : {trade_decision.percentage}% of held ETH")
            # print(upbit_client.sell_market_order("KRW-ETH", upbit_client.get_balance("KRW-ETH")))
            pass
        else:
            print("[Warning] 매도 최소 금액 미충족 (5,000원 미만)")

    elif trade_decision.decision.upper() == 'HOLD':
        print(f">> HOLD Position")

    # 거래 여부와 상관없이 현재 잔액 조회
    time.sleep(1) # API 호출 제한을 고려하여 잠시 대기
    balances = upbit_client.get_balances()
    print("balances : ", balances)
    eth_balance = next((float(balance['balance']) for balance in balances if balance['currency'] == 'ETH'),0)
    krw_balance = next((float(balance['balance']) for balance in balances if balance['currency'] == 'KRW'), 0)
    eth_avg_buy_price = next((float(balance['avg_buy_price']) for balance in balances if balance['currency'] == 'ETH'), 0)
    current_eth_price = pyupbit.get_current_price('KRW-ETH')

    log_trade = {
        "timestamp": datetime.now().isoformat(),
        "decision": trade_decision.decision.upper(),
        "percentage": trade_decision.percentage,
        "reason": trade_decision.reason,
        "eth_balance": eth_balance,
        "krw_balance": krw_balance,
        "eth_avg_buy_price": eth_avg_buy_price,
        "eth_krw_price": current_eth_price
    }
    try:
        # Setup mongodb client
        mongodb_client = get_mongodb_client()
        mongodb_client.autotradedb.trading_result.insert_one(log_trade)
        mongodb_client.close()
    except Exception as ex:
        print("[EX] Failed to insert log trade : ", str(ex.args))

    print("##### [END] AutoTrade #####")

def run_trading():
    while True:
        try:
            ai_trade()
            time.sleep(600) # 10분마다 실행
        except Exception as ex:
            logger.error(f"Auto trading error : {ex}")
            time.sleep(300) # 오류 발생 시 5분 후 재시도

if __name__ == "__main__":
    run_trading()
