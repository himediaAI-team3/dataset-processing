import pandas as pd
import os
from pathlib import Path

def update_image_names_by_excel():
    """
    cosmetic_data_processed_with_columns.xlsx의 제품명과 img_url을 기반으로
    이미지 파일명을 변경하고 엑셀의 img_url을 업데이트하는 함수
    """
    
    # 파일 경로 설정
    excel_file = "cosmetic_data_processed_with_columns.xlsx"
    image_folder = Path("화장품_이미지")
    
    # 엑셀 파일 읽기
    try:
        print("엑셀 파일을 읽는 중...")
        df = pd.read_excel(excel_file)
        print(f"총 {len(df)}개의 화장품 데이터를 로드했습니다.")
        
        # 필요한 컬럼 확인
        required_columns = ['제품명', 'img_url']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"필요한 컬럼이 없습니다: {missing_columns}")
            print(f"사용 가능한 컬럼: {list(df.columns)}")
            return
            
    except Exception as e:
        print(f"엑셀 파일 읽기 실패: {str(e)}")
        return
    
    # 이미지 폴더 확인
    if not image_folder.exists():
        print(f"{image_folder} 폴더를 찾을 수 없습니다.")
        return
    
    # 이미지 파일 목록 가져오기
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_files = {}  # {파일명(확장자제외): (파일경로, 확장자)}
    
    for file_path in image_folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            file_name_without_ext = file_path.stem
            file_extension = file_path.suffix
            image_files[file_name_without_ext] = (file_path, file_extension)
    
    print(f"{len(image_files)}개의 이미지 파일을 발견했습니다.")
    
    # 매칭 및 이름 변경 작업
    matched_count = 0
    not_matched_products = []
    renamed_files = []
    error_count = 0
    updated_urls = []
    
    print("\n제품명과 이미지 파일 매칭 중...")
    
    # 각 제품에 대해 매칭 시도
    for idx, row in df.iterrows():
        product_name = str(row['제품명']).strip()
        img_url = str(row['img_url']).strip()
        
        # img_url이 비어있거나 NaN인 경우 건너뛰기
        if pd.isna(row['img_url']) or img_url == '' or img_url == 'nan':
            not_matched_products.append(f"{product_name} (img_url 없음)")
            continue
        
        # 제품명과 일치하는 이미지 파일 찾기
        if product_name in image_files:
            original_file_path, file_extension = image_files[product_name]
            new_file_name = f"{img_url}{file_extension}"
            new_file_path = image_folder / new_file_name
            
            try:
                # 새 파일명이 이미 존재하는지 확인
                if new_file_path.exists() and new_file_path != original_file_path:
                    print(f"파일이 이미 존재합니다: {new_file_name}")
                    continue
                
                # 파일 이름 변경
                if original_file_path != new_file_path:
                    original_file_path.rename(new_file_path)
                    renamed_files.append((product_name, new_file_name))
                    matched_count += 1
                
                # 엑셀의 img_url 업데이트 (확장자 추가)
                df.at[idx, 'img_url'] = new_file_name
                updated_urls.append((product_name, img_url, new_file_name))
                
                if matched_count % 10 == 0:
                    print(f"진행률: {matched_count}개 완료")
                    
            except Exception as e:
                print(f"파일 이름 변경 실패: {original_file_path.name} -> {new_file_name} ({str(e)})")
                error_count += 1
        else:
            not_matched_products.append(product_name)
    
    # 업데이트된 엑셀 파일 저장
    try:
        output_file = "cosmetic_data_processed_with_updated_images.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\n업데이트된 엑셀 파일이 저장되었습니다: {output_file}")
    except Exception as e:
        print(f"엑셀 파일 저장 실패: {str(e)}")
    
    # 결과 출력
    print(f"\n작업 완료!")
    print(f"결과 요약:")
    print(f"  - 성공적으로 변경된 이미지: {matched_count}개")
    print(f"  - 매칭되지 않은 제품: {len(not_matched_products)}개")
    print(f"  - 오류 발생: {error_count}개")
    print(f"  - img_url 업데이트: {len(updated_urls)}개")
    
    # 변경된 파일 목록 (처음 10개만 표시)
    if renamed_files:
        print(f"\n변경된 파일 목록 (처음 10개):")
        for i, (product_name, new_name) in enumerate(renamed_files[:10]):
            print(f"  {i+1}. {product_name[:50]}... → {new_name}")
        if len(renamed_files) > 10:
            print(f"  ... 그리고 {len(renamed_files) - 10}개 더")
    
    # img_url 업데이트 목록 (처음 5개만 표시)
    if updated_urls:
        print(f"\nimg_url 업데이트 목록 (처음 5개):")
        for i, (product_name, old_url, new_url) in enumerate(updated_urls[:5]):
            print(f"  {i+1}. {product_name[:30]}... : {old_url} → {new_url}")
        if len(updated_urls) > 5:
            print(f"  ... 그리고 {len(updated_urls) - 5}개 더")
    
    # 매칭되지 않은 제품 (처음 5개만 표시)
    if not_matched_products:
        print(f"\n매칭되지 않은 제품 (처음 5개):")
        for i, product_name in enumerate(not_matched_products[:5]):
            print(f"  {i+1}. {product_name}")
        if len(not_matched_products) > 5:
            print(f"  ... 그리고 {len(not_matched_products) - 5}개 더")
    
    return {
        'matched_count': matched_count,
        'not_matched_products': not_matched_products,
        'renamed_files': renamed_files,
        'updated_urls': updated_urls,
        'error_count': error_count
    }

def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("화장품 이미지 파일명 업데이트 스크립트")
    print("=" * 60)
    
    # 현재 작업 디렉토리 확인
    current_dir = Path.cwd()
    print(f"현재 작업 디렉토리: {current_dir}")
    
    try:
        # 이미지 파일명 변경 및 엑셀 업데이트
        result = update_image_names_by_excel()
        
        if result:
            print(f"\n모든 작업이 완료되었습니다!")
            print(f"  - 이미지 파일명 변경: {result['matched_count']}개")
            print(f"  - img_url 업데이트: {len(result['updated_urls'])}개")
            print(f"  - 매칭 실패: {len(result['not_matched_products'])}개")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
