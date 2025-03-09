import os
import requests


from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands

def add_indicators(df):
    """
    보조 지표를 계산하여 DF에 삽입한다.
    :param df:
    :return:
    """
    # 볼린저 밴드
    indicator_bb = BollingerBands(
        close=df['close'],
        window=20,
        window_dev=2
    )
    df['bb_bbm'] = indicator_bb.bollinger_mavg()
    df['bb_bbh'] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()

    # RSI : 상대강도지수, 가격의 상승 압력과 하락 압력간의 상대적인 강도를 나타낸다.
    # 일정 기간 동안 주가가 전일 가격에 비해 상승한 변화량과 하락한 변화량의 평균값을 구하여,
    # 상승한 변화량이 크면 과매수로, 하락한 변화량이 크면 과매도로 판단한느 방식
    # 1. 가격이 전일 가격보다 상승한 날의 상승분은 U(up)값이라고 한다.
    # 2. 가격이 전일 가격보다 하락한 날의 하락분은 D(down)값이라고 한다.
    # 3. U값과 D값의 평균값을 구하여 그것을 각각 AU(Average ups)와 AD(Average downs)라고 한다.
    # 4. AU를 AD값으로 나눈 것을 RS(Relative Strength)값이라고 한다. RS 값이 크다는 것은 일정 기간 하락한 폭보다 상승한 폭이 크다는 것의 의미한다.
    # 5. 다음 계산에 의하여 RSI값을 구한다. RSI = RS / (1 + RS) -> 대체로 이 값을 백분율로 나타낸다.
    # Ref: https://ko.wikipedia.org/wiki/RSI_(%ED%88%AC%EC%9E%90%EC%A7%80%ED%91%9C)
    df['rsi'] = RSIIndicator(
        close=df['close'],
        window=14
    ).rsi()

    # MACD : 이동 평균 수렴 확신 지수, 주가 추세의 강도, 방향, 모멘텀 및 지속 시간의 변화를 나타낸다.
    # - 과거의 가격 데이터(대부분 증가)로부터 계산된 세가지 시계열의 모음이다.
    # - 이러한 세가지 시계열은 MACD 고유의 '신호', '평균', '확산'이다.
    # - MACD는 장기 지수 이동 평군과 단기 지수 이동 평균간의 차이이다.
    # Ref: https://ko.wikipedia.org/wiki/MACD
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    # 이동 평균선
    df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['sma_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()

    return df

def get_fear_and_greed_index():
    """
    공포 탐욕 지수를 산정한다.
    :return:
    """
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data'][0]
    else:
        print(f"[Error] Failed to fetch 'Fear and greed index'. Status code: {response.status_code}, ")

def get_etherium_news():
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_news",
        "q": "ethereum",
        "qpi_key":serpapi_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Raises a HTTPError if the status is 4xx, 5xx
        data = response.json()

        news_results = data.get("news_results", [])
        headlines = []
        for item in news_results:
            headlines.append({
                "title": item.get("title", ""),
                "date": item.get("date", "")
            })

        return headlines[:5] # 최신 5개 뉴스 헤드라인만 반환

    except requests.RequestException as ex:
        print(f"[Error] Error fetching news : {ex}")
        return []
