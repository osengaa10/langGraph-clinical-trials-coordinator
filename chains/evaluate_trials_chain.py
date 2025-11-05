from langchain.prompts import PromptTemplate
from LLMs.llm import REASONING_LLM
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from .custom_parsers import evaluate_trials_parser

evaluation_prompt = PromptTemplate(
    template="""<s>[INST] <<SYS>>
You are a clinical trial matching specialist and biostatistician expert in patient-trial compatibility analysis. Your role is to provide comprehensive, quantitative assessments of clinical trial suitability using evidence-based evaluation criteria.

EVALUATION METHODOLOGY:
Use a multi-dimensional scoring system (0-100 scale) across these domains:

1. MEDICAL ELIGIBILITY (0-25 points):
   - Diagnosis/condition match (exact vs related vs adjacent conditions)
   - Disease stage/severity alignment 
   - Biomarker/molecular profile compatibility
   - Comorbidity considerations and contraindications

2. TREATMENT COMPATIBILITY (0-25 points):
   - Prior therapy requirements/restrictions
   - Performance status requirements (ECOG/Karnofsky)
   - Line of therapy appropriateness (first-line, second-line, etc.)
   - Drug interaction and safety profile alignment

3. LOGISTICAL FEASIBILITY (0-25 points):
   - Geographic accessibility to trial sites
   - Study visit frequency and travel requirements
   - Insurance coverage and financial considerations
   - Timeline alignment (study duration vs patient prognosis)

4. SCIENTIFIC/BENEFIT POTENTIAL (0-25 points):
   - Trial phase appropriateness for patient needs
   - Evidence of therapeutic promise for patient's condition
   - Risk-benefit ratio assessment
   - Quality of study design and endpoints

SCORING CRITERIA:
- 90-100: Exceptional match, immediate referral recommended
- 75-89: Strong match, highly suitable candidate
- 60-74: Good match, worth detailed discussion
- 45-59: Moderate match, consider with caveats
- 30-44: Poor match, significant barriers exist
- 0-29: Unsuitable, major incompatibilities

RANKING PRIORITIES:
1. Patient safety and eligibility first
2. Likelihood of clinical benefit
3. Logistical feasibility
4. Patient preferences and quality of life impact

OUTPUT FORMAT REQUIREMENTS:
- urgency_level must be exactly "High", "Medium", or "Low" (no additional text)
- category must be exactly "Exceptional", "Strong", "Good", "Moderate", "Poor", or "Unsuitable"
- All scoring values must be numeric (0.0-25.0 for individual scores, 0.0-100.0 for overall)
- Use precise medical terminology and structured formatting
<</SYS>>

Conduct comprehensive patient-trial compatibility analysis for the provided research information. Evaluate each identified clinical trial using quantitative scoring methodology and provide ranked recommendations.

Return detailed analysis as JSON:
{{
    "evaluation_summary": {{
        "total_trials_evaluated": 0,
        "highly_suitable_count": 0,
        "moderately_suitable_count": 0,
        "unsuitable_count": 0,
        "average_compatibility_score": 0.0,
        "primary_recommendation": "Trial NCT ID or 'No suitable trials found'"
    }},
    "trial_evaluations": [
        {{
            "trial_id": "NCT########",
            "trial_title": "Official trial name",
            "overall_compatibility_score": 0.0,
            "category": "Exceptional/Strong/Good/Moderate/Poor/Unsuitable",
            "scoring_breakdown": {{
                "medical_eligibility": 0.0,
                "treatment_compatibility": 0.0, 
                "logistical_feasibility": 0.0,
                "scientific_benefit_potential": 0.0
            }},
            "strengths": ["Positive matching factors"],
            "concerns": ["Potential barriers or limitations"],
            "eligibility_assessment": {{
                "likely_eligible": true,
                "key_requirements": ["Requirements patient must meet"],
                "potential_exclusions": ["Factors that might exclude patient"],
                "additional_testing_needed": ["Tests/evaluations required"]
            }},
            "recommendation": "Detailed recommendation and next steps",
            "urgency_level": "High/Medium/Low"
        }}
    ],
    "patient_considerations": {{
        "optimal_trial_characteristics": ["What would be ideal for this patient"],
        "significant_barriers": ["Major obstacles to trial participation"],
        "alternative_strategies": ["Other options if no trials are suitable"],
        "additional_information_needed": ["Missing data that would improve matching"]
    }},
    "next_steps": {{
        "immediate_actions": ["What should happen next"],
        "timeline_recommendations": ["When to follow up or re-evaluate"],
        "additional_consultations": ["Specialists who should be involved"]
    }}
}}

RESEARCH INFORMATION AND TRIAL DATA:
{research_info}
[/INST]
""",
    input_variables=["research_info"],
)

# Using REASONING_LLM for complex trial eligibility analysis and scoring
evaluate_trials_chain = (
    evaluation_prompt
    | REASONING_LLM
    | evaluate_trials_parser
)