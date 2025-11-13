# Generate_Output_Gemma.py - 로컬 Gemma로 설명 생성 (GPU 버전)
# 
# [사용 방법]
# 1. 라이브러리 설치: pip install unsloth (GPU 환경 필요)
# 2. 경로 설정: DATASET_PATH, SAVE_PATH 확인
# 3. 실행: python Generate_Output_Gemma.py
# 4. 결과: skin_disease_dataset_with_output 폴더 생성
# 5. 장점: 무료, 빠름 (RTX 3050 기준 2-3시간), GPU 사용
# 6. 주의: 이미 Claude로 처리한 데이터가 있으면 스킵하고 나머지만 처리함


from datasets import load_from_disk, DatasetDict
from unsloth import FastVisionModel
import torch
from tqdm import tqdm
import os
from prompts import SYSTEM_PROMPT

# ========== 설정 (여기만 수정하세요!) ==========
DATASET_PATH = "./skin_disease_dataset"  # 전처리 (1)에서 만든 데이터셋 경로
SAVE_PATH = "./skin_disease_dataset_with_output"  # 저장할 경로
# ================================================

# System Prompt는 prompts.py에서 import (INSTRUCTION로 사용)
INSTRUCTION = SYSTEM_PROMPT


def process_with_gemma(model, tokenizer, image, label, description, symptom):
    """
    Gemma 모델로 이미지 설명 생성
    
    Args:
        model: Gemma 모델
        tokenizer: Tokenizer
        image: PIL Image
        label: 정답 라벨
        description: 질병 설명
        symptom: 증상
    
    Returns:
        생성된 설명 (str)
    """
    # 프롬프트 구성
    user_prompt = f"""정답은 {label}이다.

질병 특징: {description}
증상: {symptom}

위 정보를 참고하여 이미지를 자세히 분석하고, 정답에 맞게 설명하라."""
    
    # 대화 형식으로 변환
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": INSTRUCTION + "\n\n" + user_prompt},
                {"type": "image", "image": image}
            ]
        }
    ]
    
    # 토큰화
    inputs = tokenizer.apply_chat_template(
        conversation,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to("cuda")
    
    # 생성
    with torch.inference_mode():
        outputs = model.generate(
            inputs,
            max_new_tokens=512,
            temperature=0.3,
            do_sample=True,
            top_p=0.9
        )
    
    # 디코딩
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # assistant 답변 부분만 추출
    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()
    
    return response


def main():
    print("=" * 60)
    print("전처리 (2) - 로컬 Gemma로 설명 생성")
    print("=" * 60)
    
    # GPU 확인
    if not torch.cuda.is_available():
        print("⚠️ GPU를 찾을 수 없습니다. CPU로는 매우 느릴 수 있습니다.")
        return
    
    print(f"✅ GPU 사용 가능: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    
    # 데이터셋 불러오기
    print(f"\n📂 Dataset 불러오는 중: {DATASET_PATH}")
    dataset = load_from_disk(DATASET_PATH)
    print(f"✅ 불러오기 완료!")
    print(dataset)
    
    # Gemma 모델 불러오기
    print(f"\n🤖 Gemma 모델 로딩 중...")
    model, tokenizer = FastVisionModel.from_pretrained(
        "unsloth/gemma-3-4b-it-unsloth-bnb-4bit",
        load_in_4bit=True,
        use_gradient_checkpointing="unsloth"
    )
    FastVisionModel.for_inference(model)  # 추론 모드로 전환
    print(f"✅ 모델 로딩 완료!")
    
    # Train 데이터 처리
    print(f"\n" + "=" * 60)
    print("🚀 Train 데이터 처리 중...")
    print("=" * 60)
    
    train_outputs = dataset["train"]["output"][:]
    
    # 이미 처리된 개수 확인
    already_done = sum(1 for x in train_outputs if x)
    print(f"이미 처리된 데이터: {already_done}개")
    print(f"처리할 데이터: {len(train_outputs) - already_done}개")
    
    # 진행 루프
    for i in tqdm(range(len(dataset["train"])), desc="Processing Train"):
        # 이미 처리된 경우 스킵
        if train_outputs[i]:
            continue
        
        try:
            sample = dataset["train"][i]
            
            # Gemma로 생성
            result = process_with_gemma(
                model=model,
                tokenizer=tokenizer,
                image=sample["image"],
                label=sample["label"],
                description=sample["description"],
                symptom=sample["symptom"]
            )
            
            train_outputs[i] = result
            
        except Exception as e:
            print(f"\n⚠️ ERROR at index {i}: {str(e)}")
            train_outputs[i] = ""
        
        # 100개마다 중간 저장
        if (i + 1) % 100 == 0:
            print(f"\n💾 중간 저장 중... ({i + 1}/{len(dataset['train'])})")
            train_dataset_updated = dataset["train"].remove_columns("output")
            train_dataset_updated = train_dataset_updated.add_column("output", train_outputs)
            
            temp_dataset = DatasetDict({
                "train": train_dataset_updated,
                "test": dataset["test"]
            })
            temp_dataset.save_to_disk(SAVE_PATH + "_temp")
            print("✅ 중간 저장 완료!")
            
            # VRAM 정리
            torch.cuda.empty_cache()
    
    # 최종 Train output 업데이트
    print(f"\n📊 Train 최종 업데이트 중...")
    train_dataset_final = dataset["train"].remove_columns("output")
    train_dataset_final = train_dataset_final.add_column("output", train_outputs)
    
    # Test 데이터 처리
    print(f"\n" + "=" * 60)
    print("🚀 Test 데이터 처리 중...")
    print("=" * 60)
    
    test_outputs = dataset["test"]["output"][:]
    
    for i in tqdm(range(len(dataset["test"])), desc="Processing Test"):
        if test_outputs[i]:
            continue
        
        try:
            sample = dataset["test"][i]
            
            result = process_with_gemma(
                model=model,
                tokenizer=tokenizer,
                image=sample["image"],
                label=sample["label"],
                description=sample["description"],
                symptom=sample["symptom"]
            )
            
            test_outputs[i] = result
            
        except Exception as e:
            print(f"\n⚠️ ERROR at index {i}: {str(e)}")
            test_outputs[i] = ""
        
        # VRAM 관리
        if (i + 1) % 50 == 0:
            torch.cuda.empty_cache()
    
    # Test output 업데이트
    test_dataset_final = dataset["test"].remove_columns("output")
    test_dataset_final = test_dataset_final.add_column("output", test_outputs)
    
    # 최종 Dataset 생성
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
    print(f"Output: {final_dataset['train'][0]['output'][:300]}...")
    
    # 메모리 정리
    del model
    del tokenizer
    torch.cuda.empty_cache()
    print(f"\n🧹 GPU 메모리 정리 완료!")


if __name__ == "__main__":
    main()