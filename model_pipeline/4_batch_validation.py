#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 Validation 배치 테스트 스크립트
- 60개 이미지를 순차적으로 API에 전송
- 결과를 엑셀 파일로 저장
- 중간 저장 및 재시작 기능 포함
"""

import json
import base64
import os
import requests
import time
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
import traceback

# ========================================
# 🔧 설정 (여기서 수정하세요!)
# ========================================
API_URL = "https://api.runpod.ai/v2/d9mciy98fvkp0z/run"
API_KEY = os.getenv("RUNPOD_API_KEY", "")  # 환경 변수에서 가져오거나 여기에 직접 입력
MAX_SAMPLES = 5  # 처리할 샘플 수 (None = 전체 60개)


# 프롬프트 (이전과 동일)
PROMPT = """너는 안면부 피부 질환을 분석하는 전문 AI이다. 
주어진 얼굴 부위 피부 이미지를 관찰하고, 이미지에서 보이는 임상적 특징을 자세히 설명하라.

**중요 지침:**
- 다음 피부 질환 목록 중 가장 두드러진 주된 질환 1개를 <label>에 명시하라
- summary에서 동반 가능한 다른 질환의 소견이 있다면 함께 언급할 수 있다
- 과도한 추측보다는 이미지에서 관찰 가능한 객관적 소견 및 특징에 근거하여 기술하라
- **상세하고 포괄적인 설명을 제공하라 (최소 3-5문장, 150자 이상)**
- 색상, 형태, 경계, 분포, 크기, 질감 등 구체적인 관찰 내용을 포함하라
- **정면 이미지**: 얼굴 전체를 관찰하여 전반적인 피부 상태와 병변의 분포 패턴을 분석하라
- **측면 이미지**: 특정 부위를 확대한 이미지이므로, 병변의 세밀한 형태, 경계, 색상, 질감 등을 주의 깊게 관찰하라

다음은 진단 가능한 피부 질환 목록과 각 질환의 임상적 특징이다:

**건선_정면 / 건선_측면 (Psoriasis_Frontal / Psoriasis_Side)**
- 병변 형태: 은백색 인설이 두껍게 쌓인 붉은 구진이나 판
- 경계: 매우 명확하고 뚜렷함 (주변 정상 피부와 확연히 구분됨)
- 안면 발생: 이마, 헤어라인, 눈썹, 귀 주변에서 흔히 발생
- 핵심 특징: 건조하고 거친 피부, 은백색 광택이 나는 인설, 대칭적 분포 경향
- 관찰 포인트: 인설의 두께, 홍반 정도, 병변 경계의 명확성
- 동반 가능 증상: 심한 경우 피부 균열, 출혈

**아토피 피부염_정면 / 아토피 피부염_측면 (Atopic Dermatitis_Frontal / Atopic Dermatitis_Side)**
- 병변 형태: 건조하고 붉은 습진성 병변, 긁은 흔적, 인설 들뜸
- 경계: 불명확하고 확산된 양상
- 안면 발생: 뺨, 이마, 턱, 목 부위에 흔함
- 핵심 특징: 극심한 건조, 피부 갈라짐, 태선화(만성의 경우), 긁은 자국
- 관찰 포인트: 건조 정도, 긁은 자국 유무, 홍반 범위, 인설 들뜸
- 동반 가능 증상: 진물, 분비물, 이차 감염 징후

**여드름_정면 / 여드름_측면 (Acne_Frontal / Acne_Side)**
- 병변 형태: 면포, 붉은 구진, 고름이 찬 농포, 낭종
- 경계: 개별 병변은 명확하나, 다수의 병변이 분포
- 안면 발생: T존(이마, 코, 턱)에 특히 많으며, 뺨에도 가능
- 핵심 특징: 확대된 모공, 과도한 피지, 다양한 단계의 병변 혼재, 염증성/비염증성 병변 공존
- 관찰 포인트: 면포 개수, 염증 정도, 농포 유무, 흉터나 자국
- 동반 가능 증상: 여드름 자국, 흉터, 모공 확장

**주사_정면 / 주사_측면 (Rosacea_Frontal / Rosacea_Side)**
- 병변 형태: 지속적인 홍반, 모세혈관 확장(혈관이 보임), 간헐적 구진/농포
- 경계: 불명확하고 확산된 홍반
- 안면 발생: 얼굴 중앙부 - 뺨, 코, 이마, 턱에 대칭적
- 핵심 특징: 붉은 피부, 혈관이 보임, 쉽게 붉어짐, 여드름과 혼동 가능
- 관찰 포인트: 홍조 지속성, 모세혈관 확장 정도, 홍반 분포 패턴
- 동반 가능 증상: 안면 부종, 따끔거림, 화끈거림, 여드름 유사 병변

