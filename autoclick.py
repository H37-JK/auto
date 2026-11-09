# 4~10초 무작위 간격으로 지정한 화면 위치를 클릭하는 자동 클릭기 (추가 설치 필요 없음)
#   F8  : 지금 마우스가 있는 위치를 클릭 위치로 지정 (다시 누르면 위치 변경)
#   F9  : 일시정지 / 다시 시작
#   F10 : 종료
#   비상 정지: 마우스를 화면 왼쪽 위 모서리로 밀어 넣기
import ctypes
import time
from ctypes import wintypes

import random

MIN_SEC, MAX_SEC = 4.0, 10.0  # 클릭할 때마다 이 범위에서 무작위 간격(초)
HOLD_MIN, HOLD_MAX = 0.05, 0.12  # 누르고 떼는 사이 무작위 시간(초)
JITTER = 5  # 클릭 위치를 지정 좌표에서 x, y 각각 최대 이만큼(픽셀) 무작위로 흔들기


def gap():
    return random.uniform(MIN_SEC, MAX_SEC)

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

VK_F8, VK_F9, VK_F10 = 0x77, 0x78, 0x79
LEFTDOWN, LEFTUP = 0x0002, 0x0004


def cursor():
    p = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def pressed(vk):
    # 마지막 확인 이후 눌린 적이 있으면 True
    return bool(user32.GetAsyncKeyState(vk) & 0x0001)


def click(x, y):
    # 항상 지정 좌표를 기준으로 흔들기 때문에 누적되지 않고 ±JITTER 범위를 벗어나지 않음
    x += random.randint(-JITTER, JITTER)
    y += random.randint(-JITTER, JITTER)
    ox, oy = cursor()
    user32.SetCursorPos(x, y)
    time.sleep(0.02)
    user32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
    time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))  # 사람처럼 잠깐 누르고 있기
    user32.mouse_event(LEFTUP, 0, 0, 0, 0)
    time.sleep(0.02)
    user32.SetCursorPos(ox, oy)  # 마우스를 원래 자리로 돌려놓기
    return x, y


def main():
    print("=" * 50)
    print(" 자동 클릭기 (4~10초 무작위 간격)")
    print("  F8  : 지금 마우스 위치를 클릭 위치로 지정/변경")
    print("  F9  : 일시정지 / 다시 시작")
    print("  F10 : 종료")
    print("  비상정지: 마우스를 화면 왼쪽 위 끝으로")
    print("=" * 50)
    print("\n클릭할 곳에 마우스를 올리고 F8을 누르세요...")

    for vk in (VK_F8, VK_F9, VK_F10):
        pressed(vk)  # 이전에 눌린 기록 지우기

    target = None
    paused = False
    next_click = 0.0
    count = 0

    while True:
        if pressed(VK_F10):
            print("\nF10: 종료합니다.")
            break
        if pressed(VK_F8):
            target = cursor()
            paused = False
            next_click = time.time() + gap()
            print(f"\n클릭 위치 지정: {target}  -> 4~10초 무작위 간격으로 클릭 시작")
        if pressed(VK_F9) and target:
            paused = not paused
            print("\n일시정지" if paused else "\n다시 시작")
            next_click = time.time() + gap()
        x, y = cursor()
        if x <= 2 and y <= 2 and target:
            print("\n마우스가 왼쪽 위 모서리에 있어 비상 정지했습니다.")
            break

        if target and not paused and time.time() >= next_click:
            pos = click(*target)  # target 자체는 바뀌지 않고, 실제 클릭 위치만 흔들림
            count += 1
            next_click = time.time() + gap()
            print(f"\r클릭 {count}회  실제 위치 {pos}  다음 클릭까지 {next_click - time.time():.1f}초   ", end="", flush=True)

        time.sleep(0.03)

    time.sleep(1.5)


if __name__ == "__main__":
    main()
