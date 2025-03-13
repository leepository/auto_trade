import pandas as pd
import plotly.express as px
import streamlit as st

from mongodb_connector import get_mongodb_client


def load_data(mongodb_client):
    raws = list(mongodb_client.autotradedb.trading_result.find({}, {'_id': 0}).sort('timestamp', -1).limit(14))
    columns = ['timestamp', 'decision', 'percentage', 'reason', 'eth_balance', 'krw_balance', 'eth_avg_buy_price', 'eth_krw_price', 'reflection']
    df = pd.DataFrame(raws, columns=columns)
    return df

def main():
    st.title("Ethereum Trades Viewer")

    # Get Mongodb Client
    mongodb_client = get_mongodb_client()

    # 데이터 로드
    df = load_data(mongodb_client=mongodb_client)

    # 기본 통계
    st.header("Basic Statistics")
    st.write(f"Total number of trades: {len(df)}")
    st.write(f"First trade date: {df['timestamp'].min()}")
    st.write(f"Last trade date: {df['timestamp'].max()}")

    # 거래 내역 표시
    st.header("Trade History")
    st.dataframe(df)

    # 거래 결정 분포
    st.header("Trade Decision Distribution")
    decision_counts = df['decision'].value_counts()
    fig = px.pie(
        values=decision_counts.values,
        names=decision_counts.index,
        title='Trade Decisions'
    )
    st.plotly_chart(fig)

    # ETH 잔액 변화
    st.header('ETH Balance over time')
    fig = px.line(df, x='timestamp', y='eth_balance', title='ETH Balance')
    st.plotly_chart(fig)

    # KRW 잔액 변화
    st.header('KRW Balance over time')
    fig = px.line(df, x='timestamp', y='krw_balance', title='KRW Balance')
    st.plotly_chart(fig)

    # ETH 가격 변화
    st.header('ETH Price over time')
    fig = px.line(df, x='timestamp', y='eth_krw_price', title='ETH Price (KRW)')
    st.plotly_chart(fig)

if __name__ == '__main__':
    main()
