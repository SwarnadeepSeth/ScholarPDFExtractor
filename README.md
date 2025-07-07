# ScholarPDFExtractor
A Python tool to search PubMed for scholarly articles, retrieve their details, and download their PDFs using PMCID-based naming. This tool automates the process of searching for free full-text articles, converting PMIDs to PMCIDs, and saving PDFs with consistent filenames (e.g., PMC123456.pdf).
Features

Search PubMed for articles based on user-provided search terms.
Convert PubMed IDs (PMIDs) to PubMed Central IDs (PMCIDs).
Retrieve detailed metadata (title, DOI, PMID, PMCID) for each article.
Download PDFs using Selenium and rename them to their corresponding PMCID.
Save search results as JSON for easy reference.
Configurable download directory and maximum number of results.

Requirements

Python 3.8+
Google Chrome browser (for Selenium)
Required Python packages:
selenium
webdriver_manager
requests
lxml (for XML parsing)



Installation

Clone the repository:
git clone https://github.com/your-username/ScholarPDFExtractor.git
cd ScholarPDFExtractor


Create and activate a virtual environment (optional but recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install the required packages:
pip install -r requirements.txt


Ensure Google Chrome is installed on your system, as Selenium uses it to download PDFs.


Usage

Run the script:
python scholar_pdf_extractor.py


Follow the prompts:

Enter a search term (e.g., "cancer immunotherapy").
Specify the number of papers to download (default is 5).


The script will:

Search PubMed for free full-text articles.
Convert PMIDs to PMCIDs.
Download PDFs to the downloads directory, named as {PMCID}.pdf (e.g., PMC123456.pdf).
Save search results (metadata) to a JSON file in the downloads directory.



Example:
Enter your search term: cancer immunotherapy
Number of papers to download (default 5): 10

Output files:

PDFs in the downloads directory (e.g., PMC123456.pdf).
JSON file with search results (e.g., search_results_cancer_immunotherapy_20250707_162530.json).

Project Structure
ScholarPDFExtractor/
├── scholar_pdf_extractor.py  # Main script
├── downloads/                # Directory for downloaded PDFs and JSON results
├── requirements.txt          # Python dependencies
└── README.md                # This file

Notes

The script uses Selenium in headless mode to download PDFs, requiring Google Chrome.
Downloads are saved to the downloads directory in the project root.
If a PDF with the same PMCID already exists, the script skips renaming to avoid overwriting.
A 5-second delay is used to ensure downloads complete; adjust time.sleep(5) in the code if needed for slower connections.
The script respects NCBI's API usage guidelines by including delays between requests.

Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Make your changes and commit (git commit -m "Add your feature").
Push to your branch (git push origin feature/your-feature).
Open a pull request.

Please ensure your code follows the existing style and includes appropriate tests.
License
This project is licensed under the MIT License. See the LICENSE file for details.
Contact
For questions or issues, please open an issue on GitHub or contact [your-email@example.com].
