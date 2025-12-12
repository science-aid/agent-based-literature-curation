import json
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List

import pandas as pd
import requests
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI


class PaperAnnotator:
    def __init__(self, chunk_size: int = 25):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmids}"
        self.chunk_size = chunk_size

        # Load environment variables if .env file exists
        if os.path.exists(".env"):
            load_dotenv()

        # Skip logging setup for MCP server to avoid frequent re-initialization
        if not hasattr(self.__class__, "_logger_initialized"):
            self._setup_logging()
            self.__class__._logger_initialized = True  # type: ignore

    def _setup_logging(self):
        # 現在の作業ディレクトリを取得してログに出力
        current_dir = os.getcwd()

        # ログファイルが格納されるディレクトリを作成
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # ログファイル名（絶対パス）
        log_file_path = os.path.join(log_dir, "paper_annotator.log")
        absolute_log_path = os.path.abspath(log_file_path)

        # ロガーを取得
        self.logger = logging.getLogger("paper_annotator")
        self.logger.setLevel(logging.INFO)

        # 既存のハンドラーをクリア
        self.logger.handlers.clear()

        # ファイルハンドラーを追加
        file_handler = logging.FileHandler(log_file_path, mode="a")
        file_handler.setLevel(logging.INFO)

        # 日本時間を使用するカスタムフォーマッタ
        class JSTFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                # UTC時間を日本時間（JST, UTC+9）に変換
                utc_time = datetime.fromtimestamp(record.created, tz=timezone.utc)
                jst_time = utc_time.astimezone(timezone(timedelta(hours=9)))
                return jst_time.strftime("%Y-%m-%d %H:%M:%S JST")

        formatter = JSTFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 初期化時にログディレクトリとファイルパスを記録
        self.logger.info(f"Logger initialized - Working directory: {current_dir}")
        self.logger.info(f"Log file path: {absolute_log_path}")

    def get_text_by_tree(self, treepath, element):
        """
        Parameters:
        ------
        treepath: str
            path to the required information

        element: str
            tree element

        Returns:
        ------
        information: str
            parsed information from XML

        None: Null
            if information could not be parsed.

        """
        if element.find(treepath) is not None:
            return element.find(treepath).text
        else:
            return ""

    def query_taxonomy(self, query: str, query_type: str = "auto"):
        """
        Unified taxonomy query: ID<->Name conversion with auto-detection.

        Args:
            query (str): Taxonomy ID or species name
            query_type (str): "id_to_name", "name_to_id", or "auto" (default: "auto")

        Returns:
            str or dict:
                - If query_type is "id_to_name": dict with {"species_name": str, "class": str}
                  **Note**: Taxonomic class is only retrievable when input is taxonomy ID
                - If query_type is "name_to_id": str (taxonomy ID)

        Important:
            To get taxonomic class, you MUST provide a taxonomy ID (not species name).
            Workflow: species_name → taxonomy_id (name_to_id) → class (id_to_name)
        """
        if query_type == "auto":
            query_type = "id_to_name" if query.isdigit() else "name_to_id"

        if query_type == "id_to_name":
            return self.check_species_name_and_class_from_species_id(query)
        else:
            return self.check_species_id_from_species_name(query)

    def check_species_id_from_species_name(self, species_name: str) -> str:
        """
        Retrieve the NCBI Taxonomy ID for a given species name.

        This method queries the NCBI Taxonomy database using the E-utilities API
        to find the taxonomic ID corresponding to the provided species name.

        Parameters
        ----------
        species_name : str
            The scientific name of the species to look up in NCBI Taxonomy database.

        Returns
        -------
        str
            The NCBI Taxonomy ID for the species. Returns an empty string if no
            matching taxonomy ID is found or if the API request fails.

        Notes
        -----
        - Uses NCBI E-utilities esearch API with taxonomy database
        - Returns the first matching taxonomy ID if multiple results exist
        - Network connectivity is required for API access
        - Species name should be properly formatted (e.g., "Homo sapiens")

        Examples
        --------
        >>> finder = SpeciesFinder()
        >>> tax_id = finder.check_species_name_with_species_id("Homo sapiens")
        >>> print(tax_id)  # Expected: "9606"
        """
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=taxonomy&term="
        url = base_url + species_name
        self.logger.info(f"get taxonomyID: {url}")
        response = requests.get(url)
        tree = ET.fromstring(response.text)
        species_id = self.get_text_by_tree("./IdList/Id", tree)
        return species_id

    def list_dict_to_csv(self, data: List[dict], output_path: str) -> None:
        """
        Save a list of dictionaries to a CSV file.

        This method converts a list of dictionaries to a pandas DataFrame and
        saves it to a CSV file with proper formatting and logging of the operation.

        Parameters
        ----------
        data : List[dict]
            List of dictionaries to save to CSV. All dictionaries should have
            the same keys to ensure proper column alignment.
        output_path : str
            Path where the CSV file should be saved.

        Returns
        -------
        None

        Notes
        -----
        - The CSV file is saved without row indices (index=False)
        - The operation is logged for tracking purposes
        - Any existing file at the output path will be overwritten
        - If the data list is empty, an empty CSV with no columns will be created
        """
        if not data:
            # Create empty DataFrame if no data
            df = pd.DataFrame()
            self.logger.warning(f"No data provided for CSV export to: {output_path}")
        else:
            df = pd.DataFrame(data)

        df.to_csv(output_path, index=False)
        self.logger.info(
            f"Data saved to CSV: {output_path} ({len(df)} rows, {len(df.columns)} columns)"
        )
        print(f"Data saved to: {output_path}")

    def check_species_name_and_class_from_species_id(self, species_id: str) -> dict:
        """
        TODO 1: Retrieve species name and taxonomic class from NCBI Taxonomy ID.

        Args:
            species_id (str): NCBI Taxonomy ID

        Returns:
            dict: {
                "species_name": str,  # Species scientific name
                "class": str          # Taxonomic class from lineage
            }
            Returns empty strings for both if not found.
        """
        base_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&id={species_id}"
        self.logger.info(f"get species name and class from ID: {base_url}")

        result = {"species_name": "", "class": ""}

        try:
            response = requests.get(base_url, timeout=30)
            tree = ET.fromstring(response.text)

            # Get species name
            species_name = self.get_text_by_tree("./Taxon/ScientificName", tree)
            result["species_name"] = species_name

            # Get class from LineageEx
            lineage_ex = tree.find("./Taxon/LineageEx")
            if lineage_ex is not None:
                for taxon in lineage_ex.findall("Taxon"):
                    rank = taxon.find("Rank")
                    if rank is not None and rank.text == "class":
                        scientific_name = taxon.find("ScientificName")
                        if scientific_name is not None and scientific_name.text:
                            result["class"] = scientific_name.text
                            break

            return result
        except Exception as e:
            self.logger.error(f"Failed to get species info for ID {species_id}: {e}")
            return result

    def query_gene(
        self, query: str, query_type: str = "auto", species_id: str = ""
    ) -> dict:
        """
        Unified gene query: supports multiple query patterns.

        Args:
            query (str): Gene ID, gene name, or species+gene combination
            query_type (str): "id_to_info", "id_to_name", "species_and_name_to_id", or "auto"
            species_id (str): Required for "species_and_name_to_id" or when query_type is "auto" with gene name

        Returns:
            dict: {"gene_id": str, "gene_name": str, "description": str, "ensembl_id": str, "synonyms": list}

        Examples:
            # Get gene info from gene ID
            >>> query_gene(query="7157", query_type="id_to_info")
            {"gene_id": "7157", "gene_name": "TP53", ...}

            # Get gene ID from species + gene name (taxonomy_id + gene_name → gene_id)
            >>> query_gene(query="TP53", query_type="species_and_name_to_id", species_id="9606")
            {"gene_id": "7157", "gene_name": "TP53", ...}

            # Auto-detect (gene ID)
            >>> query_gene(query="7157")
            {"gene_id": "7157", "gene_name": "TP53", ...}

            # Auto-detect (gene name + species_id)
            >>> query_gene(query="TP53", species_id="9606")
            {"gene_id": "7157", "gene_name": "TP53", ...}
        """
        result = {
            "gene_id": "",
            "gene_name": "",
            "description": "",
            "ensembl_id": "",
            "synonyms": [],
        }

        # Auto-detect query type
        if query_type == "auto":
            if query.isdigit():
                query_type = "id_to_info"
            elif species_id:
                query_type = "species_and_name_to_id"
            else:
                self.logger.error("Auto-detection failed: provide species_id or gene_id")
                return result

        # Process based on query type
        if query_type == "species_and_name_to_id":
            if not species_id:
                self.logger.error("species_id required for species_and_name_to_id")
                return result
            gene_id = self.get_gene_id_from_species_and_gene_name(species_id, query)
            result["gene_id"] = gene_id
            if gene_id:
                info = self.get_gene_info_from_gene_id(gene_id)
                result.update(info)
                result["gene_name"] = info.get("locus", "")

        elif query_type == "id_to_name":
            result["gene_name"] = self.get_gene_name_from_gene_id(query)
            result["gene_id"] = query

        elif query_type == "id_to_info":
            info = self.get_gene_info_from_gene_id(query)
            result.update(info)
            result["gene_id"] = query
            result["gene_name"] = info.get("locus", "")

        return result

    def get_gene_id_from_species_and_gene_name(
        self, species_id: str, gene_name: str
    ) -> str:
        """
        TODO 2-1: Get gene ID from species ID and gene name.

        Args:
            species_id (str): NCBI Taxonomy ID
            gene_name (str): Gene name

        Returns:
            str: Gene ID, empty string if not found
        """
        base_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene_name}[Gene Name]+AND+txid{species_id}[Organism]"
        self.logger.info(f"get gene ID: {base_url}")

        try:
            response = requests.get(base_url, timeout=30)
            tree = ET.fromstring(response.text)
            gene_id = self.get_text_by_tree("./IdList/Id", tree)
            return gene_id
        except Exception as e:
            self.logger.error(
                f"Failed to get gene ID for {gene_name} in species {species_id}: {e}"
            )
            return ""

    def get_gene_name_from_gene_id(self, gene_id: str) -> str:
        """
        TODO 2-2: Get gene name from gene ID.

        Args:
            gene_id (str): NCBI Gene ID

        Returns:
            str: Gene name, empty string if not found
        """
        gene_info = self.get_gene_info_from_gene_id(gene_id)
        return gene_info.get("locus", "")

    def get_gene_info_from_gene_id(self, gene_id: str) -> dict:
        """
        Get detailed gene information from gene ID.

        Args:
            gene_id (str): NCBI Gene ID

        Returns:
            dict: {
                "locus": str,           # Gene symbol (e.g., "TP53")
                "description": str,     # Gene description
                "ensembl_id": str,     # Ensembl ID (e.g., "ENSG00000141510")
                "synonyms": list       # List of gene synonyms
            }
        """
        base_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=gene&id={gene_id}&retmode=xml"
        self.logger.info(f"get gene info from ID: {base_url}")

        result = {"locus": "", "description": "", "ensembl_id": "", "synonyms": []}

        try:
            response = requests.get(base_url, timeout=30)
            response.raise_for_status()

            # Parse XML
            tree = ET.fromstring(response.text)

            # Extract locus (gene symbol)
            for elem in tree.iter():
                if "Gene-ref_locus" in elem.tag and elem.text:
                    result["locus"] = elem.text
                    break

            # Extract description
            for elem in tree.iter():
                if "Gene-ref_desc" in elem.tag and elem.text:
                    result["description"] = elem.text
                    break

            # Extract synonyms - they are in Gene-ref_syn_E elements
            synonyms_found = set()  # Use set to avoid duplicates
            for elem in tree.iter():
                # Look for Gene-ref_syn_E tags which contain individual synonyms
                if "Gene-ref_syn_E" in elem.tag and elem.text and elem.text.strip():
                    synonyms_found.add(elem.text.strip())
            result["synonyms"] = list(synonyms_found)

            # Extract Ensembl ID from database references
            for elem in tree.iter():
                if "Dbtag_db" in elem.tag and elem.text == "Ensembl":
                    # Find the sibling tag element
                    parent = None
                    for p in tree.iter():
                        if elem in list(p):
                            parent = p
                            break
                    if parent is not None:
                        for tag_elem in parent.iter():
                            if "Dbtag_tag" in tag_elem.tag:
                                for id_elem in tag_elem.iter():
                                    if "Object-id_str" in id_elem.tag and id_elem.text:
                                        result["ensembl_id"] = id_elem.text
                                        break
                    if result["ensembl_id"]:
                        break

            self.logger.info(
                f"Found gene info: locus={result['locus']}, ensembl={result['ensembl_id']}, synonyms={len(result['synonyms'])}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Failed to get gene info for ID {gene_id}: {e}")
            return result

