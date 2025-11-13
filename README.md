# Dataset Processing 프로젝트

화장품 데이터와 피부질환 데이터셋을 처리하고 LLM으로 증강하는 데이터 처리 파이프라인입니다.

## 📋 프로젝트 개요

이 프로젝트는 다음과 같은 주요 기능을 제공합니다:

1. **화장품 데이터 LLM 증강**: Claude API를 사용하여 화장품 제품 정보를 분석하고 구조화된 데이터 생성
2. **화장품 데이터 파일 처리**: 이미지 파일명 변경 및 엑셀 데이터 가공
3. **화장품 벡터 DB 구축**: Qdrant를 사용한 화장품 추천 시스템 구축
4. **피부질환 데이터셋 LLM 증강**: Claude/GPT/Gemma를 사용하여 피부질환 이미지 설명 생성
5. **피부질환 데이터셋 전처리**: 원본 데이터를 HuggingFace Dataset 형식으로 변환

## 📁 프로젝트 구조

```
dataset-processing/
├── cosmetic_data_generation/          # 화장품 데이터 LLM 증강
│   ├── Generate_Cosmetic_Data_Claude.py
│   └── 화장품데이터.xlsx
│
├── cosmetic_data_processing/           # 화장품 데이터 파일 처리
│   ├── process_cosmetic_data.py        # 임베딩 텍스트에서 컬럼 추출
│   ├── rename_images_by_id.py         # 이미지 파일명 변경
│   ├── update_image_names_by_excel.py  # 엑셀 기반 이미지명 업데이트
│   ├── add_extensions_to_img_url.py   # 이미지 URL 확장자 추가
│   └── move_all_images.py              # 이미지 파일 이동
│
├── cosmetic_vector_db/                 # 화장품 벡터 DB
│   ├── build_vector_db.py              # 벡터 DB 구축 및 추천 시스템
│   └── cosmetic_data_processed.xlsx
│
├── skin_disease_dataset_processing/     # 피부질환 데이터셋 전처리
│   ├── Files_to_Dataset.py             # 원본 데이터 → Dataset 변환
│   └── Files_to_Dataset_Test.py
│
├── skin_disease_output_generation/     # 피부질환 LLM 증강
│   ├── Generate_Output_Claude.py       # Claude API로 설명 생성
│   ├── Generate_Output_GPT.py           # GPT API로 설명 생성
│   ├── Generate_Output_Gemma.py         # Gemma 모델로 설명 생성
│   └── prompts.py                      # 시스템 프롬프트
│
├── skin_disease_dataset_with_output/   # 증강된 피부질환 데이터셋
│   ├── extract_skin_samples.py
│   └── explore_all_data.py
│
└── model_pipeline/                     # 모델 검증 파이프라인
    ├── 1_prepare_validation_data.py
    ├── 2_shuffle_validation_data.py
    ├── 3_test_runpod_api.py
    ├── 4_batch_validation.py
    └── diagnosis.py
```

## 🚀 주요 기능

### 1. 화장품 데이터 LLM 증강

**위치**: `cosmetic_data_generation/`

Claude API를 사용하여 화장품 제품 정보를 분석하고 구조화된 데이터를 생성합니다.

**주요 기능**:
- 제품명, 브랜드, 제품설명, 전성분을 기반으로 분석
- 제품유형, 피부타입, 관련 피부질환, 주요 효능, 케어 증상, 핵심 성분 추출
- 임베딩용 텍스트 생성

**사용 방법**:
```python
# Generate_Cosmetic_Data_Claude.py 실행
python cosmetic_data_generation/Generate_Cosmetic_Data_Claude.py
```

**설정**:
- `api_key`: Claude API 키
- `excel_path`: 입력 엑셀 파일 경로
- `start_row`, `end_row`: 처리할 데이터 범위

**출력**:
- `cosmetic_data_processed_YYYYMMDD_HHMMSS.xlsx`: 처리된 데이터

---

### 2. 화장품 데이터 파일 처리

**위치**: `cosmetic_data_processing/`

