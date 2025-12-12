#!/usr/bin/env python3
"""
Biomni Experiment Worker Process

This worker processes a specific range of papers for the batch experiment.
Called by run_Biomni_batch_experiment.py with range parameters.

Supports two experiment modes:
- MCP enabled: Uses NCBI Gene/Taxonomy query tools
- MCP disabled: Uses default Biomni without external tools
"""

import csv
import gc
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytz

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config  # noqa: F401
from Biomni.agent import A1

# ==================== CONSTANTS ====================
PROMPT_WITH_MCP_TOOLS = """
You are a scientific annotation assistant specialized in literature curation for **non-model organism gene studies**.

You will process **one paper at a time** and verify species, gene, and study type information using MCP tools.

---

### **Input Information**

Paper Metadata:

- PMID: `{pmid}`
- PubTator Species: `{species_name}` (ID: `{species_id}`)
- PubTator Gene: `{gene_name}` (ID: `{gene_id}`)
- Paper Title: `{title}`
- Paper Abstract: `{abstract}`
- Paper MeSH Terms: `{mesh}`

---

### **Your Tasks**

1. **Extract Entities (Species / Gene)**
    - Carefully read the **title**, **abstract**, and **MeSH** terms.
    - Extract all **species names** and **gene names** that appear in the paper.
    - Use PubTator Species and PubTator Gene as **reference hints**, not as absolute truth.
    - Multiple species or multiple genes may appear — **always extract all valid entities as lists**.
2. **Validate Genes using MCP Tool `query_ncbi_gene`**
    - For each detected gene, confirm that:
        - The gene name and ID are consistent.
        - The gene belongs to the reported species.
    - Use `query_ncbi_gene` to cross-check and refine information.
    - If validation is inconclusive, perform additional queries.
    - **CRITICAL**: If no valid genes are found, you MUST still create entries with **empty gene fields** (`gene_name=""`, `gene_id=""`), preserving species information.
3. **Retrieve Species Class Information**
    - For each detected species, call `query_ncbi_taxonomy` with its taxonomy ID.
    - Retrieve the **Class-level taxonomy** (e.g., Mammalia, Insecta, Actinopterygii).
    - If necessary, obtain additional taxonomy data for confirmation.
4. **Classify Research Type**
    - Based on title, abstract, and MeSH, infer one or more research categories from:
        - `Gene Identification analysis`
        - `Functional annotation`
        - `Gene Expression Analysis`
        - `Phylogenetic and Evolutionary Analysis`
        - `Functional Validation`
    - A paper can belong to **multiple categories**; include all applicable ones.

5. **CRITICAL: Construct `species_gene_list` Correctly**
    - `species_gene_list` must be a **list of dicts**, where EACH dict contains species AND gene information.
    - **NEVER output an empty list** (`species_gene_list = []`).
    - **Rules for construction**:
        - If M species and N genes found: Create M×N dicts (Cartesian product).
        - If M species and 0 genes: Create M dicts with empty `gene_name=""` and `gene_id=""`.
        - If 0 species and N genes: Create N dicts with empty `species_name=""`, `species_id=""`, `species_class=""`.
        - If 0 species and 0 genes: Create 1 dict with all fields empty.
    - **Each dict structure**:
      ```
      {{
        "species_name": str,
        "species_id": str,
        "species_class": str,
        "gene_name": str,
        "gene_id": str
      }}
      ```

6. **Save Verification Result**
    - MUST use `save_confirmed_paper_annotation(pmid, species_gene_list, gene_research_types)` IMMEDIATELY after verification.
    - Pass the correctly constructed `species_gene_list` (NEVER empty list).
    - Pass `gene_research_types` as a list of strings.
    - Log any errors, but continue processing subsequent papers.

---

### **Error Handling Rules**

- Continue even if some tool calls fail.
- When ambiguity exists, include **all plausible** species/genes/types.
- For uncertain or missing data, use empty strings (e.g., `"gene_name": ""`), but **NEVER use empty lists** for `species_gene_list`.
"""

