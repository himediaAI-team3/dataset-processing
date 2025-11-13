import pandas as pd
import re
import os

def extract_cosmetic_info(embedding_text):
    """
    임베딩_텍스트에서 주요 효능, 케어 증상, 핵심 성분, 텍스트 설명을 추출하는 함수
    """
    if pd.isna(embedding_text) or not isinstance(embedding_text, str):
        return {
            '주요_효능': '',
            '케어_증상': '',
            '핵심_성분': '',
            '텍스트_설명': ''
        }
    
    # 기본값 설정
    result = {
        '주요_효능': '',
        '케어_증상': '',
        '핵심_성분': '',
        '텍스트_설명': ''
    }
    
    # 주요 효능 추출
    efficacy_pattern = r'\[주요\s*효능[:\s]*([^\]]+)\]'
    efficacy_match = re.search(efficacy_pattern, embedding_text)
    if efficacy_match:
        result['주요_효능'] = efficacy_match.group(1).strip()
    
    # 케어 증상 추출
    care_pattern = r'\[케어\s*증상[:\s]*([^\]]+)\]'
    care_match = re.search(care_pattern, embedding_text)
    if care_match:
        result['케어_증상'] = care_match.group(1).strip()
    
    # 핵심 성분 추출
    ingredient_pattern = r'\[핵심\s*성분[:\s]*([^\]]+)\]'
    ingredient_match = re.search(ingredient_pattern, embedding_text)
    if ingredient_match:
        result['핵심_성분'] = ingredient_match.group(1).strip()
    
    # 텍스트 설명 추출 (모든 대괄호 패턴 이후의 텍스트)
    # 모든 대괄호 패턴을 찾아서 제거하고 남은 텍스트를 설명으로 사용
    text_copy = embedding_text
    
    # 대괄호로 둘러싸인 모든 패턴 제거
    bracket_patterns = [
        r'\[제품유형[^\]]*\]',
        r'\[피부타입[^\]]*\]', 
        r'\[관련\s*피부질환[^\]]*\]',
        r'\[주요\s*효능[^\]]*\]',
        r'\[케어\s*증상[^\]]*\]',
        r'\[핵심\s*성분[^\]]*\]'
    ]
    
    for pattern in bracket_patterns:
        text_copy = re.sub(pattern, '', text_copy)
    
    # 앞뒤 공백 및 줄바꿈 제거
    text_copy = text_copy.strip()
    # 연속된 공백이나 줄바꿈을 하나로 정리
    text_copy = re.sub(r'\s+', ' ', text_copy)
    
    result['텍스트_설명'] = text_copy
    
    return result

def process_cosmetic_data(input_file_path, output_file_path=None):
    """
    화장품 데이터를 가공하여 새로운 컬럼들을 추가하는 함수
    """
    try:
        # 엑셀 파일 읽기
        print("엑셀 파일을 읽는 중...")
        df = pd.read_excel(input_file_path)
        
        print(f"원본 데이터 크기: {df.shape}")
        print(f"컬럼명: {list(df.columns)}")
        
        # 임베딩_텍스트 컬럼이 있는지 확인
        if '임베딩_텍스트' not in df.columns:
            print("경고: '임베딩_텍스트' 컬럼을 찾을 수 없습니다.")
            print("사용 가능한 컬럼:", list(df.columns))
            return None
        
        # 샘플 데이터 확인
        print("\n임베딩_텍스트 샘플:")
        for i in range(min(3, len(df))):
            if pd.notna(df.iloc[i]['임베딩_텍스트']):
                print(f"샘플 {i+1}:")
                print(df.iloc[i]['임베딩_텍스트'][:200] + "...")
                print("-" * 50)
        
        # 새로운 컬럼들 추출
        print("\n데이터 가공 중...")
        extracted_data = []
        
        for idx, row in df.iterrows():
            if idx % 100 == 0:
                print(f"진행률: {idx}/{len(df)}")
            
            embedding_text = row['임베딩_텍스트']
            extracted_info = extract_cosmetic_info(embedding_text)
            extracted_data.append(extracted_info)
        
        # 새로운 컬럼들을 데이터프레임에 추가
        for key in ['주요_효능', '케어_증상', '핵심_성분', '텍스트_설명']:
            df[key] = [item[key] for item in extracted_data]
        
        # 출력 파일 경로 설정
        if output_file_path is None:
            base_name = os.path.splitext(input_file_path)[0]
            output_file_path = f"{base_name}_processed_with_columns.xlsx"
        
        # 결과 저장
        print(f"\n가공된 데이터를 저장 중: {output_file_path}")
        df.to_excel(output_file_path, index=False)
        
        print(f"완료! 새로운 파일이 저장되었습니다: {output_file_path}")
        print(f"최종 데이터 크기: {df.shape}")
        print(f"새로 추가된 컬럼: 주요_효능, 케어_증상, 핵심_성분, 텍스트_설명")
        
        # 추출 결과 샘플 출력
        print("\n추출 결과 샘플:")
        for i in range(min(3, len(df))):
            print(f"\n샘플 {i+1}:")
            print(f"주요_효능: {df.iloc[i]['주요_효능']}")
            print(f"케어_증상: {df.iloc[i]['케어_증상']}")
            print(f"핵심_성분: {df.iloc[i]['핵심_성분']}")
            print(f"텍스트_설명: {df.iloc[i]['텍스트_설명'][:100]}...")
            print("-" * 50)
        
        return df
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    # 입력 파일 경로
    input_file = "cosmetic_data.xlsx"
    
    # 파일이 존재하는지 확인
    if not os.path.exists(input_file):
        print(f"파일을 찾을 수 없습니다: {input_file}")
        print("현재 디렉토리의 파일들:")
        for file in os.listdir("."):
            if file.endswith(('.xlsx', '.csv')):
                print(f"  - {file}")
    else:
        # 데이터 가공 실행
        result_df = process_cosmetic_data(input_file)
        
        if result_df is not None:
            print("\n데이터 가공이 성공적으로 완료되었습니다!")
        else:
            print("\n데이터 가공 중 오류가 발생했습니다.")
