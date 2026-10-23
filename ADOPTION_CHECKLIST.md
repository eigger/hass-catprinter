# 공통 규칙 적용 체크리스트

hass-catprinter 두 번째 파일럿의 실제 채택 점검 기록입니다. 구현과 추가 리뷰 결함 수정·독립 로컬 재검증을 완료했습니다. 검증 대상 구현 `36419ac76e7e148a84efa7acdd6a1c964c85dfa5`의 main 반영·원격 CI 성공·중앙 구현/검증 종료보고 등록을 확인했습니다. 본 문서 마감은 별도 후속 변경이며 아직 게시되지 않은 문서 commit의 CI 성공을 주장하지 않습니다. [사용법과 판정 기준](https://github.com/eigger/hass-repo-standards/blob/78d242092eac732a1af48770e77e3f51e566c6c2/docs/checklist.md)을 읽고, 아래 규칙은 `STANDARDS.md`에 기록한 표준 커밋에서 확인합니다. 태그·릴리스 대신 검토한 전체 커밋 SHA를 기준으로 합니다.

## 검토 대상

| 항목 | 값 |
|---|---|
| 통합 리포 / 실제 기본 브랜치 | eigger/hass-catprinter / main |
| domain / 구현 경로 | catprinter / custom_components/catprinter/ |
| 검토 대상 통합 커밋 / 채택 PR | 변경 전35b9d7524c34b3d0bc11d6dfaa5d67daa774f0d7 → 검증 구현 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 main 직접 반영; 허위 채택 PR 없음 |
| 검토한 표준 전체 커밋 SHA | 78d242092eac732a1af48770e77e3f51e566c6c2 |
| 검토일 / 조율 담당 | 2026-10-17 / root |
| 구현 서브 에이전트 / 독립 리뷰·검증 서브 에이전트 | catprinter_implementation, catprinter_docs / review_catprinter |
| 중앙 현황표 반영일 / 기록 | 2026-10-17 시작 등록8be14269fa83fbcf5991634882a2de4a5ec52457; 구현·검증 종료보고 8d4348ea951736054d08f7cfe9b19f6d44b37a5e main 게시. 표 상태 완료는 본 문서 마감 후 전환 |
| 변경 전 지원 최소 HA / 근거 파일(hacs.json·manifest·README) | hacs.json 2025.2.0; 기존 README 별도 선언 없음, manifest HA 하한 필드 없음 |
| 유지·변경할 지원 최소 / 변경 시 실제 비호환 근거·명시적 승인 | 기존 2025.2.0 유지; 상향 없음 |
| current 테스트 HA / 호환 Python·플러그인 | 실제 HA 2026.10.2 / Python 3.14.5 / 플러그인 0.13.373; 독립 로컬·원격 PASS |
| 최소 테스트 HA / 호환 Python·플러그인 | 실제 HA 2025.2.0 / Python 3.13.14 / 플러그인 0.13.210; 별도 환경 독립 로컬 PASS |
| profile / 테스트 경로 | integration / ha; tests/components/catprinter/ |
| 이전 검토 기록 | 최초 표준 채택 검토 |
| 채택 판정 | 채택 완료 — 검증 구현36419ac의 적용 대상 필수 PASS 또는 근거 있는 N/A, 예외 없음. 마감 문서 게시·중앙 표 상태 완료 전환은 별도 행정 후속 |

상태: `TODO` = 미확인·미충족, `PASS` = 근거로 확인, `EXCEPTION` = 적용 대상의 기록된 예외, `N/A` = 적용 조건에 해당 없음. 모든 항목은 미확인으로 시작합니다. `TODO`를 해당 없음으로 처리하지 않습니다. 묶은 규칙의 결과가 다르면 행을 나눕니다. 권장 항목은 별도로 표시했으며 미채택 이유를 기록합니다.

## 채택·구조·사용자 데이터

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| GOV-01, GOV-02 | `STANDARDS.md`에 표준 SHA·profile·실제 기본 브랜치·예외 기록, workflow/action은 검토 SHA로 고정 | PASS | STANDARDS.md 전체 SHA/profile/main/검증 경계 기록; 세 caller가 기준 78d242092eac732a1af48770e77e3f51e566c6c2로 고정. 태그·릴리스 미생성 |
| GOV-03 | 기준 채택 영향·이관 방법 기록, 기존 채택 리포의 규칙 변경 시 명시적 채택 PR 확인. 중앙 규칙 자체 변경 시 공통 CHANGELOG 기록 | PASS | 첫 표준 채택이며 중앙 규칙 자체 변경 없음. 사용자 직접 push 권한에 따라 main 직접 반영 완료; 기존 채택 리포의 규칙 갱신 채택 PR 조건과 구분. 실제 PR을 만들었다고 주장하지 않음. 영향·이관 방법은 STANDARDS.md/개발 문서에 기록 |
| GOV-04 | 중앙 표에 작업 시작·단계 변경·종료 상태, 담당·적용 내용·검증/리뷰 근거·남은 작업 갱신, 타 리포 기록 보존 | PASS | 중앙 시작8be14269fa83fbcf5991634882a2de4a5ec52457 및 구현·검증 종료보고 8d4348ea951736054d08f7cfe9b19f6d44b37a5e 실제 main 등록. 담당·범위·기준/구현SHA·CI/독립 리뷰/한계 기록, 타행 보존; 표 상태 완료는 문서 마감 후 전환 |
| GOV-05 | 구현과 독립 리뷰·검증을 별도 서브 에이전트에게 위임, 지적 수정·재검증 및 결과 취합 | PASS | 구현 catprinter_implementation/catprinter_docs와 별도 review_catprinter가 실제 diff·두 HA 환경·문서 검증. 문서 지적 2건 수정 후 독립 재검증 완료 |
| HA-01, HA-13 | `custom_components/<domain>/`와 domain 일치, 필요한 모듈·공개 API·생명주기는 Core 대응 구조 | PASS | custom_components/catprinter의 manifest.domain/const.DOMAIN 일치; 실제 config entry runtime_data·공개 lifecycle 및 tests/components/catprinter 구조. test_init.py/test_config_flow.py 실제 loader 검증 |
| HA-02 | manifest 필드·정렬·동작 선언 확인, 공식 품질 등급 자가 표기 없음 | PASS | manifest.json domain/name 이후 정렬·version0.1.2·codeowners·documentation·issue_tracker·local_polling/device/config_flow 확인. 실제 사용하는 bluetooth를 dependencies에 선언, recorder는 after_dependencies. quality_scale 자가 등급 없음. 원격 Hassfest도 exacthead36419ac로 성공 확인 |
| HA-03 (권장) | 공통 상수·설정·갱신·플랫폼 역할 및 프로토콜 경계에 맞게 모듈 구성 | PASS | const/config_flow/entity/platform/services/render 모듈과 catprinter_ble protocol/client/device 분리 유지. 빈 모듈 추가 없음 |
| HA-04, HA-08 | UI 설정·중복·안정적 식별 및 기능별 options/reauth/reconfigure, entity 의미·registry 영향 확인 | PASS | test_config_flow.py Bluetooth 확인·중복·미지원·수동주소 오류·options reload 검증. 기존 entry VERSION1/unique ID/엔티티 단위·통계 보존; reauth는 지원하는 인증 흐름 없어 추가하지 않음 |
| HA-01, HA-04, HA-08, REL-01, REL-03 | domain·unique ID·entry schema·상태/통계 계약 변경 시 migration 테스트와 사용자 조치 안내 | N/A | 이번 변경에 domain·unique ID·entry schema·상태/통계 계약 변경 없음. 기존 옵션 reload를 최소 HA에서도 동일하게 제공하며 migration이나 재등록을 요구하지 않음 |
| HA-05, HA-06 | setup 실패 구분, unload/reload·부분 실패의 task/listener/연결 정리, async·timeout·취소 처리 | PASS | 추가 리뷰의 부분 setup 실패/cancel 링크 누수 수정: 초기 refresh~forward 전체 cleanup guard, rollback finally device close. test_failed_platform_setup_releases_kept_link/test_cancelled_setup_releases_kept_link 실제 HA manager 회귀·양 환경 독립84passed 재검증 |
| HA-07 | 중복 polling·property I/O 방지, push 보존, unavailable/unknown·실패 후 복구 | PASS | 단일 DataUpdateCoordinator와 장치/인쇄 lock로 중복 polling 방지, property I/O 없음. test_failed_poll_retains_state_and_recovers/test_initial_connection_failure_is_recoverable 및 서비스/엔티티 검증. 기존 마지막 정상값 유지 계약 보존 |
| HA-11, HA-12 | 번역·action/schema 일치, 로그/diagnostics/fixture 비식별화와 제공 시 redaction 테스트 | PASS | strings/translations/services.yaml schema 일치 회귀 유지. session_report.redact_report/로그 주소 비식별과 test_expected_poll_failures_are_quiet_and_redacted 검증; 별도 diagnostics 다운로드 없음 |

## 실제 HA 테스트·호환성·의존성

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| TEST-08 | `tests/components/<domain>/`에 구현과 대응하는 테스트·domain fixture 배치, discovery·CI 경로 일치 | PASS | 기존6파일을 tests/components/catprinter로 이관해 58개 기존 test 함수 소실0; 신규 test_init/config_flow/services와 conftest 추가. pyproject testpaths 및 공통 ha 기본 경로 일치 |
| TEST-02, TEST-03, DEP-07 | 실제 HA·호환 플러그인과 `hass`/`enable_custom_integrations` fixture 사용, HA core stub/복사본/`--no-deps`로 대체하지 않음 | PASS | requirements_test[_min].txt에 실제 HA/호환 플러그인 정확 고정. tests/conftest.py와 domain conftest의 실제 hass/enable_custom_integrations/MockConfigEntry 사용, HA stub/--no-deps 없음 |
| TEST-09 | 실제 loader·config entry manager로 setup/플랫폼 로딩, HA 상태·registry·service/action으로 결과 검증 | PASS | 독립 두 HA 환경 각84passed. test_init/config_flow/services: 실제 entry manager/플랫폼/registry/state/action, 텍스트 및 DataMatrix 실제 렌더 픽셀 결과 검증; GATT 외부 경계만 대체 |
| TEST-01, TEST-06, TEST-07 | 구현 기능별 성공·실패·중복·migration·unload·복구 회귀 검증, 외부 통신 경계만 mock, skip 사유 | PASS | 84passed6skipped: 기존 protocol/client/model 회귀+실제 HA 성공/실패/중복/복구/반복optionsreload/unload. migration은 계약 변경 없어 N/A. skip은 brand 선택파일4+base이미지hDPI검사2이며 실제 HA검사는 skip 없음 |
| TEST-04, HACS-01 | 변경 전 지원 최소·current·각 Python/플러그인 분리, 선언한 정확한 최소 검증, 상향 시 비호환 근거·명시적 승인 확인 | PASS | 지원 최소 HA2025.2.0 유지; 실제 Python3.13.14/plugin0.13.210에서 독립84passed. current Python3.14.5/HA2026.10.2/plugin0.13.373 독립84passed. 두 pip check PASS. 최소 requirements는 Dependabot exclude-paths |
| TEST-05, HA-10, DEP-02, DEP-05 | imagespec·blesession 등 최소/현재 라이브러리 별도 환경, 실제 HA 테스트·정확한 설치값·API 경계 검증 | PASS | 구현 담당이 각 HA에서 installer current/minimum 네 조합을 실행; 독립 담당은 currentHA/current모드·최소HA/minimum모드 두 환경에서 실제 imagespec[datamatrix]1.1.0/blesession0.9.0 설치 확인. resolver current도 현재 같은 버전 선택. extras/연산자 보존. 실제 print/text/DataMatrix 및 BLE회귀 검증 |
| DEP-01, DEP-06 | Python runtime은 manifest requirements, HA domain은 dependencies/after_dependencies, 테스트·린트 requirements는 별도 | PASS | manifest Python requirements 두 개 유지; 필수 HA bluetooth 의존 정정 및 recorder after_dependencies 유지; 테스트 HA/플러그인·Ruff는 별도 requirements 파일 |
| DEP-07, CI-06 | 실제 사용하는 HA 구성요소의 requirements·필수 재귀 의존성·선택 로딩 경로 설치, resolver·`pip check` 통과 | PASS | 각 실제 HA의 bluetooth recorder image sensor binary_sensor manifest requirements/재귀 필수 의존성을 중앙 installer로 설치. resolver·두 pip check PASS; latest Core 전체 requirements 혼합 없음 |
| DEP-02, DEP-03, DEP-08 | 의존성 추가/변경의 버전·extras·marker·선언 위치·지원 플랫폼·라이선스 검토, 실제 HA 테스트와 문서 갱신 | PASS | 기존 runtime 버전/연산자/extras/marker 유지·새 runtime 패키지 추가 없음. 실제 사용 HA domain만 bluetooth_adapters→bluetooth 정정; 정확 최소/current HA 설치·공개 API·이미지 extra 실제 동작 검증. 새 외부 라이선스 추가 없음 |

독립 리뷰는 변경 전후 지원 최소와 current를 비교하고, 봇 PR이 과거 최소 requirements·constraints까지 갱신하거나 expected-ha-version·Python을 누락하지 않았는지 확인합니다. 최신 테스트 실패는 호환 수정 대상으로 처리합니다.

환경마다 아래 행을 복사합니다. 최소 HA와 최소 라이브러리 검증을 혼동하지 않고, marker가 활성인 환경에서 대상 패키지 설치값을 확인합니다. 실행하지 않은 조합은 `TODO` 또는 근거가 있는 `EXCEPTION`으로 남깁니다.

| 검증 축 / 상태 | 통합 커밋 | Python / HA / 플러그인 실제 버전 | 대상 패키지 실제 버전·extras·marker | 명령·테스트 결과·pip check / CI run·job | skip·제외·미검증 범위 |
|---|---|---|---|---|---|
| current HA / 독립 로컬 PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.14.5 / 2026.10.2 / 0.13.373 | imagespec[datamatrix]1.1.0 / blesession0.9.0, marker 없음 | review venv /tmp/catprinter-review-current; pytest tests/components/catprinter/ -q: 84 passed, 6 skipped (3.40s); pip check PASS | 선택 dark PNG4·base이미지hDPI검사2 skip; 실물/UI 미검증 |
| 정확한 최소 HA / 독립 로컬 PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.13.14 / 2025.2.0 / 0.13.210 | imagespec[datamatrix]1.1.0 / blesession0.9.0, marker 없음 | review venv /tmp/catprinter-review-min; pytest tests/components/catprinter/ -q: 84 passed, 6 skipped (3.45s); pip check PASS | 같은6 skip; 실제 HA검사 skip 없음 |
| current HA + 정확 최소 라이브러리 / 로컬 PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.14.5 / 2026.10.2 / 0.13.373 | imagespec[datamatrix]==1.1.0 / blesession==0.9.0 | 구현 담당 minimum모드 실제 설치·정확값 확인은 이전80passed tree 이력. 최종 같은 실제 설치값 환경에서84passed/6skipped·pipcheck PASS; 독립 current는 current모드의 같은 설치값 검증 | current 해결값도 같은버전이나 minimum모드 추가 제약·assert와 구분 |
| 최소 HA + 정확 최소 라이브러리 / 로컬 PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.13.14 / 2025.2.0 / 0.13.210 | imagespec[datamatrix]==1.1.0 / blesession==0.9.0 | 구현4mode 설치검증은 이전80passed tree 이력. 독립 담당은 minimum모드 정확설치 환경에서 최종84passed/6skipped·pipcheck PASS | 같은6 skip; 실물/UI 미검증 |
| 원격 current HA + current libraries / PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.14.8 / 2026.10.2 / 0.13.373 | imagespec[datamatrix]1.1.0 / blesession0.9.0 | [Tests current/current job](https://github.com/eigger/hass-catprinter/actions/runs/39036837387/job/117408295622): 84passed6skipped (5.33s), pipcheck PASS | 선택 dark PNG4·basehDPI검사2 skip; 실제 HA검사 skip0 |
| 원격 current HA + minimum libraries / PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.14.8 / 2026.10.2 / 0.13.373 | imagespec[datamatrix]==1.1.0 / blesession==0.9.0 정확 확인 | [Tests current/minimum job](https://github.com/eigger/hass-catprinter/actions/runs/39036837387/job/117408295645): 84passed6skipped (4.50s), pipcheck PASS | 같은6 skip; 실물/UI 미검증 |
| 원격 minimum HA + current libraries / PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.13.16 / 2025.2.0 / 0.13.210 | imagespec[datamatrix]1.1.0 / blesession0.9.0 | [Tests minimum/current job](https://github.com/eigger/hass-catprinter/actions/runs/39036837387/job/117408295610): 84passed6skipped (4.83s), pipcheck PASS | 같은6 skip; 실제 HA검사 skip0 |
| 원격 minimum HA + minimum libraries / PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | 3.13.16 / 2025.2.0 / 0.13.210 | imagespec[datamatrix]==1.1.0 / blesession==0.9.0 정확 확인 | [Tests minimum/minimum job](https://github.com/eigger/hass-catprinter/actions/runs/39036837387/job/117408295704): 84passed6skipped (5.91s), pipcheck PASS | 같은6 skip; 실물/UI 미검증 |
| 원격 HACS·Hassfest / PASS | 36419ac76e7e148a84efa7acdd6a1c964c85dfa5 | Validate | HACS Custom·로컬 brand, 검사 ignore 없음 | [HACS](https://github.com/eigger/hass-catprinter/actions/runs/39036837361/job/117408295725) / [Hassfest](https://github.com/eigger/hass-catprinter/actions/runs/39036837361/job/117408295603) 성공, invalid integrations0 | 로컬 brand의 HA UI 실제 표시와 구분 |

## HACS·CI·의존성 업데이트

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| HACS-01, HACS-02 | 루트 README/LICENSE/hacs.json, 검증한 최소 HA, 실제 배포 구조와 필요한 옵션 일치 | PASS | README.md/README.ko.md/LICENSE/hacs.json 및 custom_components/catprinter 배포 유지. homeassistant2025.2.0 정확 환경 검증. zip_release 등 불필요 옵션 추가 없음 |
| HACS-03, HACS-05 | Default 여부는 목록 근거로 확인, [로컬 brand/icon.png 또는 원격 brands 근거](https://github.com/eigger/hass-repo-standards/blob/main/docs/hacs.md)와 HACS/Hassfest 실제 실행, ignore는 이유·해제 조건 기록 | PASS | HACS Custom, 기존 로컬 brand/icon.png256px/icon@2x.png512px 및 PNG 회귀 유지. 구현36419ac [Validate](https://github.com/eigger/hass-catprinter/actions/runs/39036837361)에서 ignore 없이 HACS·Hassfest 성공, invalid integrations0. 실제 원격 head 독립 확인; 최소 HA 로컬 아이콘 UI 표시 검증 주장 없음 |
| HACS-06 (권장) | description·topics·issue 경로·brands 및 사용하는 HACS 필드 지원 확인 | PASS | 2026-10-17 gh api 원격 description·BLE/HACS/HA/thermal-printer topics·Issues/Discussions 활성 확인. 기존 brand assets 유지; 과거 render_readme 필드 사용 없음 |
| CI-01, CI-02 | Validate/Python Tests 공통화, 확장 job 유지, PR·실제 기본 브랜치 push·dispatch 및 필요한 schedule | PASS | tests.yml/validate.yml/update_dependencies.yml 중앙 reusable 전환. 실제 main push/PR/dispatch와 분산 schedule, 전용 frontend job 없어 손실 없음 |
| CI-03, CI-05, CI-08 | 최소 권한·checkout 자격증명 비보존·timeout·concurrency, full SHA·갱신 관리, 비신뢰 입력·secrets 경계 | PASS | caller read 권한/updater job만 write, 중앙 job timeout·credential미보존·검증취소/업데이트비취소그룹 확인. 세 caller fullSHA+검토주석·Dependabot github-actions, 비신뢰 PR 입력 shell 삽입/secrets inherit 없음; actionlint PASS |
| CI-04, CI-07, CI-12 | 실패를 숨기지 않는 실제 `ha` 필수 테스트, 버전별 환경·cache·Ruff 설정과 required checks 이름 확인 | PASS | 실제 ha 필수4matrix·Ruff2job/format48파일 및 pipcheck 성공 [Tests](https://github.com/eigger/hass-catprinter/actions/runs/39036837387)의 exacthead36419ac 독립 확인. 실패 숨김 없음. main protection404/rulesets[]로 기존 requiredchecks 없음; 각 버전 별도 환경/manifest 포함 cache·예상HA 검증 |
| DEP-03, DEP-04, CI-09 | updater의 선택 package·연산자/extras/marker 보존, 안정 버전·major 정책, 실제 기본 브랜치·단일 bot branch·PR만 제안 | PASS | update_dependencies.yml packages imagespec/blesession 중앙 updaterSHA고정. 실제 PyPI dry-run 변경없음; manifest extras/연산자 보존. 안정버전/major거부/기본branch API/단일 bot branch/PR 제안 계약은 기준 중앙 구현 재사용 |
| CI-09, CI-10, DEP-08 | 변경 tree의 새 하한·실제 HA 검증 후 PR 동기화, 실패 시 중단·변경 없음 시 기존 PR 정리, 후속 required checks 충족 방식 확인 | PASS | 중앙 dependency-update가 변경 tree의 정확한 새 하한+HA설치/pipcheck와 caller의 Ruff/format/실제HApytest 통과 후에만 PR동기화, 실패중단/변경없음 정리. 일반 토큰PR후속CI자동실행 가정 없음; 추가 requiredchecks 설정없음. 실제 새 update PR 생성·변경 manifest 시나리오는 이번 dry-run에 없어 운영 실행과 구분 |

## README·Bluetooth·유지보수

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| DOC-01, DOC-02, DOC-06 | 영어 README.md·한국어 README.ko.md·상호 링크·기존 내용 보존, 간결한 제목/소개/핵심지원/최소요구/빠른설치·설정/짧은예제/중요제한/문서목록, 상세옵션·긴YAML·참조·개발/실HA테스트·의존성/검증범위를 docs·examples 등으로 보존·분리하고 유효한 링크 제공, 실제 활성 Issues·Discussions 또는 대체 지원 경로·실제 LICENSE 링크 | PASS | README.md / README.ko.md 간결 구성·상호 링크, docs/user-guide.md 및 docs/ko/user-guide.md에 원문 상세 보존, docs/development.md 실제 HA 명령. Issues/Discussions 활성·MIT 원격 확인; 독립 review_catprinter 확인·문서 diff/link/badge 검증 PASS (2026-10-17); 원격 구현검증은 위 환경표에서 별도 확인 |
| DOC-03, DOC-04, DOC-05 | 제목 아래 관리 블록, flat-square·순서·실제 조건별 배지, CI 실제 기본 브랜치, 필수 동적 Usage·Analytics 참여 설치 의미·미집계/조회 실패와 0 설치 구분·이전 안내 보존 | PASS | 두 README 관리 배지 / .hass-standards.json / sync_badges --write; domain catprinter 동적 Usage 항상 생성, 집계 의미 안내; 독립 review_catprinter 확인·문서 diff/link/badge 검증 PASS (2026-10-17); 원격 구현검증은 위 환경표에서 별도 확인 |
| HA-09, HA-10 | BLE 사용 시 HA Bluetooth API·라이브러리 공개 경계, 지원한 proxy 경로·재연결·취소·서비스 변경 검증 | PASS | HA Bluetooth·공개 blesession API 및 proxy pacing 회귀 유지. keep 링크 SERVICE_NOT_FOUND/취소시 폐기해 fresh reconnect; 실제 HA print 취소→connection off/count0와 GATT 서비스 소실·복원 재연결 회귀를 양 환경 독립84passed 검증 |
| DOC-07 | blesession/proxy 통합 README의 핵심조건·상세문서 링크, 공통 Bluetooth 설정·추천기기·active 스캔/GATT 차이, 통합별 troubleshooting 또는 공통 링크+모델고유조건·실제진단·민감정보 제거 제보 안내 | PASS | docs/troubleshooting.md / docs/ko/troubleshooting.md: 공통 proxy·기기 추천 링크, scan/GATT 구분, 모델별 준비·실제 진단·미검증; 독립 review_catprinter 확인·문서 diff/link/badge 검증 PASS (2026-10-17); 원격 구현검증은 위 환경표에서 별도 확인 |
| DOC-07, HA-12 | 기기별 깨우기·인증·타 앱 연결·전송 제약, 실제 검증 경로와 미검증 범위, 공개 문제 로그 비식별화 | PASS | D1 미지원, 전화앱 연결 종료, 프린터 전원/용지/커버·단계별 원인·센서 속성·비식별 제보 안내. BLE ESL 전용 옵션 복사 없음; 독립 review_catprinter 확인·문서 diff/link/badge 검증 PASS (2026-10-17); 원격 구현검증은 위 환경표에서 별도 확인 |
| HACS-04, REL-01, REL-02, REL-03, CI-11 | 통합 릴리스 시 같은 검증 commit/tag·manifest 버전·산출물·권한, 사용자 영향·지원 변경·제한 안내 | N/A | 이번은 공통 규칙 최초 채택이며 새 배포/tag/Release 작업 아님. manifest.version0.1.2 기존 유지. 자동 updater가 integration version/tag/release를 생성하지 않음; 지원 최소·domain계약 유지와 미검증 범위는 문서에 명시 |
| REL-04 | 이전/중단 시 README 상단 경로·유지보수 상태·재등록 여부, 자동 이전으로 오인하지 않는 안내 | N/A | 유지 중인 catprinter 통합이며 이전·통합·중단이나 재등록 변경 없음 |
| REL-05 (권장) | 의존성/HA API 변경과 기능 변경 분리, 표준 변경은 명시적 채택 PR로 반영 | PASS | 최초 표준 채택·최소HA호환수정·검증/문서 범위이며 새 프린터 기능이나 라이브러리 버전 상승 없음. 지원 최소/통합버전 보존. 기존 표준 갱신 PR 조건은 GOV03 해석에 기록 |

## 예외와 남은 작업

예외 원본은 `STANDARDS.md`입니다. 아래에 해당 위치를 연결하고, 예외가 실제 없음을 확인한 뒤에만 `없음`으로 바꿉니다.

| 규칙 ID | 예외 위치 / 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | 검증 대상 구현36419ac의 적용 예외 없음 | root | 규칙·구현 후속 변경 시 재검토 |

| 규칙 ID / TODO | 남은 작업 / issue·PR | 담당자 | 완료 근거 |
|---|---|---|---|
| 필수 TODO 없음 | 검증 구현36419ac의 필수 PASS/N/A 확인. 본 마감 문서 게시·중앙 표 상태 완료 전환은 후속 기록 | root / review_catprinter | 구현·검증 종료보고 8d4348ea951736054d08f7cfe9b19f6d44b37a5e 등록, 마감 문서 commit/CI는 생성 후 별도 확인 |

최종 검토 시 적용 대상 필수 `TODO`와 `EXCEPTION`, 이유가 있는 `N/A`, 권장 미채택을 구분해 적습니다. CI 성공만으로 실물 기기 검증을 주장하지 않습니다. 실물 검증을 수행했다면 모델·펌웨어·어댑터/proxy·연결 경로와 결과를 별도로 기록합니다.

중앙 보고는 [적용 현황표](https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md)의 자기 리포 행에 반영합니다. 리뷰 지적·수정·재검증 결과와 중앙 갱신 실패 사유가 있으면 남은 작업에도 기록합니다.

## 문서 독립 리뷰·수정 기록 (2026-10-17)

구현 catprinter_docs와 별도인 review_catprinter가 두 언어 README·Usage 포함 배지·원문 모델/엔티티/예제 보존·실제 진단 경로와 실물 미검증 안내를 확인했습니다. 개발 installer 예제의 잘못된 `latest` 모드/packaging·RUNNER_TEMP 누락, 이동한 gallery 이미지 URL 두 건을 지적했고 구현 담당이 `current`·설치 전제·고유 임시 경로·상대 이미지 링크로 수정했습니다. 독립 재확인 결과 11 Markdown 및 HTML src 상대 링크 누락 0, 문서 범위 `git diff --check`, `sync_badges.py . --check` 통과입니다. 이는 최종 구현 커밋·원격 HA CI 판정과 별개의 문서 검토 기록입니다.

## 구현·독립 로컬 검증 기록 (2026-10-17)

review_catprinter는 구현 환경과 분리한 `/tmp/catprinter-review-current`·`/tmp/catprinter-review-min`에서 실제 중앙 installer를 실행했습니다. HA component 입력은 `bluetooth recorder image sensor binary_sensor`, profile은 `ha`, 각각 정확한 expected HA를 검증합니다. Current 환경 Pillow12.3.0/bleak3.0.2, 최소 환경 Pillow11.1.0/bleak0.22.3이며 HA가 요구하는 환경별 간접 의존성을 섞지 않았습니다. 구현 담당은 추가 cleanup 수정 전 tree에서 두 HA 각각 `current`와 `minimum` 네 조합을 설치·실행(당시80passed)했습니다. 최종 수정 후84passed 검증은 양 HA의 같은 실제 설치값 환경을 실행한 결과이며 네 조합을 새로 설치해84개씩 실행했다는 뜻은 아닙니다. 독립 담당은 current HA/current모드와 최소 HA/minimum모드 두 환경을 직접 재설치·검증했으며 선택된 runtime 버전은 imagespec1.1.0/blesession0.9.0으로 같았습니다. 최소 모드는 정확 하한 제약과 설치 assert를 추가한 별도 검증입니다.

최소 HA의 OptionsFlowWithReload 미지원은 지원 상향 대신 공개 OptionsFlow와 on_unload에 연결한 update_listener로 호환 수정했습니다. 반복 options reload에도 listener 하나·플랫폼/연결 정리를 확인하고, 실제 HA action에서 텍스트/DataMatrix 렌더를 픽셀 결과로 검증했습니다. 기존6파일58개 test 함수 손실0, 최종 두 환경84passed6skipped, pip check·Ruff check/format48·actionlint·badge check·문서 링크·diffcheck 모두 로컬 통과입니다. PyPI updater dry-run은 manifest 변경없음이었으며 실제 새 bot PR 생성으로 과장하지 않습니다.

6 skip은 미제공 dark icon/logo 변형4개와 @2x가 아닌 base 이미지의 hDPI 대응 검사2개로 기존 선택 자산 검사입니다. 실제 HA 로딩/기능 검사는 skip하지 않았습니다. 기존 로컬 brand 이미지의 라이선스·UI 표시를 새로 인증하지 않으며 HA2026.3 이전 최소 환경에서 로컬 아이콘 UI 표시를 보장하지 않습니다. 추가 리뷰의 부분 setup 실패·취소 cleanup 및 GATT 서비스 변경 회귀4개를 구현하고 양 환경 독립 재검증을 완료했습니다. 이전 초기 결과80passed에서 최종84passed로 갱신했으며, 검증 구현36419ac의 원격 네 조합·Validate 성공과 중앙 종료보고 등록을 별도 확인했습니다.

## 추가 생명주기 지적 수정·독립 재검증

부분 setup 실패/취소에서 keep 링크가 남던 결함을 독립 리뷰가 지적했습니다. 구현은 초기 refresh부터 플랫폼 forward까지 cleanup guard를 적용하고 rollback의 finally에서도 bounded close를 수행하도록 수정했습니다. 실제 HA manager의 플랫폼 로딩 실패(SETUP_ERROR)·setup 취소에서 초기 링크가 닫히는 회귀를 추가했습니다. keep 링크의 GATT 서비스 소실·인쇄 취소에서도 링크를 버리고 다음 작업이 fresh 연결을 사용하게 했습니다. 실제 HA의 인쇄 취소 이후 connection off·실패 count0, 서비스 소실 후 복원·재연결 회귀까지 4개가 추가됐습니다.

review_catprinter는 수정 diff와 두 독립 환경을 재실행해 current84passed6skipped(3.40s), minimum84passed6skipped(3.45s), Ruff/format48·diffcheck 재통과를 확인했습니다. Current의 BLEDevice 기존 API 경고19개와 minimum의 macinotify 경고1개가 있으나 테스트 실패·누락으로 숨기지 않았습니다. 해당 지적 HA-05/HA-06/HA-09는 해결했고 원격 구현36419ac의 4matrix·HACS/Hassfest 성공과 중앙 종료보고 8d4348ea951736054d08f7cfe9b19f6d44b37a5e 등록을 확인했습니다.

## 원격 검증과 종료 보고 확정

review_catprinter가 main 구현 36419ac76e7e148a84efa7acdd6a1c964c85dfa5와 Tests/Validate의 실제 head 일치를 독립 확인했습니다. [Tests](https://github.com/eigger/hass-catprinter/actions/runs/39036837387)는 네 HA/라이브러리 조합과 lint2개 job 전부 성공했고 [Validate](https://github.com/eigger/hass-catprinter/actions/runs/39036837361)는 HACS·Hassfest 성공입니다. 네 테스트 job 모두 blesession0.9.0/imagespec[datamatrix]1.1.0 실제 설치와 `pip check`의 No broken requirements를 확인했습니다. 위 환경표의 원격 Python 패치 버전은 로컬과 구분했습니다.

중앙 구현·검증 종료보고는 [커밋 8d4348e](https://github.com/eigger/hass-repo-standards/commit/8d4348ea951736054d08f7cfe9b19f6d44b37a5e)로 실제 게시됐습니다. 검증 구현의 적용 필수 항목은 PASS 또는 사유 있는 N/A이고 예외는 없습니다. 본 마감 문서는 해당 구현 검증을 기록하는 별도 후속 변경이며 자기 자신이나 미래 commit의 CI 성공을 주장하지 않습니다. 중앙 표의 상태 완료 전환은 문서 게시 후 수행합니다. 실물 프린터·새 proxy 보드·무선 성능·HA UI 미검증 한계는 유지합니다.


## 2026-10-23 HACS ZIP and Downloads (scoped)

- Target base: `7642bffba94f5230e5492e0dc2d1645dcf530da7`; reviewed release central: `fd4162c0b93fbe8e109f99c787773ae09ba157e1`.
- Scope: HACS-04/CI-11 release ZIP and DOC-03/05 Downloads replacing Analytics Usage. No release is created during this update.
- Local scoped validation: PASS — canonical badge check, no Analytics Usage, release metadata/caller contract, actionlint 1.7.12, native git diff --check, unchanged tracked integration/manifest/dependencies/tests.
- Actual archive build: PASS at `be6ff1202d417e7a71b20b1ba1b92dd784673724`; `catprinter.zip`, 32 files, SHA256 `3852b50466626a0ec1872ba8bf8040765cef3b915dfedcdf07853fef1de69049`. All archive members matched checkout bytes; manifest.json and __init__.py are at ZIP root. Final documentation-only follow-up preserves this integration tree. Windows Python 3.14.6; validation WSL Python 3.14.4/PyYAML 6.0.3/packaging 26.0.
- Full central integration checker: FAIL (pre-existing or unadopted contracts outside this scoped update; not treated as PASS). Findings:

```text
DOC-01 README.md: Exactly one ordered header marker pair required
DOC-01 README.ko.md: Exactly one ordered header marker pair required
HA-02 custom_components/catprinter/manifest.json: categories requires 1–3 actual product categories (HA-02 project policy)
TEST-08 tests/components/catprinter/test_binary_sensor.py: Required contract file is missing
TEST-08 tests/components/catprinter/test_image.py: Required contract file is missing
TEST-08 tests/components/catprinter/test_sensor.py: Required contract file is missing
TEST-08 tests/components/catprinter/test_payload_examples.py: Required contract file is missing
HA-13 custom_components/__init__.py: Required contract file is missing
GOV-02 .github/workflows/tests.yml: standards-ref must equal the reviewed reusable workflow SHA
GOV-02 .github/workflows/tests.yml: standards-ref must equal the reviewed reusable workflow SHA
GOV-02 .github/workflows/update_dependencies.yml: standards-ref must equal the reviewed reusable workflow SHA
TEST-03 tests/conftest.py: must match the central template exactly
TEST-08 tests/components/catprinter/conftest.py: Exactly one ordered domain-fixtures marker pair required
CI-02 .github/workflows/tests.yml: name and events must match the central template (actual default branch)
CI-01 .github/workflows/validate.yml: central standards composite action pinned to full SHA required
DOC-07 docs/troubleshooting.md: Use the central troubleshooting H2 headings in their fixed order
DOC-07 README.md: README must link to matching-language local troubleshooting and blesession proxy setup
DOC-07 docs/troubleshooting.ko.md: [Errno 2] No such file or directory: '/mnt/d/Source/Github/.hacs-custom-zip/hass-catprinter/docs/troubleshooting.ko.md'
DOC-07 README.ko.md: README must link to matching-language local troubleshooting and blesession proxy setup
DOC-08 .hass-standards.json: 'payload'
DOC-08 tests/components/catprinter/test_payload_examples.py: [Errno 2] No such file or directory: '/mnt/d/Source/Github/.hacs-custom-zip/hass-catprinter/tests/components/catprinter/test_payload_examples.py'
DOC-08 docs/payload.md: [Errno 2] No such file or directory: '/mnt/d/Source/Github/.hacs-custom-zip/hass-catprinter/docs/payload.md'
DOC-08 README.md: README must link its matching-language local payload guide
DOC-08 docs/payload.ko.md: [Errno 2] No such file or directory: '/mnt/d/Source/Github/.hacs-custom-zip/hass-catprinter/docs/payload.ko.md'
DOC-08 README.ko.md: README must link its matching-language local payload guide
DOC-08 .github/workflows/tests.yml: standards-ref must equal the reviewed reusable workflow SHA
DOC-08 .github/workflows/tests.yml: standards-ref must equal the reviewed reusable workflow SHA
DOC-08 .github/workflows/update_dependencies.yml: Dependency update standards-ref must equal its reviewed reusable workflow SHA
```

- Existing CI workflows are preserved, except hass-kocom-smarthome where matching reviewed central references are synchronized. Existing support minimum and prior exceptions remain.
- Independent review and remote CI: tracked in this branch's pull request; merge requires resolved actionable findings and successful applicable checks. No real release upload, device or new real HA runtime validation is claimed by these local packaging checks.
