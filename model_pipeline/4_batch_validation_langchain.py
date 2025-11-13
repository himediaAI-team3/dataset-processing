#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain을 사용한 Validation 배치 테스트 스크립트
- 학습 시와 동일한 메시지 형식 사용
- 60개 이미지를 순차적으로 API에 전송
- 결과를 엑셀 파일로 저장
"""

import json
import base64
import time
import re
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import traceback
import io
from PIL import Image

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ========================================
# 🔧 설정 (여기서 수정하세요!)
# ========================================
API_KEY = os.getenv("RUNPOD_API_KEY", "")  # 환경 변수에서 가져오거나 여기에 직접 입력
MAX_SAMPLES = 60  # 처리할 샘플 수 (None = 전체 60개)

API_ENDPOINT = "https://api.runpod.ai/v2/d9mciy98fvkp0z/openai/v1"  # OpenAI 호환 엔드포인트
MODEL_NAME = "oneandthree/qwen2.5vl_7b_skin_dataset_3000steps_r128_b8_merged"
#API_ENDPOINT = "https://api.runpod.ai/v2/43axfsb9v8wr6w/openai/v1"  # OpenAI 호환 엔드포인트
#MODEL_NAME = "oneandthree/ash-gemma-3-4b-merged"



# 학습 시와 동일한 프롬프트 (간결한 버전)
INSTRUCTION = """너는 안면부 피부 질환을 분석하는 전문 AI이다. 
주어진 얼굴 부위 피부 이미지를 관찰하고, 이미지에서 보이는 임상적 특징을 자세히 설명하라.

**중요 지침:**
- 다음 피부 질환 목록 중 가장 두드러진 주된 질환 1개를 <label>에 명시하라
- summary에서 동반 가능한 다른 질환의 소견이 있다면 함께 언급할 수 있다
- 3문장 이내로 간결하면서도 핵심적인 정보를 담아라. 같은 표현 반복을 피하라
- 과도한 추측보다는 이미지에서 관찰 가능한 객관적 소견 및 특징에 근거하여 기술하라

다음은 진단 가능한 피부 질환 목록과 각 질환의 임상적 특징이다:

**1. 질환명: 건선**
- 병변 형태: 은백색 인설이 쌓인 붉은 구진이나 판
- 경계: 매우 명확하고 뚜렷함
- 안면 발생: 이마, 헤어라인, 귀 주변에서 관찰 가능
- 핵심 특징: 두꺼운 은백색 인설, 명확한 경계, 대칭적 분포
- 증상: 가려움증 동반 가능

**2. 질환명: 아토피**
- 병변 형태: 건조하고 가려운 습진성 병변, 태선화
- 경계: 불명확
- 안면 발생: 얼굴 전반, 특히 뺨, 이마, 눈 주위
- 핵심 특징: 피부 건조, 긁은 자국, 만성 재발성
- 증상: 심한 가려움증

**3. 질환명: 여드름**
- 병변 형태: 면포(comedone), 구진, 농포, 낭종
- 경계: 개별 병변은 명확
- 안면 발생: 이마, 코, 턱 등 T존 중심, 뺨에도 가능
- 핵심 특징: 다양한 병변 동시 존재, 피지선 분포 부위
- 증상: 염증성 병변은 통증 가능

**4. 질환명: 주사**
- 병변 형태: 지속적인 홍반, 모세혈관 확장, 구진, 농포
- 경계: 불명확한 홍반
- 안면 발생: 얼굴 중앙부(코, 뺨 중심, 이마)
- 핵심 특징: 안면 홍조, 혈관 확장 두드러짐, 딸기코 가능
- 증상: 작열감, 따끔거림

**5. 질환명: 지루**
- 병변 형태: 기름기 있는 노란 비늘과 홍반
- 경계: 비교적 명확
- 안면 발생: 눈썹, 비구순 주름, 귀 주변, 헤어라인
- 핵심 특징: 기름진 각질, 피지선이 많은 부위
- 증상: 가려움증, 각질

**6. 질환명: 정상**
- 특징: 특별한 병변이 관찰되지 않음
- 피부 상태: 건강한 피부 톤과 질감

---

**답변 형식:**
<label>{질환명}</label>
<summary>{이미지에서 관찰되는 구체적 소견을 자세히 기술. 병변의 색상, 형태, 경계, 분포, 크기 등을 포함하여 해당 질환의 특징적 소견임을 설명.}</summary>

**예시 1:**
<label>건선</label>
<summary>이미지에서는 이마와 헤어라인 부위에 홍반성 판이 관찰되며, 그 위로 은백색의 두꺼운 인설이 층을 이루어 쌓여있습니다. 병변의 경계가 매우 명확하여 주변 정상 피부와 뚜렷하게 구분됩니다. 인설의 두께와 은백색 광택, 명확한 경계는 건선의 전형적인 임상 양상입니다.</summary>

