from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from .models import (
    ConsultantResponse, 
    PromptDistillerResponse, 
    TrialsSearchResponse, 
    EvaluateTrialsResponse
)
import json
import logging

logger = logging.getLogger(__name__)

class ValidatedConsultantParser(PydanticOutputParser):
    """Custom parser for Consultant Chain responses with validation"""
    
    def __init__(self):
        super().__init__(pydantic_object=ConsultantResponse)
    
    def parse(self, text: str) -> ConsultantResponse:
        try:
            return super().parse(text)
        except OutputParserException as e:
            logger.warning(f"Failed to parse consultant response: {e}")
            # Fallback parsing for malformed JSON
            try:
                data = json.loads(text)
                # Provide defaults for missing required fields
                return ConsultantResponse(
                    action=data.get('action', 'ask_question'),
                    content=data.get('content', 'Could you provide more information about your condition?'),
                    confidence=data.get('confidence', 'Low'),
                    missing_info=data.get('missing_info', 'Additional medical details needed')
                )
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
                # Return a safe default response
                return ConsultantResponse(
                    action='ask_question',
                    content='I need more information to help you find suitable clinical trials. Could you tell me about your medical condition?',
                    confidence='Low',
                    missing_info='Complete medical history and current condition details'
                )

class ValidatedPromptDistillerParser(PydanticOutputParser):
    """Custom parser for Prompt Distiller Chain responses with validation"""
    
    def __init__(self):
        super().__init__(pydantic_object=PromptDistillerResponse)
    
    def _clean_search_term_category(self, category_text: str) -> str:
        """Extract and normalize search term category from text"""
        category_text = category_text.strip().lower()
        
        # Direct matches first
        valid_categories = [
            'diagnosis', 'biomarker', 'treatment', 'staging', 
            'disease characteristics', 'symptoms', 'comorbidities',
            'clinical trial', 'trial phase'
        ]
        
        if category_text in valid_categories:
            return category_text
            
        # Fuzzy matching for variations
        if 'diagnos' in category_text or 'condition' in category_text:
            return 'diagnosis'
        elif 'biomarker' in category_text or 'molecular' in category_text or 'genetic' in category_text:
            return 'biomarker'
        elif 'treatment' in category_text or 'therapy' in category_text or 'drug' in category_text or 'therapeutic' in category_text:
            return 'treatment'
        elif 'stag' in category_text or 'grade' in category_text:
            return 'staging'
        elif 'disease' in category_text or 'metasta' in category_text or 'histol' in category_text:
            return 'disease characteristics'
        elif 'symptom' in category_text or 'clinical manifestation' in category_text:
            return 'symptoms'
        elif 'comorbid' in category_text or 'concurrent' in category_text:
            return 'comorbidities'
        elif 'trial' in category_text or 'study' in category_text:
            return 'clinical trial'
        elif 'phase' in category_text:
            return 'trial phase'
        else:
            return 'diagnosis'  # Default fallback
    
    def parse(self, text: str) -> PromptDistillerResponse:
        try:
            # First, try to parse and clean the JSON data before Pydantic validation
            data = json.loads(text)
            
            # Clean up search terms categories if they exist
            if 'search_terms' in data and data['search_terms']:
                for term in data['search_terms']:
                    if 'category' in term:
                        term['category'] = self._clean_search_term_category(term['category'])

                # Truncate to max 15 terms (model constraint from models.py:50)
                if len(data['search_terms']) > 15:
                    logger.warning(f"Truncating {len(data['search_terms'])} search terms to maximum of 15")
                    data['search_terms'] = data['search_terms'][:15]

            # Now try to create the Pydantic object with cleaned data
            return PromptDistillerResponse(**data)
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse prompt distiller response: {e}")
            # Fallback parsing
            try:
                return PromptDistillerResponse(
                    search_terms=data.get('search_terms', [
                        {"term": "medical condition", "category": "diagnosis", "specificity": "broad"}
                    ]),
                    primary_condition=data.get('primary_condition', 'unspecified condition'),
                    key_biomarkers=data.get('key_biomarkers', []),
                    treatment_history_keywords=data.get('treatment_history_keywords', [])
                )
            except Exception as fallback_error:
                logger.error(f"Fallback parsing failed: {fallback_error}")
                # Return minimal valid response
                return PromptDistillerResponse(
                    search_terms=[
                        {"term": "medical condition", "category": "diagnosis", "specificity": "broad"},
                        {"term": "clinical trial", "category": "treatment", "specificity": "broad"},
                        {"term": "therapy", "category": "treatment", "specificity": "broad"}
                    ],
                    primary_condition="unspecified medical condition",
                    key_biomarkers=[],
                    treatment_history_keywords=[]
                )

class ValidatedTrialsSearchParser(PydanticOutputParser):
    """Custom parser for Trials Search Chain responses with validation"""
    
    def __init__(self):
        super().__init__(pydantic_object=TrialsSearchResponse)
    
    def parse(self, text: str) -> TrialsSearchResponse:
        try:
            return super().parse(text)
        except OutputParserException as e:
            logger.warning(f"Failed to parse trials search response: {e}")
            # Fallback parsing
            try:
                data = json.loads(text)
                return TrialsSearchResponse(
                    search_summary=data.get('search_summary', {
                        'search_terms_analyzed': [],
                        'total_trials_found': 0,
                        'high_relevance_count': 0,
                        'recruiting_count': 0,
                        'geographic_regions': []
                    }),
                    clinical_trials=data.get('clinical_trials', []),
                    additional_considerations=data.get('additional_considerations', [
                        'No suitable trials found with current search criteria',
                        'Consider broadening search terms or consulting with specialist'
                    ])
                )
            except Exception as fallback_error:
                logger.error(f"Fallback parsing failed: {fallback_error}")
                # Return empty but valid response
                return TrialsSearchResponse(
                    search_summary={
                        'search_terms_analyzed': ['Unknown terms'],
                        'total_trials_found': 0,
                        'high_relevance_count': 0,
                        'recruiting_count': 0,
                        'geographic_regions': []
                    },
                    clinical_trials=[],
                    additional_considerations=[
                        'Search results could not be processed properly',
                        'Please try alternative search terms or consult with a clinical research coordinator'
                    ]
                )

