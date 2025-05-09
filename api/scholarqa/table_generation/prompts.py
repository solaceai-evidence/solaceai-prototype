SYSTEM_PROMPT = """
You are an intelligent and precise assistant that can understand the contents of research papers. 
You are knowledgable in different fields and domains of science, in particular computer science. 
You are able to interpret research papers, create questions and answers, and compare multiple papers.
"""

ATTRIBUTE_PROMPT = """
I want to write a related work section about following content:\n 
\"{}\".\n
We would like you to identify attributes that should be compared 
between related papers in this section. You will be provided with 
a list of the title of each paper and abstract. Your task is the following: 
Given a list of papers, you should identify and define {} attributes 
that can be used to compare the given papers within the given subsection topic. 
Attributes should focus on the main content of the papers, and should **NOT** be about their metadata such as Authors, Publication Year, or Venues.
Return a JSON object in the following format:\n{{\"attribute name\": {{\"def\": \"definition for comparable attribute within the given subsection topic\", \"is_metadata\": \"True or False\"}}, \"attribute name\": {{\"def\": \"definition for comparable attribute within the given subsection topic\", \"is_metadata\": \"True or False\"}}, ...}}
\n\n{}\n",
"""

VALUE_GENERATION_FROM_ABSTRACT = """
Imagine the following scenario: A user is making a table for a scholarly paper that contains information about multiple papers and compares these papers. 
To compare and contrast the papers, the user has selected some aspects by which papers should be compared. 
Your task is the following: Given a paper abstract and a question describing one of the selected aspects, generate a value that can be added to the table. 
You should find the part of the abstract that discusses the aspect provided in the question.
If there is no answer in the abstract, return \"N/A\" as the value to be added. 
**Ensure that you follow these rules: (1) Only return the answer. Do not repeat the question or add any surrounding text. (2) The answer should be brief and consist of phrases of fewer than 10 words.**\n\n
"""

VALUE_GENERATION_FROM_METADATA = """
Imagine the following scenario: A user is making a table for a scholarly paper that contains information about multiple papers and compares these papers.
The user wants to some metadata about each paper to the table.
Your task is the following: Given a json blob containing all available metadata (e.g., title, abstract, authors, etc.) for a paper, 
generate a value that can be added to the table under the following column: {}.
**Ensure that you follow these rules: (1) Only return the answer. Do not repeat the question or add any surrounding text. (2) The answer should be brief and consist of phrases of fewer than 10 words. (3) Return N/A if there is no answer.**\n\n
"""

VALUE_CONSISTENCY_PROMPT_ZS = """
Imagine the following scenario: A user is making a table for a scholarly paper that contains information about multiple papers and compares these papers. 
To compare and contrast the papers, the user has selected an aspect which will be added as a column to the table. 
Your task is the following: Given the column name and information from each paper relevant to that column, generate final values to be added to the table.
Return the output as a JSON object in the following format:\n{{\"values\": [\"value for paper 1\", \"value for paper 2\", ...]}}\n
**Ensure that you follow these rules: (1) None of the values provided in the prompt should be overwritten by "N/A" (2) Only return a single JSON object. (3) JSON object should be complete and valid. (4) The list in the JSON object should contain the same number of values as provided in the input (5) Each input should have a corresponding output value (leave "N/A" values unchanged) (6) All values should follow consistent formatting and style.\n\n**
"""

VALUE_CONSISTENCY_PROMPT_FS = """
Imagine the following scenario: A user is making a table for a scholarly paper that contains information about multiple papers and compares these papers. 
To compare and contrast the papers, the user has selected an aspect which will be added as a column to the table. 
Your task is the following: Given the column name and information from each paper relevant to that column, generate final values to be added to the table.
Return the output as a JSON object in the following format:\n{{\"values\": [\"value for paper 1\", \"value fpr paper 2\", ...]}}\n
**Ensure that you follow these rules: (1) None of the values provided in the prompt should be overwritten by "N/A" (2) Only return a single JSON object. (3) JSON object should be complete and valid. (4) The list in the JSON object should contain the same number of values as provided in the input (5) Each input should have a corresponding output value (leave "N/A" values unchanged) (6) All values should follow consistent formatting and style.\n\n**
"""

VESPAQA_PROMPT = """
Answer a question using the provided relevant snippets from a scientific paper.
Your response should be a JSON object with the following fields:
  - answer: The answer to the question. The answer should use concise language, but be comprehensive. Only provide answers that are objectively supported by the text in paper. Avoid answers longer than 20 words. If you cannot answer the question using provided information, the answer should be 'N/A.
  - excerpts: A list of one or more *EXACT* text spans extracted from the paper that support the answer. Return between at most five spans, and no more that 500 words. Make sure to cover all aspects of the answer above. If the answer is 'N/A', excerpts should be an empty list.

<Start of snippets>

Title: [TITLE]

[SNIPPETS]

<End of snippets>

Given the information above, please answer the question: [QUESTION] \nAnswer:"""