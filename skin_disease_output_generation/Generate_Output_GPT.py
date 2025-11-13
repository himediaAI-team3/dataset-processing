# Generate_Output_GPT.py - ChatGPT API로 설명 생성
# 
# [사용 방법]
# 1. 라이브러리 설치: pip install langchain-openai pillow tqdm
# 2. API 키 설정: OPENAI_API_KEY에 실제 키 입력
# 3. 실행: python Generate_Output_GPT.py
# 4. 결과: skin_disease_dataset_with_output 폴더 생성
# 5. 주의: 12,000개 전체 처리 시 시간 오래 걸림 (7-17시간), 비용 발생 ($5-10)

import base64
from io import BytesIO
from PIL import Image
from datasets import load_from_disk
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from tqdm import tqdm
import os
from prompts import SYSTEM_PROMPT

# ========== 설정 (여기만 수정하세요!) ==========
DATASET_PATH = "./skin_disease_dataset"  # 전처리 (1)에서 만든 데이터셋 경로
SAVE_PATH = "./skin_disease_dataset_with_output"  # 저장할 경로
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # 환경 변수에서 가져오거나 여기에 직접 입력
# ================================================

# System Prompt는 prompts.py에서 import


def process_single_image(image_pil, label, description, symptom, llm):
    """
    단일 이미지를 ChatGPT로 처리
    
    Args:
        image_pil: PIL Image 객체
        label: 정답 라벨
        description: JSON의 description
        symptom: JSON의 symptom
        llm: ChatGPT 모델
    
    Returns:
        ChatGPT의 응답 (str)
    """
    # 이미지를 base64로 인코딩
    buffered = BytesIO()
    image_pil.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # 시스템 메시지
    sys_message = SystemMessage(content=SYSTEM_PROMPT)
    
    # 사용자 메시지 (힌트 포함)
    user_text = f"""정답은 {label}이다. 

질병 특징: {description}
증상: {symptom}

위 정보를 참고하여 이미지를 자세히 분석하고, 정답에 맞게 설명하라."""

    message = HumanMessage(content=[
        {"type": "text", "text": user_text},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
    ])
    
    # ChatGPT 호출
    chain = llm | StrOutputParser()
    response = chain.invoke([sys_message, message])
    
    return response


def main():
    print("=" * 60)
    print("전처리 (2) - ChatGPT API로 설명 생성")
    print("=" * 60)
    
    # API 키 확인
    if not OPENAI_API_KEY:
        print("❌ 오류: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("환경 변수를 설정하거나 코드에서 직접 입력하세요.")
        return
    
    # 데이터셋 불러오기
    print(f"\n📂 Dataset 불러오는 중: {DATASET_PATH}")
    dataset = load_from_disk(DATASET_PATH)
    print(f"✅ 불러오기 완료!")
    print(dataset)
    
    # ChatGPT 모델 초기화
    print(f"\n🤖 ChatGPT 모델 초기화 중...")
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",  # 또는 "gpt-4o", "gpt-4"
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3  # 일관성 있는 답변을 위해 낮게 설정
    )
    print(f"✅ 초기화 완료!")
    
    # Train 데이터 처리
    print(f"\n" + "=" * 60)
    print("🚀 Train 데이터 처리 중...")
    print("=" * 60)
    
    # 기존 output을 리스트로 복사
    train_outputs = dataset["train"]["output"][:]
    
    # 이미 처리된 개수 확인
    already_done = sum(1 for x in train_outputs if x)
    print(f"이미 처리된 데이터: {already_done}개")
    print(f"처리할 데이터: {len(train_outputs) - already_done}개")
    
    # 진행 루프
    for i in tqdm(range(len(dataset["train"])), desc="Processing", mininterval=2.0):
        # 이미 처리된 경우 스킵
        if train_outputs[i]:
            continue
        
        try:
            # 데이터 가져오기
            sample = dataset["train"][i]
            
            # ChatGPT 호출
            result = process_single_image(
                image_pil=sample["image"],
                label=sample["label"],
                description=sample["description"],
                symptom=sample["symptom"],
                llm=llm
            )
            
            train_outputs[i] = result
            
        except Exception as e:
            print(f"\n⚠️ ERROR at index {i}: {str(e)}")
            train_outputs[i] = ""  # 에러 시 빈 값
        
        # 50개마다 중간 저장 (안전장치)
        if (i + 1) % 50 == 0:
            print(f"\n💾 중간 저장 중... ({i + 1}/{len(dataset['train'])})")
            # output 컬럼 업데이트
            train_dataset_updated = dataset["train"].remove_columns("output")
            train_dataset_updated = train_dataset_updated.add_column("output", train_outputs)
            
            # 임시 저장
            from datasets import DatasetDict
            temp_dataset = DatasetDict({
                "train": train_dataset_updated,
                "test": dataset["test"]
            })
            temp_dataset.save_to_disk(SAVE_PATH + "_temp")
            print("✅ 중간 저장 완료!")
    
    # 최종 output 업데이트
    print(f"\n📊 최종 업데이트 중...")
    train_dataset_final = dataset["train"].remove_columns("output")
    train_dataset_final = train_dataset_final.add_column("output", train_outputs)
    
    # Test 데이터도 동일하게 처리 (필요시)
    print(f"\n" + "=" * 60)
    print("🚀 Test 데이터 처리 중...")
    print("=" * 60)
    
    test_outputs = dataset["test"]["output"][:]
    
    for i in tqdm(range(len(dataset["test"])), desc="Processing Test", mininterval=2.0):
        if test_outputs[i]:
            continue
        
        try:
            sample = dataset["test"][i]
            result = process_single_image(
                image_pil=sample["image"],
                label=sample["label"],
                description=sample["description"],
                symptom=sample["symptom"],
                llm=llm
            )
            test_outputs[i] = result
            
        except Exception as e:
            print(f"\n⚠️ ERROR at index {i}: {str(e)}")
            test_outputs[i] = ""
    
    # Test output 업데이트
    test_dataset_final = dataset["test"].remove_columns("output")
    test_dataset_final = test_dataset_final.add_column("output", test_outputs)
    
    # 최종 Dataset 생성
    from datasets import DatasetDict
    final_dataset = DatasetDict({
        "train": train_dataset_final,
        "test": test_dataset_final
    })
    
    # 저장
    print(f"\n" + "=" * 60)
    print(f"💾 최종 Dataset 저장 중: {SAVE_PATH}")
    print("=" * 60)
    os.makedirs(SAVE_PATH, exist_ok=True)
    final_dataset.save_to_disk(SAVE_PATH)
    
    print(f"\n" + "=" * 60)
    print("✅ 전처리 (2) 완료!")
    print("=" * 60)
    print(final_dataset)
    
    # 샘플 확인
    print(f"\n🔍 샘플 확인:")
    print(f"Label: {final_dataset['train'][0]['label']}")
    print(f"Output: {final_dataset['train'][0]['output'][:200]}...")


if __name__ == "__main__":
    main()