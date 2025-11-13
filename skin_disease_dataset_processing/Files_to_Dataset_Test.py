from datasets import load_from_disk

# 불러오기
dataset = load_from_disk("./skin_disease_dataset")

# 구조 확인
print(dataset)

# 샘플 확인
print(f"\n첫 번째 데이터:")
print(f"Label: {dataset['train'][0]['label']}")
print(f"Description: {dataset['train'][0]['description'][:50]}...")

# 개수 확인
print(f"\nTrain: {len(dataset['train'])}개")
print(f"Test: {len(dataset['test'])}개")

# 라벨 분포 확인
print(f"\nTrain 라벨 분포:")
print(dataset['train'].to_pandas()['label'].value_counts())

print(f"\nTest 라벨 분포:")
print(dataset['test'].to_pandas()['label'].value_counts())