PROMPT_WITHOUT_MCP_TOOLS = """
You are a scientific annotation assistant specialized in literature curation for **non-model organism gene studies**.

You will process **one paper at a time** and verify species, gene, and study type information.

---

### **Input Information**

Paper Metadata:

- PMID: `{pmid}`
- PubTator Species: `{species_name}` (ID: `{species_id}`)
- PubTator Gene: `{gene_name}` (ID: `{gene_id}`)
- Paper Title: `{title}`
- Paper Abstract: `{abstract}`
- Paper MeSH Terms: `{mesh}`

---

### **Your Tasks**

1. **Extract Entities (Species / Gene)**
    - Carefully read the **title**, **abstract**, and **MeSH** terms.
    - Extract all **species names** and **gene names** that appear in the paper.
    - Use PubTator Species and PubTator Gene as **reference hints**, not as absolute truth.
    - Multiple species or multiple genes may appear — **always extract all valid entities as lists**.
2. **Validate Genes**
    - For each detected gene, confirm that:
        - The gene name and ID are consistent.
        - The gene belongs to the reported species.
    - If validation is inconclusive, perform additional analysis.
    - **CRITICAL**: If no valid genes are found, you MUST still create entries with **empty gene fields** (`gene_name=""`, `gene_id=""`), preserving species information.
3. **Retrieve Species Class Information**
    - For each detected species, validate its taxonomy ID.
    - Retrieve the **Class-level taxonomy** (e.g., Mammalia, Insecta, Actinopterygii).
    - If necessary, obtain additional taxonomy data for confirmation.
4. **Classify Research Type**
    - Based on title, abstract, and MeSH, infer one or more research categories from:
        - `Gene Identification analysis`
        - `Functional annotation`
        - `Gene Expression Analysis`
        - `Phylogenetic and Evolutionary Analysis`
        - `Functional Validation`
    - A paper can belong to **multiple categories**; include all applicable ones.

5. **CRITICAL: Construct `species_gene_list` Correctly**
    - `species_gene_list` must be a **list of dicts**, where EACH dict contains species AND gene information.
    - **NEVER output an empty list** (`species_gene_list = []`).
    - **Rules for construction**:
        - If M species and N genes found: Create M×N dicts (Cartesian product).
        - If M species and 0 genes: Create M dicts with empty `gene_name=""` and `gene_id=""`.
        - If 0 species and N genes: Create N dicts with empty `species_name=""`, `species_id=""`, `species_class=""`.
        - If 0 species and 0 genes: Create 1 dict with all fields empty.
    - **Each dict structure**:
      ```
      {{
        "species_name": str,
        "species_id": str,
        "species_class": str,
        "gene_name": str,
        "gene_id": str
      }}
      ```

6. **Save Verification Result**
    - IMPERATIVE ACTION & DATA SAFETY: The final resulting dictionary must be appended to the file 20251101_papers_database.json. This is a strict APPEND-ONLY operation. You are strictly prohibited from overwriting or deleting any existing content.
    - Pass the correctly constructed `species_gene_list` (NEVER empty list).
    - Pass `gene_research_types` as a list of strings.
    - Log any errors, but continue processing subsequent papers.

---

### **Error Handling Rules**

- Continue even if some tool calls fail.
- When ambiguity exists, include **all plausible** species/genes/types.
- For uncertain or missing data, use empty strings (e.g., `"gene_name": ""`), but **NEVER use empty lists** for `species_gene_list`.
"""


