# Sample Medical Charts

This directory contains sample medical charts that users can download to test the clinical trials coordinator application.

## Adding Sample PDF Files

To enable the sample download buttons in the FileUploader component, add the following PDF files to this directory:

1. **breast_cancer_chart.pdf** - 35-year-old female with BRCA mutation and metastatic breast cancer
2. **sarcoma_cancer_chart.pdf** - 52-year-old female with metastatic soft tissue sarcoma
3. **bladder_cancer_chart.pdf** - 67-year-old male with muscle-invasive bladder cancer

## Current UI Implementation

The FileUploader component now displays three download buttons below the "Upload Clinical Notes" button:
- "Breast Cancer (35F)" → downloads breast_cancer_chart.pdf
- "Soft Tissue Sarcoma (52F)" → downloads sarcoma_cancer_chart.pdf
- "Bladder Cancer (67M)" → downloads bladder_cancer_chart.pdf

## How Users Interact

1. User visits the application
2. Sees download buttons for sample charts
3. Clicks a download button to download a sample PDF
4. Drags the downloaded PDF into the uploader
5. The application processes the medical chart and begins the trial matching workflow

## File Format

All sample files should be PDF format (.pdf extension) containing realistic medical chart data that demonstrates different cancer types and patient profiles.
