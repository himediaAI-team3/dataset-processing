from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from PIL import Image
import base64
import io
import re
from pathlib import Path
from app.repository.diagnosis import DiagnosisRepository
from app.repository.file import FileRepository
from app.models.diagnosis import Diagnosis
from app.core.config.ai import RUNPOD_API_KEY, RUNPOD_API_ENDPOINT
from app.core.config.file import get_upload_path


class DiagnosisService:
    
    # 진단 프롬프트 (수정 가능)
    DIAGNOSIS_INSTRUCTION = """너는 안면부 피부 질환을 분석하는 전문 AI이다. 
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
  <summary>제공된 이미지는 얼굴 부위가 아니거나 / 이미지 품질이 불량하여 피부 질환을 판단할 수 없습니다.</summary>
"""
    
    @staticmethod
    def create_diagnosis(db: Session, analysis_id: int) -> Diagnosis:
        """
        피부 진단 생성 (AI 모델 사용)
        
        Args:
            db: 데이터베이스 세션
            analysis_id: 분석 ID
            
        Returns:
            Diagnosis 객체
        """
        # 1. 업로드된 이미지 파일 정보 조회
        file_info = FileRepository.get_by_analysis_id(db, analysis_id)
        if not file_info:
            raise ValueError(f"분석 ID {analysis_id}에 대한 파일을 찾을 수 없습니다.")
        
        # 2. 로컬 파일 경로 구성
        # file_url이 이미 전체 상대 경로를 포함하므로 그대로 사용
        image_path = Path(file_info.file_url)
        
        if not image_path.exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        # 3. 이미지 로드 및 base64 인코딩
        image = Image.open(str(image_path)).convert("RGB")
        
        # PIL 이미지를 base64로 인코딩
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # 4. OpenAI 클라이언트 초기화 및 ChatOpenAI 설정
        try:
            # API 키 확인
            if not RUNPOD_API_KEY or RUNPOD_API_KEY == "your_api_key_here" or RUNPOD_API_KEY == "EMPTY":
                raise ValueError("RUNPOD_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
            
            print(f"DEBUG - API 키 확인: {RUNPOD_API_KEY[:10]}... (길이: {len(RUNPOD_API_KEY)})")
            print(f"DEBUG - 엔드포인트: {RUNPOD_API_ENDPOINT}")
            
            # ChatOpenAI 초기화 (api_key와 base_url 직접 전달)
            llm = ChatOpenAI(
                model="oneandthree/qwen2.5vl_7b_skin_dataset_3000steps_r128_b8_merged",
                api_key=RUNPOD_API_KEY,
                base_url=RUNPOD_API_ENDPOINT
            )
            
            print("DEBUG - ChatOpenAI 초기화 성공")
        except Exception as e:
            print(f"AI 클라이언트 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            # 기본 진단 데이터로 폴백
            diagnosis_data = {
                "analysis_id": analysis_id,
                "disease_name": "진단 실패",
                "summary": f"AI 모델 연결 실패: {str(e)}"
            }
            return DiagnosisRepository.create(db, diagnosis_data)
        
        # 5. 메시지 구성
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": DiagnosisService.DIAGNOSIS_INSTRUCTION},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            )
        ]
        
        # 6. AI 모델 호출
        try:
            response = llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"AI 모델 호출 실패: {e}")
            # 기본 진단 데이터로 폴백
            diagnosis_data = {
                "analysis_id": analysis_id,
                "disease_name": "진단 실패",
                "summary": f"AI 모델 호출 실패: {str(e)}"
            }
            return DiagnosisRepository.create(db, diagnosis_data)
        
        # 7. 응답 파싱
        
        # <label>과 <summary> 태그에서 내용 추출
        label_match = re.search(r'<label>(.*?)</label>', response_text, re.DOTALL)
        summary_match = re.search(r'<summary>(.*?)</summary>', response_text, re.DOTALL)
        
        disease_name = label_match.group(1).strip() if label_match else "진단 정보 없음"
        summary = summary_match.group(1).strip() if summary_match else response_text
        
        # 8. 진단 데이터 저장
        diagnosis_data = {
            "analysis_id": analysis_id,
            "disease_name": disease_name,
            "summary": summary
        }
        
        return DiagnosisRepository.create(db, diagnosis_data)

