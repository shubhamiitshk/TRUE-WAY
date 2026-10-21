import json
m=json.load(open("ml/dataset/dataset_manifest.json"))
print("### KNOWN — 3 source photographs per POI (these are ALL the training data) ###\n")
for pid,p in m["pois"].items():
    seen=[]
    for r in p["records"]:
        if r["original_url"] not in [x[0] for x in seen]:
            seen.append((r["original_url"], r["title"]))
    print(pid)
    for _,t in seen: print("    *", t.replace("File:","")[:100])
print("\n\n### NEGATIVES — 5 source photographs per category ###\n")
for nid,p in m["negatives"].items():
    seen=[]
    for r in p["records"]:
        if r["original_url"] not in [x[0] for x in seen]:
            seen.append((r["original_url"], r["title"]))
    print(nid)
    for _,t in seen: print("    *", t.replace("File:","")[:100])