화장품 데이터의 이미지 파일명을 변경하고 엑셀 데이터를 가공합니다.

#### 2.1 데이터 가공 (`process_cosmetic_data.py`)

임베딩 텍스트에서 주요 효능, 케어 증상, 핵심 성분, 텍스트 설명을 추출합니다.

**사용 방법**:
```python
python cosmetic_data_processing/process_cosmetic_data.py
```

#### 2.2 이미지 파일명 변경 (`update_image_names_by_excel.py`)

엑셀 파일의 `img_url`을 기반으로 이미지 파일명을 변경하고 엑셀을 업데이트합니다.

**사용 방법**:
```python
python cosmetic_data_processing/update_image_names_by_excel.py
```

**입력**:
- `cosmetic_data_processed_with_columns.xlsx`: 제품명, img_url 컬럼 포함
- `화장품_이미지/`: 이미지 파일 폴더

**출력**:
- 이미지 파일명이 `img_url`로 변경됨
- `cosmetic_data_processed_with_updated_images.xlsx`: 업데이트된 엑셀 파일

---

### 3. 화장품 벡터 DB 구축

**위치**: `cosmetic_vector_db/`

Qdrant를 사용하여 화장품 데이터의 벡터 데이터베이스를 구축하고 추천 시스템을 제공합니다.

**주요 기능**:
- 화장품 데이터 임베딩 생성
- Qdrant 벡터 DB에 인덱싱
- 3단계 필터링 검색 (메타데이터 필터 → 유사도 검색 → 피부질환/피부타입 매치 보너스)
- 의학 용어를 화장품 용어로 자동 번역

**사용 방법**:
```python
python cosmetic_vector_db/build_vector_db.py
```

**기능**:
- `load_data()`: 엑셀 파일에서 데이터 로드
- `create_embeddings()`: 텍스트를 벡터로 변환
- `index_products()`: 벡터 DB에 제품 인덱싱
- `smart_search()`: 스마트 검색 (3단계 필터링)
- `recommend_products()`: 전체 추천 시스템

**의존성**:
- `sentence-transformers`: 임베딩 모델 (paraphrase-multilingual-MiniLM-L12-v2)
- `qdrant-client`: 벡터 DB

---

### 4. 피부질환 데이터셋 전처리

**위치**: `skin_disease_dataset_processing/`

원본 피부질환 이미지와 JSON 라벨링 데이터를 HuggingFace Dataset 형식으로 변환합니다.

**주요 기능**:
- 이미지와 JSON 파일 매칭
- 라벨 추출 (건선, 아토피, 여드름, 주사, 지루, 정상)
- DatasetDict 생성 (train/test 분리)

**사용 방법**:
```python
python skin_disease_dataset_processing/Files_to_Dataset.py
```

**입력 구조**:
```
안면부 피부질환 이미지 합성데이터/
├── Training/
│   ├── 원천데이터/
│   │   ├── TS_건선_정면/
│   │   ├── TS_건선_측면/
│   │   └── ...
│   └── 라벨링데이터/
│       ├── TL_건선_정면/
│       └── ...
└── Validation/
    └── ...
```

**출력**:
- `skin_disease_dataset/`: HuggingFace Dataset 형식으로 저장

---

### 5. 피부질환 데이터셋 LLM 증강

**위치**: `skin_disease_output_generation/`

Claude, GPT, Gemma를 사용하여 피부질환 이미지에 대한 상세 설명을 생성합니다.

#### 5.1 Claude API (`Generate_Output_Claude.py`)

**사용 방법**:
```python
python skin_disease_output_generation/Generate_Output_Claude.py
```

**설정**:
- `ANTHROPIC_API_KEY`: Claude API 키
- `NUM_SAMPLES`: 처리할 샘플 개수
- `DATASET_PATH`: 입력 데이터셋 경로
- `SAVE_PATH`: 저장 경로

**출력**:
- `claude_outputs.txt`: 생성된 설명 텍스트 파일

#### 5.2 GPT API (`Generate_Output_GPT.py`)

**사용 방법**:
```python
python skin_disease_output_generation/Generate_Output_GPT.py
```