class ValidatedEvaluateTrialsParser(PydanticOutputParser):
    """Custom parser for Evaluate Trials Chain responses with validation"""
    
    def __init__(self):
        super().__init__(pydantic_object=EvaluateTrialsResponse)
    
    def _clean_urgency_level(self, urgency_text: str) -> str:
        """Extract urgency level from text like 'Medium priority for follow-up' -> 'Medium'"""
        urgency_text = urgency_text.strip().lower()
        if 'high' in urgency_text:
            return 'High'
        elif 'medium' in urgency_text:
            return 'Medium'
        elif 'low' in urgency_text:
            return 'Low'
        else:
            return 'Medium'  # Default fallback
    
    def _clean_category(self, category_text: str) -> str:
        """Extract category from potentially verbose text"""
        category_text = category_text.strip().lower()
        if 'exceptional' in category_text:
            return 'Exceptional'
        elif 'strong' in category_text:
            return 'Strong'
        elif 'good' in category_text:
            return 'Good'
        elif 'moderate' in category_text:
            return 'Moderate'
        elif 'poor' in category_text:
            return 'Poor'
        elif 'unsuitable' in category_text:
            return 'Unsuitable'
        else:
            return 'Moderate'  # Default fallback
    
    def parse(self, text: str) -> EvaluateTrialsResponse:
        try:
            # First, try to parse and clean the JSON data before Pydantic validation
            data = json.loads(text)

            # Clean up trial evaluations if they exist
            if 'trial_evaluations' in data and data['trial_evaluations']:
                for trial in data['trial_evaluations']:
                    if 'urgency_level' in trial:
                        trial['urgency_level'] = self._clean_urgency_level(trial['urgency_level'])
                    if 'category' in trial:
                        trial['category'] = self._clean_category(trial['category'])

            # Fill in missing next_steps fields (common with DeepSeek)
            if 'next_steps' in data:
                next_steps = data['next_steps']
                if 'timeline_recommendations' not in next_steps:
                    next_steps['timeline_recommendations'] = ['Follow up in 2-4 weeks with healthcare provider']
                if 'additional_consultations' not in next_steps:
                    next_steps['additional_consultations'] = ['Oncology specialist', 'Clinical research coordinator']
            else:
                data['next_steps'] = {
                    'immediate_actions': ['Consult with healthcare provider'],
                    'timeline_recommendations': ['Follow up in 2-4 weeks'],
                    'additional_consultations': ['Oncologist or specialist consultation']
                }

            # Now try to create the Pydantic object with cleaned data
            return EvaluateTrialsResponse(**data)
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse evaluate trials response: {e}")
            # Fallback parsing 
            try:
                return EvaluateTrialsResponse(
                    evaluation_summary=data.get('evaluation_summary', {
                        'total_trials_evaluated': 0,
                        'highly_suitable_count': 0,
                        'moderately_suitable_count': 0,
                        'unsuitable_count': 0,
                        'average_compatibility_score': 0.0,
                        'primary_recommendation': 'No suitable trials found'
                    }),
                    trial_evaluations=data.get('trial_evaluations', []),
                    patient_considerations=data.get('patient_considerations', {
                        'optimal_trial_characteristics': [],
                        'significant_barriers': [],
                        'alternative_strategies': [],
                        'additional_information_needed': []
                    }),
                    next_steps=data.get('next_steps', {
                        'immediate_actions': ['Consult with healthcare provider'],
                        'timeline_recommendations': ['Follow up in 2-4 weeks'],
                        'additional_consultations': ['Oncologist or specialist consultation']
                    })
                )
            except Exception as fallback_error:
                logger.error(f"Fallback parsing failed: {fallback_error}")
                # Return safe default response
                return EvaluateTrialsResponse(
                    evaluation_summary={
                        'total_trials_evaluated': 0,
                        'highly_suitable_count': 0,
                        'moderately_suitable_count': 0,
                        'unsuitable_count': 0,
                        'average_compatibility_score': 0.0,
                        'primary_recommendation': 'Evaluation could not be completed'
                    },
                    trial_evaluations=[],
                    patient_considerations={
                        'optimal_trial_characteristics': ['Unable to determine without proper evaluation'],
                        'significant_barriers': ['Evaluation system error'],
                        'alternative_strategies': ['Consult directly with clinical research team'],
                        'additional_information_needed': ['Complete re-evaluation required']
                    },
                    next_steps={
                        'immediate_actions': ['Contact healthcare provider immediately'],
                        'timeline_recommendations': ['Schedule consultation within 1 week'],
                        'additional_consultations': ['Clinical research coordinator', 'Primary physician']
                    }
                )

# Export all custom parsers
consultant_parser = ValidatedConsultantParser()
prompt_distiller_parser = ValidatedPromptDistillerParser()
trials_search_parser = ValidatedTrialsSearchParser()
evaluate_trials_parser = ValidatedEvaluateTrialsParser()