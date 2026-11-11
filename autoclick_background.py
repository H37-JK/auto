# 백그라운드 자동 클릭기: 마우스 커서를 움직이지 않고 창에 직접 클릭 신호를 보냄
# 켜 놓은 동안에도 마우스를 자유롭게 쓸 수 있음 (추가 설치 필요 없음)
#   1 : 지금 마우스가 있는 위치(그 창)를 클릭 위치로 추가 (최대 POINTS곳, 다 찬 뒤 누르면 처음부터)
#   2 : 일시정지 / 다시 시작
#   3 : 종료
#   (키보드 위쪽 숫자열 키. 전역으로 감지하므로 다른 곳에서 타이핑해도 반응함)
# 주의: 클릭할 창을 최소화하면 안 됨 (다른 창 뒤에 가려지는 건 대부분 괜찮음)
#       창을 옮기거나 크기를 바꾸면 1로 위치를 다시 지정하세요.
#       일부 프로그램/게임은 이 방식의 클릭을 무시할 수 있음 -> 그때는 autoclick.py 사용
import ctypes
import random
import time
from ctypes import wintypes

MIN_SEC, MAX_SEC = 4.0, 10.0  # 클릭할 때마다 이 범위에서 무작위 간격(초)
HOLD_MIN, HOLD_MAX = 0.05, 0.12  # 누르고 떼는 사이 무작위 시간(초)
JITTER = 5  # 클릭 위치를 지정 좌표에서 x, y 각각 최대 이만큼(픽셀) 무작위로 흔들기
POINTS = 3  # 클릭할 위치 개수
GAP_MIN, GAP_MAX = 0.3, 0.8  # 한 주기 안에서 위치 사이 간격(초)

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

VK_ADD, VK_PAUSE, VK_QUIT = 0x31, 0x32, 0x33  # 숫자 1, 2, 3
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
    print(f" 백그라운드 자동 클릭기 ({POINTS}곳, 4~10초 무작위 간격)")
    print("  마우스는 자유롭게 쓰셔도 됩니다")
    print(f"  1 : 지금 마우스 위치를 클릭 위치로 추가 (최대 {POINTS}곳, 다 찬 뒤 누르면 처음부터)")
    print("  2 : 일시정지 / 다시 시작")
    print("  3 : 종료")
    print("  클릭할 창은 최소화하지 마세요")
    print("=" * 50)
    print("\n첫 번째 클릭할 곳에 마우스를 올리고 1을 누르세요...")

    for vk in (VK_ADD, VK_PAUSE, VK_QUIT):
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
        if pressed(VK_ADD):
            if len(targets) >= POINTS:
                targets = []
            target = pick_target()
            targets.append(target)
            step = 0
            paused = False
            next_click = time.time() + gap()
            print(f"\n위치 {len(targets)}/{POINTS} 지정: [{title(target[0])}] 창 안 좌표 ({target[1]}, {target[2]})")
        if pressed(VK_PAUSE) and targets:
            paused = not paused
            step = 0
            print("\n일시정지" if paused else "\n다시 시작")
            next_click = time.time() + gap()

        if targets and not all(user32.IsWindow(t[0]) for t in targets):
            print("\n클릭하던 창이 닫혔습니다. 1로 위치를 다시 지정하세요.")
            targets, step = [], 0

        if targets and not paused and time.time() >= next_click:
            step %= len(targets)
            target = targets[step]
            if user32.IsIconic(user32.GetAncestor(target[0], GA_ROOT)):
                print(f"\r창이 최소화되어 있어 위치 {step + 1}번 클릭은 건너뜁니다.          ", end="", flush=True)
            else:
                pos = click(*target)
                count += 1
                print(f"\r클릭 {count}회  위치 {step + 1}번 창 안 실제 {pos}  ", end="", flush=True)
            step += 1
            if step < len(targets):
                next_click = time.time() + random.uniform(GAP_MIN, GAP_MAX)
            else:
                step = 0
                next_click = time.time() + gap()
            print(f"다음 클릭까지 {next_click - time.time():.1f}초   ", end="", flush=True)

        time.sleep(0.03)

    time.sleep(1.5)


if __name__ == "__main__":
    main()
