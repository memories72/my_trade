import logging
import sys
from typing import Optional, Tuple

import pandas as pd

sys.path.extend(['..', '.'])
import kis_auth as ka

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


##############################################################################################
# [해외주식] 기본시세 > 해외주식 현재체결가 [v1_해외주식-009]
##############################################################################################

def price(
        auth: str = "",  # 사용자권한정보
        excd: str = "",  # 거래소코드
        symb: str = "",  # 종목코드
        env_dv: str = "real",  # 실전모의구분
) -> Optional[pd.DataFrame]:
    """
    [해외주식] 기본시세
    해외주식 현재체결가[v1_해외주식-009]
    해외주식 현재가를 조회합니다.

    Args:
        auth (str): 사용자권한정보 (공백 가능)
        excd (str): 거래소코드 (예: "NAS" - 나스닥, "NYS" - 뉴욕, "AMS" - 아멕스)
        symb (str): 종목코드 (예: "AAPL", "TSLA")
        env_dv (str): 실전모의구분 (real:실전, demo:모의)

    Returns:
        Optional[pd.DataFrame]: 해외주식 현재체결가 데이터

    Example:
        >>> df = price(excd="NAS", symb="AAPL")
        >>> print(df)
    """
    if not excd:
        logger.error("excd is required. (e.g. 'NAS')")
        raise ValueError("excd is required. (e.g. 'NAS')")

    if not symb:
        logger.error("symb is required. (e.g. 'AAPL')")
        raise ValueError("symb is required. (e.g. 'AAPL')")

    # TR ID는 실전/모의 공통
    tr_id = "HHDFS00000300"
    api_url = "/uapi/overseas-price/v1/quotations/price"

    params = {
        "AUTH": auth,
        "EXCD": excd,
        "SYMB": symb,
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        if hasattr(res.getBody(), 'output'):
            output_data = res.getBody().output
            if not isinstance(output_data, list):
                output_data = [output_data]
            dataframe = pd.DataFrame(output_data)
            logger.info("Price data fetch complete for %s", symb)
            return dataframe
        else:
            return pd.DataFrame()
    else:
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame()


##############################################################################################
# [해외주식] 주문/계좌 > 해외주식 잔고 [v1_해외주식-006]
##############################################################################################

def inquire_balance(
        cano: str,  # 종합계좌번호
        acnt_prdt_cd: str,  # 계좌상품코드
        ovrs_excg_cd: str,  # 해외거래소코드
        tr_crcy_cd: str,  # 거래통화코드
        FK200: str = "",  # 연속조회검색조건200
        NK200: str = "",  # 연속조회키200
        env_dv: str = "real",  # 실전모의구분
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    [해외주식] 주문/계좌 
    해외주식 잔고[v1_해외주식-006]
    해외주식 잔고를 조회합니다.
    
    Args:
        cano (str): 계좌번호 앞 8자리
        acnt_prdt_cd (str): 계좌번호 뒤 2자리
        ovrs_excg_cd (str): 해외거래소코드
            [모의] NASD:나스닥 NYSE:뉴욕 AMEX:아멕스
            [실전] NASD:미국전체 NAS:나스닥 NYSE:뉴욕 AMEX:아멕스
            공통: SEHK:홍콩 SHAA:상해 SZAA:심천 TKSE:일본 HASE:하노이 VNSE:호치민
        tr_crcy_cd (str): 거래통화코드 (USD, HKD, CNY, JPY, VND)
        FK200 (str): 연속조회검색조건200
        NK200 (str): 연속조회키200
        env_dv (str): 실전모의구분 (real:실전, demo:모의)
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (보유종목 데이터, 계좌요약 데이터)
        
    Example:
        >>> holdings, summary = inquire_balance(
        ...     cano="12345678",
        ...     acnt_prdt_cd="01",
        ...     ovrs_excg_cd="NASD",
        ...     tr_crcy_cd="USD"
        ... )
        >>> print(holdings)
        >>> print(summary)
    """
    if not cano:
        logger.error("cano is required. (e.g. '12345678')")
        raise ValueError("cano is required. (e.g. '12345678')")
    if not acnt_prdt_cd:
        logger.error("acnt_prdt_cd is required. (e.g. '01')")
        raise ValueError("acnt_prdt_cd is required. (e.g. '01')")
    if not ovrs_excg_cd:
        logger.error("ovrs_excg_cd is required. (e.g. 'NASD')")
        raise ValueError("ovrs_excg_cd is required. (e.g. 'NASD')")
    if not tr_crcy_cd:
        logger.error("tr_crcy_cd is required. (e.g. 'USD')")
        raise ValueError("tr_crcy_cd is required. (e.g. 'USD')")

    # TR ID 설정 (모의투자 지원)
    if env_dv == "real":
        tr_id = "TTTS3012R"
    elif env_dv == "demo":
        tr_id = "VTTS3012R"
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")

    api_url = "/uapi/overseas-stock/v1/trading/inquire-balance"

    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": ovrs_excg_cd,
        "TR_CRCY_CD": tr_crcy_cd,
        "CTX_AREA_FK200": FK200,
        "CTX_AREA_NK200": NK200,
    }

    res = ka._url_fetch(api_url=api_url, ptr_id=tr_id, tr_cont="", params=params)

    if res.isOK():
        # output1: 보유종목 리스트
        dataframe1 = pd.DataFrame()
        if hasattr(res.getBody(), 'output1'):
            output_data = res.getBody().output1
            if output_data:
                if isinstance(output_data, list):
                    dataframe1 = pd.DataFrame(output_data)
                else:
                    dataframe1 = pd.DataFrame([output_data])
        
        # output2: 계좌요약 정보
        dataframe2 = pd.DataFrame()
        if hasattr(res.getBody(), 'output2'):
            output_data = res.getBody().output2
            if output_data:
                if isinstance(output_data, list):
                    dataframe2 = pd.DataFrame(output_data)
                else:
                    dataframe2 = pd.DataFrame([output_data])
        
        logger.info("Balance inquiry complete")
        return dataframe1, dataframe2
    else:
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame(), pd.DataFrame()


##############################################################################################
# [해외주식] 주문/계좌 > 해외주식 주문 [v1_해외주식-001]
##############################################################################################

def order(
        cano: str,  # 종합계좌번호
        acnt_prdt_cd: str,  # 계좌상품코드
        ovrs_excg_cd: str,  # 해외거래소코드
        pdno: str,  # 상품번호
        ord_qty: str,  # 주문수량
        ovrs_ord_unpr: str,  # 해외주문단가
        ord_dv: str,  # 주문구분 (buy: 매수, sell: 매도)
        ord_dvsn: str = "00",  # 주문구분 (00:지정가)
        env_dv: str = "real",  # 실전모의구분
) -> Optional[pd.DataFrame]:
    """
    [해외주식] 주문/계좌 
    해외주식 주문[v1_해외주식-001]
    해외주식 매수/매도 주문을 실행합니다.
    
    Args:
        cano (str): 계좌번호 앞 8자리
        acnt_prdt_cd (str): 계좌번호 뒤 2자리
        ovrs_excg_cd (str): 해외거래소코드 (NASD, NYSE, AMEX 등)
        pdno (str): 종목코드 (예: AAPL, TSLA)
        ord_qty (str): 주문수량
        ovrs_ord_unpr (str): 1주당 가격 (시장가는 "0")
        ord_dv (str): 주문구분 (buy:매수, sell:매도)
        ord_dvsn (str): 주문구분 (00:지정가, 기타 시장가 옵션)
        env_dv (str): 실전모의구분 (real:실전, demo:모의)
        
    Returns:
        Optional[pd.DataFrame]: 주문 결과 데이터
        
    Example:
        >>> result = order(
        ...     cano="12345678",
        ...     acnt_prdt_cd="01",
        ...     ovrs_excg_cd="NASD",
        ...     pdno="AAPL",
        ...     ord_qty="1",
        ...     ovrs_ord_unpr="150.00",
        ...     ord_dv="buy"
        ... )
        >>> print(result)
    """
    # 필수 파라미터 검증
    if not cano:
        raise ValueError("cano is required")
    if not acnt_prdt_cd:
        raise ValueError("acnt_prdt_cd is required")
    if not ovrs_excg_cd:
        raise ValueError("ovrs_excg_cd is required")
    if not pdno:
        raise ValueError("pdno is required")
    if not ord_qty:
        raise ValueError("ord_qty is required")
    if not ovrs_ord_unpr:
        raise ValueError("ovrs_ord_unpr is required")
    if not ord_dv:
        raise ValueError("ord_dv is required (buy or sell)")

    # TR ID 설정 (매수/매도 및 거래소별)
    if ord_dv == "buy":
        if ovrs_excg_cd in ("NASD", "NYSE", "AMEX"):
            tr_id = "TTTT1002U"  # 미국 매수
        elif ovrs_excg_cd == "SEHK":
            tr_id = "TTTS1002U"  # 홍콩 매수
        elif ovrs_excg_cd == "SHAA":
            tr_id = "TTTS0202U"  # 상해 매수
        elif ovrs_excg_cd == "SZAA":
            tr_id = "TTTS0305U"  # 심천 매수
        elif ovrs_excg_cd == "TKSE":
            tr_id = "TTTS0308U"  # 일본 매수
        elif ovrs_excg_cd in ("HASE", "VNSE"):
            tr_id = "TTTS0311U"  # 베트남 매수
        else:
            raise ValueError(f"Unsupported exchange: {ovrs_excg_cd}")
        sll_type = ""
    elif ord_dv == "sell":
        if ovrs_excg_cd in ("NASD", "NYSE", "AMEX"):
            tr_id = "TTTT1006U"  # 미국 매도
        elif ovrs_excg_cd == "SEHK":
            tr_id = "TTTS1001U"  # 홍콩 매도
        elif ovrs_excg_cd == "SHAA":
            tr_id = "TTTS1005U"  # 상해 매도
        elif ovrs_excg_cd == "SZAA":
            tr_id = "TTTS0304U"  # 심천 매도
        elif ovrs_excg_cd == "TKSE":
            tr_id = "TTTS0307U"  # 일본 매도
        elif ovrs_excg_cd in ("HASE", "VNSE"):
            tr_id = "TTTS0310U"  # 베트남 매도
        else:
            raise ValueError(f"Unsupported exchange: {ovrs_excg_cd}")
        sll_type = "00"
    else:
        raise ValueError("ord_dv must be 'buy' or 'sell'")

    # 모의투자인 경우 TR ID 변경
    if env_dv == "demo":
        tr_id = "V" + tr_id[1:]
    elif env_dv != "real":
        raise ValueError("env_dv can only be 'real' or 'demo'")

    api_url = "/uapi/overseas-stock/v1/trading/order"

    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": ovrs_excg_cd,
        "PDNO": pdno,
        "ORD_QTY": ord_qty,
        "OVRS_ORD_UNPR": ovrs_ord_unpr,
        "CTAC_TLNO": "",
        "MGCO_APTM_ODNO": "",
        "SLL_TYPE": sll_type,
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": ord_dvsn,
    }

    res = ka._url_fetch(api_url=api_url, ptr_id=tr_id, tr_cont="", params=params, postFlag=True)

    if res.isOK():
        if hasattr(res.getBody(), 'output'):
            output_data = res.getBody().output
            if not isinstance(output_data, list):
                output_data = [output_data]
            dataframe = pd.DataFrame(output_data)
            logger.info("Order placed successfully for %s", pdno)
            return dataframe
        else:
            return pd.DataFrame()
    else:
        logger.error("Order failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame()


##############################################################################################
# [해외주식] 주문/계좌 > 해외주식 주문체결내역 [v1_해외주식-007]
##############################################################################################

def inquire_ccnl(
        cano: str,  # 종합계좌번호
        acnt_prdt_cd: str,  # 계좌상품코드
        ovrs_excg_cd: str,  # 해외거래소코드
        sort_sq: str = "DS",  # 정렬순서
        ord_dt: str = "",  # 주문일자
        ord_gno_brno: str = "",  # 주문채번지점번호
        odno: str = "",  # 주문번호
        env_dv: str = "real",  # 실전모의구분
) -> pd.DataFrame:
    """
    [해외주식] 주문/계좌 
    해외주식 주문체결내역[v1_해외주식-007]
    해외주식 주문 및 체결 내역을 조회합니다.
    
    Args:
        cano (str): 계좌번호 앞 8자리
        acnt_prdt_cd (str): 계좌번호 뒤 2자리
        ovrs_excg_cd (str): 해외거래소코드
        sort_sq (str): 정렬순서 (DS:일자순, AK:종목순)
        ord_dt (str): 주문일자 (YYYYMMDD, 공백:당일)
        ord_gno_brno (str): 주문채번지점번호
        odno (str): 주문번호
        env_dv (str): 실전모의구분 (real:실전, demo:모의)
        
    Returns:
        pd.DataFrame: 주문체결내역 데이터
        
    Example:
        >>> df = inquire_ccnl(
        ...     cano="12345678",
        ...     acnt_prdt_cd="01",
        ...     ovrs_excg_cd="NASD"
        ... )
        >>> print(df)
    """
    if not cano:
        raise ValueError("cano is required")
    if not acnt_prdt_cd:
        raise ValueError("acnt_prdt_cd is required")
    if not ovrs_excg_cd:
        raise ValueError("ovrs_excg_cd is required")

    # TR ID 설정
    if env_dv == "real":
        tr_id = "TTTS3035R"
    elif env_dv == "demo":
        tr_id = "VTTS3035R"
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")

    api_url = "/uapi/overseas-stock/v1/trading/inquire-ccnl"

    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": ovrs_excg_cd,
        "SORT_SQ": sort_sq,
        "ORD_DT": ord_dt,
        "ORD_GNO_BRNO": ord_gno_brno,
        "ODNO": odno,
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }

    res = ka._url_fetch(api_url=api_url, ptr_id=tr_id, tr_cont="", params=params)

    if res.isOK():
        if hasattr(res.getBody(), 'output'):
            output_data = res.getBody().output
            if not isinstance(output_data, list):
                output_data = [output_data]
            dataframe = pd.DataFrame(output_data)
            logger.info("Order history inquiry complete")
            return dataframe
        else:
            return pd.DataFrame()
    else:
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame()
