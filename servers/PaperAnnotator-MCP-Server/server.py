#!/usr/bin/env python3
import asyncio
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from .paper_annotator import PaperAnnotator

# MCPサーバーを初期化
mcp = FastMCP("PaperAnnotator MCP Server")

# 内部でLLMを呼ぶこともあるので、Statefulへ対応するように関数内でインスタンス化する
paper_annotator = None


def get_paper_annotator():
    """Get or create PaperAnnotator instance with lazy initialization"""
    global paper_annotator
    if paper_annotator is None:
        paper_annotator = PaperAnnotator()
    return paper_annotator


@mcp.tool()
async def query_ncbi_taxonomy(
    query: str, query_type: str = "auto"
) -> Dict[str, Any]:
    """
    Unified NCBI Taxonomy query: bidirectional conversion between ID and name.

    This tool automatically detects whether the input is a taxonomy ID or species name
    and performs the appropriate conversion. Supports explicit query type specification.

    IMPORTANT: To retrieve taxonomic class information, you MUST use taxonomy ID as input.
    If you only have a species name, use a two-step workflow:
    1. First: species_name → taxonomy_id (query_type='name_to_id')
    2. Second: taxonomy_id → species_name + class (query_type='id_to_name')

    Parameters
    ----------
    query : str (REQUIRED, must use keyword argument)
        Taxonomy ID (e.g., "9606") or species name (e.g., "Homo sapiens")
    query_type : str, optional (must use keyword argument if provided)
        Query type: "id_to_name", "name_to_id", or "auto" (default: "auto")
        - "auto": Automatically detect based on input (numeric = ID, text = name)
        - "id_to_name": Convert taxonomy ID to species name + class
        - "name_to_id": Convert species name to taxonomy ID

    Returns
    -------
    dict
        Dictionary containing:
        - result: str or dict - When query_type='id_to_name': dict with species_name and class
                                When query_type='name_to_id': str with taxonomy ID
        - query_type: str - The query type used
        - status: str - "success" or "error"
        - error: str - Error message (only if status is "error")

    Examples
    --------
    >>> # Get species name and class from taxonomy ID (MUST use keyword arguments)
    >>> query_ncbi_taxonomy(query="9606", query_type="id_to_name")
    {"result": {"species_name": "Homo sapiens", "class": "Mammalia"}, "query_type": "id_to_name", "status": "success"}

    >>> # Get taxonomy ID from species name (MUST use keyword arguments)
    >>> query_ncbi_taxonomy(query="Homo sapiens", query_type="name_to_id")
    {"result": "9606", "query_type": "name_to_id", "status": "success"}

    >>> # Two-step workflow to get class from species name
    >>> # Step 1: Get taxonomy ID
    >>> result1 = query_ncbi_taxonomy(query="Homo sapiens", query_type="name_to_id")
    >>> taxonomy_id = result1["result"]  # "9606"
    >>> # Step 2: Get class using taxonomy ID
    >>> result2 = query_ncbi_taxonomy(query=taxonomy_id, query_type="id_to_name")
    >>> species_info = result2["result"]  # {"species_name": "Homo sapiens", "class": "Mammalia"}

    >>> # Auto-detection (detects ID, returns species name and class)
    >>> query_ncbi_taxonomy(query="9606")
    {"result": {"species_name": "Homo sapiens", "class": "Mammalia"}, "query_type": "id_to_name", "status": "success"}

    >>> # Auto-detection (detects name, returns taxonomy ID)
    >>> query_ncbi_taxonomy(query="Homo sapiens")
    {"result": "9606", "query_type": "name_to_id", "status": "success"}
    """
    try:
        result = await asyncio.to_thread(
            get_paper_annotator().query_taxonomy,
            query=query,
            query_type=query_type,
        )
        detected_type = "id_to_name" if query.isdigit() else "name_to_id"
        actual_type = query_type if query_type != "auto" else detected_type
        return {"result": result, "query_type": actual_type, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}


