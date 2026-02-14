import logging
import time
import sys
from typing import Optional, Tuple

import pandas as pd

sys.path.extend(['..', '.'])
import kis_auth as ka

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


##############################################################################################
# [국내주식] 기본시세 > 국내주식 시간외잔량 순위[v1_국내주식-093]
##############################################################################################

def after_hour_balance(
        fid_input_price_1: str,  # 입력 가격1
        fid_cond_mrkt_div_code: str,  # 조건 시장 분류 코드
        fid_cond_scr_div_code: str,  # 조건 화면 분류 코드
        fid_rank_sort_cls_code: str,  # 순위 정렬 구분 코드
        fid_div_cls_code: str,  # 분류 구분 코드
        fid_input_iscd: str,  # 입력 종목코드
        fid_trgt_exls_cls_code: str,  # 대상 제외 구분 코드
        fid_trgt_cls_code: str,  # 대상 구분 코드
        fid_vol_cnt: str,  # 거래량 수
        fid_input_price_2: str,  # 입력 가격2
        tr_cont: str = "",  # 연속 거래 여부
        dataframe: Optional[pd.DataFrame] = None,  # 누적 데이터프레임
        depth: int = 0,  # 현재 재귀 깊이
        max_depth: int = 10  # 최대 재귀 깊이
) -> Optional[pd.DataFrame]:
    """
    [국내주식] 순위분석 
    국내주식 시간외잔량 순위[v1_국내주식-093]
    국내주식 시간외잔량 순위 API를 호출하여 DataFrame으로 반환합니다.
    
    Args:
        fid_input_price_1 (str): 입력값 없을때 전체 (가격 ~)
        fid_cond_mrkt_div_code (str): 시장구분코드 (주식 J)
        fid_cond_scr_div_code (str): Unique key( 20176 )
        fid_rank_sort_cls_code (str): 1: 장전 시간외, 2: 장후 시간외, 3:매도잔량, 4:매수잔량
        fid_div_cls_code (str): 0 : 전체
        fid_input_iscd (str): 0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200
        fid_trgt_exls_cls_code (str): 0 : 전체
        fid_trgt_cls_code (str): 0 : 전체
        fid_vol_cnt (str): 입력값 없을때 전체 (거래량 ~)
        fid_input_price_2 (str): 입력값 없을때 전체 (~ 가격)
        tr_cont (str): 연속 거래 여부
        dataframe (Optional[pd.DataFrame]): 누적 데이터프레임
        depth (int): 현재 재귀 깊이
        max_depth (int): 최대 재귀 깊이 (기본값: 10)
        
    Returns:
        Optional[pd.DataFrame]: 국내주식 시간외잔량 순위 데이터
        
    Example:
        >>> df = after_hour_balance(
        ...     fid_input_price_1="",
        ...     fid_cond_mrkt_div_code="J",
        ...     fid_cond_scr_div_code="20176",
        ...     fid_rank_sort_cls_code="1",
        ...     fid_div_cls_code="0",
        ...     fid_input_iscd="0000",
        ...     fid_trgt_exls_cls_code="0",
        ...     fid_trgt_cls_code="0",
        ...     fid_vol_cnt="",
        ...     fid_input_price_2=""
        ... )
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/ranking/after-hour-balance"
    # 로깅 설정
    logger = logging.getLogger(__name__)

    # 필수 파라미터 검증
    if not fid_cond_mrkt_div_code:
        logger.error("fid_cond_mrkt_div_code is required. (e.g. 'J')")
        raise ValueError("fid_cond_mrkt_div_code is required. (e.g. 'J')")

    if not fid_cond_scr_div_code:
        logger.error("fid_cond_scr_div_code is required. (e.g. '20176')")
        raise ValueError("fid_cond_scr_div_code is required. (e.g. '20176')")

    if not fid_rank_sort_cls_code:
        logger.error("fid_rank_sort_cls_code is required. (e.g. '1')")
        raise ValueError("fid_rank_sort_cls_code is required. (e.g. '1')")

    if not fid_input_iscd:
        logger.error("fid_input_iscd is required. (e.g. '0000')")
        raise ValueError("fid_input_iscd is required. (e.g. '0000')")

    # 최대 재귀 깊이 체크
    if depth >= max_depth:
        logger.warning("Maximum recursion depth (%d) reached. Stopping further requests.", max_depth)
        return dataframe if dataframe is not None else pd.DataFrame()

    # API 호출 URL 및 거래 ID 설정

    tr_id = "FHPST01760000"

    # API 요청 파라미터 설정
    params = {
        "fid_input_price_1": fid_input_price_1,
        "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
        "fid_cond_scr_div_code": fid_cond_scr_div_code,
        "fid_rank_sort_cls_code": fid_rank_sort_cls_code,
        "fid_div_cls_code": fid_div_cls_code,
        "fid_input_iscd": fid_input_iscd,
        "fid_trgt_exls_cls_code": fid_trgt_exls_cls_code,
        "fid_trgt_cls_code": fid_trgt_cls_code,
        "fid_vol_cnt": fid_vol_cnt,
        "fid_input_price_2": fid_input_price_2,
    }

    # API 호출
    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    # API 호출 성공 시 데이터 처리
    if res.isOK():
        if hasattr(res.getBody(), 'output'):
            current_data = pd.DataFrame(res.getBody().output)
        else:
            current_data = pd.DataFrame()

        # 기존 데이터프레임과 병합
        if dataframe is not None:
            dataframe = pd.concat([dataframe, current_data], ignore_index=True)
        else:
            dataframe = current_data

        # 연속 거래 여부 확인
        tr_cont = res.getHeader().tr_cont

        # 다음 페이지 호출
        if tr_cont == "M":
            logger.info("Calling next page...")
            ka.smart_sleep()
            return after_hour_balance(
                fid_input_price_1,
                fid_cond_mrkt_div_code,
                fid_cond_scr_div_code,
                fid_rank_sort_cls_code,
                fid_div_cls_code,
                fid_input_iscd,
                fid_trgt_exls_cls_code,
                fid_trgt_cls_code,
                fid_vol_cnt,
                fid_input_price_2,
                "N", dataframe, depth + 1, max_depth
            )
        else:
            logger.info("Data fetch complete.")
            return dataframe
    else:
        # API 호출 실패 시 에러 로그 출력
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 순위분석 > 국내주식 대량체결건수 상위[국내주식-107]
##############################################################################################

def bulk_trans_num(
        fid_aply_rang_prc_2: str,  # 적용 범위 가격2
        fid_cond_mrkt_div_code: str,  # 조건 시장 분류 코드
        fid_cond_scr_div_code: str,  # 조건 화면 분류 코드
        fid_input_iscd: str,  # 입력 종목코드
        fid_rank_sort_cls_code: str,  # 순위 정렬 구분 코드
        fid_div_cls_code: str,  # 분류 구분 코드
        fid_input_price_1: str,  # 입력 가격1
        fid_aply_rang_prc_1: str,  # 적용 범위 가격1
        fid_input_iscd_2: str,  # 입력 종목코드2
        fid_trgt_exls_cls_code: str,  # 대상 제외 구분 코드
        fid_trgt_cls_code: str,  # 대상 구분 코드
        fid_vol_cnt: str,  # 거래량 수
        tr_cont: str = "",  # 연속 거래 여부
        dataframe: Optional[pd.DataFrame] = None,  # 누적 데이터프레임
        depth: int = 0,  # 현재 재귀 깊이
        max_depth: int = 10  # 최대 재귀 깊이
) -> Optional[pd.DataFrame]:
    """
    [국내주식] 순위분석 
    국내주식 대량체결건수 상위[국내주식-107]
    국내주식 대량체결건수 상위 API를 호출하여 DataFrame으로 반환합니다.
    
    Args:
        fid_aply_rang_prc_2 (str): ~ 가격
        fid_cond_mrkt_div_code (str): 시장구분코드 (J:KRX, NX:NXT)
        fid_cond_scr_div_code (str): Unique key(11909)
        fid_input_iscd (str): 0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200, 4001: KRX100
        fid_rank_sort_cls_code (str): 0:매수상위, 1:매도상위
        fid_div_cls_code (str): 0:전체
        fid_input_price_1 (str): 건별금액 ~
        fid_aply_rang_prc_1 (str): 가격 ~
        fid_input_iscd_2 (str): 공백:전체종목, 개별종목 조회시 종목코드 (000660)
        fid_trgt_exls_cls_code (str): 0:전체
        fid_trgt_cls_code (str): 0:전체
        fid_vol_cnt (str): 거래량 ~
        tr_cont (str): 연속 거래 여부
        dataframe (Optional[pd.DataFrame]): 누적 데이터프레임
        depth (int): 현재 재귀 깊이
        max_depth (int): 최대 재귀 깊이 (기본값: 10)
        
    Returns:
        Optional[pd.DataFrame]: 국내주식 대량체결건수 상위 데이터
        
    Example:
        >>> df = bulk_trans_num(
                fid_aply_rang_prc_2="100000",
                fid_cond_mrkt_div_code="J",
                fid_cond_scr_div_code="11909",
                fid_input_iscd="0000",
                fid_rank_sort_cls_code="0",
                fid_div_cls_code="0",
                fid_input_price_1="50000",
                fid_aply_rang_prc_1="200000",
                fid_input_iscd_2="",
                fid_trgt_exls_cls_code="0",
                fid_trgt_cls_code="0",
                fid_vol_cnt="1000"
            )
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/ranking/bulk-trans-num"
    # 로깅 설정
    logger = logging.getLogger(__name__)

    # 필수 파라미터 검증
    if not fid_cond_mrkt_div_code:
        logger.error("fid_cond_mrkt_div_code is required. (e.g. 'J')")
        raise ValueError("fid_cond_mrkt_div_code is required. (e.g. 'J')")

    if not fid_cond_scr_div_code:
        logger.error("fid_cond_scr_div_code is required. (e.g. '11909')")
        raise ValueError("fid_cond_scr_div_code is required. (e.g. '11909')")

    if not fid_input_iscd:
        logger.error("fid_input_iscd is required. (e.g. '0000')")
        raise ValueError("fid_input_iscd is required. (e.g. '0000')")

    if not fid_rank_sort_cls_code:
        logger.error("fid_rank_sort_cls_code is required. (e.g. '0')")
        raise ValueError("fid_rank_sort_cls_code is required. (e.g. '0')")

    if not fid_div_cls_code:
        logger.error("fid_div_cls_code is required. (e.g. '0')")
        raise ValueError("fid_div_cls_code is required. (e.g. '0')")

    if not fid_trgt_exls_cls_code:
        logger.error("fid_trgt_exls_cls_code is required. (e.g. '0')")
        raise ValueError("fid_trgt_exls_cls_code is required. (e.g. '0')")

    if not fid_trgt_cls_code:
        logger.error("fid_trgt_cls_code is required. (e.g. '0')")
        raise ValueError("fid_trgt_cls_code is required. (e.g. '0')")

    # 최대 재귀 깊이 체크
    if depth >= max_depth:
        logger.warning("Maximum recursion depth (%d) reached. Stopping further requests.", max_depth)
        return dataframe if dataframe is not None else pd.DataFrame()

    tr_id = "FHKST190900C0"

    params = {
        "fid_aply_rang_prc_2": fid_aply_rang_prc_2,
        "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
        "fid_cond_scr_div_code": fid_cond_scr_div_code,
        "fid_input_iscd": fid_input_iscd,
        "fid_rank_sort_cls_code": fid_rank_sort_cls_code,
        "fid_div_cls_code": fid_div_cls_code,
        "fid_input_price_1": fid_input_price_1,
        "fid_aply_rang_prc_1": fid_aply_rang_prc_1,
        "fid_input_iscd_2": fid_input_iscd_2,
        "fid_trgt_exls_cls_code": fid_trgt_exls_cls_code,
        "fid_trgt_cls_code": fid_trgt_cls_code,
        "fid_vol_cnt": fid_vol_cnt,
    }

    # API 호출
    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    if res.isOK():
        # 응답 데이터 처리
        if hasattr(res.getBody(), 'output'):
            current_data = pd.DataFrame(res.getBody().output)
        else:
            current_data = pd.DataFrame()

        # 데이터프레임 병합
        if dataframe is not None:
            dataframe = pd.concat([dataframe, current_data], ignore_index=True)
        else:
            dataframe = current_data

        # 다음 페이지 여부 확인
        tr_cont = res.getHeader().tr_cont

        if tr_cont == "M":
            logger.info("Calling next page...")
            ka.smart_sleep()
            return bulk_trans_num(
                fid_aply_rang_prc_2,
                fid_cond_mrkt_div_code,
                fid_cond_scr_div_code,
                fid_input_iscd,
                fid_rank_sort_cls_code,
                fid_div_cls_code,
                fid_input_price_1,
                fid_aply_rang_prc_1,
                fid_input_iscd_2,
                fid_trgt_exls_cls_code,
                fid_trgt_cls_code,
                fid_vol_cnt,
                "N", dataframe, depth + 1, max_depth
            )
        else:
            logger.info("Data fetch complete.")
            return dataframe
    else:
        # API 호출 실패 시 에러 로그
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 시세분석 > 국내주식 상하한가 포착 [국내주식-190]
##############################################################################################

