# 백그라운드 자동 클릭기: 마우스 커서를 움직이지 않고 창에 직접 클릭 신호를 보냄
# 켜 놓은 동안에도 마우스를 자유롭게 쓸 수 있음 (추가 설치 필요 없음)
#   F8  : 지금 마우스가 있는 위치(그 창)를 클릭 위치로 지정 (다시 누르면 위치 변경)
#   F9  : 일시정지 / 다시 시작
#   F10 : 종료
# 주의: 클릭할 창을 최소화하면 안 됨 (다른 창 뒤에 가려지는 건 대부분 괜찮음)
#       창을 옮기거나 크기를 바꾸면 F8로 위치를 다시 지정하세요.
#       일부 프로그램/게임은 이 방식의 클릭을 무시할 수 있음 -> 그때는 autoclick.py 사용
import ctypes
import random
import time
from ctypes import wintypes

MIN_SEC, MAX_SEC = 4.0, 10.0  # 클릭할 때마다 이 범위에서 무작위 간격(초)
HOLD_MIN, HOLD_MAX = 0.05, 0.12  # 누르고 떼는 사이 무작위 시간(초)
JITTER = 5  # 클릭 위치를 지정 좌표에서 x, y 각각 최대 이만큼(픽셀) 무작위로 흔들기

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]

VK_F8, VK_F9, VK_F10 = 0x77, 0x78, 0x79
WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
MK_LBUTTON = 0x0001
GA_ROOT = 2


def gap():
    return random.uniform(MIN_SEC, MAX_SEC)


def cursor():
    p = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p


def pressed(vk):
    # 마지막 확인 이후 눌린 적이 있으면 True
    return bool(user32.GetAsyncKeyState(vk) & 0x0001)


def title(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(user32.GetAncestor(hwnd, GA_ROOT), buf, 256)
    return buf.value or "(제목 없음)"


def pick_target():
    # 커서 아래 창과, 그 창 안에서의 좌표를 기억
    p = cursor()
    hwnd = user32.WindowFromPoint(p)
    cp = wintypes.POINT(p.x, p.y)
    user32.ScreenToClient(hwnd, ctypes.byref(cp))
    return hwnd, cp.x, cp.y


def lparam(x, y):
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def click(hwnd, x, y):
    # 항상 지정 좌표를 기준으로 흔들기 때문에 누적되지 않고 ±JITTER 범위를 벗어나지 않음
    x += random.randint(-JITTER, JITTER)
    y += random.randint(-JITTER, JITTER)
    lp = lparam(x, y)
    user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.02)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))  # 사람처럼 잠깐 누르고 있기
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    return x, y


def main():
    print("=" * 50)
    print(" 백그라운드 자동 클릭기 (4~10초 무작위 간격)")
    print("  마우스는 자유롭게 쓰셔도 됩니다")
    print("  F8  : 지금 마우스 위치를 클릭 위치로 지정/변경")
    print("  F9  : 일시정지 / 다시 시작")
    print("  F10 : 종료")
    print("  클릭할 창은 최소화하지 마세요")
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
            target = pick_target()
            paused = False
            next_click = time.time() + gap()
            print(f"\n클릭 위치 지정: [{title(target[0])}] 창 안 좌표 ({target[1]}, {target[2]})"
                  "  -> 4~10초 무작위 간격으로 클릭 시작")
        if pressed(VK_F9) and target:
            paused = not paused
            print("\n일시정지" if paused else "\n다시 시작")
            next_click = time.time() + gap()

        if target and not user32.IsWindow(target[0]):
            print("\n클릭하던 창이 닫혔습니다. F8로 위치를 다시 지정하세요.")
            target = None

        if target and not paused and time.time() >= next_click:
            if user32.IsIconic(user32.GetAncestor(target[0], GA_ROOT)):
                print("\r창이 최소화되어 있어 이번 클릭은 건너뜁니다.                    ", end="", flush=True)
            else:
                pos = click(*target)
                count += 1
                print(f"\r클릭 {count}회  창 안 실제 위치 {pos}  ", end="", flush=True)
            next_click = time.time() + gap()
            print(f"다음 클릭까지 {next_click - time.time():.1f}초   ", end="", flush=True)

        time.sleep(0.03)

    time.sleep(1.5)


if __name__ == "__main__":
    main()
