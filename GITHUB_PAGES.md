# GitHub Pages 배포

대시보드(`index.html`)는 외부 의존성이 없는 단일 파일이라 그대로 올리면 됩니다.

## 1. 저장소 만들기

GitHub에서 **public** 저장소를 새로 만듭니다. (교수님이 GitHub 계정 없이 열 수 있어야 하므로 public이어야 합니다.)
저장소 이름 예: `aromatica-analysis`

## 2. 올리기

```bash
cd <이 폴더>
git init
git add .
git commit -m "아로마티카 현황분석 — 데이터·코드·대시보드"
git branch -M main
git remote add origin https://github.com/<아이디>/aromatica-analysis.git
git push -u origin main
```

## 3. Pages 켜기

저장소 → **Settings** → **Pages** →
Source를 **Deploy from a branch**, Branch를 **main / (root)** 로 두고 저장합니다.

1~2분 뒤 다음 주소에서 열립니다.

```
https://<아이디>.github.io/aromatica-analysis/
```

## 4. 제출

메일에 저장소 주소와 Pages 주소를 함께 적습니다. 저장소가 곧 "사용 데이터와 분석 코드를
확인할 수 있는 파일"이자 "저장소 링크"이므로 ZIP과 같은 내용을 가리키게 됩니다.

## 개인정보 주의

저장소를 public으로 두면 안에 든 파일이 전부 공개되고 검색엔진에 색인됩니다.
보고서 PDF에는 학번과 이름이 들어 있으므로 `.gitignore`에 `*.pdf`를 넣어 두었습니다.
보고서는 메일 첨부로만 내고, 저장소에는 데이터·코드·대시보드만 올리면 됩니다.

올리기 전에 확인하세요.

```bash
git status --short      # 커밋될 파일 목록
git ls-files | grep -i pdf   # 아무것도 안 나와야 합니다
```

## 참고

- 대시보드에는 학번·이름이 들어 있지 않습니다.
- 성적 확인 후 저장소를 private으로 바꾸거나 삭제해도 됩니다.
- `index.html`은 `code/05_build_dashboard.py`가 `metrics.json`에서 생성합니다.
  수치를 고치려면 원자료를 고치고 01~05를 다시 실행하세요.
