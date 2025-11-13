#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation 데이터 준비 스크립트
- model_pipeline/Validation 폴더의 이미지들과 라벨링 데이터를 매칭
- validation_dataset.json 파일로 메타데이터 저장
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime

def load_label_data(label_file_path):
    """라벨링 JSON 파일을 로드하고 필요한 정보 추출"""
    try:
        with open(label_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        annotation = data['annotations'][0]  # 첫 번째 annotation 사용
        
        return {
            'identifier': annotation['identifier'],
            'diagnosis_name': annotation['diagnosis_info']['diagnosis_name'],
            'onset': annotation['diagnosis_info'].get('onset', ''),
            'distribution': annotation['diagnosis_info'].get('distribution', ''),
            'bodypart': annotation['diagnosis_info'].get('bodypart', ''),
            'symptom': annotation['diagnosis_info'].get('symptom', ''),
            'description': annotation['diagnosis_info'].get('desc', ''),
            'gender': annotation['generated_parameters'].get('gender', ''),
            'age_range': annotation['generated_parameters'].get('age_range', ''),
            'race': annotation['generated_parameters'].get('race', ''),
            'image_width': annotation['photograph']['width'],
            'image_height': annotation['photograph']['height']
        }
    except Exception as e:
        print(f"라벨 파일 로드 실패: {label_file_path}, 오류: {e}")
        return None

def find_matching_label(image_filename, label_directories):
    """이미지 파일명에 해당하는 라벨링 파일 찾기"""
    # 파일명에서 확장자 제거
    base_name = os.path.splitext(image_filename)[0]
    
    # 각 라벨링 디렉토리에서 매칭되는 파일 찾기
    for label_dir in label_directories:
        label_file = os.path.join(label_dir, f"{base_name}.json")
        if os.path.exists(label_file):
            return label_file
    
    return None

def prepare_validation_dataset():
    """Validation 데이터셋 준비"""
    
    # 경로 설정
    base_dir = Path(__file__).parent
    validation_dir = base_dir / "Validation"
    image_base_dir = validation_dir / "원천데이터"
    label_base_dir = validation_dir / "라벨링데이터"
    
    # 질환 목록
    diseases = ['건선', '아토피', '여드름', '정상', '주사', '지루']
    
    # 라벨링 디렉토리 목록
    label_directories = [label_base_dir / f"VL_{disease}_정면" for disease in diseases]
    
    validation_dataset = []
    
    print("[INFO] Validation 데이터 준비 시작...")
    print(f"[INFO] 이미지 디렉토리: {image_base_dir}")
    print(f"[INFO] 라벨링 디렉토리: {label_base_dir}")
    print()
    
    total_images = 0
    matched_images = 0
    
    # 각 질환별로 처리
    for disease in diseases:
        image_dir = image_base_dir / f"VS_{disease}_정면"
        
        if not image_dir.exists():
            print(f"[WARNING] 이미지 디렉토리가 없습니다: {image_dir}")
            continue
            
        # 해당 질환의 이미지 파일들 가져오기
        image_files = list(image_dir.glob("*.png"))
        print(f"[INFO] {disease}: {len(image_files)}개 이미지 발견")
        
        disease_count = 0
        
        for image_file in image_files:
            total_images += 1
            
            # 매칭되는 라벨링 파일 찾기
            label_file = find_matching_label(image_file.name, label_directories)
            
            if label_file:
                # 라벨링 데이터 로드
                label_data = load_label_data(label_file)
                
                if label_data:
                    # validation 데이터셋에 추가
                    validation_item = {
                        'id': len(validation_dataset) + 1,
                        'image_path': str(image_file.relative_to(base_dir)),
                        'image_filename': image_file.name,
                        'label_path': str(Path(label_file).relative_to(base_dir)),
                        'disease_category': disease,
                        'true_label': label_data['diagnosis_name'],
                        'metadata': label_data
                    }
                    
                    validation_dataset.append(validation_item)
                    matched_images += 1
                    disease_count += 1
                    
                    print(f"  [OK] {image_file.name} -> {label_data['diagnosis_name']}")
                else:
                    print(f"  [ERROR] 라벨 데이터 로드 실패: {image_file.name}")
            else:
                print(f"  [ERROR] 매칭되는 라벨 파일 없음: {image_file.name}")
        
        print(f"   [RESULT] {disease}: {disease_count}개 매칭 완료")
        print()
    
    # 결과 저장
    output_file = base_dir / "validation_dataset.json"
    
    # 메타데이터 추가
    dataset_info = {
        'created_at': datetime.now().isoformat(),
        'total_images': len(validation_dataset),
        'diseases': diseases,
        'images_per_disease': {disease: len([item for item in validation_dataset if item['disease_category'] == disease]) 
                              for disease in diseases},
        'description': 'RunPod 모델 성능 평가를 위한 Validation 데이터셋'
    }
    
    final_dataset = {
        'info': dataset_info,
        'data': validation_dataset
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
    
    # 결과 요약
    print("=" * 50)
    print("[SUCCESS] Validation 데이터셋 준비 완료!")
    print(f"[INFO] 저장 파일: {output_file}")
    print(f"[INFO] 총 이미지 수: {total_images}")
    print(f"[INFO] 매칭 성공: {matched_images}")
    print(f"[INFO] 매칭 실패: {total_images - matched_images}")
    print()
    
    print("질환별 데이터 수:")
    for disease in diseases:
        count = len([item for item in validation_dataset if item['disease_category'] == disease])
        print(f"  - {disease}: {count}개")
    
    print()
    print("[NEXT] 다음 단계: 2_test_runpod_api.py 실행")
    
    return validation_dataset

if __name__ == "__main__":
    try:
        dataset = prepare_validation_dataset()
        print(f"\n[SUCCESS] 성공적으로 {len(dataset)}개의 validation 샘플을 준비했습니다!")
        
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