@mcp.tool()
async def query_ncbi_gene(
    query: str, query_type: str = "auto", species_id: str = ""
) -> Dict[str, Any]:
    """
    Unified NCBI Gene query: comprehensive gene information lookup.

    This tool supports multiple query patterns including ID-to-info conversion,
    species+gene name to ID lookup, and automatic query type detection.

    IMPORTANT: To retrieve gene ID from gene name, you MUST provide species_id (taxonomy ID).
    Use species_id + gene_name together to get gene_id with query_type='species_and_name_to_id'.

    Parameters
    ----------
    query : str (REQUIRED, must use keyword argument)
        Gene ID (e.g., "7157") or gene name (e.g., "TP53")
    query_type : str, optional (must use keyword argument if provided)
        Query type: "id_to_info", "id_to_name", "species_and_name_to_id", or "auto" (default: "auto")
        - "auto": Automatically detect (numeric = ID, text+species_id = name lookup)
        - "id_to_info": Get comprehensive gene info from gene ID
        - "id_to_name": Get gene symbol from gene ID
        - "species_and_name_to_id": Get gene ID from species ID + gene name
    species_id : str, optional (must use keyword argument if provided)
        NCBI Taxonomy ID (e.g., "9606"). REQUIRED for "species_and_name_to_id" or auto-detection with gene name

    Returns
    -------
    dict
        Dictionary containing:
        - gene_id: str - NCBI Gene ID
        - gene_name: str - Gene symbol/locus
        - description: str - Gene description
        - ensembl_id: str - Ensembl ID
        - synonyms: list - Gene synonyms
        - query_type: str - The query type used
        - status: str - "success" or "error"
        - error: str - Error message (only if status is "error")

    Examples
    --------
    >>> # Get comprehensive gene info from gene ID (MUST use keyword arguments)
    >>> query_ncbi_gene(query="7157", query_type="id_to_info")
    {
        "gene_id": "7157",
        "gene_name": "TP53",
        "description": "tumor protein p53",
        "ensembl_id": "ENSG00000141510",
        "synonyms": ["P53", "BCC7"],
        "query_type": "id_to_info",
        "status": "success"
    }

    >>> # Get gene ID from species_id + gene_name (MUST use keyword arguments)
    >>> query_ncbi_gene(query="TP53", query_type="species_and_name_to_id", species_id="9606")
    {
        "gene_id": "7157",
        "gene_name": "TP53",
        "description": "tumor protein p53",
        "query_type": "species_and_name_to_id",
        "status": "success"
    }

    >>> # Get gene symbol from gene ID (MUST use keyword arguments)
    >>> query_ncbi_gene(query="7157", query_type="id_to_name")
    {"gene_id": "7157", "gene_name": "TP53", "query_type": "id_to_name", "status": "success"}

    >>> # Auto-detection with gene ID
    >>> query_ncbi_gene(query="7157")
    {"gene_id": "7157", "gene_name": "TP53", "description": "...", "query_type": "id_to_info", "status": "success"}

    >>> # Auto-detection with gene name + species_id
    >>> query_ncbi_gene(query="TP53", species_id="9606")
    {"gene_id": "7157", "gene_name": "TP53", "query_type": "species_and_name_to_id", "status": "success"}
    """
    try:
        result = await asyncio.to_thread(
            get_paper_annotator().query_gene,
            query=query,
            query_type=query_type,
            species_id=species_id,
        )

        # Determine actual query type used
        if query_type == "auto":
            if query.isdigit():
                actual_type = "id_to_info"
            elif species_id:
                actual_type = "species_and_name_to_id"
            else:
                actual_type = "unknown"
        else:
            actual_type = query_type

        return {**result, "query_type": actual_type, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}


# @mcp.tool()
# async def llm_extract_genes_from_scientific_text(
#     scientifictexts: str, model_name: str = "gpt-5-mini-2025-08-07"
# ) -> Dict[str, Any]:
#     """
#     Analyze target species and genes in scientific text using LLM.

#     Uses a language model to identify the target organism(s), gene(s), and research type
#     from scientific text. Optimized for non-model organisms and gene-specific studies.

#     Parameters
#     ----------
#     scientifictexts : str
#         Scientific text (title, abstract, or MeSH) to analyze
#     model_name : str, optional
#         LLM model name (default: "gpt-5-mini-2025-08-07")
#         Options: "gpt-5-mini-2025-08-07", "gpt-4o-mini", "llama3.1:8b", etc.

#     Returns
#     -------
#     dict
#         Dictionary containing:
#         - species_names: list[str] - Target organism names (common and/or scientific)
#         - gene_names: list[str] - Target gene symbols/names
#         - study_type: str - Primary research type (one of 6 categories)
#         - confidence: str - "high" or "low"
#         - status: str - "success" or "error"
#         - error: str - Error message (only if status is "error")

#     Research Type Categories
#     ------------------------
#     1. Expression Analysis - gene expression patterns, RNA-seq, qPCR
#     2. Variant Analysis - SNPs, genetic variants, polymorphisms
#     3. Mutation Analysis - mutations, mutagenesis, knockouts
#     4. Functional Analysis - gene function, protein activity, phenotypes
#     5. Genome Structure Analysis - genome assembly, chromosomal organization
#     6. Regulation Analysis - gene regulation, promoters, transcription factors

#     Examples
#     --------
#     >>> llm_extract_genes_from_scientific_text(
#     ...     "Expression of HSP70 in Antarctic fish Notothenia coriiceps"
#     ... )
#     {
#         "species_names": ["Notothenia coriiceps", "Antarctic fish"],
#         "gene_names": ["HSP70"],
#         "study_type": "Expression Analysis",
#         "confidence": "high",
#         "status": "success"
#     }