#     def analyze_gene_mention_by_llm(
#         self, scientifictexts: str, model_name: str = "gpt-5-mini-2025-08-07"
#     ) -> dict:
#         """
#         Analyze species, taxonomic class, genes, and research type in scientific text using LLM.

#         Args:
#             scientifictexts (str): Scientific text (title, abstract, or MeSH)
#             model_name (str): LLM model name (default: "gpt-5-mini-2025-08-07")

#         Returns:
#             dict: {
#                 "species_names": list[str],    # Target organism names
#                 "species_classes": list[str],  # Taxonomic class of organisms
#                 "gene_names": list[str],       # Target gene names/symbols
#                 "study_type": str,             # Primary research type
#                 "confidence": str              # "high" or "low"
#             }
#         """

#         system_prompt = """You are an expert biology curator in identifying research targets in scientific literature, particularly for non-model organisms.

# Your task: Analyze the scientific text and identify:
# 1. Target organism(s) - species/organism studied (include both common and scientific names if mentioned)
# 2. Target organism categories (class) - taxonomic class of the organisms (e.g., Mammalia, Actinopterygii, Insecta)
# 3. Target gene(s) - specific genes investigated (extract exact symbols/names as written)
# 4. Gene research type - classify into ONE primary category

# CRITICAL RULES:
# - Output ONLY valid JSON, no additional text
# - Extract information ONLY from the provided text
# - Do NOT guess, infer, or hallucinate information
# - For non-model organisms, preserve exact species names as written
# - For organism categories, identify the taxonomic class if possible (e.g., mammals → Mammalia, fish → Actinopterygii)
# - If information is unclear or absent, use "Not Found"