def capture_uplowprice(
        fid_cond_mrkt_div_code: str,  # [필수] 조건시장분류코드 (ex. J:주식)
        fid_cond_scr_div_code: str,  # [필수] 조건화면분류코드 (ex. 11300)
        fid_prc_cls_code: str,  # [필수] 상하한가 구분코드 (ex. 0:상한가, 1:하한가)
        fid_div_cls_code: str,
        # [필수] 분류구분코드 (ex. 0:상하한가종목, 6:8%상하한가 근접, 5:10%상하한가 근접, 1:15%상하한가 근접, 2:20%상하한가 근접, 3:25%상하한가 근접)
        fid_input_iscd: str,  # [필수] 입력종목코드 (ex. 0000:전체, 0001:코스피, 1001:코스닥)
        fid_trgt_cls_code: str = "",  # 대상구분코드
        fid_trgt_exls_cls_code: str = "",  # 대상제외구분코드
        fid_input_price_1: str = "",  # 입력가격1
        fid_input_price_2: str = "",  # 입력가격2
        fid_vol_cnt: str = ""  # 거래량수
) -> pd.DataFrame:
    """
    국내주식 상하한가 포착 API입니다.
    한국투자 HTS(eFriend Plus) > [0917] 실시간 상하한가 포착 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    
    Args:
        fid_cond_mrkt_div_code (str): [필수] 조건시장분류코드 (ex. J:주식)
        fid_cond_scr_div_code (str): [필수] 조건화면분류코드 (ex. 11300)
        fid_prc_cls_code (str): [필수] 상하한가 구분코드 (ex. 0:상한가, 1:하한가)
        fid_div_cls_code (str): [필수] 분류구분코드 (ex. 0:상하한가종목, 6:8%상하한가 근접, 5:10%상하한가 근접, 1:15%상하한가 근접, 2:20%상하한가 근접, 3:25%상하한가 근접)
        fid_input_iscd (str): [필수] 입력종목코드 (ex. 0000:전체, 0001:코스피, 1001:코스닥)
        fid_trgt_cls_code (str): 대상구분코드
        fid_trgt_exls_cls_code (str): 대상제외구분코드
        fid_input_price_1 (str): 입력가격1
        fid_input_price_2 (str): 입력가격2
        fid_vol_cnt (str): 거래량수

    Returns:
        pd.DataFrame: 상하한가 포착 데이터
        
    Example:
        >>> df = capture_uplowprice("J", "11300", "0", "0", "0000")
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/capture-uplowprice"

    # 필수 파라미터 검증
    if fid_cond_mrkt_div_code == "":
        raise ValueError("fid_cond_mrkt_div_code is required (e.g. 'J')")

    if fid_cond_scr_div_code == "":
        raise ValueError("fid_cond_scr_div_code is required (e.g. '11300')")

    if fid_prc_cls_code == "":
        raise ValueError("fid_prc_cls_code is required (e.g. '0', '1')")

    if fid_div_cls_code == "":
        raise ValueError("fid_div_cls_code is required (e.g. '0', '6', '5', '1', '2', '3')")

    if fid_input_iscd == "":
        raise ValueError("fid_input_iscd is required (e.g. '0000', '0001', '1001')")

    tr_id = "FHKST130000C0"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
        "FID_PRC_CLS_CODE": fid_prc_cls_code,
        "FID_DIV_CLS_CODE": fid_div_cls_code,
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_TRGT_CLS_CODE": fid_trgt_cls_code,
        "FID_TRGT_EXLS_CLS_CODE": fid_trgt_exls_cls_code,
        "FID_INPUT_PRICE_1": fid_input_price_1,
        "FID_INPUT_PRICE_2": fid_input_price_2,
        "FID_VOL_CNT": fid_vol_cnt
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        return pd.DataFrame(res.getBody().output)
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 업종/기타 > 국내휴장일조회[국내주식-040]
##############################################################################################

def chk_holiday(
        bass_dt: str,  # 기준일자 (YYYYMMDD)
        NK100: str = "",  # 연속조회키
        FK100: str = "",  # 연속조회검색조건
        tr_cont: str = "",  # 연속거래여부
        dataframe: Optional[pd.DataFrame] = None,  # 누적 데이터프레임
        depth: int = 0,  # 내부 재귀깊이 (자동관리)
        max_depth: int = 10  # 최대 재귀 횟수 제한
) -> pd.DataFrame:
    """
    (★중요) 국내휴장일조회(TCA0903R) 서비스는 당사 원장서비스와 연관되어 있어 
    단시간 내 다수 호출시 서비스에 영향을 줄 수 있어 가급적 1일 1회 호출 부탁드립니다.

    국내휴장일조회 API입니다.
    영업일, 거래일, 개장일, 결제일 여부를 조회할 수 있습니다.
    주문을 넣을 수 있는지 확인하고자 하실 경우 개장일여부(opnd_yn)을 사용하시면 됩니다.
    
    Args:
        bass_dt (str): [필수] 기준일자 (ex. YYYYMMDD)
        NK100 (str): 연속조회키
        FK100 (str): 연속조회검색조건
        tr_cont (str): 연속거래여부
        dataframe (Optional[pd.DataFrame]): 누적 데이터프레임
        depth (int): 내부 재귀깊이 (자동관리)
        max_depth (int): 최대 재귀 횟수 제한

    Returns:
        pd.DataFrame: 국내휴장일조회 데이터
        
    Example:
        >>> df = chk_holiday(bass_dt="20250630")
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/chk-holiday"

    if bass_dt == "":
        raise ValueError("bass_dt is required (e.g. 'YYYYMMDD')")

    if depth > max_depth:
        logging.warning("Max recursive depth reached.")
        if dataframe is None:
            return pd.DataFrame()
        else:
            return dataframe

    tr_id = "CTCA0903R"  # 국내휴장일조회

    params = {
        "BASS_DT": bass_dt,
        "CTX_AREA_FK": FK100,
        "CTX_AREA_NK": NK100
    }

    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    if res.isOK():
        if hasattr(res.getBody(), 'output'):
            output_data = res.getBody().output
            if not isinstance(output_data, list):
                output_data = [output_data]
            current_data = pd.DataFrame(output_data)
        else:
            current_data = pd.DataFrame()

        if dataframe is not None:
            dataframe = pd.concat([dataframe, current_data], ignore_index=True)
        else:
            dataframe = current_data

        tr_cont = res.getHeader().tr_cont
        FK100 = res.getBody().ctx_area_fk
        NK100 = res.getBody().ctx_area_nk

        if tr_cont in ["M", "F"]:  # 다음 페이지 존재
            logging.info("Call Next page...")
            ka.smart_sleep()  # 시스템 안정적 운영을 위한 지연
            return chk_holiday(
                bass_dt, NK100, FK100, "N", dataframe, depth + 1, max_depth
            )
        else:
            logging.info("Data fetch complete.")
            return dataframe
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 업종/기타 > 금리 종합(국내채권_금리)[국내주식-155]
##############################################################################################

