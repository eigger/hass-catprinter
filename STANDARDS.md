# 적용한 공통 규칙

현재 적용 기준은 2026-10-25 CI 및 카테고리 호환성 후속 기록입니다. 아래 2026-10-17 채택과 ZIP 부분 적용의 PASS·제약은 당시 검증 이력이며 이번 변경의 검증 결과로 재사용하지 않습니다.

- 표준: https://github.com/eigger/hass-repo-standards/tree/v1.1.2
- 참조 커밋 SHA: df9798509d9228247ec32efb313ec7b687b5b152
- Standards release: v1.1.2
- Resolved standards SHA: df9798509d9228247ec32efb313ec7b687b5b152
- 채택 검토일: 2026-10-25 (이전 기록은 아래 보존)
- profile: integration / ha; domain `catprinter`, 실제 기본 브랜치 `main`
- 적용 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 담당: 조율 `/root`, 구현 `/root/catprinter_implementation`(코드·테스트·CI)와 `/root/catprinter_docs`(문서), 독립 리뷰·검증 `/root/review_catprinter`
- 중앙 시작 등록: 2026-10-17, `8be14269fa83fbcf5991634882a2de4a5ec52457`; 구현·검증 종료보고 `8d4348ea951736054d08f7cfe9b19f6d44b37a5e` main 등록. 규칙 기준 SHA와 현황 기록 커밋은 별개
- 테스트 경로: `tests/components/catprinter/`
- 변경 전 지원 최소: `hacs.json.homeassistant=2025.2.0`; 기존 README는 별도 HA 버전 선언 없음, manifest는 지원 HA 하한 필드 없음
- 적용 후 지원 최소: **2025.2.0 유지**. 최신 테스트와 지원 하한을 분리하며 임의 상향하지 않음
- current 테스트 목표: Python 3.14 / HA 2026.10.2 / pytest-homeassistant-custom-component 0.13.373
- 정확한 최소 HA 목표: Python 3.13 / HA 2025.2.0 / 플러그인 0.13.210
- 정확한 최소 외부 라이브러리: blesession 0.9.0, imagespec[datamatrix] 1.1.0; latest 해결값과 별도 검증

## 채택 범위와 사용자 영향

기존 모델·프로토콜 회귀를 유지하며 실제 HA fixture·loader·config entry·플랫폼·서비스 로딩을 검증합니다. 구현 구조·의존성·공통 CI·개발 문서·영문 기본/한글 README·동적 Usage·BLE 고유 문제 해결을 적용합니다. domain·unique ID·entry schema·통합 버전·기존 지원 하한은 보존합니다. 배포 tag·GitHub Release는 자동 생성하지 않습니다.

역사적 최소 requirements는 Dependabot에서 제외해 정확한 지원 조합을 보존합니다. current HA/플러그인 업데이트와 최소 환경 변경은 별도로 검토하며 상세 명령·판정은 체크리스트와 [개발 안내](docs/development.md)에 남깁니다.

## 검증 경계와 저장소 설정

실제 HA를 실행하고 Bluetooth 광고/GATT 등 외부 장치 경계만 대체합니다. 연결 발견과 GATT 쓰기는 구분하며 센서 `print_duration`, `last_failure`, `error_count`의 실제 보고만 안내합니다. 별도 diagnostics 다운로드 기능을 있다고 쓰지 않습니다.

기존 README의 X6h 펌웨어 3.0.5D 로컬 어댑터·ESPHome 프록시 확인은 기존 이력으로 보존합니다. 이번 작업은 새 실물·프록시 보드·무선 성능·HA frontend UI 검증이 아닙니다. 공통 추천 기기·구매 링크는 중앙 Bluetooth 문서로 연결하고 모든 조합 검증을 주장하지 않습니다.

원격 Issues와 Discussions는 모두 활성, LICENSE는 MIT이며 정식 release 0.1.2가 존재함을 2026-10-17에 확인했습니다. Default HACS 등재를 확인하지 않았으므로 Custom 배지를 사용합니다. Usage는 원격 집계 사전 조회와 관계없이 추가합니다. main branch protection 조회는 404(Branch not protected), rulesets는 빈 배열이라 기존 required checks 이름을 영구 대기로 만드는 설정은 확인되지 않았습니다. 저장소 설정을 변경하지 않습니다.

## 예외·검증 근거

현재 기록된 로컬 적용 예외는 없습니다. GOV-03의 기존 채택 리포에 대한 규칙 갱신 PR 조건과 달리 이번은 첫 표준 채택이며 중앙 규칙 내용은 변경하지 않습니다. 사용자 직접 push 권한에 따라 main에 직접 반영했으며 실제 PR을 만들었다고 기록하지 않습니다. 지원 최소·계약 보존과 사용자 영향은 위와 개발 안내에 기록합니다.