# VALID RESEARCH TYPE CATEGORIES (select ONE primary type):
# 1. "Gene Identification Analysis" - Genome sequencing and gene identification to determine the location and structure of genes
# 2. "Functional Annotation via Ortholog/Homolog Comparison" - Functional prediction of genes based on sequence homology and orthology with known organisms
# 3. "Gene Expression Analysis" - Analysis of gene expression profiles across tissues or conditions using transcriptomic approaches
# 4. "Phylogenetic and Evolutionary Analysis" - Investigation of gene family expansion, contraction, and evolutionary adaptation
# 5. "Functional Validation and Applied Research" - Experimental validation of gene function using methods such as CRISPR or RNA interference

# OUTPUT FORMAT (strict JSON):
# {
#   "species_names": ["exact species name from text"],
#   "species_classes": ["taxonomic class of organism"],
#   "gene_names": ["exact gene symbol/name from text"],
#   "study_type": "one of the 5 categories above",
#   "confidence": "high or low"
# }

# EXAMPLES:

# Input: "Expression of heat shock protein 70 (HSP70) in the Antarctic fish Notothenia coriiceps under thermal stress"
# Output:
# {
#   "species_names": ["Notothenia coriiceps", "Antarctic fish"],
#   "species_classes": ["Actinopterygii"],
#   "gene_names": ["HSP70", "heat shock protein 70"],
#   "study_type": "Gene Expression Analysis",
#   "confidence": "high"
# }

