import json, os, sys
from mapping import *
W = json.load(open(os.path.expanduser("~/Skills/_research/mc-agua-edit/tl_words.json"), encoding="utf8"))
for w in W:
    w.append(old2new(w[0] + 0.01))


def around_new(t, before=2.5, after=2.5):
    return " ".join(("[%s]" % w[3] if w[0] and abs(w[4] - t) < 0.15 else w[3]) for w in W if w[4] is not None and t - before <= w[4] <= t + after)


def around_old(t, before=2.5, after=2.5):
    return " ".join(w[3] for w in W if t - before <= w[0] <= t + after)


def removed_words(a_old, b_old):
    return " ".join("%s:%s" % (w[2], w[3]) for w in W if a_old - 0.02 <= w[0] and w[1] <= b_old + 0.05 or (w[0] < b_old and w[1] > a_old and min(w[1], b_old) - max(w[0], a_old) > 0.5 * (w[1] - w[0])))


if __name__ == "__main__":
    for a in sys.argv[1:]:
        t = float(a.split(":")[0]) * 60 + float(a.split(":")[1]) if ":" in a else float(a)
        print(tc(t), "|", around_new(t))