구현 및 추가 결함 수정 후 별도 review_catprinter의 실제 HA 독립 로컬 재검증을 완료했습니다. Current Python3.14.5/HA2026.10.2/플러그인0.13.373, 최소 Python3.13.14/HA2025.2.0/플러그인0.13.210에서 각각84passed6skipped·pipcheck PASS입니다. 구현 담당의 각 HA current/minimum 네 조합 설치·검증은 추가 cleanup 수정 전80개 이력입니다. 최종84개는 양 HA의 같은 실제 설치값 환경에서 실행했고 독립 담당은 currentHA/current모드·최소HA/minimum모드 두 환경을 직접 실행했으며 imagespec[datamatrix]1.1.0/blesession0.9.0 정확설치를 확인했습니다. 기존6파일58개 함수 소실0, Ruff/format48·actionlint·문서링크·배지·diffcheck PASS입니다. 6skip은 선택 dark PNG미제공4개·base이미지hDPI대응검사2개이며 실제 HA검사 skip은 없습니다.

최소 HA 비호환 OptionsFlowWithReload는 공개 OptionsFlow+on_unload listener로 동일 reload를 유지하도록 수정했습니다. 실제 HA에서 반복 reload listener 하나·unload·복구·텍스트/DataMatrix 렌더, 로그/세션 주소 비식별을 검증했습니다. 기존 버전·프로토콜 하한·unique ID는 변경하지 않습니다.

