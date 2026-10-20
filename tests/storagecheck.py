"""v39.3: the "Saved in this browser" chip tells the truth about storage, and the online build never mentions file://.

run(b, base, check, label)   probe works / throws, 0 marks vs marks, unreadable saved data is not "blocked", a one-off failure and a stuck 'blocked' that recovers, a file dropped on the page
nofile(check, dirs)          the online build folders contain no file:// (tools/art_guard.py no_file_urls), and the check does find one
Used by tests/run_all.py."""
import sys, tempfile
from pathlib import Path
import qscheck as Q

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import art_guard

CHIP = "document.getElementById('qsChip').textContent"
MENU = "(()=>{document.getElementById('qsChip').click();return document.getElementById('qsMenu').textContent})()"
FAIL_ALL = "(()=>{const o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(window.__fail)throw new DOMException('no','QuotaExceededError');return o.call(this,k,v)};window.__fail=true})()"
FAIL_ONCE = "(()=>{const o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='w3p.quests.v1'&&!window.__done){window.__done=true;throw new DOMException('no','QuotaExceededError')}return o.call(this,k,v)}})()"


def mark(pg):
    pg.click("#qsVList"); pg.click(".qsrow >> nth=0"); pg.click('.qsmark[data-s="active"]'); pg.wait_for_timeout(150)


def run(b, base, check, label):
    pg, errs, _ = Q.newpage(b, base); E = pg.evaluate; Q.opened(pg)
    c0, m0 = E(CHIP), E(MENU); pg.keyboard.press("Escape")
    check("%s: storage works and nothing is marked: the button says 'No progress yet', not 'Not saved' (%s)" % (label, c0), c0 == "No progress yet ▾" and "blocks storage" not in m0 and E("QS.ok") is True and E("localStorage.getItem('w3p.quests.v1.probe')") is None, [c0, m0[:80]])
    mark(pg); c1 = E(CHIP)
    check("%s: after a mark it says 'Saved in this browser' (%s) and the probe key is not left behind" % (label, c1), c1 == "Saved in this browser ▾" and E("localStorage.getItem('w3p.quests.v1.probe')") is None and E("localStorage.getItem('w3p.quests.v1')") is not None)
    pg.close()
    # storage that really throws
    pg, errs, _ = Q.newpage(b, base, init=FAIL_ALL); E = pg.evaluate; Q.opened(pg); c = E(CHIP); m = E(MENU)
    check("%s: a probe that throws is blocked: 'Not saved in this browser' and the warning text (%s)" % (label, c), c == "Not saved in this browser ▾" and "This browser blocks storage for the site" in m and E("QS.ok") is False, [c, m[:120]])
    mark(pg); c2 = E(CHIP)
    check("%s: blocked storage: the screen still works for the visit (mark kept in memory) and the wording stays (%s)" % (label, c2), E("Object.keys(QS.store.manual).length") == 1 and c2 == "Not saved in this browser ▾")
    E("window.__fail=false"); pg.click("#qsChip"); pg.click("#qsChip"); pg.wait_for_timeout(100); pg.keyboard.press("Escape"); mark2 = E("(()=>{qsMark(QS.byG.get(Object.keys(QS.store.manual)[0]).g,'done');return document.getElementById('qsChip').textContent})()")
    check("%s: a 'blocked' that was only a failure at that moment recovers: the next save works and the button is back to 'Saved in this browser' (%s)" % (label, mark2), mark2 == "Saved in this browser ▾" and E("QS.ok") is True and "blocks storage" not in E(MENU), mark2)
    pg.close()
    # a one-off failure of the real save (full quota, a hiccup) while storage works
    pg, errs, _ = Q.newpage(b, base, init=FAIL_ONCE); E = pg.evaluate; Q.opened(pg); mark(pg); c = E(CHIP)
    check("%s: one failed save does not make the storage 'blocked' (the probe still works): %s, no warning" % (label, c), c != "Not saved in this browser ▾" and E("QS.ok") is True and "blocks storage" not in E(MENU), c)
    pg.keyboard.press("Escape"); E("qsMark(Object.keys(QS.store.manual)[0],'done')"); pg.wait_for_timeout(100)
    check("%s: the next save is stored (%s)" % (label, E("localStorage.getItem('w3p.quests.v1')")[:40]), '"done"' in E("localStorage.getItem('w3p.quests.v1')") and E(CHIP) == "Saved in this browser ▾")
    pg.close()
    # saved data that cannot be read is not a storage problem
    pg, errs, _ = Q.newpage(b, base, init="localStorage.setItem('w3p.quests.v1','{not json')"); E = pg.evaluate; Q.opened(pg); c = E(CHIP); m = E(MENU)
    check("%s: unreadable saved progress (not JSON) is not 'blocked': %s, no blocked warning, a line says it could not be read (%s)" % (label, c, m[:60]), c == "No progress yet ▾" and "blocks storage" not in m and "could not be read" in m and E("QS.ok") is True, [c, m[:200]])
    pg.keyboard.press("Escape"); mark(pg)
    check("%s: the next mark replaces it with valid progress" % label, E("(()=>{try{return JSON.parse(localStorage.getItem('w3p.quests.v1')).v}catch(e){return null}})()") == 1 and E(CHIP) == "Saved in this browser ▾")
    pg.close()
    # a file dropped on the page must not make the browser open it (Firefox: "may not load or link to file:///")
    pg, errs, _ = Q.newpage(b, base); E = pg.evaluate
    d = E("""(()=>{const f=t=>{const dt=new DataTransfer();dt.items.add(new File(['x'],'a.json'));const e=new DragEvent(t,{dataTransfer:dt,bubbles:true,cancelable:true});document.body.dispatchEvent(e);return e.defaultPrevented},
      tx=new DataTransfer();tx.setData('text/plain','hi');const e2=new DragEvent('drop',{dataTransfer:tx,bubbles:true,cancelable:true});document.body.dispatchEvent(e2);return[f('dragover'),f('drop'),e2.defaultPrevented,document.getElementById('toastMsg').textContent.slice(0,40)]})()""")
    check("%s: a file dropped on the page is stopped (dragover and drop prevented, a notice says where files go); a text drag is left alone (%s)" % (label, d), d[0] is True and d[1] is True and d[2] is False and d[3].startswith("Files are not opened here"), d)
    pg.close()


def nofile(check, dirs):
    for name, d in dirs:
        check("the online build (%s) contains no file:// in any text file" % name, art_guard.no_file_urls(d) == [], art_guard.no_file_urls(d)[:2])
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); (t / "a").mkdir(); (t / "a" / "x.js").write_text("const u='file:///etc/passwd'"); (t / "ok.html").write_text("<p>hi</p>"); (t / "img.png").write_bytes(b"file://")
        check("the file:// check finds one in a script and ignores a picture (%s)" % art_guard.no_file_urls(t), art_guard.no_file_urls(t) == ["a/x.js contains file://"])
