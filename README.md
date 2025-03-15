# [Study] Ethereum Auto Trade

가상화폐 Ethereum에 대한 auto trading application. 매매 전략은 여러 보조 지표들과 이전 매매 내역에 대한 AI의 회고를 기반으로 한 AI의 매매 판단에 의해 수행된다.

## Requirements

Auto trade application 구동을 위해서는 다음과 같은 사항이 필요하다.
 - OPENAI_API_KEY
 - UPBIT_ACCESS_KEY
 - UPBIT_SECRET_KEY
 - SERPAPI_API_KEY
 - MONGODB Connection Info
 상기 내용은 환경 변수로 저장한다. 
 

## Packages

게시판 구현에 사용된 python version은 3.12.3이며 python package는 다음과 같다.
      
	numpy==2.2.3  
	openai==1.65.4  
	pandas==2.2.3   
	pydantic==2.10.6  
	pymongo==4.11.2  
	requests==2.32.3  
	streamlit==1.43.2  
	ta==0.11.0  
	youtube-transcript-api==0.6.3 

## Run application

Application은 다음과 같이 구동한다.

    $ ~/.venv/bin/python auto_trade.py

## Streamlit dashboard
준비중 