"""Linux X11 autoclicker. Background mode never moves the pointer.

F8 selects a target, F9 pauses/resumes, F10 exits. XSendEvent is not
accepted by every application. Native Wayland windows are unsupported.
"""
import argparse
import os
import random
import sys
import time

MIN_SEC, MAX_SEC = 4.0, 10.0
HOLD_MIN, HOLD_MAX = 0.05, 0.12
JITTER = 5


def jitter(x, y):
    return x + random.randint(-JITTER, JITTER), y + random.randint(-JITTER, JITTER)


def rising_keys(current, previous):
    return current - previous


def pick_target(root):
    window = root
    while True:
        pointer = window.query_pointer()
        if not pointer.child:
            return window, pointer.win_x, pointer.win_y
        window = pointer.child


def run(background):
    if not os.environ.get('DISPLAY'):
        raise RuntimeError('DISPLAY가 없습니다. 실제 Linux X11 데스크톱의 터미널에서 실행하세요. 현재 터미널이 GUI 세션에 연결되어 있지 않습니다.')
    if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        raise RuntimeError('네이티브 Wayland는 지원하지 않습니다. X11 세션에서 실행하세요.')
    try:
        from Xlib import X, XK, display, error
        from Xlib.protocol import event
        from Xlib.ext import xtest
    except ImportError as exc:
        raise RuntimeError('python-xlib가 필요합니다. ./setup_linux.sh 를 실행하세요.') from exc
    try:
        from x11_auth import wildcard_xauthority
        with wildcard_xauthority():
            connection = display.Display()
    except Exception as exc:
        raise RuntimeError(f'X11 화면에 연결할 수 없습니다: {exc}') from exc
    try:
        root = connection.screen().root
        if not background and not connection.has_extension('XTEST'):
            raise RuntimeError('일반 클릭 모드에는 XTEST 확장이 필요합니다.')
        keys = {name: connection.keysym_to_keycode(XK.string_to_keysym(name)) for name in ('F8', 'F9', 'F10')}
        if not all(keys.values()):
            raise RuntimeError('F8/F9/F10 키 매핑을 찾지 못했습니다.')

        def held():
            data = connection.query_keymap()
            return {name for name, code in keys.items() if data[code // 8] & (1 << (code % 8))}

        previous = held()
        target, paused, next_click, count = None, False, 0.0, 0
        print(f"Linux X11 {'백그라운드' if background else '일반'} 자동 클릭기", flush=True)
        print('F8: 위치 지정 / F9: 일시정지·재개 / F10 또는 Ctrl+C: 종료', flush=True)
        print('대상 선택 대기 중. 아직 클릭하지 않습니다.', flush=True)
        while True:
            current = held()
            pressed = rising_keys(current, previous)
            previous = current
            if 'F10' in pressed:
                break
            if 'F8' in pressed:
                if background:
                    target = pick_target(root)
                else:
                    pointer = root.query_pointer()
                    target = (root, pointer.root_x, pointer.root_y)
                paused = False
                next_click = time.monotonic() + random.uniform(MIN_SEC, MAX_SEC)
                print(f'대상 선택: 창 {target[0].id:#x}, 좌표 {target[1:]}', flush=True)
            if 'F9' in pressed and target:
                paused = not paused
                next_click = time.monotonic() + random.uniform(MIN_SEC, MAX_SEC)
                print('일시정지' if paused else '재개', flush=True)
            if not background and target:
                pointer = root.query_pointer()
                if pointer.root_x <= 2 and pointer.root_y <= 2:
                    print('왼쪽 위 모서리 비상정지', flush=True)
                    break
            if target and not paused and time.monotonic() >= next_click:
                window, x, y = target
                try:
                    if window.get_attributes().map_state != X.IsViewable:
                        next_click = time.monotonic() + random.uniform(MIN_SEC, MAX_SEC)
                        time.sleep(0.03)
                        continue
                    x, y = jitter(x, y)
                    if background:
                        translated = root.translate_coords(window, x, y)
                        fields = dict(time=X.CurrentTime, root=root, window=window,
                                      child=X.NONE, root_x=translated.x, root_y=translated.y,
                                      event_x=x, event_y=y, same_screen=1, detail=1)
                        window.send_event(event.ButtonPress(state=0, **fields), event_mask=X.ButtonPressMask)
                        connection.flush()
                        try:
                            time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))
                        finally:
                            window.send_event(event.ButtonRelease(state=X.Button1Mask, **fields), event_mask=X.ButtonReleaseMask)
                            connection.flush()
                    else:
                        pointer = root.query_pointer()
                        root.warp_pointer(x, y)
                        xtest.fake_input(connection, X.ButtonPress, 1)
                        connection.flush()
                        try:
                            time.sleep(random.uniform(HOLD_MIN, HOLD_MAX))
                        finally:
                            xtest.fake_input(connection, X.ButtonRelease, 1)
                            root.warp_pointer(pointer.root_x, pointer.root_y)
                            connection.flush()
                    connection.sync()
                    count += 1
                    print(f'클릭 이벤트 전송 {count}회: ({x}, {y})', flush=True)
                except error.XError:
                    target = None
                    print('대상 창을 사용할 수 없습니다. F8로 다시 선택하세요.', flush=True)
                next_click = time.monotonic() + random.uniform(MIN_SEC, MAX_SEC)
            time.sleep(0.03)
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--background', action='store_true', help='마우스 이동 없이 X11 창에 이벤트 전송')
    args = parser.parse_args()
    try:
        run(args.background)
    except KeyboardInterrupt:
        return 0
    except RuntimeError as exc:
        print(f'실행 불가: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
