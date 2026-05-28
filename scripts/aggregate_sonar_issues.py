#!/usr/bin/env python3
import os
import csv
import json
import argparse


def load_manifest(manifest_path):
    mapping = {}
    with open(manifest_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            fname = row.get('filename')
            if fname:
                mapping[fname] = row
    return mapping


def load_sonar(json_path):
    with open(json_path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def aggregate(manifest_map, sonar_json):
    issues = sonar_json.get('issues', [])
    out = []
    for issue in issues:
        comp = issue.get('component', '')
        # component format: PROJECT:relative/path/to/file
        if ':' in comp:
            _, rel = comp.split(':', 1)
        else:
            rel = comp
        filename = os.path.basename(rel)

        manifest_row = manifest_map.get(filename, {})

        row = {
            'issue_key': issue.get('key'),
            'component': comp,
            'path': rel,
            'filename': filename,
            'rule': issue.get('rule'),
            'severity': issue.get('severity'),
            'type': issue.get('type'),
            'line': issue.get('line'),
            'message': issue.get('message'),
            'creationDate': issue.get('creationDate'),
            'updateDate': issue.get('updateDate'),
            'tags': '|'.join(issue.get('tags', [])),
        }

        # merge manifest fields (if available)
        for k, v in manifest_row.items():
            row[f'manifest_{k}'] = v

        out.append(row)

    return out


def write_outputs(rows, out_csv, out_json):
    # compute union of all keys to avoid missing fields between rows
    if rows:
        keyset = []
        seen = set()
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.add(k)
                    keyset.append(k)
        keys = keyset
    else:
        keys = ['issue_key','component','path','filename','rule','severity','type','line','message']

    with open(out_csv, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    with open(out_json, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='Aggregate Sonar issues and join with prompts manifest')
    parser.add_argument('--root', default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
                        help='Workspace root (default: parent dir of scripts/)')
    parser.add_argument('--manifest', default='prompts_manifest.csv')
    parser.add_argument('--sonar', default='sonar_issues_TestePiloto.json')
    parser.add_argument('--out-csv', default='sonar_issues_aggregated.csv')
    parser.add_argument('--out-json', default='sonar_issues_aggregated.json')
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    manifest_path = os.path.join(root, args.manifest)
    sonar_path = os.path.join(root, args.sonar)
    out_csv = os.path.join(root, args.out_csv)
    out_json = os.path.join(root, args.out_json)

    if not os.path.exists(manifest_path):
        print('Manifest not found:', manifest_path)
        return 2
    if not os.path.exists(sonar_path):
        print('Sonar JSON not found:', sonar_path)
        return 2

    manifest = load_manifest(manifest_path)
    sonar = load_sonar(sonar_path)
    rows = aggregate(manifest, sonar)
    write_outputs(rows, out_csv, out_json)

    print(f'Wrote {len(rows)} aggregated issues to:')
    print(' -', out_csv)
    print(' -', out_json)


if __name__ == '__main__':
    raise SystemExit(main())
