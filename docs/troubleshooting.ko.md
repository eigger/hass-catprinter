# Cat Printer 문제 해결

[메인](../README.ko.md) | [English](troubleshooting.md) | **한국어**

## 공통 문제 해결

먼저 [공통 Bluetooth 문제 해결](https://github.com/eigger/blesession/blob/main/docs/troubleshooting.ko.md)을 확인하세요. [Bluetooth 프록시 설정](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md)부터 확인하세요. 프록시 펌웨어 설정과 Cat Printer 옵션은 별개입니다. 공통 문서의 기본 추천은 Ethernet·PoE·외장 안테나 구성의 XIAO W5500 Ethernet Adapter **V1.2**, USB-A 동글 형태는 **M5Stack AtomS3U**이며 구매 링크도 공통 문서에 있습니다. 모든 보드와 프린터 조합을 새로 실물 검증했다는 뜻은 아닙니다.

## 기기별 확인 사항

- 전원을 켜고 충전한 뒤 해당 모델의 조작법으로 깨웁니다. 절전 시간은 모델마다 다릅니다. 기존 X6h의 한 시간 유휴 관찰을 모든 모델의 보장으로 적용하지 않습니다.
- 호환 용지를 넣고 커버를 닫습니다. `out_of_paper`, `cover_open`, `overheating`이면 용지·커버를 조치하거나 헤드가 식기를 기다린 후 다시 시도합니다.
- 제조사·휴대전화 앱과 다른 Bluetooth 중앙 장치 연결을 종료합니다. 기존 안내처럼 시험 중 휴대전화 Bluetooth 설정으로 페어링하지 마세요. 모든 모델의 공통 초기화·본딩 절차는 확인되지 않았습니다.
- 대소문자를 구분해 정확한 모델을 선택합니다(`X6h`와 `X6H`는 다름). D1 비밀키 인증이나 미지원 흐름 제어 모델은 거부하며 비밀키 입력 흐름은 없습니다. 키를 추측하거나 반복 연결로 인증을 우회하려 하지 마세요.
- 광고 발견과 GATT 서비스·특성의 실제 사용은 별개입니다. “h” 모델도 Classic SPP 대신 BLE GATT를 사용합니다. 수동 주소·모델 선택은 없는 GATT 기능을 추가하지 않습니다.

## 증상과 조치

| 증상 | 실패 단계 | 확인 사항 | 조치 |
|---|---|---|---|
| 발견 안 됨 / unreachable | 발견 / connect | 깨우기·배터리·프록시 온라인·거리·광고 이름 | 프린터를 깨우고 충전하며 수신기를 복구합니다. 실제 일치하는 지원 프로파일이 있을 때만 수동 설정을 사용합니다. |
| 발견되지만 연결 불가 | connect | GATT용 `bluetooth_proxy.active`, 빈 슬롯, 다른 앱 연결, 프록시 전원·네트워크 | 다른 앱 연결을 종료하고 슬롯을 확보한 뒤 다시 시도합니다. `esp32_ble_tracker.scan_parameters.active`는 스캔 응답 요청 설정이며 별개입니다. passive 스캔만으로 연결 불가를 단정하지 않습니다. |
| 연결 후 무응답 | session / subscribe / query | 모델·펌웨어·인쇄 서비스·절전·사용 중 상태 | 프린터를 깨우고 모델을 확인합니다. `NotificationTimeout`은 연결·구독 후 응답 대기 실패이며 곧바로 페어링 문제로 단정하지 않습니다. |
| 줄 누락 / 조기 중단 | transfer / raster | 용지·커버·실제 경로·전송 간격 | 자동 프록시 간격은 최소 20ms, 패킷은 최대 100바이트이며 로컬은 모델 설정을 따릅니다. 구성에서 패킷 간격을 늘려 확인하되 프록시 펌웨어 옵션과 혼동하지 않습니다. |
| 연결 끊김 / write timeout | transfer / link / write | 실제 경로·배터리·프록시 재시작·전원·네트워크·동시 부하 | 전원·네트워크를 복구하고 인쇄물을 확인한 후 다시 시도합니다. 쓰기 자체가 반환되지 않은 것과 프린터 응답 대기는 다릅니다. 유지 중 링크가 멎으면 버리고 다음 작업에서 새로 연결합니다. |
| 완료 확인 timeout | completion | 실제 인쇄 여부 | 재전송 전 실제 인쇄물을 확인합니다. 이미 인쇄됐을 수 있으며 다시 보내면 중복 라벨·용지 소모가 생깁니다. |
| 간헐적 성공 | 마지막 보고의 실패 단계 | 마지막 실패·최근 인쇄·연결 유지·슬롯 점유 | 최근 성공만 보지 말고 마지막 실패를 비교합니다. 성공해도 last_failure는 유지합니다. 기본은 연결–조회–해제이며 연결 유지가 꺼져 있습니다. |

연결 복구·프린터 진단은 모든 인쇄 실패의 자동 재시도를 보장하지 않습니다. 이 통합에는 BLE ESL의 Retry Count·Debounce·guarded write 작업이 없습니다.

## 진단 및 로그

**설정 → 기기 및 서비스 → Cat Printer → 해당 기기**에서 진단 엔티티를 열거나 **개발자 도구 → 상태**에서 속성을 확인합니다. 실제 entity ID는 registry 이름에 따라 달라집니다.

- `sensor.*_print_duration`: 현재·마지막 인쇄 초 수. 완료 후 마지막 인쇄 세션 보고를 속성으로 제공합니다. 인쇄 중에는 이전 보고를 제외해 현재 시간과 혼동하지 않게 합니다.
- `sensor.*_last_failure`: 집계한 마지막 실패 시각과 보고 속성을 다음 실패까지 유지합니다. 성공으로 지우지 않습니다.
- `sensor.*_error_count`: entry 로딩 이후 집계 실패 수이며 다시 로딩하면 초기화됩니다. 연결 전에 실패한 상태 폴링은 세지 않으므로 전체 누적 오류 수가 아닙니다.
- `sensor.*_status`, `sensor.*_conditions`, 용지·커버·과열 binary sensor로 장치 오류를 구분합니다. `binary_sensor.*_connection`은 현재 링크이며 작업 사이 off는 정상일 수 있습니다.

해당 보고에 실제 있을 때 `failed_stage`, `failed_detail`, `error`, `likely_cause`, `via`, `via_type`, `rssi`, `paths`, `via_unconfirmed` 등을 확인합니다. 모든 실패에 모든 키가 있는 것은 아닙니다. 미확정·광고 수신 경로를 실제 연결 경로로 확정하거나 RSSI만으로 원인을 단정하지 않습니다.

장치 단계 `subscribe`, `precheck`, `query_info`, `query_state`는 공통 `session`으로, `raster`, `feed`는 `transfer`로 매핑됩니다. 연결·링크 오류는 blesession의 공통 단계·세부값을 사용합니다. error·cause와 함께 읽어 용지 문제와 전송·프로토콜 오류를 구분하세요. 별도 `diagnostics.py` 다운로드는 없으며 실제 센서 속성·작업 trace를 사용합니다.

HA·통합·알 수 있는 blesession/imagespec 설치 버전, 프린터 모델·펌웨어, 로컬 어댑터 또는 프록시 모델·리비전·ESPHome 버전, 실패 시각·비식별 속성·작업 YAML·실제 인쇄 여부를 남깁니다. 마지막 성공과 실패, 미검증 경로를 구분하세요.

필요한 재현 구간만 실제 로거를 켠 뒤 수집 후 끕니다.

```yaml
logger:
  logs:
    custom_components.catprinter: debug
```

## 문제가 계속되는 경우

위 증거와 기존 이슈 안내를 따라 [Issues](https://github.com/eigger/hass-catprinter/issues)에 제보하세요. 공개 전에 로그·속성·trace의 Bluetooth/MAC/기기 주소, 내부 IP·호스트명, 토큰·키, 개인 인쇄 payload·이미지를 제거하세요. 사용 질문은 [Discussions](https://github.com/eigger/hass-catprinter/discussions)를 이용합니다.

기존 실물 확인은 X6h 펌웨어 3.0.5D의 로컬 어댑터·ESPHome 프록시입니다. 이번 공통화는 자동 HA·전송 테스트이며 새 실물 모델·보드·무선 성능·프런트엔드 검증이 아닙니다. [적용 증거](../ADOPTION_CHECKLIST.md)를 확인하세요.