#     >>> llm_extract_genes_from_scientific_text(
#     ...     "CRISPR knockout of TP53 in human cell lines"
#     ... )
#     {
#         "species_names": ["human"],
#         "gene_names": ["TP53"],
#         "study_type": "Mutation Analysis",
#         "confidence": "high",
#         "status": "success"
#     }
#     """
#     try:
#         result = await asyncio.to_thread(
#             get_paper_annotator().analyze_gene_mention_by_llm,
#             scientifictexts=scientifictexts,
#             model_name=model_name,
#         )
#         return {**result, "status": "success"}
#     except Exception as e:
#         return {"error": str(e), "status": "error"}


@mcp.tool()
async def save_confirmed_paper_annotation(
    pmid: str,
    species_gene_list: list,
    gene_research_types: list,
    output_path: str = "papers_database.json"
) -> Dict[str, Any]:
    """
    Save confirmed paper annotation data after AI agent verification.

    This tool is designed for AI agents to save paper annotation results after verifying
    species, genes, and research types. It combines data formatting and database saving
    in a single step.

    Parameters
    ----------
    pmid : str
        Paper ID (PubMed ID)
    species_gene_list : list
        List of dicts with verified species and gene information (Cartesian product).
        EACH dict represents ONE (species, gene) PAIR. Each dict contains:
        - species_name (str): Scientific name (e.g., "Notothenia coriiceps")
        - species_id (str): NCBI Taxonomy ID (e.g., "8208")
        - species_class (str): Taxonomic class (e.g., "Actinopterygii", "Mammalia")
        - gene_name (str): Gene symbol (e.g., "HSP70", empty string if no gene)
        - gene_id (str): NCBI Gene ID (e.g., "123456", empty string if no gene)
        CRITICAL: If paper has M species and N genes, create M×N dicts.
                  If no genes found, create M dicts with empty gene fields.
    gene_research_types : list
        List of confirmed research type classifications. Valid types:
        - "Gene Identification Analysis"
        - "Functional Annotation via Ortholog/Homolog Comparison"
        - "Gene Expression Analysis"
        - "Phylogenetic and Evolutionary Analysis"
        - "Functional Validation and Applied Research"
    output_path : str, optional
        Path to JSON database file (default: "papers_database.json")

    Returns
    -------
    dict
        Dictionary containing:
        - message: str - Success message
        - saved_data: dict - Summary of saved data (pmid, counts)
        - output_path: str - Path to the JSON file
        - status: str - "success" or "error"

    Workflow
    --------
    1. AI agent verifies species → query_ncbi_taxonomy(query=species_id) → species_name, species_class
    2. AI agent verifies genes → query_ncbi_gene(query=gene_name, species_id=...) → gene_id
    3. AI agent determines research_type → llm_extract_genes_from_scientific_text or rule-based
    4. Call this tool to save all verified data at once
    5. Data is appended to papers_database.json

    Examples
    --------
    >>> # Example 1: Single species + single gene
    >>> save_confirmed_paper_annotation(
    ...     pmid="12345678",
    ...     species_gene_list=[
    ...         {
    ...             "species_name": "Notothenia coriiceps",
    ...             "species_id": "8208",
    ...             "species_class": "Actinopterygii",
    ...             "gene_name": "HSP70",
    ...             "gene_id": "123456"
    ...         }
    ...     ],
    ...     gene_research_types=["Gene Expression Analysis"]
    ... )
    {
        "message": "Paper annotation saved successfully",
        "saved_data": {"pmid": "12345678", "n_species_gene_pairs": 1, "n_research_types": 1},
        "output_path": "papers_database.json",
        "status": "success"
    }

    >>> # Example 2: Single species + two genes (Cartesian product = 2 entries)
    >>> save_confirmed_paper_annotation(
    ...     pmid="87654321",
    ...     species_gene_list=[
    ...         {
    ...             "species_name": "Homo sapiens",
    ...             "species_id": "9606",
    ...             "species_class": "Mammalia",
    ...             "gene_name": "TP53",
    ...             "gene_id": "7157"
    ...         },
    ...         {
    ...             "species_name": "Homo sapiens",
    ...             "species_id": "9606",
    ...             "species_class": "Mammalia",
    ...             "gene_name": "BRCA1",
    ...             "gene_id": "672"
    ...         }
    ...     ],
    ...     gene_research_types=["Functional Validation and Applied Research"]
    ... )
    {
        "message": "Paper annotation saved successfully",
        "saved_data": {"pmid": "87654321", "n_species_gene_pairs": 2, "n_research_types": 1},
        "output_path": "papers_database.json",
        "status": "success"
    }
    """
    try:
        await asyncio.to_thread(
            get_paper_annotator().save_confirmed_annotation_data,
            pmid=pmid,
            species_gene_list=species_gene_list,
            gene_research_types=gene_research_types,
            output_path=output_path
        )

        return {
            "message": "Paper annotation saved successfully",
            "saved_data": {
                "pmid": str(pmid),
                "n_species_gene_pairs": len(species_gene_list),
                "n_research_types": len(gene_research_types)
            },
            "output_path": output_path,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}


if __name__ == "__main__":
    mcp.run()
