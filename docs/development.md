# 개발·실제 HA 테스트

[English README](../README.md) · [한국어 README](../README.ko.md) · [채택 체크리스트](../ADOPTION_CHECKLIST.md)

이 통합은 HACS의 `custom_components/catprinter/`로 배포합니다. HA Core와 같은 역할의 모듈·config entry 생명주기·공개 API를 사용하며 공식 Core 포함이나 공식 품질 등급을 의미하지 않습니다.

## 구조와 테스트 경계

- 구현: `custom_components/catprinter/`의 config flow·entity·sensor·binary_sensor·image·services와 `catprinter_ble/` 프로토콜 경계.
- 테스트: `tests/components/catprinter/`, 공통 fixture는 `tests/conftest.py`. 기존 모델·프레임·클라이언트 회귀 테스트를 함께 유지합니다.
- 실제 HA와 `pytest-homeassistant-custom-component`의 `hass`, `enable_custom_integrations`, `MockConfigEntry`를 통해 loader·entry·플랫폼·registry·action을 실행합니다. `MockConfigEntry`는 실제 HA 테스트 helper이며 HA 가짜 모듈·FakeHass를 의미하지 않습니다.
- Bluetooth 광고·GATT 응답 등 외부 장치 경계만 대체합니다. BLE 프린터와 무선 경로 실물 검증은 자동 테스트와 구분합니다.

## 지원 최소와 current 테스트

| 구분 | Python | HA | pytest-homeassistant-custom-component | 선언 |
|---|---|---|---|---|
| 기존 지원 최소 보존 | 3.13 | 2025.2.0 | 0.13.210 | `hacs.json`, `requirements_test_min.txt` |
| current 검증 환경 | 3.14 | 2026.10.2 | 0.13.373 | `requirements_test.txt` |

이 표는 검증 환경의 정확한 목표 버전이며 실행 성공 판정과 실제 설치 버전·커밋·명령은 [체크리스트](../ADOPTION_CHECKLIST.md)에 기록합니다. current 도구 최신화와 `hacs.json.homeassistant` 지원 최소 변경은 별개입니다. 최신 HA에서 실패하면 호환 문제를 수정하며 그것만으로 최소 지원을 올리지 않습니다. 실제 비호환 근거와 별도 명시적 사용자 승인 없이 기존 2025.2.0 하한을 변경하지 않습니다.

최소 HA requirements는 역사적 조합을 재현하므로 Dependabot 자동 갱신에서 제외합니다. current HA와 pytest 플러그인은 호환되는 한 그룹으로 검토하며, 최소 파일이 섞인 PR·다운그레이드·Python/expected-ha-version 불일치를 자동 병합하지 않습니다.

## 설치·실행

최소와 current, 라이브러리 최소와 current는 **각각 별도 가상환경**에서 실행합니다. 중앙 표준 checkout을 위 참조 SHA로 준비한 뒤 해당 환경의 Python으로 아래 공통 installer를 사용합니다. `STANDARDS_CHECKOUT`은 실제 로컬 경로로 바꿉니다.

```bash
python3.14 -m venv .venv-current
source .venv-current/bin/activate
python -m pip install --upgrade pip packaging
STANDARDS_CHECKOUT=/path/to/hass-repo-standards
INPUT_DOMAIN=catprinter \
INPUT_REQUIREMENTS=requirements_test.txt \
INPUT_HA_COMPONENTS='bluetooth recorder image sensor binary_sensor' \
INPUT_TEST_PROFILE=ha \
INPUT_EXPECTED_HA_VERSION=2026.10.2 \
INPUT_DEPENDENCY_MODE=current \
RUNNER_TEMP="$(mktemp -d)" \
python "$STANDARDS_CHECKOUT/actions/python-environment/install.py"
# Run the mandatory payload contract before ordinary regressions.
export PAYLOAD_REPOSITORY="$PWD"
export PAYLOAD_DOMAIN=catprinter
export PYTHONPATH="$STANDARDS_CHECKOUT/scripts${PYTHONPATH:+:$PYTHONPATH}"
python -m pytest -p hass_standards_payload tests/components/catprinter/test_payload_examples.py -v
python -m pytest tests/components/catprinter/ --ignore=tests/components/catprinter/test_payload_examples.py -v
python -m pip check
```

최소 HA 검증은 Python 3.13의 별도 환경에서 `INPUT_REQUIREMENTS=requirements_test_min.txt`, `INPUT_EXPECTED_HA_VERSION=2025.2.0`로 실행합니다. 정확한 최소 라이브러리 검증은 해당 환경에서 `INPUT_DEPENDENCY_MODE=minimum`, `INPUT_MINIMUM_PACKAGES='["imagespec","blesession"]'`를 추가해 installer를 다시 실행하고 `pytest`·`pip check`를 모두 확인합니다. `--no-deps`·resolver 무시·HA stub으로 설치 실패를 우회하지 않습니다.

런타임 의존성은 manifest의 `blesession>=0.9.0`, `imagespec[datamatrix]>=1.1.0`입니다. 최소 라이브러리 환경은 각각 **0.9.0 / 1.1.0**의 실제 설치를 확인합니다. 최신 라이브러리 해결값과 최소 HA는 별개 축입니다. 환경마다 Python/HA/플러그인/imagespec/blesession 실제 설치값을 기록합니다.

```bash
python -m pip install -r requirements_lint.txt
python -m ruff check .
python -m ruff format --check .
```

정확한 원격 matrix·inputs는 [Tests workflow](../.github/workflows/tests.yml)가 원본입니다. [Validate](../.github/workflows/validate.yml)의 HACS·Hassfest 결과와 대상 commit SHA도 별도로 확인합니다.

## 의존성·문서 변경

Python 런타임은 manifest requirements, HA 구성요소는 dependencies/after_dependencies, 테스트·린트 도구는 별도 requirements에 둡니다. 새 의존성 추가는 [공통 의존성 규칙](https://github.com/eigger/hass-repo-standards/blob/v1.0.0/docs/dependencies.md)의 호환 Python/HA·extras·marker·라이선스·최소/현재 검증을 따릅니다. bot은 검증한 tree의 요구사항만 PR로 제안하며 extras와 연산자를 보존합니다.

영문 README.md·한국어 README.ko.md는 짧은 빠른 시작을 유지하고 상세 사용·문제 해결은 docs로 연결합니다. 배지는 관리 블록과 `.hass-standards.json`으로 두 언어를 함께 갱신합니다. ZIP 배포 Custom 통합이므로 Downloads 배지는 모든 GitHub Release 첨부 asset의 다운로드 합계를 표시합니다. HACS 전용 다운로드나 활성 설치 수는 아닙니다.

## 로컬 BLE 도구와 한계

`tools/probe.py`는 GATT 서비스·구독·장치 정보·상태를 조회한 뒤 **용지를 이동**합니다. `tools/print_test.py`는 테스트 띠나 이미지를 **실제로 인쇄**합니다. 둘 다 HA 밖에서 하드웨어를 조작하므로 `--help`와 소스를 확인하고 다른 앱·HA 연결을 종료한 별도 실험에서 사용하세요. 독립 스캐너는 운영 통합의 HA Bluetooth 관리 API를 대체하지 않습니다.

기존 실물 확인은 X6h 펌웨어 3.0.5D의 로컬 어댑터·ESPHome 프록시입니다. 이번 공통화의 실물 모델·새 프록시 보드·성능·HA frontend UI 검증은 미수행이며 기존 확인과 구분합니다.