**예시 2:**
<label>여드름</label>
<summary>이미지에서는 얼굴의 이마와 뺨 부위에 다수의 홍반성 구진과 농포가 관찰됩니다. 일부 병변은 중심부에 화농성 내용물이 있으며, 면포도 함께 보입니다. 피지선이 발달한 안면부에 염증성 병변과 비염증성 병변이 혼재된 양상은 심상성 여드름의 특징적 소견입니다.</summary>

**예시 3:**
<label>정상</label>
<summary>이미지에서는 특별한 병변이나 이상 소견이 관찰되지 않습니다. 피부 톤이 균일하고 질감이 매끄러우며, 홍반, 구진, 인설 등의 병적 변화가 없습니다. 건강한 정상 피부 상태를 보이고 있습니다.</summary>

**특수 상황:**
- 얼굴 부위가 아닌 이미지이거나, 이미지 품질이 매우 불량하여 판단이 불가능한 경우:
<label>진단불가</label>
<summary>제공된 이미지는 얼굴 부위가 아니거나 이미지 품질이 불량하여 피부 질환을 판단할 수 없습니다.</summary>"""

def extract_label_and_summary(response_text):
    """응답에서 label과 summary 추출"""
    try:
        # <label> 추출
        label_match = re.search(r'<label>(.*?)</label>', response_text, re.IGNORECASE)
        predicted_label = label_match.group(1).strip() if label_match else "추출실패"
        
        # <summary> 추출
        summary_match = re.search(r'<summary>(.*?)</summary>', response_text, re.IGNORECASE | re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "추출실패"
        
        return predicted_label, summary, None
        
    except Exception as e:
        return None, None, f"파싱 오류: {str(e)}"

def call_langchain_api(image_path, sample_info):
    """LangChain을 사용한 API 호출 (학습 형식과 동일)"""
    try:
        # 이미지 파일 크기 확인
        image_size = image_path.stat().st_size
        
        # 이미지 로드 및 base64 인코딩
        image = Image.open(str(image_path)).convert("RGB")
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # 입력 데이터 정보 수집
        input_info = {
            'image_size_bytes': image_size,
            'image_b64_length': len(image_base64),
            'message_format': 'langchain_human_message',
            'instruction_length': len(INSTRUCTION)
        }
        
        # ChatOpenAI 초기화
        llm = ChatOpenAI(
            model=MODEL_NAME,
            api_key=API_KEY,
            base_url=API_ENDPOINT,
            temperature=0.1,
            max_tokens=1000
        )
        
        # 학습 시와 동일한 메시지 형식 구성
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": INSTRUCTION},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            )
        ]
        
        start_time = time.time()
        
        # API 호출
        response = llm.invoke(messages)
        response_time = time.time() - start_time
        
        # 응답 텍스트 추출
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        return response_text, None, response_time, input_info
        
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
                '전체입력데이터': input_info,
                '전체응답': result.get('full_response', result.get('error', ''))
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
    """LangChain을 사용한 배치 validation 실행"""
    # API 키 확인
    if not API_KEY:
        print("[ERROR] RUNPOD_API_KEY가 설정되지 않았습니다.")
        print("환경 변수를 설정하거나 코드에서 직접 입력하세요.")
        return
    
    base_dir = Path(__file__).parent
    dataset_file = base_dir / "validation_dataset.json"
    
    # 파일명에 샘플 수 포함
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_file = base_dir / f"validation_report_langchain_{timestamp}.xlsx"
    
    print("=" * 80)
    print("🚀 LangChain Validation 배치 테스트 시작")
    print(f"📋 학습 형식과 동일한 메시지 구조 사용")
    print("=" * 80)
 
    # 데이터셋 로드
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    samples = dataset['data']
    
    # 샘플 수 제한
    if max_cnt and max_cnt < len(samples):
        samples = samples[:max_cnt]

    total_samples = len(samples)
    print(f"[INFO] 총 {total_samples}개 샘플 처리 예정")
    print(f"[INFO] 프롬프트 길이: {len(INSTRUCTION)} 문자 (학습 시와 동일)")
    print()
    
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
                'input_payload': {},
                'image_size': 'N/A',
                'image_b64_length': 'N/A',
                'full_response': '이미지 파일 없음',
                'error': '이미지 파일 없음'
            })
            continue
        
        # LangChain API 호출
        response_text, error, response_time, input_info = call_langchain_api(image_path, sample)
        
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
                'input_payload': input_info,
                'image_size': input_info.get('image_size_bytes', 'N/A'),
                'image_b64_length': input_info.get('image_b64_length', 'N/A'),
                'full_response': error,
                'error': error
            })
        else:
            # 결과 파싱
            predicted_label, summary, parse_error = extract_label_and_summary(response_text)
            
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
                'input_payload': input_info,
                'image_size': input_info.get('image_size_bytes', 'N/A'),
                'image_b64_length': input_info.get('image_b64_length', 'N/A'),
                'full_response': response_text,
                'error': None
            })
        
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
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
    except ImportError as e:
        print("[ERROR] 필요한 패키지를 설치하세요:")
        print("pip install pandas openpyxl langchain-openai")
        print(f"누락된 패키지: {e}")
        exit(1)
    
    run_batch_validation(MAX_SAMPLES)