# Input: "Genome-wide identification of AP2/ERF transcription factors in bamboo"
# Output:
# {
#   "species_names": ["bamboo"],
#   "species_classes": ["Liliopsida"],
#   "gene_names": ["AP2/ERF"],
#   "study_type": "Gene Identification Analysis",
#   "confidence": "high"
# }

# Input: "Functional characterization of CRISPR-mediated knockout of the MYC gene in human cell lines"
# Output:
# {
#   "species_names": ["human", "Homo sapiens"],
#   "species_classes": ["Mammalia"],
#   "gene_names": ["MYC"],
#   "study_type": "Functional Validation and Applied Research",
#   "confidence": "high"
# }"""

#         if model_name.startswith("gpt-oss") or model_name.startswith("llama"):
#             print(f"Using Ollama model: {model_name}")
#             llm = ChatOpenAI(
#                 base_url="http://host.docker.internal:11434/v1",
#                 api_key="ollama",  # type: ignore
#                 model=model_name,
#             )
#             messages = [
#                 SystemMessage(content=system_prompt),
#                 HumanMessage(content=scientifictexts),
#             ]
#             response = llm.invoke(messages)
#             result = response.content
#             self.logger.info(
#                 f"texts: {scientifictexts} - Ollama gene analysis: {result}"
#             )
#         else:
#             print(f"Using OpenAI model: {model_name}")
#             client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#             response = client.chat.completions.create(
#                 model=model_name,
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": scientifictexts},
#                 ],
#             )
#             result = response.choices[0].message.content
#             self.logger.info(
#                 f"texts: {scientifictexts} - OpenAI gene analysis: {result}"
#             )

