import json, numpy as np
from collections import defaultdict
d=np.load("ml/models/s0/extracted_embeddings_512.npz")
m=json.load(open("ml/dataset/dataset_manifest.json"))
paths=defaultdict(list)
for kind in ("pois","negatives"):
    for cid,p in m[kind].items():
        for r in p["records"]:
            paths[(kind,cid,r["original_url"])].append(r["local_path"])
def c(a,b): return float(d[a]@d[b])
intra_within=[]; intra_across=[]
for (kind,cid,photo),ps in paths.items():
    for i in range(len(ps)):
        for j in range(i+1,len(ps)):
            intra_within.append(c(ps[i],ps[j]))   # two synthetic derivatives of SAME photo
byclass=defaultdict(list)
for (kind,cid,photo),ps in paths.items():
    byclass[(kind,cid)].append(photo)
for key,photos in byclass.items():
    for i in range(len(photos)):
        for j in range(i+1,len(photos)):
            a=paths[(key[0],key[1],photos[i])][0]; b=paths[(key[0],key[1],photos[j])][0]
            intra_across.append(c(a,b))
intra_within=np.array(intra_within); intra_across=np.array(intra_across)
print("INTRA-CLASS COSINE SIMILARITY (MobileCLIP-S0, 512-d)")
print("  between two synthetic derivatives of the SAME source photo : n=%d  mean=%.4f  p5=%.4f" % (len(intra_within), intra_within.mean(), np.percentile(intra_within,5)))
print("  between two DIFFERENT source photos of the same class       : n=%d  mean=%.4f  p5=%.4f" % (len(intra_across), intra_across.mean(), np.percentile(intra_across,5)))
print()
print("  -> the synthetic augmentation produces %.4f cosine to its own source photo," % intra_within.mean())
print("     vs %.4f to a DIFFERENT photo of the same monument." % intra_across.mean())
print("     The 'extra' %d images per class therefore carry almost NO new viewpoint information." % (len(list(paths.values())[0])-1))
print()
print("INTER-CLASS confusion structure (mean cosine between class centroids, top-10 closest pairs):")
cents={}
for kind in ("pois","negatives"):
    for cid,p in m[kind].items():
        vs=[d[r["local_path"]] for r in p["records"]]
        v=np.mean(vs,axis=0); cents[(kind,cid)]=v/np.linalg.norm(v)
pairs=[]
ks=list(cents)
for i in range(len(ks)):
    for j in range(i+1,len(ks)):
        pairs.append((float(cents[ks[i]]@cents[ks[j]]), ks[i], ks[j]))
pairs.sort(reverse=True)
for s,a,b in pairs[:10]:
    print("   %.4f  %-42s <-> %s" % (s, a[1], b[1]))
