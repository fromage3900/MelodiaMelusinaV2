from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:29229")
    ctx = b.contexts[0] if b.contexts else b.new_context()
    pg = ctx.new_page()
    pg.set_viewport_size({"width":1360,"height":1000})
    pg.goto("file:///home/ubuntu/melodia-design-system/variations.html")
    pg.wait_for_timeout(3800)
    pg.screenshot(path="melodia-variations.png", full_page=True)
    print("saved")
    pg.close()