#         # Parse JSON result
#         if result is None:
#             llm_result = {
#                 "species_names": ["ERROR"],
#                 "species_classes": ["ERROR"],
#                 "gene_names": ["ERROR"],
#                 "study_type": "ERROR",
#                 "confidence": "low",
#             }
#         else:
#             cleaned_result = result if isinstance(result, str) else ""
#             cleaned_result = cleaned_result.strip()
#             if cleaned_result.startswith("```json"):
#                 cleaned_result = cleaned_result[7:]
#             if cleaned_result.startswith("```"):
#                 cleaned_result = cleaned_result[3:]
#             if cleaned_result.endswith("```"):
#                 cleaned_result = cleaned_result[:-3]
#             cleaned_result = cleaned_result.strip()

#             try:
#                 llm_result = json.loads(cleaned_result)
#             except json.JSONDecodeError as e:
#                 self.logger.error(f"JSON parsing failed for gene analysis: {e}")
#                 self.logger.error(f"Raw result: {cleaned_result}")
#                 llm_result = {
#                     "species_names": ["ERROR"],
#                     "species_classes": ["ERROR"],
#                     "gene_names": ["ERROR"],
#                     "study_type": f"ERROR: {str(e)}",
#                     "confidence": "low",
#                 }

#         return {
#             "species_names": llm_result.get("species_names", ["Not Found"]),
#             "species_classes": llm_result.get("species_classes", ["Not Found"]),
#             "gene_names": llm_result.get("gene_names", ["Not Found"]),
#             "study_type": llm_result.get("study_type", "Not Found"),
#             "confidence": llm_result.get("confidence", "low"),
#         }

    def save_confirmed_annotation_data(
        self,
        pmid: str,
        species_gene_list: list[dict],
        gene_research_types: list[str],
        output_path: str = "papers_database.json"
    ) -> None:
        """
        Save confirmed paper annotation data to JSON database after AI agent verification.

        This function is designed for AI agents to save paper annotation results after
        verifying species, genes, and research types through MCP tools (query_ncbi_taxonomy,
        query_ncbi_gene). It saves the species_gene_list directly without modification.

        Args:
            pmid (str): Paper ID (PubMed ID)
            species_gene_list (list[dict]): Verified species and gene information (Cartesian product)
                Each dict contains ONE (species, gene) pair:
                - species_name (str): Scientific name
                - species_id (str): NCBI Taxonomy ID
                - species_class (str): Taxonomic class (e.g., Mammalia, Actinopterygii)
                - gene_name (str): Gene symbol (empty string if no gene)
                - gene_id (str): NCBI Gene ID (empty string if no gene)
            gene_research_types (list[str]): Confirmed research type classifications
                Valid types: "Gene Identification Analysis", "Functional Annotation via Ortholog/Homolog Comparison",
                "Gene Expression Analysis", "Phylogenetic and Evolutionary Analysis",
                "Functional Validation and Applied Research"
            output_path (str): Path to JSON database file (default: "papers_database.json")

        Returns:
            None

        Workflow:
            1. AI agent verifies species with query_ncbi_taxonomy → species_id, species_class
            2. AI agent verifies genes with query_ncbi_gene → gene_id
            3. AI agent constructs species_gene_list as Cartesian product of (species, gene) pairs
            4. Call this function to save verified data
            5. Data is appended to papers_database.json

        Example:
            >>> # After AI agent verification
            >>> save_confirmed_annotation_data(
            ...     pmid="12345678",
            ...     species_gene_list=[
            ...         {
            ...             "species_name": "Notothenia coriiceps",
            ...             "species_id": "8208",
            ...             "species_class": "Actinopterygii",
            ...             "gene_name": "HSP70",
            ...             "gene_id": "123456"
            ...         },
            ...         {
            ...             "species_name": "Notothenia coriiceps",
            ...             "species_id": "8208",
            ...             "species_class": "Actinopterygii",
            ...             "gene_name": "HSP90",
            ...             "gene_id": "789012"
            ...         }
            ...     ],
            ...     gene_research_types=["Gene Expression Analysis"]
            ... )
        """
        paper_data = {
            "pmid": str(pmid),
            "species_gene_list": species_gene_list,
            "gene_research_type": gene_research_types
        }
        self.add_paper_to_json(paper_data, output_path)

    def add_paper_to_json(self, paper_data: dict, output_path: str = "papers_database.json") -> None:
        """
        Add paper data to JSON file (append mode).

        Args:
            paper_data (dict): Paper information with the following structure:
                {
                    "pmid": str/int - Paper ID
                    "species_gene_list": list[dict] - List of {
                        "species_name": str,
                        "species_id": str,
                        "species_class": str,
                        "gene_name": str,
                        "gene_id": str
                    }
                    "gene_research_type": list[str] - List of research type strings
                }
            output_path (str): Path to JSON file (default: papers_database.json)

        Returns:
            None
        """
        # Ensure pmid is string
        paper_data["pmid"] = str(paper_data.get("pmid", ""))

        # Load existing data or create new list
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    database = json.load(f)
                    if not isinstance(database, list):
                        self.logger.warning(f"Existing file {output_path} is not a list. Creating new list.")
                        database = []
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse existing JSON file: {e}. Creating new list.")
                database = []
        else:
            database = []

        # Check for duplicate PMIDs
        existing_pmids = {entry.get("pmid") for entry in database}
        if paper_data["pmid"] in existing_pmids:
            self.logger.warning(f"PMID {paper_data['pmid']} already exists in database. Skipping.")
            return

        # Append new paper data
        database.append(paper_data)

        # Save to JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)

        self.logger.info(
            f"Added paper to {output_path}: pmid={paper_data['pmid']}, "
            f"species_gene_pairs={len(paper_data.get('species_gene_list', []))}, "
            f"research_types={len(paper_data.get('gene_research_type', []))}"
        )
        print(f"Paper data saved to: {output_path} (PMID: {paper_data['pmid']})")


