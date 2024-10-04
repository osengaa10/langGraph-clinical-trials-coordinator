from rag import chunk_and_embed
import requests
import os

def write_markdown_file(content, filename):
  """Writes the given content as a markdown file to the local directory.

  Args:
    content: The string content to write to the file.
    filename: The filename to save the file as.
  """
  if type(content) == dict:
    content = '\n'.join(f"{key}: {value}" for key, value in content.items())
  if type(content) == list:
    content = '\n'.join(content)
  with open(f"{filename}.md", "w") as f:
    f.write(content)



def clinical_trials_search(condition: str) -> str:
    """Fetches data from ClinicalTrials.gov API for a given condition. Input is a medical condition search term"""  
    # Base URL for the ClinicalTrials.gov API
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Parameters for the API request
    params = {
        "format": "json",
        "markupFormat": "markdown",
        "query.cond": condition,
        "filter.overallStatus": "RECRUITING",
        "pageToken": None
    }
    print("====PARAMS====")
    print(params)
    print("====PARAMS====")
    # Make the GET request
    response = requests.get(base_url, params=params)
    raw_trials = response.json()
    print("====RESPONSE====")
    print(response)
    print("====RESONSE====")

    study_details_list = []
    counter = 0
    while True:
        # Make the GET request
        response = requests.get(base_url, params=params)
        # print("response: ", response)
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            break  # Break the loop if there's an error in the response

        raw_trials = response.json()
        # Extract studies and append details to the list
        for study in raw_trials["studies"]:
            protocol_section = study.get("protocolSection", {})
            study_details_list.append({
                "nctId": protocol_section.get("identificationModule").get("nctId"),
                "officialTitle": protocol_section.get("identificationModule", {}).get("officialTitle"),        
                "eligibilityModule": protocol_section.get("eligibilityModule"),
                "centralContacts": protocol_section.get("contactsLocationsModule", {}).get("centralContacts"),
                "conditions": protocol_section.get("conditionsModule", {}).get("conditions"),
                "armsInterventionsModule": protocol_section.get("armsInterventionsModule"),
                "outcomesModule": protocol_section.get("outcomesModule"),
                "designModule": protocol_section.get("designModule"),
                "briefSummary": protocol_section.get("descriptionModule", {}).get("briefSummary") 
            })

        # Update the pageToken to the next page token from the response, if any
        nextPageToken = raw_trials.get("nextPageToken")
        if not nextPageToken or counter > 2:
            break
        params["pageToken"] = nextPageToken
        counter = counter + 1

    print(f"Number of studies found for {condition}:", len(study_details_list))
    for index, trial in enumerate(study_details_list):
        report_content = create_trial_report(trial)
        with open(f'./studies/{condition.replace(" ", "_")}_{index + 1}.txt', "w") as file:
            file.write(report_content)
    
    new_studies = []
    for index, trial in enumerate(study_details_list):
        report_content = create_trial_report(trial)
        file_name = f'{condition.replace(" ", "_")}_{index + 1}.txt'
        file_path = os.path.join('./studies', file_name)
        with open(file_path, "w") as file:
            file.write(report_content)
        new_studies.append((file_name, file_path))
    chunk_and_embed(new_studies)
    # Return the response in JSON format
    return new_studies




def create_trial_report(trial):
    """Generate a formatted string for a clinical trial report."""
    # Safely access values, replacing None with 'Not available'
    title = trial.get('officialTitle', 'Not available')
    eligibility_criteria = trial['eligibilityModule'].get('eligibilityCriteria', 'Not available')
    nctId = trial.get('nctId', 'Not available')
    report = f"nctId: {nctId} Title: {title}\n\n"
    report += "Eligibility Criteria:\n"
    report += eligibility_criteria + "\n\n"
    
    report += "Contact Information:\n"
    # Ensure centralContacts is iterable, default to empty list if None
    for contact in trial.get('centralContacts', []) or []:
        name = contact.get('name', 'Not available')
        role = contact.get('role', 'Not available')
        phone = contact.get('phone', 'Not available')
        email = contact.get('email', 'Not available')
        report += f"{name} - {role}\n"
        report += f"Phone: {phone}, Email: {email}\n\n"
    
    # Ensure conditions is iterable, default to empty list if None
    conditions = ", ".join([condition for condition in trial.get('conditions', []) if condition])
    report += "Conditions:\n" + conditions + "\n\n"
    
    report += "Interventions:\n"
    # Check if 'armsInterventionsModule' exists and is not None before accessing 'interventions'
    interventions = (trial.get('armsInterventionsModule', {}) or {}).get('interventions', [])
    for intervention in interventions:
        intervention_type = intervention.get('type', 'Not available')
        intervention_name = intervention.get('name', 'Not available')
        description = intervention.get('description', 'Not available')
        report += f"{intervention_type} - {intervention_name}: {description}\n"
    
    report += "\nPrimary Outcomes:\n"
    # Ensure primaryOutcomes is iterable, default to empty list if None
    for outcome in trial['outcomesModule'].get('primaryOutcomes', []) or []:
        measure = outcome.get('measure', 'Not available')
        description = outcome.get('description', 'Not available')
        time_frame = outcome.get('timeFrame', 'Not available')
        report += f"{measure}: {description} (Time frame: {time_frame})\n"
    
    return report