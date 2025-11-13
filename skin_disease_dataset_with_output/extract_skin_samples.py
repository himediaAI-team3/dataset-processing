import pandas as pd
import os
import re

def extract_summary_from_output(output_text):
    """output 텍스트에서 <summary> 태그 내용을 추출"""
    if not output_text:
        return None
    
    # <summary>...</summary> 패턴 찾기
    summary_match = re.search(r'<summary>(.*?)</summary>', output_text, re.DOTALL)
    if summary_match:
        return summary_match.group(1).strip()
    else:
        # <summary> 태그가 없으면 전체 텍스트 반환
        return output_text.strip()

def main():
    # 목표 피부질환 라벨들
    target_diseases = ['건선', '아토피', '여드름', '주사', '지루', '정상']
    
    # parquet 파일들
    parquet_files = [
        'test-00000-of-00003.parquet',
        'test-00001-of-00003.parquet', 
        'test-00002-of-00003.parquet'
    ]
    
    print("=== 6개 피부질환 샘플 데이터 추출 ===")
    print(f"목표 질환: {target_diseases}")
    print(f"검색할 파일: {parquet_files}")
    print()
    
    # 각 질환별로 찾은 샘플 저장
    found_samples = {}
    
    # 각 parquet 파일을 순회
    for file_name in parquet_files:
        if not os.path.exists(file_name):
            print(f"[오류] {file_name} 파일을 찾을 수 없습니다.")
            continue
            
        print(f"[파일] {file_name} 분석 중...")
        
        try:
            # parquet 파일 읽기
            df = pd.read_parquet(file_name)
            print(f"   - 총 {len(df)}개 샘플 로드")
            print(f"   - 컬럼: {list(df.columns)}")
            
            # 이 파일에서 찾을 수 있는 라벨들 확인
            if 'label' in df.columns:
                unique_labels = df['label'].unique()
                print(f"   - 발견된 라벨: {list(unique_labels)}")
                
                # 각 목표 질환에 대해 샘플 찾기
                for disease in target_diseases:
                    # 이미 해당 질환의 샘플을 찾았다면 스킵
                    if disease in found_samples:
                        continue
                        
                    # 해당 질환의 데이터 찾기
                    disease_data = df[df['label'] == disease]
                    
                    if len(disease_data) > 0:
                        # 첫 번째 샘플 선택
                        sample = disease_data.iloc[0]
                        
                        # output에서 summary 추출
                        output_text = sample.get('output', '')
                        summary = extract_summary_from_output(output_text)
                        
                        # 샘플 정보 저장
                        found_samples[disease] = {
                            'label': sample['label'],
                            'summary': summary,
                            'source_file': file_name,
                            'full_output': output_text
                        }
                        
                        print(f"   [성공] '{disease}' 샘플 발견!")
            
            print()
            
        except Exception as e:
            print(f"   [오류] {file_name} 읽기 실패: {e}")
            print()
    
    # 결과 출력
    print("=" * 60)
    print("[결과] 추출된 샘플 데이터")
    print("=" * 60)
    
    for i, disease in enumerate(target_diseases, 1):
        print(f"\n{i}. [{disease}]")
        
        if disease in found_samples:
            sample = found_samples[disease]
            print(f"   출처: {sample['source_file']}")
            print(f"   라벨: {sample['label']}")
            print(f"   요약:")
            
            summary = sample['summary']
            if summary:
                # 전체 요약 출력 (길이 제한 없음)
                print(f"      {summary}")
            else:
                print("      (요약 없음)")
        else:
            print("   [실패] 샘플을 찾을 수 없습니다.")
    
    # 통계 출력
    print(f"\n[통계] 결과:")
    print(f"   - 목표 질환 수: {len(target_diseases)}")
    print(f"   - 찾은 샘플 수: {len(found_samples)}")
    print(f"   - 성공률: {len(found_samples)}/{len(target_diseases)} ({len(found_samples)/len(target_diseases)*100:.1f}%)")
    
    if len(found_samples) == len(target_diseases):
        print("\n[성공] 모든 피부질환 샘플을 성공적으로 찾았습니다!")
    else:
        missing = [d for d in target_diseases if d not in found_samples]
        print(f"\n[경고] 찾지 못한 질환: {missing}")
    
    # 각 질환별로 txt 파일로 저장
    print("\n" + "=" * 60)
    print("[저장] 각 질환별 txt 파일 생성 중...")
    print("=" * 60)
    
    for disease, sample in found_samples.items():
        filename = f"{disease}_sample.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"질환명: {sample['label']}\n")
                f.write(f"출처 파일: {sample['source_file']}\n")
                f.write(f"생성 시간: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write("요약 내용:\n")
                f.write(sample['summary'] if sample['summary'] else "(요약 없음)")
                f.write("\n\n" + "=" * 50 + "\n")
                f.write("전체 Output 내용:\n")
                f.write(sample['full_output'] if sample['full_output'] else "(출력 없음)")
            
            print(f"   [완료] {filename} 저장됨")
            
        except Exception as e:
            print(f"   [오류] {filename} 저장 실패: {e}")
    
    print(f"\n[완료] 총 {len(found_samples)}개의 txt 파일이 생성되었습니다.")
    
    return found_samples

if __name__ == "__main__":
    samples = main()
