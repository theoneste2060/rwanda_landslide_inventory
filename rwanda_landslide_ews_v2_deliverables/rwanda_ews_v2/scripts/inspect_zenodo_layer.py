#!/usr/bin/env python3
"""Inspect the public Zenodo shapefile schema without guessing field semantics."""
import argparse, json
from collections import Counter
from pathlib import Path
import shapefile

def audit(path):
    r=shapefile.Reader(str(path))
    names=[x[0] for x in r.fields[1:]]
    records=[list(x) for x in r.records()]
    vals={name:[x[i] for x in records] for i,name in enumerate(names)}
    year=vals.get('Year',[])
    return {
      'source_file':str(path), 'records':len(records), 'geometry_type':r.shapeTypeName,
      'bbox':list(r.bbox), 'fields':[{'name':f[0],'type':f[1],'width':f[2],'decimals':f[3]} for f in r.fields[1:]],
      'null_count_by_field':{name:sum(v is None for v in values) for name,values in vals.items()},
      'year':{'negative_count':sum(v<0 for v in year),'positive_count':sum(v>0 for v in year),
              'zero_count':sum(v==0 for v in year),'distinct_signed_values':len(set(year)),
              'frequency':{str(k):int(v) for k,v in sorted(Counter(year).items())}},
      'interpretation_warning':'This script reports raw signed Year values only. The source package does not document the sign convention; do not use as event dates until confirmed by the data owner.',
      'field_semantics_warning':'Raw names area and dep_area are preserved; field meanings/units are not inferred from names.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shapefile',default='source/zenodo_5027004_extracted/landslide_data.shp')
    p.add_argument('--out',default='outputs/zenodo_layer_audit.json')
    a=p.parse_args();result=audit(Path(a.shapefile));out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='year'},indent=2));print('year',result['year']['negative_count'],'negative /',result['year']['positive_count'],'positive')
if __name__=='__main__':main()
