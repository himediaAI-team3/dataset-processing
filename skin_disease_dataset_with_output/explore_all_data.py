import pandas as pd
from datasets import load_from_disk
import os

try:
    print("=== 전체 데이터셋 탐색 ===")
    
    # 현재 디렉토리에서 데이터셋 로드 시도
    dataset = load_from_disk('.')
    
    print(f"데이터셋 분할: {list(dataset.keys())}")
    
    # 각 분할별 정보 확인
    for split_name in dataset.keys():
        split_data = dataset[split_name]
        print(f"\n=== {split_name.upper()} 데이터 ===")
        print(f"샘플 수: {len(split_data)}")
        print(f"컬럼: {split_data.column_names}")
        
        # 라벨 분포 확인
        if 'label' in split_data.column_names:
            labels = split_data['label']
            unique_labels = list(set(labels))
            print(f"고유 라벨: {unique_labels}")
            
            # 각 라벨별 개수 세기
            label_counts = {}
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
            
            print("라벨별 개수:")
            for label, count in sorted(label_counts.items()):
                print(f"  {label}: {count}개")
        
        # 첫 번째 샘플 확인
        if len(split_data) > 0:
            first_sample = split_data[0]
            print(f"\n첫 번째 샘플:")
            for key, value in first_sample.items():
                if key == 'image':
                    print(f"  {key}: <이미지 데이터>")
                elif key == 'output':
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")
        
        print("-" * 60)

except Exception as e:
    print(f"datasets 라이브러리로 로드 실패: {e}")
    print("\n=== 개별 파일 확인 방식으로 전환 ===")
    
    # 개별 parquet 파일들 확인
    parquet_files = []
    for file in os.listdir('.'):
        if file.endswith('.parquet'):
            parquet_files.append(file)
    
    print(f"발견된 parquet 파일들: {parquet_files}")
    
    # 각 parquet 파일 분석
    for file in parquet_files:
        try:
            print(f"\n=== {file} 분석 ===")
            df = pd.read_parquet(file)
            print(f"행 수: {len(df)}")
            print(f"컬럼: {list(df.columns)}")
            
            if 'label' in df.columns:
                unique_labels = df['label'].unique()
                print(f"고유 라벨: {list(unique_labels)}")
                
                label_counts = df['label'].value_counts()
                print("라벨별 개수:")
                for label, count in label_counts.items():
                    print(f"  {label}: {count}개")
            
        except Exception as file_error:
            print(f"{file} 읽기 실패: {file_error}")



