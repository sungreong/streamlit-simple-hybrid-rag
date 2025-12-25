#!/usr/bin/env python3
"""
비밀번호 변경 도구
.streamlit/secrets.toml 파일의 비밀번호를 쉽게 변경할 수 있습니다.
"""
import hashlib
import os
import sys

def hash_password(password):
    """비밀번호를 SHA-256으로 해시합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def update_secrets_file(hashed_password):
    """secrets.toml 파일을 업데이트합니다."""
    secrets_path = ".streamlit/secrets.toml"
    
    if not os.path.exists(secrets_path):
        print(f"❌ 오류: {secrets_path} 파일을 찾을 수 없습니다.")
        print("   .streamlit/secrets.toml.template 파일을 복사하여 secrets.toml을 만드세요.")
        return False
    
    try:
        # 기존 파일 읽기
        with open(secrets_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # password 라인 찾아서 업데이트
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith('password'):
                lines[i] = f'password = "{hashed_password}"\n'
                updated = True
                break
        
        if not updated:
            print("❌ 오류: secrets.toml 파일에서 'password' 항목을 찾을 수 없습니다.")
            return False
        
        # 파일 쓰기
        with open(secrets_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    
    except Exception as e:
        print(f"❌ 오류: 파일 업데이트 중 문제가 발생했습니다: {e}")
        return False

def main():
    print("=" * 50)
    print("🔐 비밀번호 변경 도구")
    print("=" * 50)
    print()
    
    # 비밀번호 입력
    while True:
        new_password = input("새 비밀번호를 입력하세요 (취소: Ctrl+C): ").strip()
        
        if not new_password:
            print("⚠️  비밀번호는 비어있을 수 없습니다. 다시 입력하세요.")
            continue
        
        if len(new_password) < 6:
            print("⚠️  보안을 위해 최소 6자 이상 입력하세요.")
            continue
        
        # 확인
        confirm = input("비밀번호 확인: ").strip()
        
        if new_password != confirm:
            print("❌ 비밀번호가 일치하지 않습니다. 다시 시도하세요.\n")
            continue
        
        break
    
    print()
    print("🔄 비밀번호 해시 생성 중...")
    hashed = hash_password(new_password)
    
    print(f"✅ 해시 생성 완료: {hashed[:20]}...")
    print()
    
    # 자동 업데이트 여부 확인
    auto_update = input("secrets.toml 파일을 자동으로 업데이트할까요? (y/n): ").strip().lower()
    
    if auto_update == 'y':
        print()
        print("📝 secrets.toml 파일 업데이트 중...")
        
        if update_secrets_file(hashed):
            print("✅ 비밀번호가 성공적으로 변경되었습니다!")
            print()
            print("📌 다음 단계:")
            print("   1. Docker를 재시작하세요:")
            print("      docker-compose restart")
            print()
            print("   2. 새 비밀번호로 로그인하세요!")
        else:
            print()
            print("⚠️  자동 업데이트에 실패했습니다. 수동으로 변경하세요:")
            print(f"   1. .streamlit/secrets.toml 파일을 여세요")
            print(f"   2. password = \"{hashed}\" 로 변경하세요")
            print(f"   3. docker-compose restart 실행하세요")
    else:
        print()
        print("📋 수동 변경 방법:")
        print(f"   1. .streamlit/secrets.toml 파일을 여세요")
        print(f"   2. password = \"{hashed}\" 로 변경하세요")
        print(f"   3. docker-compose restart 실행하세요")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 취소되었습니다.")
        sys.exit(0)