**지루 피부염_정면 / 지루 피부염_측면 (Seborrheic Dermatitis_Frontal / Seborrheic Dermatitis_Side)**
- 병변 형태: 기름진 노란색 인설과 홍반
- 경계: 비교적 명확함
- 안면 발생: 두피 경계선, 눈썹, 코 주변, 비구순 주름, 귀 주변, T존
- 핵심 특징: 기름지고 축축한 인설, 과도한 피지, 노란색 인설, 홍반
- 관찰 포인트: 인설의 기름기, 노란색 정도, T존 유분기, 인설 외관
- 동반 가능 증상: 가려움, 두피 비듬, 안면과 두피 지루 동반

**정상_정면 / 정상_측면 (Normal_Frontal / Normal_Side)**
- 병변: 특별한 병변이나 이상 소견 없음
- 경계: 해당 없음
- 피부 상태: 균일한 피부 톤, 건강한 질감
- 핵심 특징: 수분-유분 밸런스 양호, 정상 모공, 탄력 있음
- 관찰 포인트: 피부 톤 균일성, 매끄러운 피부 질감, 홍반/염증 없음, 인설 없음
- 전체 특징: 건강하고 안정적인 피부 상태

---

**답변 형식 (중요: 한국어로 답변):**
<label>질병명</label>
<summary>이미지에서 관찰되는 구체적 소견을 자세히 기술. 병변의 색상, 형태, 경계, 분포, 크기 등을 포함하여 해당 질환의 특징적 소견임을 설명.</summary>

**예시 1:**
<label>건선</label>
<summary>이미지에서는 팔꿈치 부위에 홍반성 판이 관찰되며, 그 위로 은백색의 두꺼운 인설이 층을 이루어 쌓여있습니다. 병변의 경계가 매우 명확하여 주변 정상 피부와 뚜렷하게 구분됩니다. 인설의 두께와 은백색 광택, 명확한 경계는 건선의 전형적인 임상 양상입니다.</summary>

**예시 2:**
<label>여드름</label>
<summary>이미지에서는 얼굴의 이마와 뺨 부위에 다수의 홍반성 구진과 농포가 관찰됩니다. 일부 병변은 중심부에 화농성 내용물이 있으며, 면포도 함께 보입니다. 피지선이 발달한 안면부에 염증성 병변과 비염증성 병변이 혼재된 양상은 심상성 여드름의 특징적 소견입니다. 추가로 뺨 부위에 약한 홍조와 모세혈관 확장이 관찰되어 주사가 동반되어 있을 가능성도 있습니다.</summary>

**예시 3:**
<label>정상</label>
<summary>이미지에서는 특별한 병변이나 이상 소견이 관찰되지 않습니다. 피부 톤이 균일하고 질감이 매끄러우며, 홍반, 구진, 인설 등의 병적 변화가 없습니다. 건강한 정상 피부 상태를 보이고 있습니다.</summary>

---

