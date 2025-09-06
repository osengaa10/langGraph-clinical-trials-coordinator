from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union, Dict, Any
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ConsultantAction(str, Enum):
    ASK_QUESTION = "ask_question"
    GENERATE_REPORT = "generate_report"

class ConsultantResponse(BaseModel):
    """Structured response model for consultant chain conversation output"""
    action: ConsultantAction
    content: str = Field(..., description="The question to ask or report readiness message")
    confidence: ConfidenceLevel = Field(..., description="Confidence in current information completeness")
    missing_info: Optional[str] = Field(None, description="Brief list of critical missing information (only if action is ask_question)")
    
    @validator('missing_info')
    def validate_missing_info(cls, v, values):
        if values.get('action') == ConsultantAction.ASK_QUESTION and not v:
            raise ValueError('missing_info is required when action is ask_question')
        return v

class SearchTermCategory(str, Enum):
    DIAGNOSIS = "diagnosis"
    BIOMARKER = "biomarker"
    TREATMENT = "treatment"
    STAGING = "staging"
    DISEASE_CHARACTERISTICS = "disease characteristics"
    SYMPTOMS = "symptoms"
    COMORBIDITIES = "comorbidities"
    CLINICAL_TRIAL = "clinical trial"
    TRIAL_PHASE = "trial phase"

class SearchTermSpecificity(str, Enum):
    BROAD = "broad"
    SPECIFIC = "specific"

class SearchTerm(BaseModel):
    """Individual search term with metadata"""
    term: str = Field(..., description="The medical search term/phrase")
    category: SearchTermCategory = Field(..., description="Category of the search term")
    specificity: SearchTermSpecificity = Field(..., description="Specificity level of the term")

class PromptDistillerResponse(BaseModel):
    """Structured response model for prompt distiller chain output"""
    search_terms: List[SearchTerm] = Field(..., min_items=3, max_items=15, description="List of generated search terms")
    primary_condition: str = Field(..., description="Most important condition for trial matching")
    key_biomarkers: List[str] = Field(default=[], description="List of relevant biomarkers")
    treatment_history_keywords: List[str] = Field(default=[], description="Prior therapy keywords")

class TrialPhase(str, Enum):
    PHASE_0 = "Phase 0"
    PHASE_I = "Phase I"
    PHASE_I_II = "Phase I/II"
    PHASE_II = "Phase II"
    PHASE_II_III = "Phase II/III"
    PHASE_III = "Phase III"
    PHASE_IV = "Phase IV"

class TrialStatus(str, Enum):
    NOT_YET_RECRUITING = "Not yet recruiting"
    RECRUITING = "Recruiting"
    ACTIVE_NOT_RECRUITING = "Active not recruiting"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"
    SUSPENDED = "Suspended"
    WITHDRAWN = "Withdrawn"

class ClinicalTrial(BaseModel):
    """Individual clinical trial information"""
    nct_id: str = Field(..., pattern=r'^NCT\d{8}$', description="NCT identifier")
    title: str = Field(..., description="Official trial title")
    phase: TrialPhase = Field(..., description="Trial phase")
    status: TrialStatus = Field(..., description="Current enrollment status")
    condition: str = Field(..., description="Primary condition being studied")
    intervention: str = Field(..., description="Drug/Device/Procedure name")
    primary_endpoint: str = Field(..., description="Main outcome being measured")
    key_inclusion_criteria: List[str] = Field(..., description="Key inclusion criteria")
    key_exclusion_criteria: List[str] = Field(..., description="Key exclusion criteria")
    estimated_enrollment: int = Field(..., ge=0, description="Estimated number of participants")
    locations: List[str] = Field(..., description="Geographic locations")
    sponsor: str = Field(..., description="Sponsor organization")
    pi_contact: str = Field(..., description="Principal Investigator contact info")
    completion_date: str = Field(..., description="Estimated completion date")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")
    patient_match_factors: List[str] = Field(..., description="Factors indicating patient match")
    next_steps: str = Field(..., description="How patient can inquire/enroll")

class SearchSummary(BaseModel):
    """Summary of clinical trials search results"""
    search_terms_analyzed: List[str] = Field(..., description="Terms that were analyzed")
    total_trials_found: int = Field(..., ge=0, description="Total number of trials found")
    high_relevance_count: int = Field(..., ge=0, description="Number of highly relevant trials")
    recruiting_count: int = Field(..., ge=0, description="Number of currently recruiting trials")
    geographic_regions: List[str] = Field(..., description="Geographic regions with trials")

