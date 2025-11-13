import pandas as pd
import sys

try:
    print("파일 읽기 시작...")
    # parquet 파일 읽기
    df = pd.read_parquet('test-00000-of-00003.parquet')
    print(f"데이터 로드 완료! 행 수: {len(df)}, 열 수: {len(df.columns)}")
    
    # 데이터셋 구조 확인
    print("\n=== 데이터셋 정보 ===")
    print(f"컬럼명: {list(df.columns)}")
    print(f"데이터 타입:")
    print(df.dtypes)
    
    # 첫 몇 개 샘플 보기
    print("\n=== 첫 5개 샘플 ===")
    print(df.head())
    
    # 각 컬럼별 샘플 데이터 출력
    print(f"\n'text' 컬럼이 없습니다. 사용 가능한 컬럼: {list(df.columns)}")
    
    # system_prompt 컬럼 샘플
    if 'system_prompt' in df.columns:
        print(f"\n=== 'system_prompt' 컬럼 샘플 ===")
        print(df['system_prompt'].iloc[0])
        print("-" * 50)
    
    # label 컬럼 샘플
    if 'label' in df.columns:
        print(f"\n=== 'label' 컬럼 샘플 (첫 5개) ===")
        print(df['label'].head().tolist())
        print("-" * 50)
    
    # output 컬럼 샘플 (텍스트 데이터로 보임)
    if 'output' in df.columns:
        print(f"\n=== 'output' 컬럼 샘플 (첫 3개) ===")
        for i, output in enumerate(df['output'].head(3)):
            print(f"샘플 {i+1}:")
            print(str(output)[:300] + "..." if len(str(output)) > 300 else str(output))
            print("-" * 50)
    
    # image 컬럼 정보
    if 'image' in df.columns:
        print(f"\n=== 'image' 컬럼 정보 ===")
        sample_image = df['image'].iloc[0]
        if isinstance(sample_image, dict) and 'bytes' in sample_image:
            print(f"이미지 바이트 크기: {len(sample_image['bytes'])} bytes")
            print("이미지는 바이너리 데이터로 저장되어 있습니다.")
        else:
            print(f"이미지 데이터 타입: {type(sample_image)}")
            print(f"샘플: {str(sample_image)[:100]}...")
        print("-" * 50)
            
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()