"""#64 身份头对齐官方 + 风控计数。

    python tests/_test_risk_identity.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _suite_head import *          # noqa: F401,F403

P, A = bootstrap()
declare_suite(__file__, ["qoder_sign.py", "qoder_proxy.py"])
import qoder_sign as S             # noqa: E402


def _hdr(uid, sse=True):
    sess = S.CosySession(uid)
    return sess.headers("{}", "https://api3.qoder.sh/algo/x", sse=sse)


# ---- 官方 infer-sse 头：machineos / machinehostname
_h1 = _hdr("uid-a")
check("#64 推理头含 cosy-machineos", "cosy-machineos" in _h1, list(_h1))
check("#64 推理头含 cosy-machinehostname", "cosy-machinehostname" in _h1, list(_h1))
check("#64 主机名形如 DESKTOP-XXXXXXX",
      str(_h1.get("cosy-machinehostname", "")).startswith("DESKTOP-")
      and len(_h1["cosy-machinehostname"]) == 15, _h1.get("cosy-machinehostname"))
_h1b = _hdr("uid-a")
check("#64 同一账号主机名稳定",
      _h1["cosy-machinehostname"] == _h1b["cosy-machinehostname"])
_h2 = _hdr("uid-b")
check("#64 不同账号主机名不同（避免多号关联）",
      _h1["cosy-machinehostname"] != _h2["cosy-machinehostname"],
      (_h1["cosy-machinehostname"], _h2["cosy-machinehostname"]))
check("#64 非 sse 请求不带 infer-sse 专属头",
      "cosy-machinehostname" not in _hdr("uid-a", sse=False))

os.environ["QD_COSY_OS_HEADERS"] = "0"
try:
    _h3 = _hdr("uid-a")
finally:
    os.environ.pop("QD_COSY_OS_HEADERS", None)
check("#64 开关可关闭（QD_COSY_OS_HEADERS=0）",
      "cosy-machineos" not in _h3 and "cosy-machinehostname" not in _h3)

# ---- 风控计数
_before = P.risk_snapshot()
P.note_risk("queue", "10605 test")
P.note_risk("rate", "429 test")
_snap = P.risk_snapshot()
check("#64 risk 计数累加（queue/rate）",
      _snap["queue"] == _before["queue"] + 1
      and _snap["rate"] == _before["rate"] + 1, _snap)
check("#64 risk 记录最近一次信号（kind/at/detail）",
      isinstance(_snap.get("last"), dict)
      and _snap["last"].get("kind") == "rate"
      and _snap["last"].get("at"), _snap.get("last"))
_src = open(os.path.join(ROOT, "qoder_proxy.py"), encoding="utf-8").read()
check("#64 /health 暴露 risk 快照", '"risk": risk_snapshot()' in _src)

finish()