def comp_interest(
        fid_cond_mrkt_div_code: str,  # 조건시장분류코드
        fid_cond_scr_div_code: str,  # 조건화면분류코드
        fid_div_cls_code: str,  # 분류구분코드
        fid_div_cls_code1: str,  # 분류구분코드
        dataframe1: Optional[pd.DataFrame] = None,  # 누적 데이터프레임 (output1)
        dataframe2: Optional[pd.DataFrame] = None,  # 누적 데이터프레임 (output2)
        tr_cont: str = "",
        depth: int = 0,
        max_depth: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    [국내주식] 업종/기타 
    금리 종합(국내채권_금리)[국내주식-155]
    금리 종합(국내채권_금리) API를 호출하여 DataFrame으로 반환합니다.
    
    Args:
        fid_cond_mrkt_div_code (str): 조건시장분류코드 (필수)
        fid_cond_scr_div_code (str): 조건화면분류코드 (필수)
        fid_div_cls_code (str): 분류구분코드 (필수)
        fid_div_cls_code1 (str): 분류구분코드 (공백 허용)
        dataframe1 (Optional[pd.DataFrame]): 누적 데이터프레임 (output1)
        dataframe2 (Optional[pd.DataFrame]): 누적 데이터프레임 (output2)
        tr_cont (str): 연속 거래 여부
        depth (int): 현재 재귀 깊이
        max_depth (int): 최대 재귀 깊이 (기본값: 10)
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: 금리 종합(국내채권_금리) 데이터
        
    Example:
        >>> df1, df2 = comp_interest('01', '20702', '1', '')
        >>> print(df1)
        >>> print(df2)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/comp-interest"
    # 로깅 설정
    logger = logging.getLogger(__name__)

    # 필수 파라미터 검증
    if not fid_cond_mrkt_div_code:
        logger.error("fid_cond_mrkt_div_code is required. (e.g. '01')")
        raise ValueError("fid_cond_mrkt_div_code is required. (e.g. '01')")

    if not fid_cond_scr_div_code:
        logger.error("fid_cond_scr_div_code is required. (e.g. '20702')")
        raise ValueError("fid_cond_scr_div_code is required. (e.g. '20702')")

    if not fid_div_cls_code:
        logger.error("fid_div_cls_code is required. (e.g. '1')")
        raise ValueError("fid_div_cls_code is required. (e.g. '1')")

    # 최대 재귀 깊이 체크
    if depth >= max_depth:
        logger.warning("Maximum recursion depth (%d) reached. Stopping further requests.", max_depth)
        return dataframe1 if dataframe1 is not None else pd.DataFrame(), dataframe2 if dataframe2 is not None else pd.DataFrame()

    tr_id = "FHPST07020000"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
        "FID_DIV_CLS_CODE": fid_div_cls_code,
        "FID_DIV_CLS_CODE1": fid_div_cls_code1,
    }

    # API 호출
    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    if res.isOK():
        # output1 처리
        if hasattr(res.getBody(), 'output1'):
            output_data = res.getBody().output1
            if output_data:
                current_data1 = pd.DataFrame(output_data if isinstance(output_data, list) else [output_data])
                dataframe1 = pd.concat([dataframe1, current_data1],
                                       ignore_index=True) if dataframe1 is not None else current_data1
            else:
                dataframe1 = dataframe1 if dataframe1 is not None else pd.DataFrame()

        # output2 처리
        if hasattr(res.getBody(), 'output2'):
            output_data = res.getBody().output2
            if output_data:
                current_data2 = pd.DataFrame(output_data if isinstance(output_data, list) else [output_data])
                dataframe2 = pd.concat([dataframe2, current_data2],
                                       ignore_index=True) if dataframe2 is not None else current_data2
            else:
                dataframe2 = dataframe2 if dataframe2 is not None else pd.DataFrame()

        tr_cont = res.getHeader().tr_cont

        if tr_cont in ["M", "F"]:
            logger.info("Calling next page...")
            ka.smart_sleep()
            return comp_interest(
                fid_cond_mrkt_div_code,
                fid_cond_scr_div_code,
                fid_div_cls_code,
                fid_div_cls_code1,
                "N", dataframe1, dataframe2, depth + 1, max_depth
            )
        else:
            logger.info("Data fetch complete.")
            return dataframe1, dataframe2
    else:
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame(), pd.DataFrame()


