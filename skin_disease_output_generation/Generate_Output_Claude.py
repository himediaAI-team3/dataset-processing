# Generate_Output_Claude.py - Claude API로 설명 생성
# 
# [사용 방법]
# 1. 라이브러리 설치: pip install anthropic pillow tqdm datasets
# 2. API 키 설정: ANTHROPIC_API_KEY에 실제 키 입력, NUM_SAMPLES 설정
# 3. 실행: python Generate_Output_Claude.py
# 4. 결과: skin_disease_dataset_with_output 폴더 생성
# 5. 나머지는 Generate_Output_Gemma.py로 처리

import base64
from io import BytesIO
from PIL import Image
from datasets import load_from_disk, DatasetDict
from anthropic import Anthropic
from tqdm import tqdm
import os
from prompts import SYSTEM_PROMPT

# ========== 설정 (여기만 수정하세요!) ==========
DATASET_PATH = "../skin_disease_dataset"  # 전처리 (1)에서 만든 데이터셋 경로 
SAVE_PATH = "../skin_disease_dataset_with_output"  # 저장할 경로
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # 환경 변수에서 가져오거나 여기에 직접 입력
NUM_SAMPLES = 10  # Claude로 처리할 개수 (1000개 추천)
TXT_OUTPUT_FILE = "claude_outputs.txt"  # 원하는 파일명으로 변경 가능!
# ================================================

# System Prompt는 prompts.py에서 import


def process_with_claude(client, image_pil, label, description, symptom):
    """
    Claude API로 이미지 설명 생성
    
    Args:
        client: Anthropic 클라이언트
        image_pil: PIL Image 객체
        label: 정답 라벨
        description: JSON의 description
        symptom: JSON의 symptom
    
    Returns:
        Claude의 응답 (str)
    """
    # 이미지를 base64로 인코딩
    buffered = BytesIO()
    image_pil.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # 사용자 메시지
    user_text = f"""정답은 {label}이다. 

                질병 특징: {description}
                증상: {symptom}

                위 정보를 참고하여 이미지를 자세히 분석하고, 정답에 맞게 설명하라."""
        
    # Claude API 호출
    message = client.messages.create(
        model="claude-sonnet-4-20250514",  # 최신 Claude Sonnet
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": user_text
                    }
                ],
            }
        ],
    )
    
    # 응답 추출
    response = message.content[0].text
    return response


def save_outputs_to_txt(dataset, num_samples, output_file):
    """
    처리된 output들을 txt 파일로 저장
    
    Args:
        dataset: 데이터셋
        num_samples: 저장할 샘플 개수
        output_file: 저장할 txt 파일명
    """
    print(f"\n" + "=" * 60)
    print(f"📝 Output을 txt 파일로 저장 중...")
    print("=" * 60)
    
    with open(output_file, "w", encoding="utf-8") as f:
        saved_count = 0
        for i in range(num_samples):
            sample = dataset["train"][i]
            
            # output이 있는 것만 저장
            if sample["output"]:
                f.write(f"{'='*70}\n")
                f.write(f"[샘플 {i+1}]\n")
                f.write(f"Label: {sample['label']}\n")
                f.write(f"Description: {sample['description'][:100]}...\n")
                f.write(f"{'='*70}\n")
                f.write(sample["output"])
                f.write(f"\n\n")
                saved_count += 1
    
    print(f"✅ txt 저장 완료!")
    print(f"   파일명: {output_file}")
    print(f"   저장된 샘플: {saved_count}개")


def main():
    print("=" * 60)
    print("Generate_Output_Claude.py - Claude API로 설명 생성")
    print("=" * 60)
    
    # API 키 확인
    if not ANTHROPIC_API_KEY:
        print("❌ 오류: ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("환경 변수를 설정하거나 코드에서 직접 입력하세요.")
        return
    
    # 데이터셋 불러오기
    print(f"\n📂 Dataset 불러오는 중: {DATASET_PATH}")
    dataset = load_from_disk(DATASET_PATH)
    print(f"✅ 불러오기 완료!")
    print(dataset)
    
    # Claude 클라이언트 초기화
    print(f"\n🤖 Claude API 초기화 중...")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    print(f"✅ 초기화 완료!")
    
    # Train 데이터 처리 (일부만)
    print(f"\n" + "=" * 60)
    print(f"🚀 Train 데이터 처리 중... (처음 {NUM_SAMPLES}개)")
    print("=" * 60)
    
    # 기존 output을 리스트로 복사
    train_outputs = dataset["train"]["output"][:]
    
    # 이미 처리된 개수 확인
    already_done = sum(1 for i, x in enumerate(train_outputs[:NUM_SAMPLES]) if x)
    print(f"이미 처리된 데이터: {already_done}개")
    print(f"처리할 데이터: {NUM_SAMPLES - already_done}개")
    print(f"⚠️ 예상 비용: 약 ${(NUM_SAMPLES - already_done) * 0.004:.2f}")
    
    # 진행 루프 (처음 NUM_SAMPLES개만)
    for i in tqdm(range(NUM_SAMPLES), desc="Processing with Claude", mininterval=2.0):
        # 이미 처리된 경우 스킵
        if train_outputs[i]:
            continue
        
        try:
            # 데이터 가져오기
            sample = dataset["train"][i]
            
            # Claude API 호출
            result = process_with_claude(
                client=client,
                image_pil=sample["image"],
                label=sample["label"],
                description=sample["description"],
                symptom=sample["symptom"]
            )
            
            train_outputs[i] = result
            
        except Exception as e:
            print(f"\n⚠️ ERROR at index {i}: {str(e)}")
            train_outputs[i] = ""  # 에러 시 빈 값
        
        # 50개마다 중간 저장 (안전장치)
        if (i + 1) % 50 == 0:
            print(f"\n💾 중간 저장 중... ({i + 1}/{NUM_SAMPLES})")
            # output 컬럼 업데이트
            train_dataset_updated = dataset["train"].remove_columns("output")
            train_dataset_updated = train_dataset_updated.add_column("output", train_outputs)
            
            # 임시 저장
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
    
    # 최종 Dataset 생성
    final_dataset = DatasetDict({
        "train": train_dataset_final,
        "test": dataset["test"]
    })
    
    # 저장
    # print(f"\n" + "=" * 60)
    # print(f"💾 Dataset 저장 중: {SAVE_PATH}")
    # print("=" * 60)
    # os.makedirs(SAVE_PATH, exist_ok=True)
    # final_dataset.save_to_disk(SAVE_PATH)
    
    print(f"\n" + "=" * 60)
    print("✅ Claude API 처리 완료!")
    print("=" * 60)
    print(f"처리된 개수: {NUM_SAMPLES}개")
    print(f"나머지: {len(dataset['train']) - NUM_SAMPLES}개 (Gemma로 처리 필요)")
    
    # txt 파일로 저장 (새로 추가된 부분!)
    save_outputs_to_txt(final_dataset, NUM_SAMPLES, TXT_OUTPUT_FILE)

    # 샘플 확인
    print(f"\n🔍 샘플 확인:")
    for i in range(min(3, NUM_SAMPLES)):
        if final_dataset['train'][i]['output']:
            print(f"\n[샘플 {i+1}]")
            print(f"Label: {final_dataset['train'][i]['label']}")
            print(f"Output: {final_dataset['train'][i]['output'][:200]}...")
            break


if __name__ == "__main__":
    main()