**특수 상황:**
- 얼굴 부위가 아닌 이미지이거나, 이미지 품질이 매우 불량하여 판단이 불가능한 경우:
  <label>진단불가</label>
  <summary>제공된 이미지는 얼굴 부위가 아니거나 / 이미지 품질이 불량하여 피부 질환을 판단할 수 없습니다.</summary>"""

def extract_label_and_summary(api_response):
    """API 응답에서 label과 summary 추출"""
    try:
        if not api_response or 'output' not in api_response:
            return None, None, "API 응답 형식 오류"
        
        output = api_response['output']
        if not output or 'choices' not in output[0]:
            return None, None, "응답 데이터 없음"
        
        full_text = output[0]['choices'][0]['tokens'][0]
        
        # <label> 추출
        label_match = re.search(r'<label>(.*?)</label>', full_text, re.IGNORECASE)
        predicted_label = label_match.group(1).strip() if label_match else "추출실패"
        
        # <summary> 추출
        summary_match = re.search(r'<summary>(.*?)</summary>', full_text, re.IGNORECASE | re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "추출실패"
        
        return predicted_label, summary, None
        
    except Exception as e:
        return None, None, f"파싱 오류: {str(e)}"

def call_api(image_path, sample_info):
    """단일 이미지에 대해 API 호출"""
    try:
        # 이미지 파일 크기 확인
        image_size = image_path.stat().st_size
        
        # 이미지 인코딩
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "prompt": PROMPT,
                "image": image_b64
            }
        }
        
        # 입력 데이터 정보 수집
        input_info = {
            'image_size_bytes': image_size,
            'image_b64_length': len(image_b64),
            'payload_structure': {
                'input': {
                    'prompt': f"[프롬프트 길이: {len(PROMPT)} 문자]",
                    'image': f"[base64 이미지 길이: {len(image_b64)} 문자]"
                }
            }
        }
        
        start_time = time.time()
        
        # API 호출
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return None, f"API 호출 실패: {response.status_code}", time.time() - start_time, input_info
        
        result = response.json()
        job_id = result['id']
        
        # 결과 대기 (최대 3분)
        status_url = f"https://api.runpod.ai/v2/d9mciy98fvkp0z/status/{job_id}"
        
        for i in range(36):  # 5초씩 36번 = 3분
            time.sleep(5)
            
            status_response = requests.get(status_url, headers=headers, timeout=10)
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                status = status_result.get('status', 'UNKNOWN')
                
                if status == 'COMPLETED':
                    response_time = time.time() - start_time
                    return status_result, None, response_time, input_info
                elif status == 'FAILED':
                    error = status_result.get('error', 'Unknown error')
                    return None, f"작업 실패: {error}", time.time() - start_time, input_info
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    continue
            else:
                return None, f"상태 확인 실패: {status_response.status_code}", time.time() - start_time, input_info
        
        return None, "타임아웃 (3분)", time.time() - start_time, input_info
        
    except Exception as e:
        return None, f"예외 발생: {str(e)}", 0, {}

def save_results_to_excel(results, output_file):
    """결과를 엑셀 파일로 저장"""
    try:
        # 상세 결과 데이터프레임 생성
        df_data = []
        
        for result in results:
            # 입력 데이터 정보
            input_info = ""
            if result.get('input_payload'):
                input_info = json.dumps(result['input_payload'], ensure_ascii=False, indent=2)
            
            df_data.append({
                'ID': result['id'],
                '이미지파일명': result['image_filename'],
                '실제라벨': result['true_label'],
                '예측라벨': result['predicted_label'],
                '정확여부': 'O' if result['is_correct'] else 'X',
                'Summary': result['summary'],
                'API응답시간(초)': f"{result['response_time']:.1f}",
                '이미지크기(bytes)': result.get('image_size', 'N/A'),
                '이미지base64길이': result.get('image_b64_length', 'N/A'),
                '입력프롬프트': result['input_prompt'],
                '전체입력데이터': input_info,
                '전체응답': json.dumps(result['full_api_response'], ensure_ascii=False, indent=2) if result['full_api_response'] else result['error']
            })
        
        df_details = pd.DataFrame(df_data)
        
        # 요약 통계 계산
        total_samples = len(results)
        correct_predictions = sum(1 for r in results if r['is_correct'])
        overall_accuracy = (correct_predictions / total_samples * 100) if total_samples > 0 else 0
        
        # 질환별 정확도 계산
        disease_stats = {}
        for result in results:
            disease = result['true_label']
            if disease not in disease_stats:
                disease_stats[disease] = {'total': 0, 'correct': 0}
            disease_stats[disease]['total'] += 1
            if result['is_correct']:
                disease_stats[disease]['correct'] += 1
        
        # 요약 데이터프레임 생성
        summary_data = [
            {'항목': '전체 샘플 수', '값': total_samples},
            {'항목': '정확 예측 수', '값': correct_predictions},
            {'항목': '전체 정확도(%)', '값': f"{overall_accuracy:.1f}%"},
            {'항목': '평균 응답시간(초)', '값': f"{sum(r['response_time'] for r in results if r['response_time']) / len([r for r in results if r['response_time']]):.1f}"}
        ]
        
        for disease, stats in disease_stats.items():
            accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            summary_data.append({
                '항목': f'{disease} 정확도(%)', 
                '값': f"{accuracy:.1f}% ({stats['correct']}/{stats['total']})"
            })
        
        df_summary = pd.DataFrame(summary_data)
        
        # Confusion Matrix 생성
        diseases = list(set(r['true_label'] for r in results))
        diseases.sort()
        
        confusion_matrix = pd.DataFrame(0, index=diseases, columns=diseases)
        for result in results:
            if result['predicted_label'] in diseases:
                confusion_matrix.loc[result['true_label'], result['predicted_label']] += 1
        
        # 엑셀 파일로 저장
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_details.to_excel(writer, sheet_name='상세결과', index=False)
            df_summary.to_excel(writer, sheet_name='요약통계', index=False)
            confusion_matrix.to_excel(writer, sheet_name='Confusion Matrix')
        
        print(f"[SUCCESS] 결과가 엑셀 파일로 저장되었습니다: {output_file}")
        
    except Exception as e:
        print(f"[ERROR] 엑셀 저장 실패: {e}")
        traceback.print_exc()

def run_batch_validation(max_cnt=None):
    """배치 validation 실행
    
    Args:
        max_cnt (int, optional): 처리할 최대 샘플 수. None이면 전체 처리
    """
    # API 키 확인
    if not API_KEY:
        print("[ERROR] RUNPOD_API_KEY가 설정되지 않았습니다.")
        print("환경 변수를 설정하거나 코드에서 직접 입력하세요.")
        return
    
    base_dir = Path(__file__).parent
    dataset_file = base_dir / "validation_dataset_original.json"
    
    # 파일명에 샘플 수 포함
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_file = base_dir / f"validation_report_full_{timestamp}.xlsx"
    
    print("=" * 80)
    print("🚀 Validation 배치 테스트 시작")
 
    # 데이터셋 로드
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    samples = dataset['data']
    
    # 샘플 수 제한
    if max_cnt and max_cnt < len(samples):
        samples = samples[:max_cnt]

    total_samples = len(samples)
    print(f"[INFO] 총 {total_samples}개 샘플 처리 예정")
    
    results = []
    
    for i, sample in enumerate(samples, 1):
        print(f"[{i:2d}/{total_samples}] 처리 중: {sample['image_filename']} ({sample['true_label']})")
        
        image_path = base_dir / sample['image_path']
        
        if not image_path.exists():
            print(f"  [ERROR] 이미지 파일 없음: {image_path}")
            results.append({
                'id': sample['id'],
                'image_filename': sample['image_filename'],
                'true_label': sample['true_label'],
                'predicted_label': 'ERROR',
                'summary': 'ERROR',
                'is_correct': False,
                'response_time': 0,
                'input_prompt': PROMPT,
                'input_payload': {},
                'image_size': 'N/A',
                'image_b64_length': 'N/A',
                'full_api_response': None,
                'error': '이미지 파일 없음'
            })
            continue
        
        # API 호출
        api_response, error, response_time, input_info = call_api(image_path, sample)
        
        if error:
            print(f"  [ERROR] {error}")
            results.append({
                'id': sample['id'],
                'image_filename': sample['image_filename'],
                'true_label': sample['true_label'],
                'predicted_label': 'ERROR',
                'summary': 'ERROR',
                'is_correct': False,
                'response_time': response_time,
                'input_prompt': PROMPT,
                'input_payload': input_info,
                'image_size': input_info.get('image_size_bytes', 'N/A'),
                'image_b64_length': input_info.get('image_b64_length', 'N/A'),
                'full_api_response': None,
                'error': error
            })
        else:
            # 결과 파싱
            predicted_label, summary, parse_error = extract_label_and_summary(api_response)
            
            if parse_error:
                print(f"  [ERROR] {parse_error}")
                predicted_label = 'PARSE_ERROR'
                summary = 'PARSE_ERROR'
            
            is_correct = predicted_label == sample['true_label']
            
            print(f"  [RESULT] 예측: {predicted_label} | 정답: {sample['true_label']} | {'✅' if is_correct else '❌'} | {response_time:.1f}초")
            
            results.append({
                'id': sample['id'],
                'image_filename': sample['image_filename'],
                'true_label': sample['true_label'],
                'predicted_label': predicted_label,
                'summary': summary,
                'is_correct': is_correct,
                'response_time': response_time,
                'input_prompt': PROMPT,
                'input_payload': input_info,
                'image_size': input_info.get('image_size_bytes', 'N/A'),
                'image_b64_length': input_info.get('image_b64_length', 'N/A'),
                'full_api_response': api_response,
                'error': None
            })
        
        # 진행상황 표시 (10개마다)
        if i % 10 == 0:
            print(f"  [INFO] 진행상황: {i}개 완료")
        
        print()
    
    # 엑셀 리포트 생성
    save_results_to_excel(results, excel_file)
    
    # 최종 요약
    correct_count = sum(1 for r in results if r['is_correct'])
    accuracy = (correct_count / total_samples * 100) if total_samples > 0 else 0
    
    print("=" * 80)
    print("🎯 최종 결과 요약")
    print("=" * 80)
    print(f"전체 샘플: {total_samples}개")
    print(f"정확 예측: {correct_count}개")
    print(f"전체 정확도: {accuracy:.1f}%")
    print(f"Excel 리포트: {excel_file}")
    print("=" * 80)

if __name__ == "__main__":
    # 필요한 패키지 확인
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        print("[ERROR] 필요한 패키지를 설치하세요:")
        print("pip install pandas openpyxl")
        exit(1)
    
    run_batch_validation(MAX_SAMPLES)