##############################################################################################
# [국내주식] 시세분석 > 프로그램매매 종합현황(일별)[국내주식-115]
##############################################################################################

def comp_program_trade_daily(
        fid_cond_mrkt_div_code: str,  # [필수] 조건시장분류코드 (ex. J:주식,NX:NXT,UN:통합)
        fid_mrkt_cls_code: str,  # [필수] 시장구분코드 (ex. K:코스피,Q:코스닥)
        fid_input_date_1: str = "",  # 검색시작일
        fid_input_date_2: str = ""  # 검색종료일
) -> pd.DataFrame:
    """
    프로그램매매 종합현황(일별) API입니다. 
    한국투자 HTS(eFriend Plus) > [0460] 프로그램매매 종합현황 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    
    Args:
        fid_cond_mrkt_div_code (str): [필수] 조건시장분류코드 (ex. J:주식,NX:NXT,UN:통합)
        fid_mrkt_cls_code (str): [필수] 시장구분코드 (ex. K:코스피,Q:코스닥)
        fid_input_date_1 (str): 검색시작일
        fid_input_date_2 (str): 검색종료일

    Returns:
        pd.DataFrame: 프로그램매매 종합현황(일별) 데이터
        
    Example:
        >>> df = comp_program_trade_daily("J", "K", "20250101", "20250617")
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/comp-program-trade-daily"

    if fid_cond_mrkt_div_code == "":
        raise ValueError("fid_cond_mrkt_div_code is required (e.g. 'J:주식,NX:NXT,UN:통합')")

    if fid_mrkt_cls_code == "":
        raise ValueError("fid_mrkt_cls_code is required (e.g. 'K:코스피,Q:코스닥')")

    tr_id = "FHPPG04600001"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_MRKT_CLS_CODE": fid_mrkt_cls_code,
        "FID_INPUT_DATE_1": fid_input_date_1,
        "FID_INPUT_DATE_2": fid_input_date_2
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        return pd.DataFrame(res.getBody().output)
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 시세분석 > 프로그램매매 종합현황(시간) [국내주식-114]
##############################################################################################

def comp_program_trade_today(
        fid_cond_mrkt_div_code: str,  # [필수] 시장 구분 코드 (J:KRX,NX:NXT,UN:통합)
        fid_mrkt_cls_code: str,  # [필수] 시장구분코드 (K:코스피, Q:코스닥)
        fid_sctn_cls_code: str = "",  # 구간 구분 코드
        fid_input_iscd: str = "",  # 입력종목코드
        fid_cond_mrkt_div_code1: str = "",  # 시장분류코드
        fid_input_hour_1: str = ""  # 입력시간
) -> pd.DataFrame:
    """
    프로그램매매 종합현황(시간) API입니다. 
    한국투자 HTS(eFriend Plus) > [0460] 프로그램매매 종합현황 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

    ※ 장시간(09:00~15:30) 동안의 최근 30분간의 데이터 확인이 가능하며, 다음조회가 불가합니다.
    ※ 장시간(09:00~15:30) 이후에는 bsop_hour 에 153000 ~ 170000 까지의 시간데이터가 출력되지만 데이터는 모두 동일한 장마감 데이터인 점 유의 부탁드립니다.
    
    Args:
        fid_cond_mrkt_div_code (str): [필수] 시장 구분 코드 (ex. J:KRX,NX:NXT,UN:통합)
        fid_mrkt_cls_code (str): [필수] 시장구분코드 (ex. K:코스피, Q:코스닥)
        fid_sctn_cls_code (str): 구간 구분 코드
        fid_input_iscd (str): 입력종목코드
        fid_cond_mrkt_div_code1 (str): 시장분류코드
        fid_input_hour_1 (str): 입력시간
        
    Returns:
        pd.DataFrame: 프로그램매매 종합현황 데이터
        
    Example:
        >>> df = comp_program_trade_today("J", "K")
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/comp-program-trade-today"

    # 필수 파라미터 검증
    if fid_cond_mrkt_div_code == "":
        raise ValueError("fid_cond_mrkt_div_code is required (e.g. 'J:KRX,NX:NXT,UN:통합')")

    if fid_mrkt_cls_code == "":
        raise ValueError("fid_mrkt_cls_code is required (e.g. 'K:코스피, Q:코스닥')")

    tr_id = "FHPPG04600101"  # 프로그램매매 종합현황(시간)

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,  # 시장 구분 코드
        "FID_MRKT_CLS_CODE": fid_mrkt_cls_code,  # 시장구분코드
        "FID_SCTN_CLS_CODE": fid_sctn_cls_code,  # 구간 구분 코드
        "FID_INPUT_ISCD": fid_input_iscd,  # 입력종목코드
        "FID_COND_MRKT_DIV_CODE1": fid_cond_mrkt_div_code1,  # 시장분류코드
        "FID_INPUT_HOUR_1": fid_input_hour_1  # 입력시간
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        # array 타입이므로 DataFrame으로 반환
        current_data = pd.DataFrame(res.getBody().output)
        logging.info("Data fetch complete.")
        return current_data
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 순위분석 > 국내주식 신용잔고 상위 [국내주식-109]
##############################################################################################