# ==================== WORKER EXECUTION ====================
def process_papers_batch(
    start_index: int, end_index: int, use_mcp: bool, csv_path: Path, log_dir: Path
) -> Dict[str, Any]:
    """
    Process a batch of papers with specified configuration.

    Args:
        start_index: Starting paper index (0-based)
        end_index: Ending paper index (exclusive)
        use_mcp: Whether to use MCP tools
        csv_path: Path to input CSV file
        log_dir: Directory for log files

    Returns:
        Dictionary with processing statistics
    """
    # Initialize agent
    print(f"Initializing agent for papers {start_index + 1} to {end_index}...")
    print(f"MCP enabled: {use_mcp}")
    agent = A1(path="/app/data", llm="gpt-4.1-mini-2025-04-14", timeout_seconds=10000)

    # Add MCP server if enabled
    if use_mcp:
        agent.add_mcp(config_path="config/mcp_config.yaml")
        prompt_template = PROMPT_WITH_MCP_TOOLS
        experiment_mode = "custom"
    else:
        prompt_template = PROMPT_WITHOUT_MCP_TOOLS
        experiment_mode = "default"

    # Prepare log file
    jst = pytz.timezone("Asia/Tokyo")
    current_time_jst = datetime.now(jst)
    log_filename = (
        current_time_jst.strftime("%Y%m%d_%H%M%S")
        + f"_worker_{experiment_mode}_{start_index}_{end_index}.log"
    )
    log_file = log_dir / log_filename
    current_time = current_time_jst.strftime("%Y年%m月%d日 %H時%M分%S秒（JST）")

    # Write log header
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"{'=' * 80}\n")
        f.write(f"ワーカープロセスログ: {current_time}\n")
        f.write(
            f"実験モード: {'Custom Biomni (MCP有効)' if use_mcp else 'Default Biomni (MCP無効)'}\n"
        )
        f.write(f"処理範囲: {start_index + 1} - {end_index}\n")
        f.write(f"{'=' * 80}\n\n")

    # Statistics
    total_papers = 0
    cumulative_input_tokens = 0
    cumulative_output_tokens = 0
    cumulative_cost = 0.0
    cumulative_llm_calls = 0

    start_time = time.time()

    # Process papers in range
    with open(csv_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for idx, row in enumerate(reader):
            # Skip papers outside range
            if idx < start_index:
                continue
            if idx >= end_index:
                break

            paper_start_time = time.time()
            global_idx = idx

            print(f"\n  Paper {global_idx + 1}: PMID={row['pmid']}")

            # Format prompt with paper data
            prompt = prompt_template.format(
                pmid=row["pmid"],
                species_name=row["species_name"],
                species_id=row["species_id"],
                gene_name=row["gene_name"],
                gene_id=row["gene_id"],
                title=row["title"],
                abstract=row["abstract"],
                mesh=row["mesh"],
            )

            try:
                log_messages, final_result, token_stats = agent.go(prompt)
                paper_elapsed_time = time.time() - paper_start_time

                # Update cumulative statistics
                total_papers += 1
                cumulative_input_tokens += token_stats["total_input_tokens"]
                cumulative_output_tokens += token_stats["total_output_tokens"]
                cumulative_cost += token_stats["total_cost"]
                cumulative_llm_calls += token_stats["call_count"]

                # Write to log
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"Paper {global_idx + 1}: PMID={row['pmid']}\n")
                    f.write(f"{'=' * 80}\n\n")
                    for log_entry in log_messages:
                        f.write(log_entry + "\n")
                    f.write(f"\n処理時間: {paper_elapsed_time:.2f}秒\n")
                    f.write(f"入力トークン: {token_stats['total_input_tokens']:,}, ")
                    f.write(f"出力トークン: {token_stats['total_output_tokens']:,}, ")
                    f.write(f"費用: ${token_stats['total_cost']:.6f}\n")

                # Free memory
                del log_messages
                gc.collect()

                print(
                    f"    ✓ Completed in {paper_elapsed_time:.2f}s (Cost: ${token_stats['total_cost']:.6f})"
                )

            except Exception as e:
                print(f"    ✗ Error: {e}")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"Paper {global_idx + 1}: PMID={row['pmid']} - ERROR\n")
                    f.write(f"{'=' * 80}\n\n")
                    f.write(f"Error: {str(e)}\n")

    # Calculate execution time
    execution_time = time.time() - start_time

    # Prepare final summary
    final_summary = f"""
{"=" * 80}
ワーカー処理完了
{"=" * 80}

=== 実験設定 ===
- モード: {"Custom Biomni (MCP有効)" if use_mcp else "Default Biomni (MCP無効)"}

=== 処理範囲 ===
- 開始: {start_index + 1}
- 終了: {end_index}

=== 処理時間 ===
- 総処理時間: {execution_time:.2f}秒 ({execution_time / 60:.2f}分)
- 処理論文数: {total_papers}論文
- 1論文あたり平均時間: {execution_time / total_papers if total_papers > 0 else 0:.2f}秒

=== トークン使用量 ===
- 累計入力トークン: {cumulative_input_tokens:,}
- 累計出力トークン: {cumulative_output_tokens:,}
- 累計総トークン: {cumulative_input_tokens + cumulative_output_tokens:,}
- 累計LLM呼び出し回数: {cumulative_llm_calls}

=== 費用 ===
- 累計費用: ${cumulative_cost:.6f}
- 1論文あたり平均費用: ${cumulative_cost / total_papers if total_papers > 0 else 0:.6f}

=== ログファイル ===
- {log_file}

{"=" * 80}
"""

    print(final_summary)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{final_summary}")

    return {
        "total_papers": total_papers,
        "execution_time": execution_time,
        "cumulative_input_tokens": cumulative_input_tokens,
        "cumulative_output_tokens": cumulative_output_tokens,
        "cumulative_cost": cumulative_cost,
        "cumulative_llm_calls": cumulative_llm_calls,
        "log_file": str(log_file),
    }


def main() -> None:
    """Main entry point for worker process."""
    # Parse command line arguments
    if len(sys.argv) != 4:
        print(
            "Usage: python Biomni_experiment_worker.py <start_index> <end_index> <use_mcp>"
        )
        sys.exit(1)

    start_index = int(sys.argv[1])
    end_index = int(sys.argv[2])
    use_mcp = sys.argv[3].lower() in ("true", "1", "yes")

    # Setup paths
    csv_path = (
        project_root / "data/Biomni_data/data_lake/20241201_20241203_pubtator.csv"
    )
    log_dir = project_root / "logs" / "run_agent_batch"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Process papers
    process_papers_batch(start_index, end_index, use_mcp, csv_path, log_dir)


if __name__ == "__main__":
    main()
