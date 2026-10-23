# Cat Printer payload 안내

[README](../README.ko.md) | [English](payload.md) | **한국어**

## 공통 payload 안내

공통 문법·요소·속성·색상·회전·디더링은 [imagespec payload 안내](https://github.com/eigger/imagespec/blob/main/docs/payload.ko.md)를 확인하세요. 이 통합의 액션 틀과 프린터 설정은 아래에서 설명합니다.

## 이 통합에서 payload 사용

**개발자 도구 → 작업**, 스크립트 또는 자동화에서 `catprinter.print`를 호출합니다. 설정한 프린터를 `target.device_id`로 선택하거나 해당 프린터의 엔티티를 `target.entity_id`로 지정합니다. 영역 대상도 로드된 프린터로 해석합니다. 로드된 프린터가 하나뿐이면 대상 없이 선택할 수 있으며 여러 대라면 원하는 대상을 명시하세요.

`data.payload`는 imagespec 요소 목록입니다. Home Assistant가 액션 데이터의 템플릿을 평가한 후 통합이 렌더링하며, 통합은 준비된 payload를 별도의 Jinja 재평가 없이 imagespec에 전달합니다. 글자·QR 코드·다운로드 이미지·인쇄 조정은 기존 [사용 안내 예제](ko/user-guide.md#인쇄-작업)를 함께 확인하세요.

## 최소 동작 예제

[전체 액션 YAML](../examples/payload/minimal.yaml)은 X6h 프로파일, 글자 요소, 기본 내장 폰트로 **384 × 80픽셀** 흑백 이미지를 렌더링합니다. `image.cat_printer_last_print`를 설정한 프린터의 엔티티로 바꾸거나 작업 편집기에서 해당 기기를 선택하세요. 실제 엔티티 ID는 레지스트리 이름에 따라 달라집니다.

예제의 `preview: true`는 마지막 인쇄 이미지를 갱신하고 PNG 데이터 URL을 반환하며 인쇄 명령은 보내지 않습니다. 미리보기를 확인한 후 `preview: false`로 바꾸면 인쇄합니다. 미리보기도 헤드 폭을 알아야 하므로 로드된 프린터 항목이 필요합니다. 공통 안내의 요소 목록만 있는 예제와 달리 대상·데이터를 포함한 전체 HA 액션입니다.

## 기기 출력 설정

폭은 설정한 모델이 결정하며 X6h는 **384픽셀, 200dpi** 헤드입니다. 폭을 지정하는 액션 옵션은 없습니다. `height` 기본값은 240픽셀이며 작업 편집기는 8–4000을 제공합니다. 모든 요소와 여백을 담도록 높이를 선택하세요. 다른 프로파일은 각자의 헤드 폭을 사용하며 [지원 모델](ko/user-guide.md#지원-모델)을 확인하세요.

`rotate`는 0·90·180·270도입니다. 통합 내부의 imagespec `rotate_mode`는 `canvas`로 고정됩니다. 90·270도에서는 높이 × 헤드 폭 캔버스에 작성하며 최종 이미지는 계속 헤드 폭 × 높이입니다. 예제는 0도입니다. 출력은 흑백(`#000000`, `#ffffff`)이고 `background` 기본값은 흰색입니다. 내부 전역 렌더러 디더링은 꺼져 있으며(`dither=False`), 기존 `dlimg` 예제 같은 요소별 이미지 처리는 imagespec 요소 옵션을 따릅니다. `rotate_mode`와 전역 `dither`는 액션 옵션이 아닙니다.

기본 폰트는 내장 `ppb.ttf`이며 `rbm.ttf`도 포함합니다. 요청한 폰트의 기본 파일명은 통합의 `fonts` 디렉터리, Home Assistant의 `www/fonts` 순서로 찾습니다. 사용자 폰트는 먼저 해당 경로에 설치한 뒤 이름을 지정하세요. 렌더링 컨텍스트는 로컬 이미지를 허용하며 다운로드 이미지는 접근 가능한 원본이 필요합니다. 이 예제와 문서는 네트워크 이미지나 사용자 폰트를 요구하지 않습니다.

`mode`·`density`·`energy`·`speed`·`feed`·`copies`는 렌더링 이후 기기 작업을 조정하며 캔버스 폭을 바꾸지 않습니다. [사용 안내](ko/user-guide.md#인쇄-작업)에 각 조정 항목이 있습니다. 감열지는 단색으로 출력하며 컬러 프린터가 아닙니다.

## 지원 기능과 제한

manifest는 `imagespec[datamatrix]>=1.1.0`을 요구합니다. 요소 지원과 속성은 실제 설치한 imagespec 버전을 따르므로 최신 릴리스의 기능을 가정하지 말고 공통 안내를 확인하세요. 글자·QR 코드·다운로드 이미지 예제는 사용 안내에 보존되어 있습니다. datamatrix extra는 선언되어 있지만 그 밖의 선택 extras를 이 통합이 보장하지는 않습니다.

통합은 실제 폰트 resolver와 Home Assistant recorder 히스토리 제공자(`get_significant_states`)를 imagespec에 전달합니다. 히스토리 요소에는 요청한 엔티티·시간 범위의 recorder 데이터가 필요하며 빈 히스토리는 Bluetooth 실패의 근거가 아닙니다. HA 액션 템플릿은 HA의 일반 템플릿 컨텍스트로 엔티티 상태를 읽을 수 있습니다. 별도의 통합 전용 템플릿 엔진·폰트 다운로드 액션·히스토리 설정 액션은 없습니다.

기존 로컬 어댑터·프록시 실물 확인은 X6h 펌웨어 3.0.5D뿐이며 다른 지원 프로파일은 미검증입니다. D1 비밀키 인증·미지원 credit-window 흐름 제어·Classic SPP·A4·Wi-Fi 인쇄는 지원하지 않습니다. 미리보기 렌더링 성공만으로 GATT 전송·용지 처리·실물 출력을 검증할 수 없습니다.

## 문제 해결

렌더링 오류는 설치한 imagespec 버전의 요소 속성·폰트 이름·이미지 접근·캔버스 경계를 확인하세요. 렌더링 실패는 `Failed to create image`, BLE 인쇄 실패는 `Failed to print`로 보고합니다. 전송 설정을 바꾸기 전에 마지막 인쇄 이미지를 확인하세요.

전원·용지·연결·세션 보고는 [기기별 문제 해결](troubleshooting.ko.md)을 따르세요. 재현 가능한 문제는 기존 [Issues](https://github.com/eigger/hass-catprinter/issues)의 제보 안내를 이용하고 공개 증거에서 개인 payload·이미지·주소를 제거하세요.
