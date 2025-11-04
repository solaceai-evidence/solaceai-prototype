# LLM Prompt Usage by Pipeline Stage

This document maps which LLM prompts are used in each pipeline stage. All prompts are defined in the codebase and referenced by name for easy lookup.

## Purpose

For non-technical team members to understand:
- Which stages use AI/LLM processing vs algorithmic processing
- What each prompt does conceptually
- How to find the actual prompt content in the codebase

## Pipeline Stages and Their Prompts

### Stage 1: Query Decomposition

**Uses LLM:** ✅ Yes

**Prompts Used:**
- `QUERY_DECOMPOSER_PROMPT` (from `solaceai.llms.prompts`)
  - **Purpose:** Analyzes user query and extracts structured search parameters
  - **Inputs:** Raw user query
  - **Outputs:** 
    - Rewritten query (simplified version)
    - Keyword query (search-optimized version)
    - Search filters (year, venue, authors, fields of study)

**Example Output:**
```
LLM PROMPTS USED:
  QUERY_DECOMPOSER_PROMPT (from solaceai.llms.prompts)
     Purpose: Analyzes query and extracts structured search parameters
     Outputs: Rewritten query, keyword query, and search filters
```

---

### Stage 2: Document Retrieval

**Uses LLM:** ✅ Yes (but only via Stage 1)

**Prompts Used:**
- Uses decomposed query from Stage 1 (`QUERY_DECOMPOSER_PROMPT`)
- No additional prompts in Stage 2 itself

**Note:** This stage performs pure retrieval operations using the decomposed query from Stage 1. It searches academic databases and ranks results algorithmically.

**Example Output:**
```
STEP 1: QUERY DECOMPOSITION

LLM Prompt: QUERY_DECOMPOSER_PROMPT (from solaceai.llms.prompts)
```

---

### Stage 3: Reranking & Aggregation

**Uses LLM:** ❌ No

**Prompts Used:** None

**Note:** This stage uses pure algorithmic reranking and aggregation. No LLM calls are made. It processes the retrieved papers from Stage 2 using scoring algorithms.

**Example Output:**
```
NOTE: Stage 3 uses no LLM prompts
   This stage performs pure algorithmic reranking and aggregation
   LLM was only used in Stage 1 (QUERY_DECOMPOSER_PROMPT)
```

---

### Stage 4: Evidence Extraction

**Uses LLM:** ✅ Yes

**Prompts Used:**
- `SYSTEM_PROMPT_QUOTE_PER_PAPER` (from `solaceai.llms.prompts`)
  - **Purpose:** Extracts relevant evidence quotes from each paper
  - **Inputs:** User query + paper content (title, abstract, snippets)
  - **Outputs:** Direct text excerpts that answer the query (or "None" if no relevant content)
  - **Processing:** Runs in parallel across multiple papers using batch LLM calls

**Example Output:**
```
LLM PROMPTS USED:
   SYSTEM_PROMPT_QUOTE_PER_PAPER (from solaceai.llms.prompts)
   Purpose: Extracts relevant evidence quotes from each paper
   Outputs: Direct text excerpts that answer the query
```

---

### Stage 5: Section Generation

**Uses LLM:** ✅ Yes (Multiple prompts)

**Prompts Used:**

1. **`SYSTEM_PROMPT_QUOTE_PER_PAPER`** (from `solaceai.llms.prompts`)
   - Used in sub-stage 4 (evidence extraction)
   - **Purpose:** Extracts evidence quotes from papers
   
2. **`SYSTEM_PROMPT_QUOTE_CLUSTER`** (from `solaceai.llms.prompts`)
   - **Purpose:** Groups quotes into thematic dimensions/sections
   - **Inputs:** All extracted quotes from papers
   - **Outputs:** Structured plan with section names and quote assignments
   - **Example sections:** "Introduction", "Methods Comparison", "Results Analysis"

3. **`PROMPT_ASSEMBLE_SUMMARY`** (from `solaceai.llms.prompts`)
   - **Purpose:** Generates narrative text for each section
   - **Inputs:** Section name, assigned quotes, previously written sections
   - **Outputs:** Final written sections with inline citations
   - **Format:** Produces both synthesis paragraphs and bulleted lists

**Example Output:**
```
LLM PROMPTS USED:
   1. SYSTEM_PROMPT_QUOTE_PER_PAPER (from solaceai.llms.prompts)
      Stage 4 - Extracts evidence quotes from papers
   2. SYSTEM_PROMPT_QUOTE_CLUSTER (from solaceai.llms.prompts)
      Purpose: Groups quotes into thematic dimensions
      Outputs: Structured plan with sections and quote assignments
   3. PROMPT_ASSEMBLE_SUMMARY (from solaceai.llms.prompts)
      Purpose: Generates narrative text for each section
      Outputs: Final written sections with citations
```

---

### Stage 6: Table Generation

**Uses LLM:** ✅ Yes (Multiple prompts)

**Prompts Used:**

1. **`ATTRIBUTE_PROMPT`** (from `solaceai.table_generation.prompts`)
   - **Purpose:** Identifies attributes/columns for comparing papers
   - **Inputs:** Query + paper titles and abstracts
   - **Outputs:** Column definitions with descriptions (JSON format)
   - **Example columns:** "Dataset Used", "Model Architecture", "Performance Metrics"

