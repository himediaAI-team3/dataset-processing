# 전처리 (1) - Files to Dataset (피부질환 버전)

# conda 가상환경 설정
# - 가상환경 생성: conda create -n dataset-processing python=3.9 -y
# - 가상환경 활성화: conda activate dataset-processing

# 필요한 패키지 설치: pip install datasets pandas matplotlib pillow


from datasets import Dataset, Image, DatasetDict
import os
import pandas as pd
import json

# ========== 경로 설정 (여기만 수정하세요!) ==========
train_image_root = "./안면부 피부질환 이미지 합성데이터/Training/원천데이터"  # Training 이미지 폴더
train_label_root = "./안면부 피부질환 이미지 합성데이터/Training/라벨링데이터"  # Training JSON 폴더
val_image_root = "./안면부 피부질환 이미지 합성데이터/Validation/원천데이터"  # Validation 이미지 폴더
val_label_root = "./안면부 피부질환 이미지 합성데이터/Validation/라벨링데이터"  # Validation JSON 폴더

SAVE_PATH = "./skin_disease_dataset"  # 저장할 경로
# ===================================================


def parse_skin_disease_data(image_root, label_root):
    """
    피부질환 데이터셋을 읽어서 Dataset 객체로 변환
    
    Args:
        image_root: 원천데이터(이미지) 최상위 폴더
        label_root: 라벨링데이터(JSON) 최상위 폴더
    
    Returns:
        Dataset 객체
    """
    data = []
    
    # 이미지 폴더 순회 (TS_건선_정면, TS_건선_측면, ...)
    for folder_name in os.listdir(image_root):
        image_folder_path = os.path.join(image_root, folder_name)
        
        # 폴더가 아니면 스킵
        if not os.path.isdir(image_folder_path):
            continue
        
        # 라벨 이름 추출
        # "TS_건선_정면" -> "건선"
        # "VS_아토피_측면" -> "아토피"
        label_name = folder_name.replace("TS_", "").replace("VS_", "")
        label_name = label_name.replace("_정면", "").replace("_측면", "")
        
        # 대응되는 JSON 폴더 찾기
        # "TS_건선_정면" -> "TL_건선_정면"
        # "VS_건선_정면" -> "VL_건선_정면"
        json_folder_name = folder_name.replace("TS_", "TL_").replace("VS_", "VL_")
        json_folder_path = os.path.join(label_root, json_folder_name)
        
        # JSON 폴더가 없으면 경고
        if not os.path.exists(json_folder_path):
            print(f"⚠️ 경고: JSON 폴더를 찾을 수 없습니다: {json_folder_path}")
            continue
        
        # 폴더 안의 모든 이미지 파일 처리
        for fname in os.listdir(image_folder_path):
            # PNG 파일만 처리
            if not fname.lower().endswith(".png"):
                continue
            
            # 이미지 경로
            image_path = os.path.join(image_folder_path, fname)
            
            # 대응되는 JSON 파일 경로
            json_fname = fname.replace(".png", ".json")
            json_path = os.path.join(json_folder_path, json_fname)
            
            # JSON 파일 읽기
            description = ""
            symptom = ""
            
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        
                    # JSON 구조에서 정보 추출
                    if "annotations" in json_data and len(json_data["annotations"]) > 0:
                        annotation = json_data["annotations"][0]
                        
                        # diagnosis_info에서 정보 가져오기
                        if "diagnosis_info" in annotation:
                            diag_info = annotation["diagnosis_info"]
                            description = diag_info.get("desc", "")
                            symptom = diag_info.get("symptom", "")
                
                except Exception as e:
                    print(f"⚠️ JSON 읽기 오류 ({json_fname}): {str(e)}")
            else:
                print(f"⚠️ JSON 파일 없음: {json_path}")
            
            # 데이터 추가
            data.append({
                "image": {"path": image_path},
                "label": label_name,
                "description": description,
                "symptom": symptom,
                "system_prompt": "You are an expert dermatologist.",
                "output": ""  # 나중에 ChatGPT가 채울 부분
            })
    
    # DataFrame으로 변환
    df = pd.DataFrame(data)
    print(f"✅ 총 {len(df)}개 데이터 로드 완료")
    
    # 라벨별 개수 확인
    print("\n📊 라벨별 데이터 개수:")
    print(df["label"].value_counts())
    
    # Dataset 객체로 변환
    ds = Dataset.from_pandas(df)
    
    # 이미지 경로를 실제 이미지 객체로 변환
    ds = ds.cast_column("image", Image())
    
    return ds


def save_sample_images(dataset, save_path="./sample_images.png"):
    """
    샘플 이미지들을 파일로 저장
    """
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 5))
    for i in range(min(3, len(dataset["train"]))):
        plt.subplot(1, 3, i+1)
        plt.imshow(dataset["train"][i]["image"])
        plt.title(f"Label: {dataset['train'][i]['label']}")
        plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"📸 샘플 이미지 저장 완료: {save_path}")


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🚀 Training 데이터 처리 중...")
    print("=" * 50)
    trainset = parse_skin_disease_data(train_image_root, train_label_root)

    print("\n" + "=" * 50)
    print("🚀 Validation 데이터 처리 중...")
    print("=" * 50)
    testset = parse_skin_disease_data(val_image_root, val_label_root)

    # DatasetDict으로 합치기
    dataset = DatasetDict({
        "train": trainset,
        "test": testset
    })

    # 결과 확인
    print("\n" + "=" * 50)
    print("📦 최종 Dataset 구조:")
    print("=" * 50)
    print(dataset)

    # 샘플 데이터 확인
    print("\n" + "=" * 50)
    print("🔍 샘플 데이터 확인:")
    print("=" * 50)
    print(f"Label: {dataset['train'][0]['label']}")
    print(f"Description: {dataset['train'][0]['description'][:100]}...")
    print(f"Symptom: {dataset['train'][0]['symptom']}")

    # 저장
    print("\n" + "=" * 50)
    print(f"💾 Dataset 저장 중: {SAVE_PATH}")
    print("=" * 50)
    dataset.save_to_disk(SAVE_PATH)
    print("✅ 저장 완료!")
    
    # 샘플 이미지 저장 (선택사항)
    try:
        save_sample_images(dataset)
    except Exception as e:
        print(f"⚠️ 샘플 이미지 저장 실패: {str(e)}")


if __name__ == "__main__":
    main()