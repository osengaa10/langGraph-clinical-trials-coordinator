from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from LLMs.llm import GROQ_LLM  # You might need to change this import depending on the LLM you're using
from langchain.prompts import PromptTemplate
from .custom_parsers import prompt_distiller_parser

prompt = PromptTemplate(
    template="""<s>[INST] <<SYS>>
You are a clinical research specialist and medical terminologist expert in extracting precise, medically accurate search terms for clinical trial databases. Your role is to analyze complex medical reports and generate comprehensive search strategies.

MEDICAL TERMINOLOGY STANDARDS:
- Use MeSH (Medical Subject Headings) terminology when possible
- Include ICD-10 diagnostic codes and terminology
- Consider FDA drug classifications and biomarker terminology
- Utilize oncology staging systems (TNM, AJCC) when relevant

SEARCH TERM EXTRACTION STRATEGY:
1. PRIMARY CONDITION: Main diagnosis with specific subtype/stage
2. MOLECULAR TARGETS: Biomarkers, genetic mutations, protein expressions  
3. TREATMENT MODALITIES: Therapy types, drug classes, interventions
4. DISEASE CHARACTERISTICS: Stage, grade, receptor status, histology, metastases
5. STAGING: Disease stage, tumor classification, progression status
6. SYMPTOMS: Clinical manifestations and presentations
7. COMORBIDITIES: Concurrent conditions affecting treatment options
8. CLINICAL TRIAL: Trial phase preferences, study design types
9. TRIAL PHASE: Phase I, II, III, IV trial specifications

OUTPUT REQUIREMENTS:
- Generate between 3 and 15 search terms (MAXIMUM 15 - DO NOT EXCEED THIS LIMIT)
- Each term should be 2-8 words for optimal database searching
- Include both broad and specific terms for comprehensive coverage
- Consider phase-appropriate terms (early-stage, advanced, metastatic)
- Avoid overly generic terms that would return too many irrelevant results
- Prioritize high-value terms that capture different aspects of the patient's condition
- Focus on quality over quantity - select only the most relevant terms

EXISTING SEARCH TERMS: {existing_terms}
Ensure new terms complement existing ones without exact duplication.
<</SYS>>

Analyze the medical report and extract comprehensive search terms for clinical trial databases. Generate multiple complementary search terms that cover different aspects of the patient's condition.

Return your response as a JSON object with search terms.

IMPORTANT: For each search term, the "category" field must be EXACTLY ONE of these values:
- "diagnosis"
- "biomarker"
- "treatment"
- "staging"
- "disease characteristics"
- "symptoms"
- "comorbidities"
- "clinical trial"
- "trial phase"

The "specificity" field must be either "broad" or "specific".

JSON format:
{{
    "search_terms": [
        {{"term": "specific medical term/phrase", "category": "diagnosis", "specificity": "broad"}},
        {{"term": "another medical term/phrase", "category": "biomarker", "specificity": "specific"}}
    ],
    "primary_condition": "most important condition for trial matching",
    "key_biomarkers": ["list", "of", "relevant", "biomarkers"],
    "treatment_history_keywords": ["prior", "therapies", "keywords"]
}}

MEDICAL REPORT:
{medical_report}

EXISTING TERMS TO AVOID DUPLICATION:
{existing_terms}
[/INST]
""",
    input_variables=["medical_report", "existing_terms"],
)

prompt_distiller_chain = prompt | GROQ_LLM | prompt_distiller_parser