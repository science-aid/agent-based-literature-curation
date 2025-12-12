#!/usr/bin/env python3
"""
PubTatorのPMIDに対応する解析結果を収集し、top20生物種とgene情報でフィルタリング
"""

import ast
import csv
import json
import re
from pathlib import Path

project_root = Path(__file__).parent.parent.parent

# ファイルパス
pubtator_csv = (
    project_root / "results/wf_pre_agent/FINAL_20251117_172057_20241201_20241203.csv"
)
analyzed_json = project_root / "results/Biomni_default/20251101_papers_database.json"
log_dir = project_root / "logs/run_agent_batch/デフォルトBiomni実験結果ログ"
top20_csv = project_root / "config/top20_organisms_with_taxid.csv"
output_all_json = project_root / "20251101_all_papers_collected.json"
output_filtered_json = project_root / "20251101_filtered_papers_database.json"

# top20生物種IDと種名をセットで読み込み
top20_ids = set()
top20_names = set()
with open(top20_csv, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        top20_ids.add(row["NCBI_taxonomy_id"])
        top20_names.add(row["species_name"])

print(f"Top20 species IDs loaded: {len(top20_ids)}")
print(f"Top20 species names loaded: {len(top20_names)}")

# PubTatorからPMIDリストを取得（重複を排除）
pmid_set = set()
with open(pubtator_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pmid_set.add(row["pmid"])

pmid_list = sorted(pmid_set)  # ソートして安定した順序にする

print(f"Total unique PMIDs in PubTator: {len(pmid_list)}")

# 20251101_papers_database.jsonから解析済みデータを読み込み
analyzed_data = {}
with open(analyzed_json, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line.strip())
        # PMIDもしくはpmidキーを取得
        pmid = data.get("PMID") or data.get("pmid")
        if pmid:
            analyzed_data[pmid] = data

print(f"Analyzed data loaded: {len(analyzed_data)} papers")


# ログファイルからPMIDを含むdictを抽出する関数
def extract_from_logs(pmid):
    """ログファイルから指定PMIDのdictを探す"""
    log_files = sorted(log_dir.glob("20251101_*.log"))

    for log_file in log_files:
        content = log_file.read_text(encoding="utf-8")

        # Paper XXX: PMID=XXXXXXXX を探してその後の<solution>を取得
        paper_pattern = rf"Paper \d+: PMID={pmid}\b"
        paper_match = re.search(paper_pattern, content)

        if not paper_match:
            continue

        # Paper行以降のコンテンツを取得
        content_after_paper = content[paper_match.start() :]

        # パターン1: {'pmid': 'XXXXXXXX', ...} 形式（シングルクォート、大文字小文字両対応）
        pattern1 = (
            rf"\{{'(?:pmid|PMID)':\s*'{pmid}'.*?'gene_research_types':\s*\[.*?\]\}}"
        )
        matches = re.findall(pattern1, content_after_paper, re.DOTALL)

        if matches:
            try:
                data = ast.literal_eval(matches[0])
                # PMIDキーを正規化（小文字に統一）
                if "PMID" in data:
                    data["pmid"] = data.pop("PMID")
                return data
            except:
                pass

        # パターン2: <solution>内のJSON形式（ダブルクォート、大文字小文字両対応）
        pattern2 = rf'<solution>\s*\{{\s*"(?:pmid|PMID)":\s*"{pmid}".*?"gene_research_types":\s*\[.*?\]\s*\}}\s*</solution>'
        matches = re.findall(pattern2, content_after_paper, re.DOTALL)

        if matches:
            try:
                json_str = re.search(r"\{.*\}", matches[0], re.DOTALL).group()
                data = json.loads(json_str)
                # PMIDキーを正規化（小文字に統一）
                if "PMID" in data:
                    data["pmid"] = data.pop("PMID")
                return data
            except:
                pass

        # パターン3: <solution>内にPMIDがない場合（Paper行から推測）
        pattern3 = r'<solution>\s*(\{[^}]*"species_gene_list"[^}]*\})\s*</solution>'
        matches = re.findall(pattern3, content_after_paper, re.DOTALL)

        if matches:
            try:
                json_str = matches[0]
                data = json.loads(json_str)
                # PMIDがない場合は追加
                if "pmid" not in data and "PMID" not in data:
                    data["pmid"] = pmid
                # PMIDキーを正規化
                if "PMID" in data:
                    data["pmid"] = data.pop("PMID")
                return data
            except:
                pass

        # パターン4: <execute>タグ内のresult_dict形式
        # より柔軟な抽出：result_dict = { ... } の全体を取得
        pattern4 = r"result_dict\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})"
        matches = re.findall(pattern4, content_after_paper, re.DOTALL)

        for match in matches:
            try:
                # Pythonの辞書リテラルをパース
                data = ast.literal_eval(match)
                # species_gene_listキーがあることを確認
                if "species_gene_list" in data:
                    # PMIDを追加または正規化
                    if "pmid" not in data and "PMID" not in data:
                        data["pmid"] = pmid
                    elif "PMID" in data:
                        data["pmid"] = data.pop("PMID")
                    return data
            except:
                continue

        # パターン5: <execute>と<solution>が混在する場合、より広範囲に探す
        pattern5 = r"<execute>.*?</execute>|<solution>.*?</solution>"
        blocks = re.findall(pattern5, content_after_paper, re.DOTALL)

        for block in blocks:
            # ブロック内のすべての辞書構造を探す
            dict_pattern = r'\{[^{}]*"species_gene_list"[^{}]*\[[^\]]*\][^{}]*"gene_research_types"[^{}]*\[[^\]]*\][^{}]*\}'
            dict_matches = re.findall(dict_pattern, block, re.DOTALL)

            for dict_str in dict_matches:
                try:
                    # JSON形式で試す
                    data = json.loads(dict_str)
                    if "pmid" not in data and "PMID" not in data:
                        data["pmid"] = pmid
                    elif "PMID" in data:
                        data["pmid"] = data.pop("PMID")
                    return data
                except:
                    try:
                        # Python辞書形式で試す
                        data = ast.literal_eval(dict_str)
                        if "pmid" not in data and "PMID" not in data:
                            data["pmid"] = pmid
                        elif "PMID" in data:
                            data["pmid"] = data.pop("PMID")
                        return data
                    except:
                        continue

    return None


# 全PMIDに対応するデータを収集（重複排除のため辞書を使用）
collected_papers_dict = {}
missing_count = 0

print("\nCollecting paper data...")
for i, pmid in enumerate(pmid_list, 1):
    if i % 50 == 0:
        print(f"  Progress: {i}/{len(pmid_list)}")

    # すでに収集済みの場合はスキップ
    if pmid in collected_papers_dict:
        continue

    # まず analyzed_data から探す
    if pmid in analyzed_data:
        collected_papers_dict[pmid] = analyzed_data[pmid]
    else:
        # ログファイルから探す
        data = extract_from_logs(pmid)
        if data:
            collected_papers_dict[pmid] = data
        else:
            print(f"  Warning: PMID {pmid} not found")
            missing_count += 1

# 辞書からリストに変換
collected_papers = list(collected_papers_dict.values())

print(f"\nCollected: {len(collected_papers)} papers (unique)")
print(f"Missing: {missing_count} papers")

# 全データをJSONとして出力
with open(output_all_json, "w", encoding="utf-8") as f:
    json.dump(collected_papers, f, ensure_ascii=False, indent=2)

print(f"All collected data saved: {output_all_json}")

# フィルタリング処理（重複排除）
filtered_papers_dict = {}

for paper in collected_papers:
    # PMIDを取得（正規化）
    pmid = paper.get("pmid") or paper.get("PMID")
    if not pmid:
        continue

    # すでにフィルタ済みの場合はスキップ
    if pmid in filtered_papers_dict:
        continue

    species_gene_list = paper.get("species_gene_list", [])

    # 生物種IDと種名を取得
    species_ids = {s["species_id"] for s in species_gene_list if s.get("species_id")}
    species_names = {
        s["species_name"] for s in species_gene_list if s.get("species_name")
    }

    # top20に該当する生物種（IDまたは種名）が1つでもあれば除外
    if (species_ids & top20_ids) or (species_names & top20_names):
        continue

    # gene_nameまたはgene_idが存在するか確認
    has_gene = any(s.get("gene_name") or s.get("gene_id") for s in species_gene_list)

    if has_gene:
        filtered_papers_dict[pmid] = paper

# 辞書からリストに変換
filtered_papers = list(filtered_papers_dict.values())

# フィルタリング結果を出力
with open(output_filtered_json, "w", encoding="utf-8") as f:
    json.dump(filtered_papers, f, ensure_ascii=False, indent=2)

print("\nFiltering complete:")
print(f"  Total collected: {len(collected_papers)}")
print(f"  After filtering: {len(filtered_papers)}")
print(f"  Filtered output: {output_filtered_json}")
