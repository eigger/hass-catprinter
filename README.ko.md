<!-- hass-standards:header:start -->
# hass-catprinter

Home Assistant의 Bluetooth 스택과 ESPHome 프록시를 통해 저렴한 Bluetooth 감열식 “고양이 프린터”에 글자·QR 코드·이미지를 인쇄하는 HACS 커스텀 통합입니다.

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

## 기능과 최소 요구사항

- `catprinter.print`로 [imagespec](https://github.com/eigger/imagespec) 레이아웃을 인쇄하고 `catprinter.feed`로 용지를 이동합니다. 상태·배터리·마지막 이미지·세션 진단 엔티티를 제공합니다.
- 기존 실물 확인: **X6h, 펌웨어 3.0.5D**, 로컬 어댑터·ESPHome 프록시. 나머지 프로토콜 모델은 **미검증**이며 [지원 모델과 제한](docs/ko/user-guide.md#지원-모델)을 확인하세요.
- Home Assistant **2025.2.0 이상**, 지원 BLE 프린터, 정상 동작하는 HA Bluetooth 어댑터나 프록시가 필요합니다. 프록시는 GATT 연결을 지원해야 하며 프린터를 깨우고 다른 앱의 연결을 종료해야 합니다.

## 설치

<!-- hass-standards:installation:start -->
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=eigger&repository=hass-catprinter&category=integration)
<!-- hass-standards:installation:end -->

1. **HACS → 사용자 지정 저장소 → 통합**에 `https://github.com/eigger/hass-catprinter`를 추가하거나 `custom_components/catprinter`를 HA 설정의 `custom_components/` 아래로 복사합니다.
2. Home Assistant를 재시작합니다.
3. **설정 → 기기 및 서비스**에서 발견한 프린터를 확인하거나 **통합 추가 → Cat Printer**를 선택합니다. 지원 프린터를 찾지 못하면 주소·모델을 수동으로 입력합니다.

[Bluetooth 프록시 설정](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md)에서 XIAO W5500 V1.2와 USB-A 동글 형태의 M5Stack AtomS3U 준비 방법을 확인하세요. 공통 추천은 모든 보드를 이 프린터와 실물 검증했다는 뜻은 아닙니다.

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

## 중요한 제한

모델명은 대소문자를 구분합니다(`X6h`와 `X6H`는 다름). 광고 발견만으로 GATT 인쇄가 되는 것은 아닙니다. 제조사 `D1` 비밀키·다른 흐름 제어가 필요한 모델, A4·Wi-Fi 프린터는 지원하지 않으며 Bluetooth Classic SPP를 사용하지 않습니다. 휴대전화·제조사 앱 연결을 종료하고 용지를 넣은 뒤 커버를 닫으세요. 이번 공통화에서 실물 프린터·HA 프런트엔드 검증을 새로 수행하지는 않았습니다.

## 문서

| 주제 | 한국어 | English |
|---|---|---|
| 모델·엔티티·작업·예제·전송 조정 | [사용 안내](docs/ko/user-guide.md) | [User guide](docs/user-guide.md) |
| 전원·연결·용지·세션 오류 | [문제 해결](docs/troubleshooting.ko.md) | [Troubleshooting](docs/troubleshooting.md) |
| payload 액션 예제·렌더링·출력 설정 | [payload 안내](docs/payload.ko.md) | [Payload guide](docs/payload.md) |
| 실제 HA 테스트·의존성·참여 | [개발 안내](docs/development.md) | [Development (Korean)](docs/development.md) |
| 프레임·CRC·모델 프로파일 | [프로토콜 원문 (영어)](docs/protocol.md) | [Protocol](docs/protocol.md) |
| 기준·검증 증거 | [적용 규칙](STANDARDS.md) | [Adoption checklist (Korean)](ADOPTION_CHECKLIST.md) |

Downloads 배지는 HACS가 사용하는 통합 ZIP을 포함한 현재 GitHub Release 첨부 파일의 다운로드 합계이며 활성 설치 수나 고유 사용자 수가 아닙니다. 이전 Usage 배지는 HA Analytics 참여 설치만 집계했으며 미집계나 조회 실패는 0 설치를 뜻하지 않았습니다.

버그는 [Issues](https://github.com/eigger/hass-catprinter/issues)에 문제 해결 문서의 비식별 증거와 함께 제보하고, 질문·제안은 [Discussions](https://github.com/eigger/hass-catprinter/discussions)를 이용하세요.

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
