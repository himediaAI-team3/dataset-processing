from datasets import load_from_disk
import pandas as pd

try:
    print("=== OUTPUT 컬럼 내용 상세 분석 ===")
    
    # 데이터셋 로드
    dataset = load_from_disk('.')
    
    # TEST 데이터 분석
    test_data = dataset['test']
    print(f"TEST 데이터 총 샘플 수: {len(test_data)}")
    
    # 각 라벨별로 output 내용 확인
    labels = test_data['label']
    outputs = test_data['output']
    
    unique_labels = list(set(labels))
    print(f"\n고유 라벨: {unique_labels}")
    
    for label in unique_labels:
        print(f"\n{'='*50}")
        print(f"라벨: {label}")
        print(f"{'='*50}")
        
        # 해당 라벨의 인덱스 찾기
        label_indices = [i for i, l in enumerate(labels) if l == label]
        print(f"샘플 수: {len(label_indices)}개")
        
        # 처음 3개 샘플의 output 확인
        for i, idx in enumerate(label_indices[:3]):
            output_content = outputs[idx]
            print(f"\n--- {label} 샘플 {i+1} ---")
            
            # output이 비어있는지 확인
            if not output_content or output_content.strip() == "":
                print("❌ OUTPUT이 비어있습니다!")
            else:
                print("✅ OUTPUT이 채워져 있습니다.")
                print(f"길이: {len(output_content)} 문자")
                print(f"내용 미리보기: {output_content[:200]}...")
                
                # XML 태그 확인
                if '<label>' in output_content and '<summary>' in output_content:
                    print("✅ 올바른 XML 형식 포함")
                else:
                    print("⚠️ XML 형식이 완전하지 않을 수 있음")
        
        # 해당 라벨의 모든 output이 채워져 있는지 확인
        empty_count = 0
        for idx in label_indices:
            if not outputs[idx] or outputs[idx].strip() == "":
                empty_count += 1
        
        print(f"\n📊 {label} 라벨 통계:")
        print(f"  - 전체 샘플: {len(label_indices)}개")
        print(f"  - 비어있는 output: {empty_count}개")
        print(f"  - 채워진 output: {len(label_indices) - empty_count}개")
        
        if empty_count == 0:
            print("✅ 모든 output이 채워져 있습니다!")
        else:
            print(f"❌ {empty_count}개의 output이 비어있습니다!")

except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()



