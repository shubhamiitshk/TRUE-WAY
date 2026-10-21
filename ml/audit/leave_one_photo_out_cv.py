"""CORRECTED leave-one-photograph-out CV for TrueWay vision, with a
threshold sweep so we can recommend an honestly-calibrated operating point.

Protocol: for rotation r in {0,1,2}: every class holds out its r-th source
photograph; train = all remaining photographs; test = held-out photographs of
ALL classes. Negatives likewise hold out 1 of their 5 photographs per rotation
(sampled so each negative photograph is held out exactly once across the 3
rotations -> 5 rotations-worth of coverage over 5 photos; we use 5 rotations).
"""
import json, math, time
from collections import defaultdict
import numpy as np
import torch
import torch.nn.functional as F

ROOT = r"C:\Users\PLEXTEK\Desktop\TRUE-WAY"
import importlib.util
_s = importlib.util.spec_from_file_location("tap", ROOT + r"\ml\train_arcface_pipeline.py")
tap = importlib.util.module_from_spec(_s); _s.loader.exec_module(tap)

ABS_T, HARD_MARGIN, SIB_MARGIN = 0.72, 0.06, 0.04
DEN = 127.0 * 127.0

emb_npz = np.load(ROOT + r"\ml\models\s0\extracted_embeddings_512.npz")
manifest = json.load(open(ROOT + r"\ml\dataset\dataset_manifest.json", encoding="utf-8"))
emb = {k: emb_npz[k] for k in emb_npz.files}
recs = []
for pid, p in manifest["pois"].items():
    for r in p["records"]:
        recs.append(("known", pid, r["split"], r["original_url"], r["local_path"]))
for nid, p in manifest["negatives"].items():
    for r in p["records"]:
        recs.append(("neg", nid, r["split"], r["original_url"], r["local_path"]))
poi_ids = list(manifest["pois"].keys()); neg_cats = list(manifest["negatives"].keys())
p2i = {p: i for i, p in enumerate(poi_ids)}; n2i = {c: i for i, c in enumerate(neg_cats)}

kphotos = defaultdict(list); nphotos = defaultdict(list)
seen = set()
for kind, cls, sp, photo, path in recs:
    key = (kind, cls, photo)
    if key in seen: continue
    seen.add(key)
    (kphotos if kind == "known" else nphotos)[cls].append((photo, [p for p in by_path[key]] if False else []))
# rebuild path lists
paths_by_photo = defaultdict(list)
for kind, cls, sp, photo, path in recs:
    paths_by_photo[(kind, cls, photo)].append(path)
kphotos = defaultdict(list); nphotos = defaultdict(list)
for (kind, cls, photo), ps in paths_by_photo.items():
    (kphotos if kind == "known" else nphotos)[cls].append((photo, ps))
for d in (kphotos, nphotos):
    for k in d: d[k].sort(key=lambda x: x[0])

def q8(v):
    n = float(np.linalg.norm(v)) or 1.0
    return np.clip(np.round((v / n) * 127.0), -127, 127).astype(np.int32)

def cp_upper(k, n, alpha=0.05):
    if n <= 0: return 1.0
    if k >= n: return 1.0
    if k == 0: return 1 - alpha ** (1.0 / n)
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = .5 * (lo + hi)
        cdf = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(k + 1))
        if cdf > alpha: lo = mid
        else: hi = mid
    return .5 * (lo + hi)

