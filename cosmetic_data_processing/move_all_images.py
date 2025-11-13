import os
import shutil
from pathlib import Path

def move_all_images_to_root():
    """
    화장품_이미지 폴더 내의 모든 하위 폴더에서 이미지 파일들을 
    상위 폴더(화장품_이미지)로 이동하는 함수
    """
    
    # 기본 경로 설정
    base_path = Path("화장품_이미지")
    
    if not base_path.exists():
        print(f"❌ {base_path} 폴더를 찾을 수 없습니다.")
        return
    
    # 지원하는 이미지 확장자
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # 이동할 파일들 정보 수집
    files_to_move = []
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    print("🔍 이미지 파일들을 검색 중...")
    
    # 모든 하위 폴더 탐색
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        
        # 상위 폴더(화장품_이미지)는 건너뛰기
        if root_path == base_path:
            continue
            
        for file in files:
            file_path = root_path / file
            file_extension = file_path.suffix.lower()
            
            # 이미지 파일인지 확인
            if file_extension in image_extensions:
                target_path = base_path / file
                files_to_move.append((file_path, target_path))
    
    print(f"📊 총 {len(files_to_move)}개의 이미지 파일을 발견했습니다.")
    
    if len(files_to_move) == 0:
        print("✅ 이동할 이미지 파일이 없습니다.")
        return
    
    # 사용자 확인
    print("\n📋 이동할 파일들 (처음 10개만 표시):")
    for i, (source, target) in enumerate(files_to_move[:10]):
        print(f"  {i+1}. {source.relative_to(base_path)} → {target.name}")
    
    if len(files_to_move) > 10:
        print(f"  ... 그리고 {len(files_to_move) - 10}개 더")
    
    # 파일 이동 시작
    print(f"\n🚀 이미지 파일 이동을 시작합니다...")
    
    for i, (source_path, target_path) in enumerate(files_to_move, 1):
        try:
            # 진행률 표시
            if i % 10 == 0 or i == len(files_to_move):
                print(f"진행률: {i}/{len(files_to_move)}")
            
            # 대상 파일이 이미 존재하는지 확인
            if target_path.exists():
                print(f"⚠️  파일이 이미 존재합니다: {target_path.name}")
                skipped_count += 1
                continue
            
            # 파일 이동
            shutil.move(str(source_path), str(target_path))
            moved_count += 1
            
        except Exception as e:
            print(f"❌ 파일 이동 실패: {source_path.name} - {str(e)}")
            error_count += 1
    
    print(f"\n✅ 이미지 파일 이동 완료!")
    print(f"📊 결과 요약:")
    print(f"  - 성공적으로 이동: {moved_count}개")
    print(f"  - 건너뛴 파일: {skipped_count}개")
    print(f"  - 오류 발생: {error_count}개")
    
    return moved_count, skipped_count, error_count

def remove_empty_folders():
    """
    화장품_이미지 폴더 내의 빈 폴더들을 제거하는 함수
    """
    base_path = Path("화장품_이미지")
    removed_folders = []
    
    print(f"\n🗂️  빈 폴더 정리 중...")
    
    # 하위 폴더부터 상위 폴더 순으로 정렬 (깊은 폴더부터 삭제)
    all_dirs = []
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            all_dirs.append(dir_path)
    
    # 깊이 순으로 정렬 (깊은 폴더부터)
    all_dirs.sort(key=lambda x: len(x.parts), reverse=True)
    
    for dir_path in all_dirs:
        try:
            # 폴더가 비어있는지 확인 (Thumbs.db 같은 시스템 파일 제외)
            contents = list(dir_path.iterdir())
            image_or_folder_contents = [
                item for item in contents 
                if not item.name.lower().startswith('thumbs.db')
            ]
            
            if len(image_or_folder_contents) == 0:
                # Thumbs.db 파일이 있다면 먼저 삭제
                for item in contents:
                    if item.name.lower().startswith('thumbs.db'):
                        try:
                            item.unlink()
                        except:
                            pass
                
                # 빈 폴더 삭제
                dir_path.rmdir()
                removed_folders.append(dir_path.name)
                print(f"🗑️  삭제된 빈 폴더: {dir_path.name}")
                
        except Exception as e:
            print(f"⚠️  폴더 삭제 실패: {dir_path.name} - {str(e)}")
    
    print(f"✅ 총 {len(removed_folders)}개의 빈 폴더를 삭제했습니다.")
    return removed_folders

def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("🖼️  화장품 이미지 파일 정리 스크립트")
    print("=" * 60)
    
    # 현재 작업 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 현재 작업 디렉토리: {current_dir}")
    
    # 화장품_이미지 폴더 존재 확인
    image_folder = current_dir / "화장품_이미지"
    if not image_folder.exists():
        print(f"❌ {image_folder} 폴더를 찾을 수 없습니다.")
        print("cosmetic_data_processing 폴더에서 실행해주세요.")
        return
    
    try:
        # 1단계: 이미지 파일 이동
        moved, skipped, errors = move_all_images_to_root()
        
        # 2단계: 빈 폴더 정리
        if moved > 0:
            removed_folders = remove_empty_folders()
        
        print(f"\n🎉 모든 작업이 완료되었습니다!")
        print(f"이제 모든 이미지가 '화장품_이미지' 폴더에 정리되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
