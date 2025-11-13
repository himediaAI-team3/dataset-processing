#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation 데이터 섞기 스크립트
- validation_dataset.json의 데이터 순서를 랜덤하게 섞기
- 원본은 백업하고 새로운 파일 생성
"""

import json
import random
from pathlib import Path
from datetime import datetime

def shuffle_validation_data():
    """validation 데이터 순서 섞기"""
    
    base_dir = Path(__file__).parent
    original_file = base_dir / "validation_dataset.json"
    backup_file = base_dir / "validation_dataset_original.json"
    
    print("[INFO] Validation 데이터 섞기 시작...")
    
    # 원본 파일 로드
    with open(original_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"[INFO] 총 {len(dataset['data'])}개 샘플 로드")
    
    # 원본 백업
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 원본 백업 완료: {backup_file}")
    
    # 데이터 섞기 (재현 가능하도록 시드 고정)
    random.seed(42)  # 고정 시드로 재현 가능
    random.shuffle(dataset['data'])
    
    # ID 재할당
    for i, item in enumerate(dataset['data'], 1):
        item['id'] = i
    
    # 메타데이터 업데이트
    dataset['info']['shuffled_at'] = datetime.now().isoformat()
    dataset['info']['shuffle_seed'] = 42
    dataset['info']['description'] += " (랜덤 섞기 완료)"
    
    # 섞인 데이터 저장
    with open(original_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print("[SUCCESS] 데이터 섞기 완료!")
    print(f"[INFO] 섞인 데이터 저장: {original_file}")
    
    # 섞인 결과 확인
    print("\n[INFO] 섞인 순서 확인 (처음 10개):")
    for i in range(min(10, len(dataset['data']))):
        item = dataset['data'][i]
        print(f"  {i+1:2d}. {item['disease_category']:4s} - {item['image_filename']}")
    
    print(f"\n[INFO] 질환별 분포 확인:")
    disease_count = {}
    for item in dataset['data']:
        disease = item['disease_category']
        disease_count[disease] = disease_count.get(disease, 0) + 1
    
    for disease, count in disease_count.items():
        print(f"  - {disease}: {count}개")

if __name__ == "__main__":
    shuffle_validation_data()