if __name__ == "__main__":
    # Test PaperAnnotator's 4 core functions
    annotator = PaperAnnotator()

    print("=" * 80)
    print("PaperAnnotator - Testing Core Functions")
    print("=" * 80)

    # Test 1: query_taxonomy - Unified taxonomy query
    print("\n[Test 1] query_taxonomy - NCBI Taxonomy ID <-> Name conversion")

    # ID to Name
    taxonomy_id = "9606"
    print(f"\n  Input: query='{taxonomy_id}', query_type='auto'")
    result = annotator.query_taxonomy(taxonomy_id, query_type="auto")
    print(f"  Output: {result}")

    # Name to ID
    species_name = "Mus musculus"
    print(f"\n  Input: query='{species_name}', query_type='auto'")
    result = annotator.query_taxonomy(species_name, query_type="auto")
    print(f"  Output: {result}")

    # Test 2: query_gene - Unified gene query
    print("\n[Test 2] query_gene - NCBI Gene information lookup")

    # Gene ID to full info
    gene_id = "7157"  # TP53
    print(f"\n  Input: query='{gene_id}', query_type='auto'")
    result = annotator.query_gene(gene_id, query_type="auto")
    print("  Output:")
    print(f"    gene_id: {result.get('gene_id')}")
    print(f"    gene_name: {result.get('gene_name')}")
    print(f"    description: {result.get('description', 'N/A')[:60]}...")
    print(f"    ensembl_id: {result.get('ensembl_id')}")
    print(f"    synonyms: {result.get('synonyms', [])[:3]}")

    # Species + gene name to ID
    print("\n  Input: query='BRCA1', species_id='9606', query_type='auto'")
    result = annotator.query_gene("BRCA1", query_type="auto", species_id="9606")
    print(f"  Output: gene_id={result.get('gene_id')}, gene_name={result.get('gene_name')}")


    # Test 5: add_paper_to_json - Save to JSON database (DEPRECATED - Use save_confirmed_annotation_data instead)
    print("\n[Test 5] add_paper_to_json - JSON database (DEPRECATED)")
    print("  Note: This test uses the old format. Use save_confirmed_annotation_data (Test 6) for new format.")

    # Test 6: save_confirmed_annotation_data - Main annotation save function
    print("\n[Test 6] save_confirmed_annotation_data - Save confirmed annotation data")
    print("\n  This function saves species_gene_list directly without modification")

    # Clean up old test file
    test_output = "test_confirmed_annotations.json"
    if os.path.exists(test_output):
        os.remove(test_output)
        print(f"  ✓ Removed old test file: {test_output}")

    # Test 6a: Single species + gene
    print("\n[Test 6a] Single species + gene")
    species_gene_list_1 = [
        {
            "species_name": "Danio rerio",
            "species_id": "7955",
            "species_class": "Actinopterygii",
            "gene_name": "tp53",
            "gene_id": "30590"
        }
    ]
    gene_research_types_1 = ["Gene Expression Analysis"]

    print(f"  Input:")
    print(f"    pmid: '99999001'")
    print(f"    species_gene_list: {species_gene_list_1}")
    print(f"    gene_research_types: {gene_research_types_1}")
    print(f"    output_path: {test_output}")

    try:
        annotator.save_confirmed_annotation_data(
            pmid="99999001",
            species_gene_list=species_gene_list_1,
            gene_research_types=gene_research_types_1,
            output_path=test_output
        )
        print("  ✓ Data saved successfully")

        # Verify saved data
        with open(test_output, "r", encoding="utf-8") as f:
            database = json.load(f)
        print(f"  Database contains {len(database)} entry(ies)")

        entry = database[-1]
        print(f"\n  Saved entry:")
        print(f"    pmid: {entry['pmid']}")
        print(f"    species_gene_list: {entry['species_gene_list']}")
        print(f"    gene_research_type: {entry['gene_research_type']}")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 6b: Multiple species + genes (Cartesian product)
    print("\n[Test 6b] Multiple species + genes (Cartesian product)")
    species_gene_list_2 = [
        {
            "species_name": "Homo sapiens",
            "species_id": "9606",
            "species_class": "Mammalia",
            "gene_name": "TP53",
            "gene_id": "7157"
        },
        {
            "species_name": "Homo sapiens",  # Duplicate species (should be deduplicated)
            "species_id": "9606",
            "species_class": "Mammalia",
            "gene_name": "BRCA1",
            "gene_id": "672"
        },
        {
            "species_name": "Mus musculus",
            "species_id": "10090",
            "species_class": "Mammalia",
            "gene_name": "Tp53",
            "gene_id": "22059"
        },
        {
            "species_name": "Mus musculus",  # Duplicate species (should be deduplicated)
            "species_id": "10090",
            "species_class": "Mammalia",
            "gene_name": "Brca1",
            "gene_id": "12190"
        }
    ]
    gene_research_types_2 = [
        "Functional Annotation via Ortholog/Homolog Comparison",
        "Phylogenetic and Evolutionary Analysis"
    ]

    print(f"  Input:")
    print(f"    pmid: '99999002'")
    print(f"    species_gene_list: {len(species_gene_list_2)} items (2 species × 2 genes = 4 entries)")
    print(f"    gene_research_types: {gene_research_types_2}")

    try:
        annotator.save_confirmed_annotation_data(
            pmid="99999002",
            species_gene_list=species_gene_list_2,
            gene_research_types=gene_research_types_2,
            output_path=test_output
        )
        print("  ✓ Data saved successfully")

        # Verify saved data
        with open(test_output, "r", encoding="utf-8") as f:
            database = json.load(f)
        print(f"  Database contains {len(database)} entry(ies)")

        entry = database[-1]
        print(f"\n  Saved entry:")
        print(f"    pmid: {entry['pmid']}")
        print(f"    species_gene_list entries: {len(entry['species_gene_list'])} (should be 4)")
        print(f"    research_types: {entry['gene_research_type']}")
        print(f"\n    Full species_gene_list:")
        for i, item in enumerate(entry['species_gene_list'], 1):
            print(f"      [{i}] {item['species_name']} ({item['species_id']}) + {item['gene_name']} ({item['gene_id']})")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 6c: Edge case - Empty gene_id (should be kept with empty gene fields)
    print("\n[Test 6c] Edge case - Empty gene_id (species only)")
    species_gene_list_3 = [
        {
            "species_name": "Unknown species",
            "species_id": "",  # Empty species_id
            "species_class": "",
            "gene_name": "unknown_gene",
            "gene_id": ""  # Empty gene_id
        },
        {
            "species_name": "Danio rerio",
            "species_id": "7955",
            "species_class": "Actinopterygii",
            "gene_name": "tp53",
            "gene_id": "30590"
        }
    ]
    gene_research_types_3 = ["Gene Identification Analysis"]

    print(f"  Input: 2 items (1 with empty IDs, 1 valid)")

    try:
        annotator.save_confirmed_annotation_data(
            pmid="99999003",
            species_gene_list=species_gene_list_3,
            gene_research_types=gene_research_types_3,
            output_path=test_output
        )
        print("  ✓ Data saved successfully")

        # Verify saved data
        with open(test_output, "r", encoding="utf-8") as f:
            database = json.load(f)

        entry = database[-1]
        print(f"\n  Saved entry:")
        print(f"    species_gene_list entries: {len(entry['species_gene_list'])} (should be 2)")
        print(f"    All entries saved (including ones with empty IDs):")
        for i, item in enumerate(entry['species_gene_list'], 1):
            print(f"      [{i}] species='{item['species_name']}' (ID:{item['species_id']}), gene='{item['gene_name']}' (ID:{item['gene_id']})")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 6d: Duplicate PMID check
    print("\n[Test 6d] Duplicate PMID check")
    print(f"  Attempting to add duplicate PMID: 99999001")

    try:
        annotator.save_confirmed_annotation_data(
            pmid="99999001",  # Duplicate from Test 6a
            species_gene_list=species_gene_list_1,
            gene_research_types=gene_research_types_1,
            output_path=test_output
        )
        print("  ✓ Duplicate check working (entry should be skipped)")

        # Verify no duplicate was added
        with open(test_output, "r", encoding="utf-8") as f:
            database = json.load(f)
        print(f"  Database still contains {len(database)} entry(ies) (should be 3, not 4)")
    except Exception as e:
        print(f"  Error: {e}")

    # Display full database
    print("\n  Full database (pretty print):")
    try:
        with open(test_output, "r", encoding="utf-8") as f:
            database = json.load(f)
        print(json.dumps(database, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"  Error reading database: {e}")

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