class TrialsSearchResponse(BaseModel):
    """Structured response model for trials search chain output"""
    search_summary: SearchSummary
    clinical_trials: List[ClinicalTrial] = Field(..., description="List of relevant clinical trials")
    additional_considerations: List[str] = Field(..., description="Additional factors and recommendations")

class TrialCompatibilityCategory(str, Enum):
    EXCEPTIONAL = "Exceptional"
    STRONG = "Strong"
    GOOD = "Good"
    MODERATE = "Moderate"
    POOR = "Poor"
    UNSUITABLE = "Unsuitable"

class UrgencyLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ScoringBreakdown(BaseModel):
    """Detailed scoring breakdown for trial evaluation"""
    medical_eligibility: float = Field(..., ge=0.0, le=25.0, description="Medical eligibility score (0-25)")
    treatment_compatibility: float = Field(..., ge=0.0, le=25.0, description="Treatment compatibility score (0-25)")
    logistical_feasibility: float = Field(..., ge=0.0, le=25.0, description="Logistical feasibility score (0-25)")
    scientific_benefit_potential: float = Field(..., ge=0.0, le=25.0, description="Scientific benefit potential score (0-25)")

class EligibilityAssessment(BaseModel):
    """Patient eligibility assessment for a trial"""
    likely_eligible: bool = Field(..., description="Whether patient is likely eligible")
    key_requirements: List[str] = Field(..., description="Requirements patient must meet")
    potential_exclusions: List[str] = Field(..., description="Factors that might exclude patient")
    additional_testing_needed: List[str] = Field(..., description="Tests/evaluations required")

class TrialEvaluation(BaseModel):
    """Detailed evaluation of a single clinical trial"""
    trial_id: str = Field(..., description="Trial identifier (NCT number)")
    trial_title: str = Field(..., description="Official trial name")
    overall_compatibility_score: float = Field(..., ge=0.0, le=100.0, description="Overall compatibility score (0-100)")
    category: TrialCompatibilityCategory = Field(..., description="Compatibility category")
    scoring_breakdown: ScoringBreakdown
    strengths: List[str] = Field(..., description="Positive matching factors")
    concerns: List[str] = Field(..., description="Potential barriers or limitations")
    eligibility_assessment: EligibilityAssessment
    recommendation: str = Field(..., description="Detailed recommendation and next steps")
    urgency_level: UrgencyLevel = Field(..., description="Priority level for follow-up")

class EvaluationSummary(BaseModel):
    """Summary of trial evaluation results"""
    total_trials_evaluated: int = Field(..., ge=0, description="Total number of trials evaluated")
    highly_suitable_count: int = Field(..., ge=0, description="Number of highly suitable trials")
    moderately_suitable_count: int = Field(..., ge=0, description="Number of moderately suitable trials")
    unsuitable_count: int = Field(..., ge=0, description="Number of unsuitable trials")
    average_compatibility_score: float = Field(..., ge=0.0, le=100.0, description="Average compatibility score")
    primary_recommendation: str = Field(..., description="Trial NCT ID or 'No suitable trials found'")

class PatientConsiderations(BaseModel):
    """Patient-specific considerations for trial matching"""
    optimal_trial_characteristics: List[str] = Field(..., description="What would be ideal for this patient")
    significant_barriers: List[str] = Field(..., description="Major obstacles to trial participation")
    alternative_strategies: List[str] = Field(..., description="Other options if no trials are suitable")
    additional_information_needed: List[str] = Field(..., description="Missing data that would improve matching")

class NextSteps(BaseModel):
    """Recommended next steps after trial evaluation"""
    immediate_actions: List[str] = Field(..., description="What should happen next")
    timeline_recommendations: List[str] = Field(..., description="When to follow up or re-evaluate")
    additional_consultations: List[str] = Field(..., description="Specialists who should be involved")

class EvaluateTrialsResponse(BaseModel):
    """Structured response model for evaluate trials chain output"""
    evaluation_summary: EvaluationSummary
    trial_evaluations: List[TrialEvaluation] = Field(..., description="Detailed evaluation of each trial")
    patient_considerations: PatientConsiderations
    next_steps: NextSteps

# Utility function to get all model classes for easy importing
def get_all_models():
    """Return a dictionary of all Pydantic models for easy access"""
    return {
        'ConsultantResponse': ConsultantResponse,
        'PromptDistillerResponse': PromptDistillerResponse,
        'TrialsSearchResponse': TrialsSearchResponse,
        'EvaluateTrialsResponse': EvaluateTrialsResponse
    }