def credit_balance(
        fid_cond_scr_div_code: str,  # 조건 화면 분류 코드
        fid_input_iscd: str,  # 입력 종목코드
        fid_option: str,  # 증가율기간
        fid_cond_mrkt_div_code: str,  # 조건 시장 분류 코드
        fid_rank_sort_cls_code: str,  # 순위 정렬 구분 코드
        dataframe1: Optional[pd.DataFrame] = None,  # 누적 데이터프레임 (output1)
        dataframe2: Optional[pd.DataFrame] = None,  # 누적 데이터프레임 (output2)
        tr_cont: str = "",
        depth: int = 0,
        max_depth: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    [국내주식] 순위분석 
    국내주식 신용잔고 상위[국내주식-109]
    국내주식 신용잔고 상위 API를 호출하여 DataFrame으로 반환합니다.
    
    Args:
        fid_cond_scr_div_code (str): Unique key(11701)
        fid_input_iscd (str): 0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200,
        fid_option (str): 2~999
        fid_cond_mrkt_div_code (str): 시장구분코드 (주식 J)
        fid_rank_sort_cls_code (str): '(융자)0:잔고비율 상위, 1: 잔고수량 상위, 2: 잔고금액 상위, 3: 잔고비율 증가상위, 4: 잔고비율 감소상위  (대주)5:잔고비율 상위, 6: 잔고수량 상위, 7: 잔고금액 상위, 8: 잔고비율 증가상위, 9: 잔고비율 감소상위 '
        dataframe1 (Optional[pd.DataFrame]): 누적 데이터프레임 (output1)
        dataframe2 (Optional[pd.DataFrame]): 누적 데이터프레임 (output2)
        tr_cont (str): 연속 거래 여부
        depth (int): 현재 재귀 깊이
        max_depth (int): 최대 재귀 깊이 (기본값: 10)
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: 국내주식 신용잔고 상위 데이터
        
    Example:
        >>> df1, df2 = credit_balance('11701', '0000', '2', 'J', '0')
        >>> print(df1)
        >>> print(df2)
    """
    api_url = "/uapi/domestic-stock/v1/ranking/credit-balance"
    # 필수 파라미터 검증
    if not fid_cond_scr_div_code:
        logger.error("fid_cond_scr_div_code is required. (e.g. '11701')")
        raise ValueError("fid_cond_scr_div_code is required. (e.g. '11701')")

    if not fid_input_iscd:
        logger.error("fid_input_iscd is required. (e.g. '0000')")
        raise ValueError("fid_input_iscd is required. (e.g. '0000')")

    if not fid_option:
        logger.error("fid_option is required. (e.g. '2')")
        raise ValueError("fid_option is required. (e.g. '2')")

    if not fid_cond_mrkt_div_code:
        logger.error("fid_cond_mrkt_div_code is required. (e.g. 'J')")
        raise ValueError("fid_cond_mrkt_div_code is required. (e.g. 'J')")

    if fid_rank_sort_cls_code not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
        logger.error("fid_rank_sort_cls_code is required. (e.g. '0')")
        raise ValueError("fid_rank_sort_cls_code is required. (e.g. '0')")

    # 최대 재귀 깊이 체크
    if depth >= max_depth:
        logger.warning("Maximum recursion depth (%d) reached. Stopping further requests.", max_depth)
        return dataframe1 if dataframe1 is not None else pd.DataFrame(), dataframe2 if dataframe2 is not None else pd.DataFrame()

    tr_id = "FHKST17010000"

    params = {
        "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_OPTION": fid_option,
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_RANK_SORT_CLS_CODE": fid_rank_sort_cls_code,
    }

    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    if res.isOK():
        # output1 처리
        if hasattr(res.getBody(), 'output1'):
            output_data = res.getBody().output1
            if output_data:
                # output1은 단일 객체, output2는 배열일 수 있음
                if isinstance(output_data, list):
                    current_data1 = pd.DataFrame(output_data)
                else:
                    # 단일 객체인 경우 리스트로 감싸서 DataFrame 생성
                    current_data1 = pd.DataFrame([output_data])

                if dataframe1 is not None:
                    dataframe1 = pd.concat([dataframe1, current_data1], ignore_index=True)
                else:
                    dataframe1 = current_data1
            else:
                if dataframe1 is None:
                    dataframe1 = pd.DataFrame()
        else:
            if dataframe1 is None:
                dataframe1 = pd.DataFrame()
        # output2 처리
        if hasattr(res.getBody(), 'output2'):
            output_data = res.getBody().output2
            if output_data:
                # output1은 단일 객체, output2는 배열일 수 있음
                if isinstance(output_data, list):
                    current_data2 = pd.DataFrame(output_data)
                else:
                    # 단일 객체인 경우 리스트로 감싸서 DataFrame 생성
                    current_data2 = pd.DataFrame([output_data])

                if dataframe2 is not None:
                    dataframe2 = pd.concat([dataframe2, current_data2], ignore_index=True)
                else:
                    dataframe2 = current_data2
            else:
                if dataframe2 is None:
                    dataframe2 = pd.DataFrame()
        else:
            if dataframe2 is None:
                dataframe2 = pd.DataFrame()
        tr_cont = res.getHeader().tr_cont

        if tr_cont in ["M", "F"]:
            logger.info("Calling next page...")
            ka.smart_sleep()
            return credit_balance(
                fid_cond_scr_div_code,
                fid_input_iscd,
                fid_option,
                fid_cond_mrkt_div_code,
                fid_rank_sort_cls_code,
                "N", dataframe1, dataframe2, depth + 1, max_depth
            )
        else:
            logger.info("Data fetch complete.")
            return dataframe1, dataframe2
    else:
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame(), pd.DataFrame()


##############################################################################################
# [국내주식] 종목정보 > 국내주식 당사 신용가능종목[국내주식-111]
##############################################################################################

def credit_by_company(
        fid_rank_sort_cls_code: str,  # 순위 정렬 구분 코드
        fid_slct_yn: str,  # 선택 여부
        fid_input_iscd: str,  # 입력 종목코드
        fid_cond_scr_div_code: str,  # 조건 화면 분류 코드
        fid_cond_mrkt_div_code: str,  # 조건 시장 분류 코드
        tr_cont: str = "",  # 연속 거래 여부
        dataframe: Optional[pd.DataFrame] = None,  # 누적 데이터프레임
        depth: int = 0,  # 현재 재귀 깊이
        max_depth: int = 10  # 최대 재귀 깊이
) -> Optional[pd.DataFrame]:
    """
    [국내주식] 종목정보 
    국내주식 당사 신용가능종목[국내주식-111]
    국내주식 당사 신용가능종목 API를 호출하여 DataFrame으로 반환합니다.
    
    Args:
        fid_rank_sort_cls_code (str): 0:코드순, 1:이름순
        fid_slct_yn (str): 0:신용주문가능, 1: 신용주문불가
        fid_input_iscd (str): 0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200, 4001: KRX100
        fid_cond_scr_div_code (str): Unique key(20477)
        fid_cond_mrkt_div_code (str): 시장구분코드 (주식 J)
        tr_cont (str): 연속 거래 여부
        dataframe (Optional[pd.DataFrame]): 누적 데이터프레임
        depth (int): 현재 재귀 깊이
        max_depth (int): 최대 재귀 깊이 (기본값: 10)
        
    Returns:
        Optional[pd.DataFrame]: 국내주식 당사 신용가능종목 데이터
        
    Example:
        >>> df = credit_by_company(
        ...     fid_rank_sort_cls_code="1",
        ...     fid_slct_yn="0",
        ...     fid_input_iscd="0000",
        ...     fid_cond_scr_div_code="20477",
        ...     fid_cond_mrkt_div_code="J"
        ... )
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/credit-by-company"
    # 로깅 설정
    logger = logging.getLogger(__name__)

    # 필수 파라미터 검증
    if not fid_rank_sort_cls_code:
        logger.error("fid_rank_sort_cls_code is required. (e.g. '1')")
        raise ValueError("fid_rank_sort_cls_code is required. (e.g. '1')")

    if not fid_slct_yn:
        logger.error("fid_slct_yn is required. (e.g. '0')")
        raise ValueError("fid_slct_yn is required. (e.g. '0')")

    if not fid_input_iscd:
        logger.error("fid_input_iscd is required. (e.g. '0000')")
        raise ValueError("fid_input_iscd is required. (e.g. '0000')")

    if not fid_cond_scr_div_code:
        logger.error("fid_cond_scr_div_code is required. (e.g. '20477')")
        raise ValueError("fid_cond_scr_div_code is required. (e.g. '20477')")

    if not fid_cond_mrkt_div_code:
        logger.error("fid_cond_mrkt_div_code is required. (e.g. 'J')")
        raise ValueError("fid_cond_mrkt_div_code is required. (e.g. 'J')")

    # 최대 재귀 깊이 체크
    if depth >= max_depth:
        logger.warning("Maximum recursion depth (%d) reached. Stopping further requests.", max_depth)
        return dataframe if dataframe is not None else pd.DataFrame()

    # API 호출 URL 및 ID 설정

    tr_id = "FHPST04770000"

    # 요청 파라미터 설정
    params = {
        "fid_rank_sort_cls_code": fid_rank_sort_cls_code,
        "fid_slct_yn": fid_slct_yn,
        "fid_input_iscd": fid_input_iscd,
        "fid_cond_scr_div_code": fid_cond_scr_div_code,
        "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
    }

    # API 호출
    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    # API 호출 성공 시 데이터 처리
    if res.isOK():
        if hasattr(res.getBody(), 'output'):
            output_data = res.getBody().output
            if not isinstance(output_data, list):
                output_data = [output_data]
            current_data = pd.DataFrame(output_data)
        else:
            current_data = pd.DataFrame()

        # 기존 데이터프레임과 병합
        if dataframe is not None:
            dataframe = pd.concat([dataframe, current_data], ignore_index=True)
        else:
            dataframe = current_data

        # 연속 거래 여부 확인
        tr_cont = res.getHeader().tr_cont

        # 다음 페이지 호출
        if tr_cont == "M":
            logger.info("Calling next page...")
            ka.smart_sleep()
            return credit_by_company(
                fid_rank_sort_cls_code,
                fid_slct_yn,
                fid_input_iscd,
                fid_cond_scr_div_code,
                fid_cond_mrkt_div_code,
                "N", dataframe, depth + 1, max_depth
            )
        else:
            logger.info("Data fetch complete.")
            return dataframe
    else:
        # API 호출 실패 시 에러 로그 출력
        logger.error("API call failed: %s - %s", res.getErrorCode(), res.getErrorMessage())
        res.printError(api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 시세분석 > 국내주식 신용잔고 일별추이[국내주식-110]
##############################################################################################

def daily_credit_balance(
        fid_cond_mrkt_div_code: str,  # [필수] 시장 분류 코드
        fid_cond_scr_div_code: str,  # [필수] 화면 분류 코드
        fid_input_iscd: str,  # [필수] 종목코드
        fid_input_date_1: str,  # [필수] 결제일자
        tr_cont: str = "",  # 연속 거래 여부
        dataframe: Optional[pd.DataFrame] = None,  # 누적 데이터프레임
        depth: int = 0,  # 내부 재귀깊이 (자동관리)
        max_depth: int = 10  # 최대 재귀 횟수 제한
) -> pd.DataFrame:
    """
    국내주식 신용잔고 일별추이 API입니다.
    한국투자 HTS(eFriend Plus) > [0476] 국내주식 신용잔고 일별추이 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    한 번의 호출에 최대 30건 확인 가능하며, fid_input_date_1 을 입력하여 다음 조회가 가능합니다.
    
    ※ 상환수량은 "매도상환수량+현금상환수량"의 합계 수치입니다.
    
    Args:
        fid_cond_mrkt_div_code (str): [필수] 시장 분류 코드 (ex. J: 주식)
        fid_cond_scr_div_code (str): [필수] 화면 분류 코드 (ex. 20476)
        fid_input_iscd (str): [필수] 종목코드 (ex. 005930)
        fid_input_date_1 (str): [필수] 결제일자 (ex. 20240313)
        tr_cont (str): 연속 거래 여부
        dataframe (Optional[pd.DataFrame]): 누적 데이터프레임
        depth (int): 내부 재귀깊이 (자동관리)
        max_depth (int): 최대 재귀 횟수 제한

    Returns:
        pd.DataFrame: 국내주식 신용잔고 일별추이 데이터
        
    Example:
        >>> df = daily_credit_balance("J", "20476", "005930", "20240313")
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/daily-credit-balance"

    if fid_cond_mrkt_div_code == "":
        raise ValueError("fid_cond_mrkt_div_code is required (e.g. 'J')")

    if fid_cond_scr_div_code == "":
        raise ValueError("fid_cond_scr_div_code is required (e.g. '20476')")

    if fid_input_iscd == "":
        raise ValueError("fid_input_iscd is required (e.g. '005930')")

    if fid_input_date_1 == "":
        raise ValueError("fid_input_date_1 is required (e.g. '20240313')")

    if depth > max_depth:
        logging.warning("Max recursive depth reached.")
        if dataframe is None:
            return pd.DataFrame()
        else:
            return dataframe

    tr_id = "FHPST04760000"  # 국내주식 신용잔고 일별추이

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,  # 시장 분류 코드
        "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,  # 화면 분류 코드
        "FID_INPUT_ISCD": fid_input_iscd,  # 종목코드
        "FID_INPUT_DATE_1": fid_input_date_1  # 결제일자
    }

    res = ka._url_fetch(api_url, tr_id, tr_cont, params)

    if res.isOK():
        current_data = pd.DataFrame(res.getBody().output)

        if dataframe is not None:
            dataframe = pd.concat([dataframe, current_data], ignore_index=True)
        else:
            dataframe = current_data

        tr_cont = res.getHeader().tr_cont

        if tr_cont in ["M", "F"]:  # 다음 페이지 존재
            logging.info("Call Next page...")
            ka.smart_sleep()  # 시스템 안정적 운영을 위한 지연
            return daily_credit_balance(
                fid_cond_mrkt_div_code, fid_cond_scr_div_code, fid_input_iscd, fid_input_date_1, "N", dataframe,
                depth + 1, max_depth
            )
        else:
            logging.info("Data fetch complete.")
            return dataframe
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 시세분석 > 종목별 일별 대차거래추이 [국내주식-135]
##############################################################################################

def daily_loan_trans(
        mrkt_div_cls_code: str,  # [필수] 조회구분 (ex. 1:코스피,2:코스닥,3:종목)
        mksc_shrn_iscd: str,  # [필수] 종목코드 (ex. 123456)
        start_date: str = "",  # 시작일자
        end_date: str = "",  # 종료일자
        cts: str = ""  # 이전조회KEY
) -> pd.DataFrame:
    """
    종목별 일별 대차거래추이 API입니다.
    한 번의 조회에 최대 100건까지 조회 가능하며, start_date, end_date 를 수정하여 다음 조회가 가능합니다.
    
    Args:
        mrkt_div_cls_code (str): [필수] 조회구분 (ex. 1:코스피,2:코스닥,3:종목)
        mksc_shrn_iscd (str): [필수] 종목코드 (ex. 123456)
        start_date (str): 시작일자
        end_date (str): 종료일자
        cts (str): 이전조회KEY

    Returns:
        pd.DataFrame: 종목별 일별 대차거래추이 데이터
        
    Example:
        >>> df = daily_loan_trans(mrkt_div_cls_code="1", mksc_shrn_iscd="005930")
        >>> print(df)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/daily-loan-trans"

    # 필수 파라미터 검증
    if mrkt_div_cls_code == "":
        raise ValueError("mrkt_div_cls_code is required (e.g. '1', '2', '3')")

    if mksc_shrn_iscd == "":
        raise ValueError("mksc_shrn_iscd is required (e.g. '123456')")

    tr_id = "HHPST074500C0"

    params = {
        "MRKT_DIV_CLS_CODE": mrkt_div_cls_code,
        "MKSC_SHRN_ISCD": mksc_shrn_iscd,
        "START_DATE": start_date,
        "END_DATE": end_date,
        "CTS": cts
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        result_data = pd.DataFrame(res.getBody().output1)
        return result_data
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 시세분석 > 국내주식 공매도 일별추이[국내주식-134]
##############################################################################################

def daily_short_sale(
        fid_cond_mrkt_div_code: str,  # [필수] 시장분류코드 (ex. J:주식)
        fid_input_iscd: str,  # [필수] 종목코드 (ex. 123456)
        fid_input_date_1: str = "",  # 시작일자
        fid_input_date_2: str = ""  # 종료일자
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    국내주식 공매도 일별추이를 조회합니다.
    
    Args:
        fid_cond_mrkt_div_code (str): [필수] 시장분류코드 (ex. J:주식)
        fid_input_iscd (str): [필수] 종목코드 (ex. 123456)
        fid_input_date_1 (str): 시작일자
        fid_input_date_2 (str): 종료일자

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (output1, output2) 데이터프레임 쌍
        
    Example:
        >>> df1, df2 = daily_short_sale("J", "005930", "20240301", "20240328")
        >>> print(df1)
        >>> print(df2)
    """
    api_url = "/uapi/domestic-stock/v1/quotations/daily-short-sale"

    # 필수 파라미터 검증
    if fid_cond_mrkt_div_code == "":
        raise ValueError("fid_cond_mrkt_div_code is required (e.g. 'J:주식')")

    if fid_input_iscd == "":
        raise ValueError("fid_input_iscd is required (e.g. '123456')")

    tr_id = "FHPST04830000"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_INPUT_DATE_1": fid_input_date_1,
        "FID_INPUT_DATE_2": fid_input_date_2
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        # output1 처리 (object 타입 -> DataFrame)
        output1_data = pd.DataFrame(res.getBody().output1, index=[0])

        # output2 처리 (array 타입 -> DataFrame)
        output2_data = pd.DataFrame(res.getBody().output2)

        return output1_data, output2_data
    else:
        res.printError(url=api_url)
        return pd.DataFrame(), pd.DataFrame()


##############################################################################################
# [국내주식] 순위분석 > 국내주식 이격도 순위 [v1_국내주식-095]
##############################################################################################

def disparity(
        fid_input_price_2: str  # 입력 가격2
) -> pd.DataFrame:
    """
    [국내주식] 순위분석 > 국내주식 이격도 순위 [v1_국내주식-095]
    
    # TODO: 함수 구현 필요
    """
    raise NotImplementedError("disparity function is not yet implemented")

##############################################################################################
# [국내주식] 순위분석 > 거래량/거래대금 순위[v1_국내주식-047] - ADDED BY BOMI
##############################################################################################
def inquire_transaction_rank(
        fid_cond_mrkt_div_code: str,      # 조건 시장 분류 코드 (J: 주식)
        fid_cond_scr_div_code: str,       # 조건 화면 분류 코드 (21010: 거래대금상위, 21011: 거래량상위)
        fid_input_iscd: str,              # 입력 종목코드 (0000: 전체)
        fid_vol_cnt: str,                 # 거래량 수 (e.g., "100")
        fid_rank_sort_cls_code: str = "0" # 순위 정렬 구분 코드
) -> Tuple[int, Optional[pd.DataFrame]]:
    """
    [국내주식] 순위분석
    거래량/거래대금 순위[v1_국내주식-047]
    거래량 또는 거래대금 상위 종목 API를 호출하여 DataFrame으로 반환합니다.
    (Bomi가 추가한 함수입니다)

    Args:
        fid_cond_mrkt_div_code (str): 시장구분코드 (주식 J)
        fid_cond_scr_div_code (str): 화면분류코드 (21010: 거래대금, 21011: 거래량)
        fid_input_iscd (str): 종목코드 (0000:전체, 0001:거래소, 1001:코스닥)
        fid_vol_cnt (str): 조회할 상위 N개 (e.g., "100")
        fid_rank_sort_cls_code (str): 순위 정렬 구분 코드

    Returns:
        Tuple[int, Optional[pd.DataFrame]]: (리턴코드, 순위 데이터프레임). 성공 시 0, 실패 시 -1.
    """
    api_url = "/uapi/domestic-stock/v1/ranking/transaction"
    tr_id = "FHPST01710000"

    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_VOL_CNT": fid_vol_cnt,
        "FID_RANK_SORT_CLS_CODE": fid_rank_sort_cls_code
    }

    res = ka._url_fetch(api_url, tr_id, "", params)

    if res.isOK():
        return 0, pd.DataFrame(res.getBody().output)
    else:
        res.printError(url=api_url)
        return -1, pd.DataFrame()


##############################################################################################
# [국내주식] 기본시세 > 주식현재가 시세[v1_국내주식-008]
# From examples_llm - Added for compatibility
##############################################################################################

def inquire_price(
    env_dv: str,
    fid_cond_mrkt_div_code: str,
    fid_input_iscd: str
) -> pd.DataFrame:
    """주식 현재가 시세 API"""
    api_url = "/uapi/domestic-stock/v1/quotations/inquire-price"
    
    if env_dv == "real":
        tr_id = "FHKST01010100"
    elif env_dv == "demo":
        tr_id = "FHKST01010100"
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")
    
    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_INPUT_ISCD": fid_input_iscd
    }
    
    res = ka._url_fetch(api_url, tr_id, "", params)
    
    if res.isOK():
        return pd.DataFrame(res.getBody().output, index=[0])
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 기본시세 > 주식현재가 일자별[v1_국내주식-010]  
# From examples_llm - Added for compatibility
##############################################################################################

def inquire_daily_price(
    env_dv: str,
    fid_cond_mrkt_div_code: str,
    fid_input_iscd: str,
    fid_period_div_code: str,
    fid_org_adj_prc: str
) -> pd.DataFrame:
    """주식현재가 일자별 API"""
    api_url = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    
    if env_dv == "real":
        tr_id = "FHKST01010400"
    elif env_dv == "demo":
        tr_id = "FHKST01010400"
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")
    
    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_PERIOD_DIV_CODE": fid_period_div_code,
        "FID_ORG_ADJ_PRC": fid_org_adj_prc
    }
    
    res = ka._url_fetch(api_url, tr_id, "", params)
    
    if res.isOK():
        return pd.DataFrame(res.getBody().output)
    else:
        res.printError(url=api_url)
        return pd.DataFrame()


##############################################################################################
# [국내주식] 주문/계좌 > 주식주문(현금)[v1_국내주식-001]
# From examples_llm - Added for compatibility
##############################################################################################

def order_cash(
    cano: str,
    acnt_prdt_cd: str,
    pdno: str,
    ord_dvsn: str,
    ord_qty: str,
    ord_unpr: str,
    env_dv: str = "real"
) -> dict:
    """주식주문(현금) API"""
    api_url = "/uapi/domestic-stock/v1/trading/order-cash"
    
    if env_dv == "real":
        tr_id = "TTTC0802U"  # 매수: TTTC0802U, 매도: TTTC0801U
    elif env_dv == "demo":
        tr_id = "VTTC0802U"  # 매수: VTTC0802U, 매도: VTTC0801U
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")
    
    body = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "PDNO": pdno,
        "ORD_DVSN": ord_dvsn,
        "ORD_QTY": ord_qty,
        "ORD_UNPR": ord_unpr
    }
    
    res = ka._url_post(api_url, tr_id, body)
    
    if res.isOK():
        return res.getBody().__dict__
    else:
        res.printError(url=api_url)
        return {}


##############################################################################################
# [국내주식] 주문/계좌 > 주식잔고조회[v1_국내주식-006]
# From examples_llm - Added for compatibility
##############################################################################################

def inquire_balance(
    env_dv: str,
    cano: str,
    acnt_prdt_cd: str,
    afhr_flpr_yn: str = "N",
    inqr_dvsn: str = "01",
    unpr_dvsn: str = "01",
    fund_sttl_icld_yn: str = "N",
    fncg_amt_auto_rdpt_yn: str = "N",
    prcs_dvsn: str = "00",
    ctx_area_fk100: str = "",
    ctx_area_nk100: str = ""
):
    """주식잔고조회 API - Returns (output1, output2)"""
    api_url = "/uapi/domestic-stock/v1/trading/inquire-balance"
    
    if env_dv == "real":
        tr_id = "TTTC8434R"
    elif env_dv == "demo":
        tr_id = "VTTC8434R"
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")
    
    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "AFHR_FLPR_YN": afhr_flpr_yn,
        "INQR_DVSN": inqr_dvsn,
        "UNPR_DVSN": unpr_dvsn,
        "FUND_STTL_ICLD_YN": fund_sttl_icld_yn,
        "FNCG_AMT_AUTO_RDPT_YN": fncg_amt_auto_rdpt_yn,
        "PRCS_DVSN": prcs_dvsn,
        "CTX_AREA_FK100": ctx_area_fk100,
        "CTX_AREA_NK100": ctx_area_nk100
    }
    
    res = ka._url_fetch(api_url, tr_id, "", params)
    
    if res.isOK():
        output1 = pd.DataFrame(res.getBody().output1)
        output2 = pd.DataFrame(res.getBody().output2, index=[0]) if hasattr(res.getBody(), 'output2') else pd.DataFrame()
        return output1, output2
    else:
        res.printError(url=api_url)
        return pd.DataFrame(), pd.DataFrame()


##############################################################################################
# [국내주식] 기본시세 > 주식현재가 투자자[v1_국내주식-012]
# From examples_llm - Added for compatibility
##############################################################################################

def inquire_investor(
    env_dv: str,
    fid_cond_mrkt_div_code: str,
    fid_input_iscd: str
) -> pd.DataFrame:
    """주식현재가 투자자 API"""
    api_url = "/uapi/domestic-stock/v1/quotations/inquire-investor"
    
    if env_dv == "real":
        tr_id = "FHKST01010900"
    elif env_dv == "demo":
        tr_id = "FHKST01010900"
    else:
        raise ValueError("env_dv can only be 'real' or 'demo'")
    
    params = {
        "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
        "FID_INPUT_ISCD": fid_input_iscd
    }
    
    res = ka._url_fetch(api_url, tr_id, "", params)
    
    if res.isOK():
        return pd.DataFrame(res.getBody().output, index=[0])
    else:
        res.printError(url=api_url)
        return pd.DataFrame()