추가 독립 리뷰의 초기 poll 후 플랫폼 forward 실패/취소 keep 링크 누수는 refresh~forward 전체 cleanup guard 및 rollback finally close로 수정했습니다. GATT 서비스 변경·인쇄 취소에서 keep 링크를 폐기하고 fresh 연결로 복원하는 동작까지 실제 HA 회귀4개를 추가해 독립 재검증했습니다. 초기80passed에서 최종84passed로 갱신했으며 두 환경 경고(current BLEDevice19개/minimum macinotify1개)와 실물 미검증은 별도 한계입니다. 검증 구현 `36419ac76e7e148a84efa7acdd6a1c964c85dfa5`의 main 반영과 [Tests](https://github.com/eigger/hass-catprinter/actions/runs/39036837387) 네 조합·[Validate](https://github.com/eigger/hass-catprinter/actions/runs/39036837361) HACS/Hassfest 원격 성공을 독립 확인했습니다. 중앙 구현·검증 종료보고 `8d4348ea951736054d08f7cfe9b19f6d44b37a5e`도 실제 main에 등록됐습니다. 상세 판정·실제 명령·환경은 체크리스트를 따릅니다.

## 최종 채택 판정과 마감 문서 경계

검증 대상 구현은 36419ac76e7e148a84efa7acdd6a1c964c85dfa5이며 기준 표준78d242092eac732a1af48770e77e3f51e566c6c2를 유지합니다. 원격 current Python3.14.8/HA2026.10.2/플러그인0.13.373과 최소 Python3.13.16/HA2025.2.0/플러그인0.13.210에서 각 current/minimum 라이브러리 네 조합 모두84passed6skipped·pipcheck 성공입니다. 네 조합의 실제 imagespec[datamatrix]1.1.0/blesession0.9.0 정확값·최소환경 보존을 확인했습니다. 6skip은 기존 선택 darkPNG4개 미제공과 base이미지hDPI검사2개이며 실제 HA검사 skip은 없습니다. 원격 HACS/Hassfest도 같은 구현 SHA로 성공했습니다.

적용 필수 항목은 PASS 또는 근거 있는 N/A이고 현재 예외·필수 TODO는 없습니다. 이 판정은 검증 구현에 대한 것으로 본 마감 문서 자체의 미래 commit/CI를 미리 성공 처리하지 않습니다. 중앙 종료보고는 실제 등록됐고 표의 상태 완료 전환은 문서 게시 이후 수행합니다. 최초 채택은 사용자 직접 push 권한에 따라 main에 반영했으며 가짜 PR·tag·GitHub Release를 만들지 않습니다.


## 2026-10-23 ZIP release and Downloads update

Base commit: `7642bffba94f5230e5492e0dc2d1645dcf530da7`. HACS remains Custom. `hacs.json` now selects `catprinter.zip`; publishing the next release builds and attaches that integration ZIP through the pinned central action. Analytics Usage is replaced by Downloads. The archive contains tracked integration files at its root. No existing release/tag/assets are modified.

Implementation and review: root; generated release caller reuses the independently reviewed central ZIP contract. Support minimum, manifest, code, dependencies, README body and prior adoption exceptions are preserved. Verification evidence is recorded in ADOPTION_CHECKLIST.md; this scoped update does not establish full standards compliance.

## 2026-10-23 최신 공용화 적용

- 대상 기준: `9aee8a47c9d6ab2a48c2cd1d5f8de62282e640dd`의 로컬 작업 트리.
- 검토 표준: `26946e9075503633c16fb1b0f7380d0101ed7b45` (원격 main과 일치 확인).
- 공통 README 관리 영역·HACS 설치 링크·중앙 Validate 검사·payload 계약과 실제 HA 플랫폼 테스트를 적용합니다. 공용 workflow/action과 standards-ref는 같은 전체 SHA로 고정합니다.
- 실제 제품은 Bluetooth 감열 프린터이므로 주 분류는 `computers_network.printers`입니다. 엔티티 플랫폼에서 추정하지 않으며 근거는 `.hass-standards.json.categories_review`에 기록합니다.
- 기존 HA 최소 2025.2.0, manifest 버전 0.2.0, 라이브러리 하한, domain·unique ID·설정 스키마를 보존합니다. `print` 등록 스키마는 기존 native list payload와 출력·target 확장 필드를 유지하며 preview boolean을 정규화합니다.
- 기존 Tests의 주간 실행은 중앙 tests.yml 이벤트 계약에 맞춰 `tests_scheduled.yml`로 옮겨 유지합니다. 최소/current HA × current/minimum 라이브러리 네 조합과 기존 의존성 봇 일정을 보존합니다.
- 기존 README 본문·한국어 문제 해결 경로를 보존하고 양언어 payload/기기 문제 해결 문서를 연결합니다. 새 기기 기능·실물 검증·릴리스를 주장하지 않습니다.
- 담당: root 구현/통합, docs 문서, test_contract 테스트; 별도 independent_review가 독립 검토합니다. 검증 결과·미실행 범위는 ADOPTION_CHECKLIST.md의 같은 날짜 후속 기록을 따릅니다.
- 적용 예외 없음. 원격 게시·채택 PR·CI는 로컬 검증과 별도이며 이번 작업에서 아직 실행하지 않았습니다.

2026-10-23 후속 사용자 지시 “문제 없으면 스쿼시 머지”에 따라 명시적 채택 PR 게시와 원격 CI 검증 후 스쿼시 머지를 진행합니다. 위 미게시 표기는 로컬 검증 종료 시점의 이력이며 최종 원격 상태는 실제 PR을 따릅니다.

Hassfest 배포 이미지의 categories 스키마 지연은 중앙 CI-규약의 hassfest-core-ref=ec18d8b25d1ee39aa8b85a72a170e42bee33228c로 대응합니다. upstream 공식 전체 validator를 수정 없이 빌드하는 중앙 지원 입력이며 검사 예외나 지원 최소 변경이 아닙니다. 원격 실패·수정 근거는 ADOPTION_CHECKLIST.md를 따릅니다.


## 2026-10-25 CI 및 카테고리 호환성

중앙 PR #19의 `4ccbffa9af618b14d1a32a9939cbf1fcee6cb7a0`을 적용합니다. Release 검사에서 `actions/*`의 40자리 SHA 고정은 유지하되 실제 SHA 값 차이는 허용합니다. 모든 중앙 workflow/action과 standards-ref를 같은 검토 SHA로 갱신합니다.

<a id="temporary-categories-compatibility"></a>

### Temporary categories compatibility

예외 ID: `catprinter-categories-pending-hacs`. 사용자가 2026-10-25 이 대화에서 HACS default PR 검증의 categories 미지원을 이유로 카테고리 임시 비활성화를 명시적으로 요청했습니다. JSON은 주석을 지원하지 않으므로 `custom_components/catprinter/manifest.json`에서 다음 필드만 임시 제거합니다.

```json
"categories": ["computers_network.printers"]
```

실제 제품 분류와 근거는 `.hass-standards.json.categories_review`에 보존합니다. 중앙 HA-02 규칙의 임시 예외는 이 manifest 경로에만 적용하며 HACS default PR 검증이 해당 필드를 지원하면 위 값을 복원하고 예외를 제거합니다. 이전 upstream Hassfest Core 고정 우회는 제거하고 중앙 기본 Hassfest 검증을 사용합니다. 이 기록이 앞선 categories 유지 및 예외 없음 기록을 대체합니다.
### 2026-10-25 immutable central release reference migration

- User-requested partial migration: current central caller references use immutable `v1.0.0` resolved to `44349ee5621eea5d80e5c427f7a2435d2c2491bb`. Prior scoped ZIP SHA evidence is retained here: `4ccbffa9af618b14d1a32a9939cbf1fcee6cb7a0`. Runtime code, dependencies, support minimum, manifest and integration version are unchanged.

## 2026-10-25 Standards workflow 분리

기준 `v1.0.0` / `44349ee5621eea5d80e5c427f7a2435d2c2491bb`를 유지하고 기존 Validate의 중앙 검사 job만 `standards.yml`로 이동해 workflow/job을 `Standards`로 표시합니다. 단계·SHA·이벤트·예약·권한·timeout과 기존 Validate caller 입력은 유지합니다. 실제 검증과 미게시 범위는 [체크리스트](ADOPTION_CHECKLIST.md#2026-10-25-standards-workflow-분리)를 따릅니다.
