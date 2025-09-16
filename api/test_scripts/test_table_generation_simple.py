#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Test for ScholarQA Pipeline Stage 6: Table GenerationTest for ScholarQA Pipeline Stage 6: Table Generation

Shows key steps in table generation process using semantic search and LLMShows key steps in table generation process using semantic search and LLM

""""""

import osimport os

import sysimport sys

from pathlib import Pathfrom pathlib import Path

from typing import Optionalfrom typing import Optional



try:# Setup paths

    from dotenv import load_dotenvapi_dir = str(Path(__file__).parent.parent)

except ImportError:if api_dir not in sys.path:

    load_dotenv = None    sys.path.append(api_dir)



from scholarqa.preprocess.query_preprocessor import decompose_query# Load environment variables

from scholarqa.llms.constants import CLAUDE_4_SONNET, CostReportingArgsif not os.getenv("S2_API_KEY"):

from scholarqa.scholar_qa import ScholarQA    try:

from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient        from dotenv import load_dotenv

from scholarqa.rag.retrieval import PaperFinder        load_dotenv(Path(api_dir).parent / ".env")

from scholarqa.rag.retriever_base import FullTextRetriever    except ImportError:

from scholarqa.postprocess.json_output_utils import get_json_summary        pass

from scholarqa.table_generation.column_suggestion import generate_attribute_suggestions

from scholarqa.table_generation.table_generator import generate_table_cellsif not os.getenv("S2_API_KEY"):

    sys.exit("Error: Missing S2_API_KEY in environment variables")

# Setup paths and environment

api_dir = str(Path(__file__).parent.parent)from scholarqa.preprocess.query_preprocessor import decompose_query

if api_dir not in sys.path:from scholarqa.llms.constants import CLAUDE_4_SONNET, CostReportingArgs

    sys.path.append(api_dir)from scholarqa.scholar_qa import ScholarQA

from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient

if load_dotenv and not os.getenv("S2_API_KEY"):from scholarqa.rag.retrieval import PaperFinder

    load_dotenv(Path(api_dir).parent / ".env")from scholarqa.rag.retriever_base import FullTextRetriever

from scholarqa.postprocess.json_output_utils import get_json_summary

if not os.getenv("S2_API_KEY"):from scholarqa.table_generation.column_suggestion import generate_attribute_suggestions

    sys.exit("Error: Missing S2_API_KEY in environment variables")from scholarqa.table_generation.table_generator import generate_table_cells