def train_stack(known_tr, neg_tr, epochs=180, lr=0.008, seed=42):
    torch.manual_seed(seed); np.random.seed(seed)
    X = torch.from_numpy(np.stack([e for e, _ in known_tr]))
    Y = torch.tensor([c for _, c in known_tr], dtype=torch.long)
    Xn = torch.from_numpy(np.stack([e for e, _ in neg_tr]))
    Yn = torch.tensor([c for _, c in neg_tr], dtype=torch.long)
    ad = tap.LinearResidualAdapter(dim=512, alpha_init=0.35)
    arc = tap.SubCenterArcFace(num_classes=len(poi_ids), num_neg_categories=len(neg_cats),
                               dim=512, k_subcenters=3, s=24.0, m=0.25)
    with torch.no_grad():
        arc.init_from_data(ad(X), Y, ad(Xn), Yn)
    opt = torch.optim.AdamW(list(ad.parameters()) + list(arc.parameters()), lr=lr, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs, eta_min=1e-4)
    for _ in range(epochs):
        ad.train(); arc.train(); opt.zero_grad()
        zp = ad(F.normalize(X + torch.randn_like(X) * 0.015, p=2, dim=-1))
        zn = ad(F.normalize(Xn + torch.randn_like(Xn) * 0.015, p=2, dim=-1))
        (arc.forward_loss(zp, Y, zn, Yn) + ad.reg_loss()).backward()
        opt.step(); sch.step()
    ad.eval(); arc.eval()
    with torch.no_grad():
        w = F.normalize(arc.weights, p=2, dim=-1).numpy()
        u = F.normalize(arc.neg_prototypes, p=2, dim=-1).numpy()
        ztr = ad(X).detach().numpy(); ztrn = ad(Xn).detach().numpy()
        prim = np.zeros((len(poi_ids), 512), np.float32)
        for c in range(len(poi_ids)):
            m = Y.numpy() == c
            v = 0.6 * ztr[m].mean(axis=0) + 0.4 * w[c, 0]
            prim[c] = v / (np.linalg.norm(v) + 1e-8)
        negc = np.zeros((len(neg_cats), 512), np.float32)
        for n in range(len(neg_cats)):
            m = Yn.numpy() == n
            v = 0.5 * ztrn[m].mean(axis=0) + 0.5 * u[n]
            negc[n] = v / (np.linalg.norm(v) + 1e-8)
    return ad, prim, w, negc

def eval_fold(prim, w, negc, kte, nte):
    PQ = np.stack([q8(prim[c]) for c in range(len(poi_ids))])
    SQ = np.stack([[q8(w[c, k]) for k in range(3)] for c in range(len(poi_ids))])
    NQ = np.stack([q8(negc[n]) for n in range(len(neg_cats))])
    def one(z):
        q = q8(z)
        sp = np.maximum((PQ @ q) / DEN, np.max((SQ @ q) / DEN, axis=1))
        sn = float(np.max((NQ @ q) / DEN))
        o = np.argsort(-sp)
        return float(sp[o[0]]), float(sp[o[1]]), sn, poi_ids[int(o[0])], [poi_ids[int(i)] for i in o[:3]]
    K = []; N = []
    for cls, z in kte:
        s1, s2, sn, pred, t3 = one(z)
        K.append(dict(cls=cls, s1=s1, s2=s2, sn=sn, pred=pred, t3=t3))
    for cls, z in nte:
        s1, s2, sn, pred, t3 = one(z)
        N.append(dict(cls=cls, s1=s1, s2=s2, sn=sn, pred=pred, t3=t3))
    return K, N

print("=" * 78)
print("LEAVE-ONE-PHOTOGRAPH-OUT CV  (corrected: all classes held out per rotation)")
print("=" * 78)
allK = []; allN = []
ROT = 5
for rot in range(ROT):
    ktr = []; kte = []
    for cls, pl in kphotos.items():
        hold = pl[rot % len(pl)][0]
        for photo, ps in pl:
            for p in ps:
                (kte if photo == hold else ktr).append((emb[p], p2i[cls]) if photo != hold else (cls, emb[p]))
    ktr = [(e, c) for e, c in ktr]; kte = [(c, e) for c, e in kte]
    ntr = []; nte = []
    for cls, pl in nphotos.items():
        hold = pl[(rot + 1) % len(pl)][0]
        for photo, ps in pl:
            for p in ps:
                if photo == hold: nte.append((cls, emb[p]))
                else: ntr.append((emb[p], n2i[cls]))
    ad, prim, w, negc = train_stack(ktr, ntr)
    with torch.no_grad():
        kte_z = [(c, ad(torch.from_numpy(z)).detach().numpy()) for c, z in kte]
        nte_z = [(c, ad(torch.from_numpy(z)).detach().numpy()) for c, z in nte]
    K, N = eval_fold(prim, w, negc, kte_z, nte_z)
    allK += K; allN += N
    t1 = sum(1 for r in K if r["pred"] == r["cls"])
    print(f"  rotation {rot+1}/{ROT}: known test {len(K)} (from "
          f"{len({r['cls'] for r in K})} classes) top1={t1}/{len(K)}  neg test {len(N)}")

