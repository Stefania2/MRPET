import csv
rows=[]
with open('critical_region_refined.csv','r',encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append((float(row['velocity']), float(row['coherence']), int(row['physical_influence']), int(row['restored_index']), float(row['probability'])))
rows.sort(key=lambda x:x[4], reverse=True)
for r in rows[:20]:
    print(r)