**설정**:
- `OPENAI_API_KEY`: OpenAI API 키
- `DATASET_PATH`: 입력 데이터셋 경로
- `SAVE_PATH`: 저장 경로

#### 5.3 Gemma 모델 (`Generate_Output_Gemma.py`)

로컬 또는 RunPod에서 실행되는 Gemma 모델을 사용합니다.

**사용 방법**:
```python
python skin_disease_output_generation/Generate_Output_Gemma.py
```

---

## 📦 설치 및 요구사항

### 필수 패키지

```bash
# 데이터 처리
pip install pandas openpyxl

# 벡터 DB
pip install sentence-transformers qdrant-client

# LLM API
pip install anthropic openai langchain-openai

# 데이터셋 처리
pip install datasets pillow

# 이미지 처리
pip install pillow

# 기타
pip install tqdm
```

### 환경 변수 설정

API 키는 각 스크립트 내에서 직접 설정하거나 환경 변수로 설정할 수 있습니다.

---

## 🔄 워크플로우

### 화장품 데이터 처리 파이프라인

1. **데이터 증강**: `cosmetic_data_generation/Generate_Cosmetic_Data_Claude.py`
   - 원본 엑셀 → LLM 분석 → 구조화된 데이터

2. **데이터 가공**: `cosmetic_data_processing/process_cosmetic_data.py`
   - 임베딩 텍스트에서 컬럼 추출

3. **이미지 파일명 변경**: `cosmetic_data_processing/update_image_names_by_excel.py`
   - 이미지 파일명을 ID 기반으로 변경

4. **벡터 DB 구축**: `cosmetic_vector_db/build_vector_db.py`
   - 벡터 임베딩 생성 및 인덱싱

### 피부질환 데이터 처리 파이프라인

1. **데이터셋 변환**: `skin_disease_dataset_processing/Files_to_Dataset.py`
   - 원본 이미지/JSON → HuggingFace Dataset

2. **LLM 증강**: `skin_disease_output_generation/Generate_Output_*.py`
   - 이미지 설명 생성 (Claude/GPT/Gemma)

3. **데이터 검증**: `model_pipeline/` 스크립트들
   - 검증 데이터 준비 및 배치 검증

---

## 📝 주요 데이터 형식

### 화장품 데이터 컬럼

- `브랜드`: 브랜드명
- `제품명`: 제품명
- `제품설명`: 제품 설명
- `전성분`: 전성분 리스트
- `임베딩_텍스트`: LLM이 생성한 구조화된 텍스트
- `제품유형`: 크림, 로션, 세럼 등
- `피부타입`: 지성, 건성, 복합성, 민감성
- `관련_피부질환`: 건선, 아토피, 여드름, 주사, 지루, 정상
- `주요_효능`: 보습, 진정, 피부장벽강화 등
- `케어_증상`: 건조, 인설, 홍조, 가려움 등
- `핵심_성분`: 주요 성분 리스트
- `가격`: 제품 가격

### 피부질환 데이터 형식

```python
{
    "image": PIL.Image,           # 이미지 객체
    "label": str,                  # 라벨 (건선, 아토피, 여드름, 주사, 지루, 정상)
    "description": str,            # 질병 특징 설명
    "symptom": str,                # 증상
    "system_prompt": str,          # 시스템 프롬프트
    "output": str                  # LLM이 생성한 설명
}
```

---

## ⚠️ 주의사항

1. **API 키 보안**: API 키는 코드에 하드코딩하지 말고 환경 변수나 설정 파일로 관리하세요.
2. **비용 관리**: LLM API 사용 시 비용이 발생할 수 있으므로 샘플 개수를 조절하세요.
3. **데이터 백업**: 원본 데이터는 반드시 백업하세요.
4. **파일 경로**: 각 스크립트의 경로 설정을 프로젝트 구조에 맞게 수정하세요.

---

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

---

## 👥 기여

프로젝트 개선 사항이나 버그 리포트는 이슈로 등록해주세요.

---

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 생성해주세요.

