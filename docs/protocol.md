# Cat printer BLE 프로토콜

`custom_components/catprinter/catprinter_ble/`가 구현하는 내용. 실기 검증: **X6h** (펌웨어 3.0.5D).

## 1. 전송

### GATT

| 서비스 | write | notify |
|---|---|---|
| `AE30` (일반적) | `AE01` | `AE02` |
| `AE00` | `AE01` | 서비스 내 첫 NOTIFY |
| `FF00` | `FF02` | 서비스 내 첫 NOTIFY |
| `AB00` | `AB01` | 서비스 내 첫 NOTIFY |
| `AE80` | `AE81` | 서비스 내 첫 NOTIFY |
| `49535343-FE7D-…` | `49535343-8841-…` | 서비스 내 첫 NOTIFY |

위 순서로 첫 매칭을 쓴다. 광고 패킷에는 보통 `AF30`이 실린다(X6h). 이름은 `<모델>-<hex>` 형태.

### 쓰기

- write **without response**, `packet = min(협상 MTU − 3, 프로파일 MTU − 3, 사용자 상한)` 바이트 단위
- 청크 사이 `interval` ms 대기 (프로파일, 대부분 2~6 ms)
- 프린터가 `AE 10 70`을 보내면 정지, `AE 00 00`을 보내면 재개 (§4.3)

### 알림 재조립

알림은 여러 프레임이 붙거나 잘려 올 수 있다. `51 78`을 찾아 `LEN_LO + 8` 바이트를 한 프레임으로 자르고, 부족하면 다음 알림과 합친다.

## 2. 프레임

```
51 78 CMD DIR LEN_LO LEN_HI PAYLOAD… CRC8 FF
```

- `DIR`: 0 = 호스트→프린터, 1 = 프린터→호스트
- `LEN`: payload 길이, little-endian
- `CRC8`: poly 0x07, init 0, **payload만**

예) 상태 조회 `51 78 A3 00 01 00 00 00 FF`

## 3. 명령

| CMD | 이름 | payload | 비고 |
|---|---|---|---|
| `A0` | retract | `n_lo n_hi 11` | 역급지 |
| `A1` | feed | `n_lo n_hi` | 급지. 200 dpi는 48, 300 dpi는 72 도트씩 나눠 보냄 |
| `A2` | raw line | `width/8` B | 비압축 1행, **LSB-first** (픽셀 0 → bit 0) |
| `A3` | get state | `00` | §5.1 |
| `A4` | quality | `'1'`~`'5'` | 항상 `'3'` |
| `A6` | control | `05` | 인쇄 중지 |
| `A8` | get info | `00` | §5.2 |
| `AF` | energy | `e_lo e_hi` | 발열 에너지 |
| `BA` | battery | `00` | 미사용 (`A3`에 포함) |
| `BD` | speed | 1 B | 행당 지연. 작을수록 빠름. 200행마다 재전송 |
| `BE` | mode | `00` image / `01` text | |
| `BF` | RLE line | 가변 | §4.2 |

## 4. 래스터

### 4.1 전처리

imagespec 렌더 → 헤드 폭으로 맞춤(좁으면 오른쪽 흰색 패딩, 넓으면 축소) → Floyd–Steinberg 1bpp. 1 = 검정.

### 4.2 행 인코딩

행마다:

1. RLE: 바이트 = `color<<7 | length`, `length ≤ 127`. 흰 행도 흰 런으로 보낸다 (384 px → `7F 7F 7F 03`).
2. RLE 길이 ≤ `width/8` → `BF`, 아니면 `A2` raw (LSB-first).

### 4.3 흐름 제어

| 프레임 | 의미 |
|---|---|
| `51 78 AE 01 01 00 10 70 FF` | 버퍼 가득 → 전송 중단 |
| `51 78 AE 01 01 00 00 00 FF` | 버퍼 빔 → 재개 |

재개 알림이 15 s 안 오면 경고 후 계속 보낸다.

## 5. 응답

### 5.1 `A3` 상태

```
51 78 A3 01 03 00 STATUS LABEL BATT CRC FF
```

| STATUS bit | 조건 |
|---|---|
| 0 | out_of_paper |
| 1 | cover_open |
| 2 | overheating |
| 3 | low_battery |
| 4 | charging |
| 7 | printing |

`LABEL`: 라벨 센서 값(진단용). `BATT`: 프로파일 `battery_model`에 따라 해석 —
`0` 무시, `1` hex 표기를 10진으로 읽어(0x27 → 27) 23~28을 6단계로, `2` 값+1 = %.

### 5.2 `A8` 정보

```
51 78 A8 01 0A 00 TYPE ? WIFI VER[7] CRC FF
```

`TYPE` → `XW00<n>`, `VER` 7바이트 문자열(예: `3.0.5D`).

## 6. 인쇄 시퀀스

```
A4 '3'
[AF energy]              ← 프로파일 에너지 × (1 + (density−4)×0.15), 0이면 생략
BE mode
BD speed
rows (BF | A2)           ← 200행마다 BD speed
BD 25
A1 feed                  ← 기본 paper_num × 48(또는 72) 도트, 48/72씩 분할
A3                       ← 응답이 오면 작업 소비 완료
```

`copies`만큼 `A3` 앞까지 반복. `A3` 응답의 fault 비트 또는 도중 도착한 fault 상태는 `PrinterError`.

## 7. 프로파일 (`models_data.py`)

```
model_no, name_prefix, width_px, dpi, mtu, can_change_mtu, interval_ms,
img_speed, text_speed, energy_thin, energy_mid, energy_deep, energy_text,
rle, paper_num, battery_model, app_uses_spp, unsupported_reason
```

- 이름 매칭은 대소문자 구분 최장 일치 후, 무시 매칭으로 폴백 (`X6h` ≠ `X6H`)
- `can_change_mtu == false`면 MTU 23으로 취급(20 B 패킷)
- `app_uses_spp`: 제조사 앱은 SPP로 쓰는 모델. GATT 경로는 X6h에서 확인됨
- `unsupported_reason`: `auth`(D1 챌린지 필요), `window`(YMS-BT01 credit 흐름 제어)

X6h: 384 px · 200 dpi · MTU 180 · interval 4 · speed 10/10 · energy 5000/5000/5000/8000 · paper_num 2 · battery_model 1

## 8. 구현하지 않은 것

라벨 모드(`A1 … 11`, `AC`, `A6 10 02`, 갭 감지), 그레이스케일(`BE 00 01`), 타투(`BE 02`), 압축 블록(`CE`), `D1` 인증, YMS-BT01 credit 흐름 제어, ESC/POS 변형(LY 계열), 4"/8" 모델, Wi-Fi/활성화/펌웨어 명령.
