#!/usr/bin/env python3
"""Match uncovered RFEs against closed Features to find closure candidates.

Reads:
  - RFE JSONL files (one per component) from a data directory
  - Closed Features JSONL file

Produces a markdown report of RFEs that likely match completed Features,
ranked by match confidence.

Usage:
    python3 rfe-match-features.py --rfe-dir <DIR> --features <FILE> --output <FILE>
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict


def tokenize(text):
    """Extract meaningful tokens from text, lowercased."""
    text = text.lower()
    # Remove common prefixes/noise
    text = re.sub(r'\[rfe\]', '', text)
    text = re.sub(r'\bcee\.?ne?xt\b', '', text)
    text = re.sub(r'rfe-\d+', '', text)
    # Split on non-alphanumeric
    tokens = re.findall(r'[a-z][a-z0-9_.-]{1,}', text)
    # Remove very common words
    stop = {
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'has',
        'not', 'are', 'was', 'were', 'been', 'being', 'will', 'would', 'could',
        'should', 'can', 'may', 'might', 'shall', 'must', 'need', 'also',
        'when', 'where', 'which', 'what', 'how', 'who', 'whom', 'than',
        'then', 'there', 'here', 'into', 'over', 'after', 'before',
        'between', 'under', 'above', 'below', 'about', 'such', 'each',
        'some', 'any', 'all', 'both', 'most', 'other', 'more', 'less',
        'very', 'just', 'only', 'even', 'still', 'already', 'using',
        'used', 'use', 'new', 'like', 'make', 'made', 'want', 'able',
        'openshift', 'ocp', 'red', 'hat', 'cluster', 'support', 'add',
        'feature', 'request', 'allow', 'enable', 'provide', 'option',
        'ability', 'customer', 'user', 'users',
    }
    return [t for t in tokens if t not in stop and len(t) > 1]


def build_ngrams(tokens, n=2):
    """Build n-grams from token list."""
    grams = set(tokens)  # unigrams
    for i in range(len(tokens) - n + 1):
        grams.add(' '.join(tokens[i:i + n]))
    return grams


def jaccard(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def match_score(rfe_tokens, feature_tokens, rfe_ngrams, feature_ngrams):
    """Compute a weighted match score."""
    # Jaccard on unigrams
    uni_score = jaccard(set(rfe_tokens), set(feature_tokens))
    # Jaccard on bigrams
    bi_score = jaccard(rfe_ngrams, feature_ngrams)
    # Weighted combination (bigrams worth more — they capture phrases)
    return uni_score * 0.4 + bi_score * 0.6


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rfe-dir', required=True, help='Directory with component JSONL files')
    parser.add_argument('--features', required=True, help='Closed features JSONL file')
    parser.add_argument('--output', '-o', required=True, help='Output markdown report')
    parser.add_argument('--threshold', type=float, default=0.15, help='Min match score (0-1)')
    args = parser.parse_args()

    # Load closed features
    features = []
    with open(args.features) as f:
        for line in f:
            line = line.strip()
            if line:
                features.append(json.loads(line))

    print(f"Loaded {len(features)} closed Features", file=sys.stderr)

    # Pre-tokenize features
    for feat in features:
        feat['_tokens'] = tokenize(feat['summary'])
        feat['_ngrams'] = build_ngrams(feat['_tokens'])

    # Load all uncovered RFEs from component files
    rfes = []
    for fname in sorted(os.listdir(args.rfe_dir)):
        if not fname.endswith('.jsonl') or fname == 'closed-features.jsonl' or fname == '_index.json':
            continue
        component = fname.replace('.jsonl', '')
        with open(os.path.join(args.rfe_dir, fname)) as f:
            for line in f:
                line = line.strip()
                if line:
                    rfe = json.loads(line)
                    if rfe.get('coverage') == 'none':
                        rfe['_component'] = component
                        rfes.append(rfe)

    print(f"Loaded {len(rfes)} uncovered RFEs", file=sys.stderr)

    # Pre-tokenize RFEs
    for rfe in rfes:
        text = rfe['summary'] + ' ' + rfe.get('description', '')
        rfe['_tokens'] = tokenize(text)
        rfe['_ngrams'] = build_ngrams(rfe['_tokens'])

    # Match each RFE against all features
    matches = []
    for i, rfe in enumerate(rfes):
        if i % 200 == 0:
            print(f"  Matching RFE {i}/{len(rfes)}...", file=sys.stderr)

        best_score = 0
        best_features = []

        for feat in features:
            score = match_score(rfe['_tokens'], feat['_tokens'],
                                rfe['_ngrams'], feat['_ngrams'])
            if score >= args.threshold:
                best_features.append((score, feat))

        # Keep top 3 matches
        best_features.sort(key=lambda x: x[0], reverse=True)
        best_features = best_features[:3]

        if best_features:
            matches.append({
                'rfe': rfe,
                'matches': [(s, f['key'], f['summary'], f['project'], f['status'])
                            for s, f in best_features],
                'top_score': best_features[0][0],
            })

    matches.sort(key=lambda m: m['top_score'], reverse=True)
    print(f"\nFound {len(matches)} RFEs with Feature matches above threshold {args.threshold}", file=sys.stderr)

    # Generate report
    L = []
    L.append("# RFE Closure Candidates: Matched Against Closed Features")
    L.append(f"**Generated:** {__import__('datetime').date.today().isoformat()}")
    L.append(f"**Uncovered RFEs scanned:** {len(rfes)}")
    L.append(f"**Closed Features indexed:** {len(features)}")
    L.append(f"**Match threshold:** {args.threshold}")
    L.append(f"**RFEs with matches:** {len(matches)}")
    L.append("")

    # High confidence (score >= 0.3)
    high = [m for m in matches if m['top_score'] >= 0.3]
    medium = [m for m in matches if 0.2 <= m['top_score'] < 0.3]
    low = [m for m in matches if m['top_score'] < 0.2]

    L.append("## Summary")
    L.append("")
    L.append(f"| Confidence | Count | Action |")
    L.append(f"|------------|------:|--------|")
    L.append(f"| High (score >= 0.3) | {len(high)} | Review and close |")
    L.append(f"| Medium (0.2 - 0.3) | {len(medium)} | Review carefully |")
    L.append(f"| Low (< 0.2) | {len(low)} | Spot check |")
    L.append("")

    # High confidence matches
    L.append("## High Confidence Matches (score >= 0.3)")
    L.append("")
    L.append("These RFEs very likely match completed Features and should be reviewed for closure.")
    L.append("")
    if high:
        L.append("| RFE | Votes | Component | RFE Summary | Score | Feature | Feature Summary |")
        L.append("|-----|------:|-----------|-------------|------:|---------|-----------------|")
        for m in high:
            rfe = m['rfe']
            score, fkey, fsumm, fproj, fstatus = m['matches'][0]
            comp = rfe['_component'].replace('---', ' - ')
            L.append(f"| {rfe['key']} | {rfe['votes']} | {comp} | {rfe['summary'][:50]} | {score:.2f} | {fkey} | {fsumm[:50]} |")
    L.append("")

    # Medium confidence
    L.append("## Medium Confidence Matches (0.2 - 0.3)")
    L.append("")
    if medium:
        L.append("| RFE | Votes | Component | RFE Summary | Score | Feature | Feature Summary |")
        L.append("|-----|------:|-----------|-------------|------:|---------|-----------------|")
        for m in medium[:100]:  # cap at 100
            rfe = m['rfe']
            score, fkey, fsumm, fproj, fstatus = m['matches'][0]
            comp = rfe['_component'].replace('---', ' - ')
            L.append(f"| {rfe['key']} | {rfe['votes']} | {comp} | {rfe['summary'][:50]} | {score:.2f} | {fkey} | {fsumm[:50]} |")
    L.append("")

    # Detailed view for high confidence
    L.append("## Detailed High-Confidence Match Analysis")
    L.append("")
    for m in high:
        rfe = m['rfe']
        L.append(f"### {rfe['key']}: {rfe['summary'][:80]}")
        L.append(f"**Component:** {rfe['_component']} | **Votes:** {rfe['votes']} | **Status:** {rfe['status']} | **Priority:** {rfe['priority']}")
        L.append("")
        L.append("| Rank | Score | Feature | Project | Status | Summary |")
        L.append("|-----:|------:|---------|---------|--------|---------|")
        for i, (score, fkey, fsumm, fproj, fstatus) in enumerate(m['matches'], 1):
            L.append(f"| {i} | {score:.2f} | {fkey} | {fproj} | {fstatus} | {fsumm[:70]} |")
        L.append("")

    report = '\n'.join(L) + '\n'
    with open(args.output, 'w') as f:
        f.write(report)

    print(f"Report written to {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