nk, nn = len(allK), len(allN)
top1 = sum(1 for r in allK if r["pred"] == r["cls"])
top3 = sum(1 for r in allK if r["cls"] in r["t3"])

def gate(r, thr, hard=SIB_MARGIN):
    if (r["s1"] - r["sn"]) < HARD_MARGIN: return False
    if r["s1"] < thr: return False
    if (r["s1"] - r["s2"]) < SIB_MARGIN: return False
    return True

print()
print(f"POOLED out-of-fold: known={nk}  unknown={nn}")
print(f"  Top-1 (raw)            {top1}/{nk} = {100*top1/nk:.1f}%")
print(f"  Top-3 (raw)            {top3}/{nk} = {100*top3/nk:.1f}%")
print()
print("  threshold sweep (absolute threshold; hard-negative & sibling gates fixed):")
print("   thr    coverage(known acc)  abst_known   FAR        CP95@N_eff")
# effective independent counts
eff_k = len({(r["cls"]) for r in allK})  # placeholder, real count below
eff_neg_photos = len(nphotos) * ROT
for thr in (0.50, 0.55, 0.60, 0.62, 0.65, 0.68, 0.70, 0.72, 0.75, 0.78, 0.80, 0.85):
    accK = [r for r in allK if gate(r, thr)]
    cov = len(accK) / nk
    prec = sum(1 for r in accK if r["pred"] == r["cls"]) / max(1, len(accK))
    abst = 1 - cov
    fa = sum(1 for r in allN if gate(r, thr))
    far = fa / nn
    print(f"   {thr:.2f}   {100*cov:5.1f}%  ({sum(1 for r in accK if r['pred']==r['cls'])}/{len(accK)} correct)"
          f"   {100*abst:5.1f}%   {100*far:5.2f}%   {100*cp_upper(fa, eff_neg_photos):6.2f}%"
          f"   prec={100*prec:.1f}%")

ks = np.array([r["s1"] for r in allK]); ns = np.array([r["s1"] for r in allN])
print()
print(f"  known   score: min={ks.min():.3f} p10={np.percentile(ks,10):.3f} med={np.median(ks):.3f} max={ks.max():.3f}")
print(f"  unknown score: min={ns.min():.3f} p10={np.percentile(ns,10):.3f} med={np.median(ns):.3f} max={ns.max():.3f}")
print(f"  OVERLAP: known p10={np.percentile(ks,10):.3f}  vs  unknown med={np.median(ns):.3f}")
print()
print("  per-class top-1 (out-of-fold):")
from collections import defaultdict as dd
pc = dd(lambda: [0, 0])
for r in allK:
    pc[r["cls"]][1] += 1
    if r["pred"] == r["cls"]: pc[r["cls"]][0] += 1
for c, (h, n) in sorted(pc.items(), key=lambda x: x[1][0] / max(1, x[1][1])):
    print(f"    {c:45s} {h}/{n}")
print()
print("  false accepts by predicted place:")
fa_pred = dd(int)
for r in allN:
    if gate(r, 0.72): fa_pred[r["pred"]] += 1
for c, v in sorted(fa_pred.items(), key=lambda x: -x[1]):
    print(f"    {c:45s} {v}")
print()
print(f"  effective independent negative photographs across all rotations: {eff_neg_photos}")
print(f"  CP95 upper bound at that N with 0 errors: {100*cp_upper(0, eff_neg_photos):.2f}%")
