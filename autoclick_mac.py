# macOS 자동 클릭기: 4~10초 무작위 간격으로 지정한 위치들을 순서대로 클릭 (추가 설치 필요 없음)
#   1 : 지금 마우스가 있는 위치를 클릭 위치로 추가 (최대 POINTS곳, 다 찬 뒤 누르면 처음부터)
#   2 : 일시정지 / 다시 시작
#   3 : 종료 (Ctrl+C 도 가능)
#   (키보드 위쪽 숫자열 키. 전역으로 감지하므로 다른 곳에서 타이핑해도 반응함)
#   비상 정지: 마우스를 화면 왼쪽 위 모서리로 밀어 넣기
# 처음 실행할 때 시스템 설정 > 개인정보 보호 및 보안 에서 터미널에
# '손쉬운 사용'과 '입력 모니터링' 권한을 줘야 클릭과 키 입력이 동작합니다.
import ctypes
import ctypes.util
import random
import sys
import time

MIN_SEC, MAX_SEC = 4.0, 10.0  # 주기 간격(초)
HOLD_MIN, HOLD_MAX = 0.05, 0.12  # 누르고 떼는 사이 무작위 시간(초)
JITTER = 5  # 클릭 위치 흔들림(픽셀)
POINTS = 3  # 클릭할 위치 개수
GAP_MIN, GAP_MAX = 0.3, 0.8  # 한 주기 안에서 위치 사이 간격(초)

# macOS 가상 키코드: 위쪽 숫자열 1, 2, 3
KEY_ADD, KEY_PAUSE, KEY_QUIT = 18, 19, 20
HID_STATE = 1  # kCGEventSourceStateHIDSystemState
HID_TAP = 0  # kCGHIDEventTap
LEFT_DOWN, LEFT_UP = 1, 2  # kCGEventLeftMouseDown / Up
LEFT_BUTTON = 0


class CGPoint(ctypes.Structure):
    _fields_ = [('x', ctypes.c_double), ('y', ctypes.c_double)]


def load():
    if sys.platform != 'darwin':
        raise RuntimeError('이 스크립트는 macOS 전용입니다.')
    cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
    cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))
    cg.CGEventCreate.restype = ctypes.c_void_p
    cg.CGEventCreate.argtypes = [ctypes.c_void_p]
    cg.CGEventGetLocation.restype = CGPoint
    cg.CGEventGetLocation.argtypes = [ctypes.c_void_p]
    cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
    cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
    cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
    cg.CGEventSourceKeyState.restype = ctypes.c_bool
    cg.CGEventSourceKeyState.argtypes = [ctypes.c_int32, ctypes.c_uint16]
    cg.CGWarpMouseCursorPosition.argtypes = [CGPoint]
    cg.AXIsProcessTrusted.restype = ctypes.c_bool
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    return cg, cf


def main():
    try:
        cg, cf = load()
    except (RuntimeError, OSError) as exc:
        print(f'실행 불가: {exc}', file=sys.stderr)
        return 1

    def cursor():
        ev = cg.CGEventCreate(None)
        p = cg.CGEventGetLocation(ev)
        cf.CFRelease(ev)
        return round(p.x), round(p.y)

    def held():
        return {key for key in (KEY_ADD, KEY_PAUSE, KEY_QUIT) if cg.CGEventSourceKeyState(HID_STATE, key)}

    def post(kind, x, y):
        ev = cg.CGEventCreateMouseEvent(None, kind, CGPoint(x, y), LEFT_BUTTON)
        cg.CGEventPost(HID_TAP, ev)
        cf.CFRelease(ev)

    def click(x, y):
        x += random.randint(-JITTER, JITTER)
        y += random.randint(-JITTER, JITTER)
        ox, oy = cursor()
        post(LEFT_DOWN, x, y)
        try:
            time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))
        finally:
            post(LEFT_UP, x, y)
            time.sleep(0.02)
            cg.CGWarpMouseCursorPosition(CGPoint(ox, oy))  # 마우스를 원래 자리로
        return x, y

    def gap():
        return random.uniform(MIN_SEC, MAX_SEC)

    print('=' * 50)
    print(f' macOS 자동 클릭기 ({POINTS}곳, 4~10초 무작위 간격)')
    print(f'  1 : 지금 마우스 위치를 클릭 위치로 추가 (최대 {POINTS}곳, 다 찬 뒤 누르면 처음부터)')
    print('  2 : 일시정지 / 다시 시작')
    print('  3 또는 Ctrl+C : 종료')
    print('  비상정지: 마우스를 화면 왼쪽 위 끝으로')
    print('=' * 50)
    if not cg.AXIsProcessTrusted():
        print('\n주의: 손쉬운 사용 권한이 없어 클릭이 무시될 수 있습니다.')
        print('시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 에서 터미널을 켜고 다시 실행하세요.')
    print('\n첫 번째 클릭할 곳에 마우스를 올리고 1을 누르세요...', flush=True)

    previous = held()
    targets, step, paused, next_click, count = [], 0, False, 0.0, 0
    try:
        while True:
            current = held()
            pressed = current - previous
            previous = current
            if KEY_QUIT in pressed:
                print('\n3: 종료합니다.')
                break
            if KEY_ADD in pressed:
                if len(targets) >= POINTS:
                    targets = []
                targets.append(cursor())
                step, paused = 0, False
                next_click = time.monotonic() + gap()
                print(f'\n위치 {len(targets)}/{POINTS} 지정: {targets[-1]}', flush=True)
            if KEY_PAUSE in pressed and targets:
                paused, step = not paused, 0
                next_click = time.monotonic() + gap()
                print('\n일시정지' if paused else '\n다시 시작', flush=True)
            x, y = cursor()
            if targets and x <= 2 and y <= 2:
                print('\n마우스가 왼쪽 위 모서리에 있어 비상 정지했습니다.')
                break
            if targets and not paused and time.monotonic() >= next_click:
                step %= len(targets)
                pos = click(*targets[step])
                count += 1
                print(f'\r클릭 {count}회  위치 {step + 1}번 실제 {pos}   ', end='', flush=True)
                step += 1
                if step < len(targets):
                    next_click = time.monotonic() + random.uniform(GAP_MIN, GAP_MAX)
                else:
                    step = 0
                    next_click = time.monotonic() + gap()
            time.sleep(0.03)
    except KeyboardInterrupt:
        print('\n종료합니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