2. **`VALUE_GENERATION_FROM_ABSTRACT`** (from `solaceai.table_generation.prompts`)
   - **Purpose:** Extracts values from paper abstracts for each column
   - **Inputs:** Paper abstract + column question
   - **Outputs:** Brief phrases (<10 words) or "N/A" if not found
   - **Constraint:** Must be concise and fact-based

3. **`VALUE_CONSISTENCY_PROMPT_ZS`** (from `solaceai.table_generation.prompts`)
   - **Purpose:** Ensures consistent formatting across all table cells
   - **Inputs:** Column name + all extracted values
   - **Outputs:** Standardized values in JSON format
   - **Example:** Converts "2020", "2020-2021", "last year" → consistent format

**Example Output:**
```
LLM PROMPTS USED IN STAGE 6:
   1. ATTRIBUTE_PROMPT (from solaceai.table_generation.prompts)
      Purpose: Identifies attributes for comparing papers
      Outputs: Column definitions with descriptions
   2. VALUE_GENERATION_FROM_ABSTRACT (from solaceai.table_generation.prompts)
      Purpose: Extracts values from paper abstracts for each column
      Outputs: Brief phrases (<10 words) or 'N/A'
   3. VALUE_CONSISTENCY_PROMPT_ZS (from solaceai.table_generation.prompts)
      Purpose: Ensures consistent formatting across table cells
      Outputs: Standardized values in JSON format
```

---

## Summary Table

| Stage | Uses LLM? | Number of Prompts | Prompt Names |
|-------|-----------|-------------------|--------------|
| **1. Query Decomposition** | ✅ Yes | 1 | `QUERY_DECOMPOSER_PROMPT` |
| **2. Document Retrieval** | ➖ Indirect | 0 (uses Stage 1) | (none) |
| **3. Reranking & Aggregation** | ❌ No | 0 | (none) |
| **4. Evidence Extraction** | ✅ Yes | 1 | `SYSTEM_PROMPT_QUOTE_PER_PAPER` |
| **5. Section Generation** | ✅ Yes | 3 | `SYSTEM_PROMPT_QUOTE_PER_PAPER`<br>`SYSTEM_PROMPT_QUOTE_CLUSTER`<br>`PROMPT_ASSEMBLE_SUMMARY` |
| **6. Table Generation** | ✅ Yes | 3 | `ATTRIBUTE_PROMPT`<br>`VALUE_GENERATION_FROM_ABSTRACT`<br>`VALUE_CONSISTENCY_PROMPT_ZS` |

---

## How to Find Prompt Content

### For `solaceai.llms.prompts` (Stages 1-5):
**File Location:** `/api/solaceai/llms/prompts.py`

Contains these prompts:
- `QUERY_DECOMPOSER_PROMPT`
- `SYSTEM_PROMPT_QUOTE_PER_PAPER`
- `SYSTEM_PROMPT_QUOTE_CLUSTER`
- `PROMPT_ASSEMBLE_SUMMARY`
- `USER_PROMPT_PAPER_LIST_FORMAT`
- `USER_PROMPT_QUOTE_LIST_FORMAT`

### For `solaceai.table_generation.prompts` (Stage 6):
**File Location:** `/api/solaceai/table_generation/prompts.py`

Contains these prompts:
- `SYSTEM_PROMPT`
- `ATTRIBUTE_PROMPT`
- `VALUE_GENERATION_FROM_ABSTRACT`
- `VALUE_GENERATION_FROM_METADATA`
- `VALUE_CONSISTENCY_PROMPT_ZS`
- `VALUE_CONSISTENCY_PROMPT_FS`
- `VESPAQA_PROMPT`

---

## Updated Test Scripts

All test scripts now display prompt information when running:

```bash
# Run any stage to see prompt information in output
python run_pipeline_stage1.py --query "your question"
python run_pipeline_stage2.py --query "your question"
python run_pipeline_stage3.py --query "your question"
python run_pipeline_stage4.py --query "your question"
python run_pipeline_stage5.py --query "your question"
python run_pipeline_stage6.py --query "your question"
```

Each script will now show:
- Which prompts are being used
- The purpose of each prompt
- What outputs to expect

This makes the pipeline transparent for both technical and non-technical team members.

---

## Notes for Non-Technical Team Members

### What is an LLM Prompt?
A prompt is the instruction text sent to an AI language model (like Claude or GPT) telling it what task to perform. Think of it as a detailed job description for the AI.

### Why Document Prompt Names?
- **Transparency:** Team members can see when AI is being used vs when it's pure algorithms
- **Reproducibility:** Knowing which prompt was used helps explain results
- **Debugging:** If output quality changes, we know which prompt to review
- **Collaboration:** Engineers and researchers can discuss specific prompts by name

### How AI is Used in the Pipeline:
- **Stage 1:** AI understands your question and extracts search filters (like "recent papers" → 2022-2025)
- **Stage 2-3:** No AI, just database search and algorithmic ranking
- **Stage 4:** AI reads each paper and pulls out relevant quotes
- **Stage 5:** AI organizes quotes into themes and writes coherent sections
- **Stage 6:** AI identifies comparison dimensions and fills in table cells

This hybrid approach combines the best of both:
- **AI** for understanding language and generating text
- **Algorithms** for fast, reliable retrieval and ranking
