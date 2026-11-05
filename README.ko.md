<!-- hass-standards:header:start -->
# Cat Printer for Home Assistant

Home Assistant Bluetooth와 ESPHome 프록시를 통해 Bluetooth 감열식 고양이 프린터에 글자·QR 코드·이미지를 인쇄하는 커스텀 통합입니다.

[English](README.md) | **한국어**

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-catprinter?style=flat)](https://github.com/eigger/hass-catprinter/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat)](#설치)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.2.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-catprinter/tests.yml?branch=main&style=flat&label=Tests)](https://github.com/eigger/hass-catprinter/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-catprinter/validate.yml?branch=main&style=flat&label=Validate)](https://github.com/eigger/hass-catprinter/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-catprinter?style=flat)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/eigger/hass-catprinter/latest/total?style=flat&color=41BDF5&label=Downloads)](https://github.com/eigger/hass-catprinter/releases)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

![Cat Printer](custom_components/catprinter/brand/logo.png)

## 주요 기능

- `catprinter.print`로 [imagespec](https://github.com/eigger/imagespec) 레이아웃을 인쇄하고 `catprinter.feed`로 용지를 이동합니다. 상태·배터리·마지막 이미지·세션 진단 엔티티를 제공합니다.
- 기존 실물 확인: **X6h, 펌웨어 3.0.5D**, 로컬 어댑터·ESPHome 프록시. 나머지 프로토콜 모델은 **미검증**이며 [지원 모델과 제한](docs/ko/user-guide.md#지원-모델)을 확인하세요.

## 요구사항

- **Home Assistant:** 2025.2.0 이상.
- **Bluetooth:** 정상 동작하는 Home Assistant Bluetooth 어댑터 또는 GATT 연결이 활성화된 프록시.
- **기기:** [지원 BLE 프린터](docs/ko/user-guide.md#지원-모델).

## 설치

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-catprinter&category=integration)
<!-- hass-standards:installation:end -->

1. 위 배지를 클릭해 마켓플레이스에서 저장소를 엽니다.
2. 저장소를 직접 추가하려면 **설정 → 마켓플레이스 → 링크에서 추가**에서 <https://github.com/eigger/hass-catprinter>을 입력합니다. 안내가 표시되면 GitHub 계정을 연결합니다.
3. **설치**를 선택합니다. 재시작 안내가 표시되면 Home Assistant를 재시작합니다. 설치가 끝나면 [설정](#설정)으로 이동합니다.

## 설정

1. 프린터를 깨우고 용지를 넣은 뒤 커버를 닫습니다. 휴대전화·제조사 앱 연결을 종료합니다.
2. **설정 → 기기 및 서비스**에서 발견된 프린터를 확인하거나 **통합 추가 → Cat Printer**를 선택합니다. 프린터가 발견되지 않으면 주소와 모델을 입력합니다.

원격 Bluetooth 연결에는 [프록시 설정 가이드](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md)의 XIAO W5500 V1.2와 USB-A M5Stack AtomS3U 안내를 참고하세요. 일반 추천 보드이며 프린터 실물 검증 범위는 주요 기능 절에 있습니다.

## 빠른 시작

**개발자 도구 → 작업**에서 프린터 기기를 대상으로 실행합니다.

```yaml
action: catprinter.print
target:
  device_id: YOUR_PRINTER_DEVICE_ID
data:
  payload:
    - type: text
      value: Hello Home Assistant!
      x: 8
      y: 8
      size: 40
  height: 80
```

## 중요 제한사항

- 모델명은 대소문자를 구분합니다(`X6h`와 `X6H`는 다릅니다). 광고 발견만으로 GATT 인쇄 가능 여부를 판단할 수 없습니다.
- 제조사 `D1` 비밀키나 호환되지 않는 흐름 제어가 필요한 모델, A4·Wi-Fi 프린터, Bluetooth Classic SPP는 지원하지 않습니다.
- 기존 실물 검증 범위는 위에 기재했습니다. 이번 공통화에서는 실물 프린터나 Home Assistant 화면을 새로 검증하지 않았습니다.

## 문서

| 주제 | 한국어 | English |
|---|---|---|
| 모델·엔티티·작업·예제·전송 조정 | [사용 안내](docs/ko/user-guide.md) | [User guide](docs/user-guide.md) |
| 전원·연결·용지·세션 오류 | [문제 해결](docs/troubleshooting.ko.md) | [Troubleshooting](docs/troubleshooting.md) |
| payload 액션 예제·렌더링·출력 설정 | [payload 안내](docs/payload.ko.md) | [Payload guide](docs/payload.md) |
| 실제 HA 테스트·의존성·참여 | [개발 안내](docs/development.md) | [Development (Korean)](docs/development.md) |
| 프레임·CRC·모델 프로파일 | [프로토콜 원문 (영어)](docs/protocol.md) | [Protocol](docs/protocol.md) |
| 기준·검증 증거 | [적용 규칙](STANDARDS.md) | [Adoption checklist (Korean)](ADOPTION_CHECKLIST.md) |

버그 제보에는 문제 해결 문서에 따라 개인 정보를 제거한 진단 자료를 첨부하세요.

<!-- hass-standards:support:start -->
## 지원

- [Issues](https://github.com/eigger/hass-catprinter/issues): 버그를 신고하거나 기능을 요청하세요.
- [Discussions](https://github.com/eigger/hass-catprinter/discussions): 질문하고 사용 경험을 공유하세요.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## 라이선스

[MIT License](LICENSE) 라이선스로 배포됩니다.
<!-- hass-standards:license:end -->