def test_table_generation(query: Optional[str] = None) -> None:def test_table_generation(query: Optional[str] = None) -> None:

    """    """

    Test the table generation stage of the ScholarQA pipeline.    Test the table generation stage of the ScholarQA pipeline.

    Shows column generation and table cell population using LLM.    Shows column generation and table cell population using LLM.

        

    Args:    Args:

        query: Optional predefined query string        query: Optional predefined query string

    """    """

    if not query:    if not query:

        query = input("\nEnter query for table generation testing: ").strip()        query = input("\nEnter query for table generation testing: ").strip()

    if not query:    if not query:

        print("Error: No query provided. Exiting.")        print("Error: No query provided. Exiting.")

        return        return



    print(f"\nTESTING TABLE GENERATION STAGE")    print(f"\nTESTING TABLE GENERATION STAGE")

    print(f"Input Query: '{query}'\n")    print(f"Input Query: '{query}'\n")



    try:    try:

        # Initialize pipeline components        # Initialize pipeline components

        retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)        retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)

        paper_finder = PaperFinder(retriever=retriever)        paper_finder = PaperFinder(retriever=retriever)

        scholar_qa = ScholarQA(        scholar_qa = ScholarQA(

            paper_finder=paper_finder,            paper_finder=paper_finder,

            llm_model=CLAUDE_4_SONNET,            llm_model=CLAUDE_4_SONNET,

            state_mgr_client=LocalStateMgrClient("logs"),            state_mgr_client=LocalStateMgrClient("logs"),

        )        )



        # Stage 1-5: Get evidence collection        # Stage 1-5: Get evidence collection

        print("Running prerequisite stages (retrieval and evidence collection)...")        print("Running prerequisite stages (retrieval and evidence collection)...")

        evidence_result = scholar_qa.collect_evidence(query)        evidence_result = scholar_qa.collect_evidence(query)

        print(f"Retrieved {len(evidence_result.papers)} papers for table generation\n")        print(f"Retrieved {len(evidence_result.papers)} papers for table generation\n")



        # Stage 6A: Column Generation        # Stage 6A: Column Generation

        print("STAGE 6A: TABLE GENERATOR CONFIGURATION")        print("STAGE 6A: TABLE GENERATOR CONFIGURATION")

        print("=" * 50)        print("=" * 50)

        print("\nSYSTEM CONFIGURATION:")        print("\nSYSTEM CONFIGURATION:")

        print(f"   Model (Columns): {CLAUDE_4_SONNET}")        print(f"   Model (Columns): {CLAUDE_4_SONNET}")

        print(f"   Model (Values): {CLAUDE_4_SONNET}")        print(f"   Model (Values): {CLAUDE_4_SONNET}")

        print("   Max Worker Threads: 3")        print("   Max Worker Threads: 3")

        print("   Max Columns: 10")        print("   Max Columns: 10")

        print("   Table Subselection: Enabled")        print("   Table Subselection: Enabled")

        print("   - Max Rows After Selection: 6")         print("   - Max Rows After Selection: 6") 

        print("   - Max Columns After Selection: 6\n")        print("   - Max Columns After Selection: 6\n")



        print("STAGE 6B: COLUMN GENERATION")        print("STAGE 6B: COLUMN GENERATION")

        print("=" * 50)        print("=" * 50)

        print("\nColumn Generation Query:")        print("\nColumn Generation Query:")

        column_query = f"Methods Comparison, a section included in an answer to the question: {query}"        column_query = f"Methods Comparison, a section included in an answer to the question: {query}"

        print(f"   {column_query}\n")        print(f"   {column_query}\n")



        print("Generating Column Suggestions...")        print("Generating Column Suggestions...")

        cost_args = CostReportingArgs(        cost_args = CostReportingArgs(

            task_id="test_columns",            task_id="test_columns",

            user_id="test_user",            user_id="test_user",

            msg_id="test_msg",            msg_id="test_msg",

            description="Test Column Generation",            description="Test Column Generation",

            model=CLAUDE_4_SONNET,            model=CLAUDE_4_SONNET,

        )        )

                

        column_output = generate_attribute_suggestions(        column_output = generate_attribute_suggestions(

            query=column_query,            query=column_query,

            papers=evidence_result.papers,            papers=evidence_result.papers,

            cost_args=cost_args,            cost_args=cost_args,

        )        )

                

        if column_output.error:        if column_output.error:

            raise Exception(f"Error during column generation: {column_output.error}")            raise Exception(f"Error during column generation: {column_output.error}")

                        

        print(f"\nGenerated {len(column_output.columns)} columns:")        print(f"\nGenerated {len(column_output.columns)} columns:")

        for col in column_output.columns:        for col in column_output.columns:

            print(f"   {col}")            print(f"   {col}")

        print(f"\nColumn Generation Cost: ${column_output.tot_cost:.4f}\n")        print(f"\nColumn Generation Cost: ${column_output.tot_cost:.4f}\n")



        # Stage 6C: Table Generation        # Stage 6C: Table Generation

        print("STAGE 6C: TABLE CELL GENERATION")        print("STAGE 6C: TABLE CELL GENERATION")

        print("=" * 50)        print("=" * 50)

                

        table_result = generate_table_cells(        table_result = generate_table_cells(

            query=query,            query=query,

            papers=evidence_result.papers,            papers=evidence_result.papers,

            columns=column_output.columns,            columns=column_output.columns,

            cost_args=cost_args,            cost_args=cost_args,

        )        )

                

        if table_result.error:        if table_result.error:

            raise Exception(f"Error during table generation: {table_result.error}")            raise Exception(f"Error during table generation: {table_result.error}")



        print(f"\nGenerated table with {len(table_result.rows)} rows")        print(f"\nGenerated table with {len(table_result.rows)} rows")

        print(f"Table Generation Cost: ${table_result.tot_cost:.4f}")        print(f"Table Generation Cost: ${table_result.tot_cost:.4f}")

        print("\nTABLE GENERATION STAGE COMPLETE")        print("\nTABLE GENERATION STAGE COMPLETE")



    except Exception as e:    except Exception as e:

        print(f"Error during table generation: {e}")        print(f"Error during table generation: {e}")





if __name__ == "__main__":if __name__ == "__main__":

    import argparse    import argparse

    parser = argparse.ArgumentParser(    parser = argparse.ArgumentParser(

        description="Test ScholarQA Pipeline Stage 6: Table Generation"        description="Test ScholarQA Pipeline Stage 6: Table Generation"

    )    )

    parser.add_argument("--query", help="Research query to process")    parser.add_argument("--query", help="Research query to process")

    args = parser.parse_args()    args = parser.parse_args()

        

    test_table_generation(args.query)    test_table_generation(args.query)