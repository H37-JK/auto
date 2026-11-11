# 4~7초 무작위 간격으로 지정한 화면 위치들을 순서대로 클릭하는 자동 클릭기 (추가 설치 필요 없음)
#   1 : 지금 마우스가 있는 위치를 클릭 위치로 추가 (최대 POINTS곳, 다 찬 뒤 누르면 처음부터)
#   2 : 일시정지 / 다시 시작
#   3 : 종료
#   4 : 지정한 위치 모두 지우기 (처음부터 다시 지정)
#   (키보드 위쪽 숫자열 키. 전역으로 감지하므로 다른 곳에서 타이핑해도 반응함)
#   비상 정지: 마우스를 화면 왼쪽 위 모서리로 밀어 넣기
import ctypes
import time
from ctypes import wintypes

import random

MIN_SEC, MAX_SEC = 4.0, 7.0  # 클릭할 때마다 이 범위에서 무작위 간격(초)
HOLD_MIN, HOLD_MAX = 0.05, 0.12  # 누르고 떼는 사이 무작위 시간(초)
JITTER = 5  # 클릭 위치를 지정 좌표에서 x, y 각각 최대 이만큼(픽셀) 무작위로 흔들기
POINTS = 6  # 클릭할 위치 개수
GAP_MIN, GAP_MAX = 0.3, 0.8  # 한 주기 안에서 위치 사이 간격(초)


def gap():
    return random.uniform(MIN_SEC, MAX_SEC)

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

VK_ADD, VK_PAUSE, VK_QUIT, VK_RESET = 0x31, 0x32, 0x33, 0x34  # 숫자 1, 2, 3, 4
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
    print(f" 자동 클릭기 ({POINTS}곳, 4~7초 무작위 간격)")
    print(f"  1 : 지금 마우스 위치를 클릭 위치로 추가 (최대 {POINTS}곳, 다 찬 뒤 누르면 처음부터)")
    print("  2 : 일시정지 / 다시 시작")
    print("  3 : 종료")
    print("  4 : 위치 모두 지우기")
    print("  비상정지: 마우스를 화면 왼쪽 위 끝으로")
    print("=" * 50)
    print("\n첫 번째 클릭할 곳에 마우스를 올리고 1을 누르세요...")

    for vk in (VK_ADD, VK_PAUSE, VK_QUIT, VK_RESET):
        pressed(vk)  # 이전에 눌린 기록 지우기

    targets = []
    step = 0
    paused = False
    next_click = 0.0
    count = 0

    while True:
        if pressed(VK_QUIT):
            print("\n3: 종료합니다.")
            break
        if pressed(VK_RESET) and targets:
            targets, step = [], 0
            print("\n위치를 모두 지웠습니다. 1로 다시 지정하세요.")
        if pressed(VK_ADD):
            if len(targets) >= POINTS:
                targets = []
            targets.append(cursor())
            step = 0
            paused = False
            next_click = time.time() + gap()
            print(f"\n위치 {len(targets)}/{POINTS} 지정: {targets[-1]}")
        if pressed(VK_PAUSE) and targets:
            paused = not paused
            step = 0
            print("\n일시정지" if paused else "\n다시 시작")
            next_click = time.time() + gap()
        x, y = cursor()
        if x <= 2 and y <= 2 and targets:
            print("\n마우스가 왼쪽 위 모서리에 있어 비상 정지했습니다.")
            break

        if targets and not paused and time.time() >= next_click:
            step %= len(targets)
            pos = click(*targets[step])  # 지정 위치는 바뀌지 않고, 실제 클릭 위치만 흔들림
            count += 1
            step += 1
            if step < len(targets):
                next_click = time.time() + random.uniform(GAP_MIN, GAP_MAX)
            else:
                step = 0
                next_click = time.time() + gap()
            print(f"\r클릭 {count}회  위치 {(step or len(targets))}번 실제 {pos}  다음 클릭까지 {next_click - time.time():.1f}초   ", end="", flush=True)

        time.sleep(0.03)

    time.sleep(1.5)


if __name__ == "__main__":
    main()
