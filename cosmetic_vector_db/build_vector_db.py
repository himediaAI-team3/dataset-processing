"""
화장품 벡터 DB 구축 (심플 버전)
"""

import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class CosmeticVectorDB:
    def __init__(self):
        # 임베딩 모델 로드 (한국어 지원)
        self.embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        
        # Qdrant 클라이언트 (메모리 모드)
        self.qdrant_client = QdrantClient(":memory:")
        
        # 컬렉션 이름
        self.collection_name = "cosmetic_products"
    
    def load_data(self, excel_path: str) -> pd.DataFrame:
        """엑셀 파일에서 화장품 데이터 로드"""
        return pd.read_excel(excel_path)
    
    def create_embeddings(self, texts: list):
        """텍스트 리스트를 벡터로 변환"""
        return self.embedding_model.encode(texts, show_progress_bar=True)
    
    def setup_collection(self):
        """Qdrant 컬렉션 생성"""
        # 기존 컬렉션 삭제
        try:
            self.qdrant_client.delete_collection(self.collection_name)
        except:
            pass
        
        # 새 컬렉션 생성
        embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE
            )
        )
    
    def index_products(self, df: pd.DataFrame):
        """화장품 데이터를 벡터 DB에 저장"""
        
        # 1. 임베딩 생성 (임베딩_텍스트 컬럼만 사용)
        embedding_texts = df['임베딩_텍스트'].fillna('').tolist()
        embeddings = self.create_embeddings(embedding_texts)
        
        # 2. Qdrant에 저장할 포인트 생성
        points = []
        for idx, row in df.iterrows():
            # 메타데이터 구성
            payload = {
                # 기본 정보
                "제품명": str(row['제품명']),
                "브랜드": str(row['브랜드']),
                
                # 필터링용 (가격만)
                "가격": int(row.get('가격', 0)) if pd.notna(row.get('가격')) else 0,
                
                # 참고용 (결과 표시용)
                "제품유형": str(row.get('제품유형', '')),
                "피부타입": str(row.get('피부타입', '')),
                "관련_피부질환": row.get('관련_피부질환', []),  # 리스트 그대로 저장!
                "제품설명": str(row.get('제품설명', '')),
            }
            
            points.append(PointStruct(
                id=idx,
                vector=embeddings[idx].tolist(),
                payload=payload
            ))
        
        # 3. Qdrant에 업로드
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    def search(self, query: str, price_limit: int = None, top_k: int = 3):
        """
        기본 화장품 검색 (하위 호환성 유지)
        """
        # 1. 쿼리를 벡터로 변환
        query_vector = self.embedding_model.encode([query])[0]
        
        # 2. 검색 조건 설정
        search_params = {
            "collection_name": self.collection_name,
            "query_vector": query_vector.tolist(),
            "limit": top_k
        }
        
        # 3. 가격 필터링 (선택사항)
        if price_limit:
            from qdrant_client.models import Filter, FieldCondition, Range
            search_params["query_filter"] = Filter(
                must=[
                    FieldCondition(
                        key="가격",
                        range=Range(lte=price_limit)
                    )
                ]
            )
        
        # 4. 검색 실행
        results = self.qdrant_client.search(**search_params)
        
        # 5. 결과 정리
        products = []
        for result in results:
            product = result.payload
            product['유사도점수'] = result.score
            products.append(product)
        
        return products
    
    def smart_search(self, query: str, ai_diagnosis: dict, user_input: dict, top_k: int = 3):
        """
        3단계 필터링 + 유사도 검색
        
        Args:
            query: 검색 쿼리
            ai_diagnosis: AI 진단 결과 {"피부질환": "건선", "설명": "..."}
            user_input: 사용자 입력 {"피부타입": "건성", "가격대": 30000}
            top_k: 최종 반환할 제품 수
        """
        from qdrant_client.models import Filter, FieldCondition, Range, MatchText
        
        # 1단계: 메타데이터 필터링 (하드 제약)
        filters = []
        
        # 가격 필터
        price_limit = user_input.get("가격대")
        if price_limit and price_limit > 0:
            filters.append(FieldCondition(
                key="가격",
                range=Range(lte=price_limit)
            ))
        
        # 피부타입 필터 -> 하드 필터 대신 소프트 스코어링으로 변경!
        # (하드 필터는 너무 제한적이므로 3단계에서 보너스 점수로 처리)
        
        # 2단계: 임베딩 유사도 검색
        query_vector = self.embedding_model.encode([query])[0]
        
        search_params = {
            "collection_name": self.collection_name,
            "query_vector": query_vector.tolist(),
            "limit": top_k * 10  # 임베딩 유사도로 넓게 검색 (임베딩 유사도 30개 -> 최종 화장품 추천 3개)
        }
        
        if filters:
            search_params["query_filter"] = Filter(must=filters)
        
        candidates = self.qdrant_client.search(**search_params)
        
        # 3단계: 피부질환 + 피부타입 매치 보너스
        target_condition = ai_diagnosis.get("피부질환")
        user_skin_types = user_input.get("피부타입", "")
        
        # 디버깅: 타겟 조건 출력
        print(f"[DEBUG] 찾는 피부질환: '{target_condition}'")
        
        # 사용자 피부타입을 리스트로 변환
        if isinstance(user_skin_types, str):
            user_skin_types_list = [s.strip() for s in user_skin_types.split(',')]
        else:
            user_skin_types_list = user_skin_types if user_skin_types else []
        
        products = []
        skin_condition_matches = 0  # 매치 카운터
        
        for result in candidates:
            product = result.payload
            score = result.score
            bonuses = []
            original_score = score  # 원본 점수 저장
            
            # 1. 피부질환 매치 보너스
            product_conditions = product.get('관련_피부질환', [])
            # 리스트가 아닌 경우 (기존 문자열 데이터) 처리
            if isinstance(product_conditions, str):
                try:
                    # 문자열로 저장된 리스트를 파싱 (예: "['건선', '아토피']")
                    import ast
                    product_conditions = ast.literal_eval(product_conditions)
                except:
                    # 파싱 실패시 빈 리스트
                    product_conditions = []
            
            print(f"[CHECK] 제품: {product.get('제품명', 'N/A')[:20]}... | 관련질환: {product_conditions} | 매치: {target_condition in product_conditions if target_condition else False}")
            
            if target_condition and target_condition in product_conditions:
                score += 0.3  # 피부질환 보너스
                bonuses.append('피부질환_매치')
                skin_condition_matches += 1
                print(f"  [MATCH] 피부질환 매치! 점수: {original_score:.3f} -> {score:.3f}")
            
            # 2. 피부타입 매치 보너스
            product_skin_types = product.get('피부타입', '')
            for user_skin_type in user_skin_types_list:
                if user_skin_type in product_skin_types:
                    score += 0.2  # 피부타입 보너스
                    bonuses.append(f'피부타입_매치_{user_skin_type}')
                    break  # 하나만 매치되면 충분
            
            product['매치_보너스'] = bonuses if bonuses else False
            product['유사도점수'] = score
            product['원본_유사도'] = original_score  # 디버깅용
            products.append(product)
        
        print(f"[RESULT] 총 {len(candidates)}개 후보 중 {skin_condition_matches}개가 피부질환 매치됨")
        
        # 4단계: 최종 정렬 및 반환
        products.sort(key=lambda x: x['유사도점수'], reverse=True)
        return products[:top_k]
    
    def translate_medical_to_cosmetic(self, medical_description: str, skin_condition: str) -> str:
        """
        의학적 진단 용어를 화장품 용어로 번역
        
        Args:
            medical_description: 의학적 진단 설명
            skin_condition: 피부질환명
            
        Returns:
            화장품 용어로 번역된 설명
        """
        # 피부질환별 핵심 화장품 키워드 매핑
        condition_keywords = {
            "건선": [
                "피부장벽 강화", "보습", "진정", "각질 케어", "인설 완화",
                "세라마이드", "콜레스테롤", "판테놀", "시어버터", 
                "건조 완화", "민감성 피부", "수분 공급", "피부 재생"
            ],
            "아토피": [
                "피부장벽 복원", "보습", "진정", "가려움 완화", "염증 진정",
                "세라마이드", "히알루론산", "알란토인", "센텔라",
                "민감성 피부", "수분 보충", "자극 완화", "스크래치 케어"
            ],
            "여드름": [
                "피지 조절", "모공 케어", "각질 제거", "항염", "염증 진정",
                "살리실산", "나이아신아마이드", "징크", "티트리",
                "지성 피부", "블랙헤드", "화이트헤드", "논코메도제닉"
            ],
            "주사": [
                "홍조 완화", "진정", "혈관 케어", "민감성 피부", "자극 완화",
                "센텔라", "알란토인", "나이아신아마이드", "아젤라산",
                "쿨링", "항염", "발적 완화", "모세혈관 케어"
            ],
            "지루": [
                "피지 조절", "각질 케어", "항염", "T존 케어", "기름기 조절",
                "살리실산", "징크 피리치온", "나이아신아마이드", "티트리",
                "지성 피부", "인설 케어", "가려움 완화", "유수분 밸런스"
            ],
            "정상": [
                "보습", "수분 공급", "유수분 밸런스", "피부 보호", "영양 공급",
                "히알루론산", "글리세린", "판테놀", "비타민E",
                "건강한 피부", "윤기", "탄력", "매끄러운 질감"
            ]
        }
        
        # 의학 용어 → 화장품 용어 매핑
        medical_to_cosmetic = {
            # 건선 관련
            "홍반성 판": "홍조 피부장벽손상",
            "은백색 인설": "각질 인설 건조",
            "병변": "문제 피부",
            "경계가 명확": "국소적 피부트러블",
            "헤어라인": "이마 경계부위",
            "두꺼운 인설": "심한 각질 건조",
            "염증 반응": "자극 홍조",
            
            # 아토피 관련  
            "홍조": "염증 자극",
            "가려움": "간지러움 자극",
            "긁은 자국": "상처 손상",
            "거친 피부": "건조 거칠음",
            "스크래치 자국": "긁힌 자국 손상",
            "벗겨짐 현상": "각질 탈락",
            "리켄화": "피부 두꺼워짐",
            "경계가 모호": "불규칙한 트러블",
            
            # 여드름 관련
            "염증성 구진": "염증 뾰루지",
            "농포": "화농성 여드름",
            "면포성 병변": "블랙헤드 화이트헤드",
            "피지 분비": "기름기 과다분비",
            "모공 확대": "넓어진 모공",
            "홍반성 구진": "빨간 뾰루지",
            "농화": "고름 염증",
            "피지선": "기름샘 활성",
            
            # 주사 관련
            "지속적인 홍반": "만성 홍조",
            "모세혈관 확장": "혈관 확장 홍조",
            "텔랑지에타지아": "실핏줄 확장",
            "발적": "빨갛게 달아오름",
            "경계가 불명확": "번진 홍조",
            "자극적인 징후": "민감 반응",
            "구진성 병변": "돌기 염증",
            
            # 지루 관련
            "기름진 노란색 인설": "유분기 많은 각질",
            "T존": "이마코턱 기름부위",
            "기름짐": "과도한 유분",
            "비늘 같은 인설": "각질 비듬",
            "습기 있는 느낌": "끈적한 유분감",
            
            # 정상 관련
            "특별한 병변": "특이사항",
            "건강한 광택": "자연스러운 윤기",
            "매끄럽고 고른 질감": "부드러운 피부결",
            "수분과 유분의 균형": "유수분 밸런스"
        }
        
        # 번역 수행
        translated = medical_description
        for medical_term, cosmetic_term in medical_to_cosmetic.items():
            translated = translated.replace(medical_term, cosmetic_term)
        
        # 해당 피부질환의 핵심 키워드 추가
        keywords = condition_keywords.get(skin_condition, [])
        cosmetic_keywords = " ".join(keywords[:8])  # 상위 8개만 사용
        
        return f"{translated} {cosmetic_keywords}"

    def create_search_query(self, ai_diagnosis: dict, user_input: dict) -> str:
        """
        AI 진단 + 사용자 입력 → 검색 쿼리 자동 생성 (도메인 번역 적용)
        
        Args:
            ai_diagnosis: {"피부질환": "건선", "설명": "..."}
            user_input: {"피부타입": "민감성", "가격대": 30000}
        
        Returns:
            검색 쿼리 문자열
        """
        query_parts = []
        
        # 1. 피부질환 강조 (3번 반복으로 가중치 강화)
        skin_condition = ai_diagnosis.get("피부질환", "")
        if skin_condition:
            query_parts.extend([skin_condition] * 3)
        
        # 2. 피부질환 진단의 의학적 설명을 화장품 용어로 번역 ⭐ 핵심 개선!
        description = ai_diagnosis.get("설명", "")
        if description and skin_condition:
            cosmetic_description = self.translate_medical_to_cosmetic(description, skin_condition)
            query_parts.append(cosmetic_description)
        
        # 3. 사용자 피부타입
        skin_type = user_input.get("피부타입", "")
        if skin_type:
            query_parts.append(f"{skin_type} 피부")
        
        # 4. 케어 관련 단어 추가
        query_parts.extend(["케어", "화장품", "스킨케어"])
        
        # 5. 최종 쿼리 생성
        query = " ".join(query_parts)
        return query
    
    def recommend_products(self, ai_diagnosis: dict, user_input: dict, top_k: int = 3) -> dict:
        """
        전체 추천 시스템 (3단계 필터링 적용)
        
        Args:
            ai_diagnosis: AI 진단 결과
            user_input: 사용자 입력 (피부타입, 가격대)
            top_k: 추천할 제품 수
        
        Returns:
            추천 결과 딕셔너리
        """
        # 1. 검색 쿼리 자동 생성
        query = self.create_search_query(ai_diagnosis, user_input)
        
        # 2. 스마트 검색 (3단계 필터링)
        products = self.smart_search(
            query=query,
            ai_diagnosis=ai_diagnosis,
            user_input=user_input,
            top_k=top_k
        )
        
        # 3. 결과 구성
        recommendation = {
            "입력정보": {
                "피부질환": ai_diagnosis.get("피부질환"),
                "피부타입": user_input.get("피부타입"),
                "가격대": user_input.get("가격대"),
                "생성된_쿼리": query
            },
            "추천제품": products,
            "추천개수": len(products)
        }
        
        return recommendation
    
    def print_recommendation(self, recommendation: dict):
        """추천 결과를 보기 좋게 출력"""
        print("=" * 60)
        print("화장품 추천 결과")
        print("=" * 60)
        
        info = recommendation["입력정보"]
        print(f"피부질환: {info['피부질환']}")
        print(f"피부타입: {info['피부타입']}")
        print(f"가격대: {info['가격대']:,}원 이하")
        print(f"검색쿼리: {info['생성된_쿼리']}")
        
        print(f"\n추천 제품 ({recommendation['추천개수']}개):")
        print("-" * 60)
        
        for i, product in enumerate(recommendation["추천제품"], 1):
            print(f"\n[{i}] {product['제품명']}")
            print(f"    브랜드: {product['브랜드']}")
            print(f"    가격: {product['가격']:,}원")
            print(f"    유사도: {product['유사도점수']:.3f}")
            
            # 관련 피부질환을 문자열로 표시
            conditions = product['관련_피부질환']
            if isinstance(conditions, list):
                conditions_str = ', '.join(conditions)
            else:
                conditions_str = str(conditions)
            print(f"    관련 피부질환: {conditions_str}")
            
            # 매치 보너스 표시
            bonuses = product.get('매치_보너스', False)
            if bonuses:
                bonus_text = ", ".join(bonuses)
                print(f"    매치 보너스: {bonus_text}")
            
            print(f"    피부타입: {product['피부타입']}")


