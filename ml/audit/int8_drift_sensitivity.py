import numpy as np, json
d=np.load("ml/models/s0/extracted_embeddings_512.npz")
keys=list(d.keys())
print("n cached embeddings:",len(keys))
m=json.load(open("ml/dataset/dataset_manifest.json"))
# map local_path -> place
p2c={}
for pid,p in m["pois"].items():
    for r in p["records"]: p2c[r["local_path"]]=(pid,r["split"])
n2c={}
for nid,p in m["negatives"].items():
    for r in p["records"]: n2c[r["local_path"]]=(nid,r["split"])
emb={k:d[k] for k in keys}
known=[k for k in keys if k in p2c]; negs=[k for k in keys if k in n2c]
print("known cached:",len(known),"neg cached:",len(negs))
# frozen per-place centroids from ref+calib only (mimic training)
cent={}
for pid in set(p2c[k][0] for k in known):
    vs=[emb[k] for k in known if p2c[k][0]==pid and p2c[k][1] in ("ref","calib")]
    v=np.mean(vs,axis=0); cent[pid]=v/np.linalg.norm(v)
# query = test known
sims=[]
for k in known:
    if p2c[k][1]!="test": continue
    pid=p2c[k][0]
    s=float(emb[k]@cent[pid]); sims.append((s,pid))
sims.sort()
print()
print("FROZEN MobileCLIP-S0 (no adapter), test known -> own-centroid cosine:")
arr=np.array([s for s,_ in sims])
print("  n=",len(arr)," min",round(arr.min(),4)," p10",round(np.percentile(arr,10),4)," median",round(np.median(arr),4)," max",round(arr.max(),4))
print("  below 0.72:", int((arr<0.72).sum()), " below 0.60:", int((arr<0.60).sum()))
# perturbation bound from measured cross-backend cosine drift
cb=0.9888574728447277
beta=np.degrees(np.arccos(cb)); print()
print("measured encoder cross-backend cosine %.4f -> direction drift %.2f deg" % (cb,beta))
alpha=np.arccos(np.clip(arr, -1, 1))
lo=np.cos(alpha+np.radians(beta)); hi=np.cos(np.maximum(alpha-np.radians(beta),0))
print("  worst-case query->centroid similarity band: [%.4f .. %.4f] (span %.4f)" % (lo.min(), hi.max(), (hi-lo).max()))
print("  decision margins used by the app: siblingMargin=0.04, hardNegativeMargin=0.06, threshold=0.72")
print("  queries whose score could fall below threshold 0.72 under drift: %d of %d" % (int((lo<0.72).sum()), len(lo)))
print("  queries whose score could cross the 0.72 threshold in EITHER direction: %d" % int(((lo<0.72)&(hi>=0.72)).sum()))
