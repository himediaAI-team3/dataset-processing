import pandas as pd
import os
from pathlib import Path

def add_extensions_to_img_url():
    """
    cosmetic_data_processed_with_columns.xlsx의 img_url에 
    화장품_이미지 폴더의 이미지 확장자를 찾아서 추가하는 함수
    """
    
    # 파일 경로 설정
    excel_file = "cosmetic_data_processed_with_columns.xlsx"
    image_folder = Path("화장품_이미지")
    
    # 엑셀 파일 읽기
    try:
        print("엑셀 파일을 읽는 중...")
        df = pd.read_excel(excel_file)
        print(f"총 {len(df)}개의 화장품 데이터를 로드했습니다.")
        
        # img_url 컬럼 확인
        if 'img_url' not in df.columns:
            print("img_url 컬럼을 찾을 수 없습니다.")
            print(f"사용 가능한 컬럼: {list(df.columns)}")
            return
            
    except Exception as e:
        print(f"엑셀 파일 읽기 실패: {str(e)}")
        return
    
    # 이미지 폴더 확인
    if not image_folder.exists():
        print(f"{image_folder} 폴더를 찾을 수 없습니다.")
        return
    
    # 이미지 파일 목록 가져오기 (파일명 -> 확장자 매핑)
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    image_map = {}  # {파일명(확장자제외): 확장자}
    
    for file_path in image_folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            file_name_without_ext = file_path.stem
            file_extension = file_path.suffix
            image_map[file_name_without_ext] = file_extension
    
    print(f"{len(image_map)}개의 이미지 파일을 발견했습니다.")
    
    # img_url 업데이트 작업
    updated_count = 0
    not_found_count = 0
    already_has_extension_count = 0
    error_count = 0
    
    updated_list = []
    not_found_list = []
    
    print("\nimg_url에 확장자 추가 중...")
    
    for idx, row in df.iterrows():
        img_url = str(row['img_url']).strip()
        
        # img_url이 비어있거나 NaN인 경우 건너뛰기
        if pd.isna(row['img_url']) or img_url == '' or img_url == 'nan':
            continue
        
        try:
            # 이미 확장자가 있는지 확인
            if '.' in img_url and any(img_url.lower().endswith(ext) for ext in image_extensions):
                already_has_extension_count += 1
                continue
            
            # 매칭되는 이미지 파일 찾기
            if img_url in image_map:
                extension = image_map[img_url]
                new_img_url = f"{img_url}{extension}"
                
                # 엑셀 업데이트
                df.at[idx, 'img_url'] = new_img_url
                updated_list.append((img_url, new_img_url))
                updated_count += 1
                
                if updated_count % 10 == 0:
                    print(f"진행률: {updated_count}개 완료")
            else:
                not_found_list.append(img_url)
                not_found_count += 1
                
        except Exception as e:
            print(f"처리 실패: {img_url} - {str(e)}")
            error_count += 1
    
    # 업데이트된 엑셀 파일 저장
    try:
        output_file = "cosmetic_data_processed_with_extensions.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\n업데이트된 엑셀 파일이 저장되었습니다: {output_file}")
    except Exception as e:
        print(f"엑셀 파일 저장 실패: {str(e)}")
    
    # 결과 출력
    print(f"\n작업 완료!")
    print(f"결과 요약:")
    print(f"  - 확장자 추가 완료: {updated_count}개")
    print(f"  - 이미 확장자 있음: {already_has_extension_count}개")
    print(f"  - 매칭되지 않음: {not_found_count}개")
    print(f"  - 오류 발생: {error_count}개")
    
    # 업데이트된 목록 (처음 10개만 표시)
    if updated_list:
        print(f"\n확장자 추가된 목록 (처음 10개):")
        for i, (old_url, new_url) in enumerate(updated_list[:10]):
            print(f"  {i+1}. {old_url} → {new_url}")
        if len(updated_list) > 10:
            print(f"  ... 그리고 {len(updated_list) - 10}개 더")
    
    # 매칭되지 않은 목록 (처음 5개만 표시)
    if not_found_list:
        print(f"\n매칭되지 않은 img_url (처음 5개):")
        for i, img_url in enumerate(not_found_list[:5]):
            print(f"  {i+1}. {img_url}")
        if len(not_found_list) > 5:
            print(f"  ... 그리고 {len(not_found_list) - 5}개 더")
    
    # 확장자별 통계
    extension_stats = {}
    for old_url, new_url in updated_list:
        ext = new_url.split('.')[-1]
        extension_stats[ext] = extension_stats.get(ext, 0) + 1
    
    if extension_stats:
        print(f"\n확장자별 통계:")
        for ext, count in extension_stats.items():
            print(f"  - .{ext}: {count}개")
    
    return {
        'updated_count': updated_count,
        'already_has_extension_count': already_has_extension_count,
        'not_found_count': not_found_count,
        'error_count': error_count,
        'updated_list': updated_list,
        'not_found_list': not_found_list
    }

def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("img_url에 확장자 추가 스크립트")
    print("=" * 60)
    
    # 현재 작업 디렉토리 확인
    current_dir = Path.cwd()
    print(f"현재 작업 디렉토리: {current_dir}")
    
    try:
        # img_url에 확장자 추가
        result = add_extensions_to_img_url()
        
        if result:
            print(f"\n모든 작업이 완료되었습니다!")
            print(f"  - 확장자 추가: {result['updated_count']}개")
            print(f"  - 이미 확장자 있음: {result['already_has_extension_count']}개")
            print(f"  - 매칭 실패: {result['not_found_count']}개")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()