# ============================================
# 사용 예시
# ============================================

if __name__ == "__main__":
    
    # 1. 벡터 DB 초기화
    db = CosmeticVectorDB()
    
    # 2. 화장품 데이터 로드
    df = db.load_data("cosmetic_data_processed.xlsx")
    
    # 3. 컬렉션 생성
    db.setup_collection()
    
    # 4. 데이터 인덱싱
    db.index_products(df)
    
    print("벡터 DB 구축 완료!\n")
    
    # 5. 테스트 케이스 정의
    test_cases = [
        {
            # 케이스 1: 건선 환자
            "ai_diagnosis": {
                "피부질환": "건선",
                "설명": "이미지에서는 이마와 양 볼 부위에 경미한 홍반이 관찰되며, 피부 표면의 질감은 약간 건조한 느낌을 줍니다. 그러나 전반적으로 두꺼운 은백색 인설이 뚜렷하게 보이지 않아서, 보다 초기 단계의 건선으로 보일 수 있습니다. 병변의 경계는 명확하게 구분되어 있으며, 주변 정상 피부와 대조됩니다. 환자의 피부는 전반적으로 약간의 염증 반응이 있으나, 일반적인 건선의 전형적인 사진과는 다른 심한 병변은 관찰되지 않습니다."            },
            "user_input": {
                "피부타입": "민감성",
                "가격대": 80000
            }
        },
        {
            # 케이스 2: 아토피 환자
            "ai_diagnosis": {
                "피부질환": "아토피",
                "설명": "이미지에서 환자의 얼굴에는 드물게 나타나는 건조하고 붉은 피부가 관찰됩니다. 특히, 뺨 부분에 뚜렷한 홍조와 함께 스크래치 자국이 존재하며, 병변이 불규칙하고 경계가 모호한 형태를 띠고 있습니다. 피부가 극도로 건조해 보이며, 종종 벗겨짐 현상도 눈에 띄는 특징을 보입니다. 이러한 소견은 아토피 피부염의 전형적인 모습이며, 만성적일 경우 피부가 두꺼워지는 리켄화 현상도 관찰될 수 있습니다."
            },
            "user_input": {
                "피부타입": "건성",
                "가격대": 80000
            }
        },
        {
            # 케이스 3: 여드름 환자
            "ai_diagnosis": {
                "피부질환": "여드름",
                "설명": "이미지에서는 이마와 뺨 부위에 여러 개의 홍반성 구진이 관찰됩니다. 병변들은 비교적 작은 크기로, 중심부에 농화가 있는 농포도 일부 포함되어 있습니다. 이마 중앙과 양쪽 뺨에서 피지선이 발달한 부위에 염증성 병변들이 집중되어 있으며, 경계는 개별적으로 명확하게 구분되어 있습니다. 이러한 임상 소견은 여드름의 전형적인 특징으로, 피지 분비 증가와 염증이 동반된 양상으로 보입니다."
            },
            "user_input": {
                "피부타입": "지성",
                "가격대": 80000
            }
        },
        {
            # 케이스 4: 주사 환자
            "ai_diagnosis": {
                "피부질환": "주사",
                "설명": "이미지에서는 중앙 얼굴부에 지속적인 홍반이 관찰됩니다. 뺨, 코, 이마 부위에 눈에 띄는 경계가 불명확한 발적이 있으며, 작은 혈관이 드러난 모세혈관 확장(텔랑지에타지아)도 보입니다. 얼굴의 홍반은 대칭적으로 나타나며, 이는 주사의 전형적인 소견입니다. 피부는 쉽게 붉어지고, 환자가 불편함을 느낄 수 있는 자극적인 징후가 나타날 수도 있습니다. 추가적으로, 홍반과 함께 미세한 구진성 병변이 보이고 있어 염증성 반응이 동반되고 있을 가능성이 있습니다."            },
            "user_input": {
                "피부타입": "민감성",
                "가격대": 80000
            }
        },
        {
            # 케이스 5: 지루 환자
            "ai_diagnosis": {
                "피부질환": "지루",
                "설명": "이미지에서는 얼굴의 T존 부위와 코 주변에 약간의 홍반과 함께 기름진 노란색 인설이 관찰됩니다. 병변의 경계는 상대적으로 명확하게 나타나 있으며, 피부의 기름짐과 습기 있는 느낌이 강조됩니다. 얼굴의 특정 부위, 특히 이마와 뺨에 미세한 비늘 같은 인설이 존재하여, 지루성 피부염의 전형적인 특징을 나타냅니다. 추가적으로, 가벼운 가려움증이 체감될 수 있으며, 두피에도 동반될 가능성이 있습니다."
            },
            "user_input": {
                "피부타입": "지성",
                "가격대": 80000
            }
        },
        {
            # 케이스 6: 정상 
            "ai_diagnosis": {
                "피부질환": "정상",
                "설명": "이미지에서는 특별한 병변이나 이상 소견이 관찰되지 않습니다. 피부 톤이 균일하고 건강한 광택을 보이며, 표면이 매끄럽고 고른 질감을 유지하고 있습니다. 모공이 잘 보이고, 홍반, 구진, 인설 등의 병적 변화가 없으며, 전반적으로 수분과 유분의 균형이 잘 맞춰진 정상 피부 상태를 나타냅니다. 이러한 특성들은 정상 피부의 전형적인 소견입니다."            },
            "user_input": {
                "피부타입": "복합성",
                "가격대": 80000
            }
        }
    ]
    
    # 6. 테스트 실행
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"테스트 케이스 {i}")
        print(f"{'='*60}")
        
        # 추천 실행
        recommendation = db.recommend_products(
            ai_diagnosis=test_case["ai_diagnosis"],
            user_input=test_case["user_input"],
            top_k=3
        )
        
        # 결과 출력
        db.print_recommendation(recommendation)

