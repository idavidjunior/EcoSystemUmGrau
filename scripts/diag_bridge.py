import webview, sys, time

class Bridge:
    def ping(self):
        return 'pong'

def main():
    b = Bridge()
    win = webview.create_window('diag-bridge', url='about:blank',
                                js_api=b, width=400, height=200,
                                frameless=True, focus=False, shadow=False)

    def run_check():
        time.sleep(3)
        try:
            r = win.evaluate_js("window.pywebview && window.pywebview.api ? window.pywebview.api.ping() : 'NO_API'")
            print('RESULT:', r)
            time.sleep(1)
            win.destroy()
        except Exception as e:
            print('ERRO:', type(e).__name__, e)
            try:
                win.destroy()
            except Exception:
                pass
        print('FIM')

    webview.start(func=run_check)

if __name__ == '__main__':
    main()
