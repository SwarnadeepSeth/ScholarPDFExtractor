from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time, os
from urllib.parse import urljoin
import requests
from xml.etree import ElementTree as ElementTree

def search_pubmed_and_convert(search_term, max_results=10):
    """
    Search PubMed and convert PMIDs to PMCIDs for more comprehensive results
    """
    print(f"🔍 Searching PubMed for: '{search_term}'")
    
    # Search PubMed for PMIDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        'db': 'pubmed',
        'term': f'{search_term} AND "free full text"[Filter]',
        'retmax': max_results,
        'retmode': 'xml',
        'sort': 'relevance'
    }
    
    try:
        response = requests.get(search_url, params=search_params, timeout=30)
        response.raise_for_status()
        tree = ElementTree.fromstring(response.content)
        
        # Extract PMIDs
        pmids = []
        for id_elem in tree.findall('.//Id'):
            pmids.append(id_elem.text)
        
        if not pmids:
            return []
        
        print(f"Found {len(pmids)} PubMed articles. Converting to PMC IDs...")
        
        # Convert PMIDs to PMCIDs
        pmc_ids = []
        for pmid in pmids:
            pmcid = convert_pmid_to_pmcid(pmid)
            if pmcid:
                pmc_ids.append(pmcid)
                print(f"✅ PMID {pmid} → {pmcid}")
            else:
                print(f"❌ PMID {pmid} → No PMC version")
        
        return pmc_ids
        
    except Exception as e:
        print(f"PubMed search failed: {e}")
        return []

def get_paper_details(pmc_ids):
    """Get detailed information about papers including titles and authors"""
    if not pmc_ids:
        return []
    
    # Get paper details
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    ids_str = ",".join([id.replace("PMC", "") for id in pmc_ids])
    
    params = {
        'db': 'pmc',
        'id': ids_str,
        'retmode': 'xml'
    }
    
    try:
        response = requests.get(summary_url, params=params, timeout=30)
        response.raise_for_status()
        tree = ElementTree.fromstring(response.content)
        
        papers = []
        for doc_sum in tree.findall('.//DocSum'):
            pmcid = None
            title = "Unknown Title"
            authors = "Unknown Authors"
            
            # Extract PMC ID
            id_elem = doc_sum.find('Id')
            if id_elem is not None:
                pmcid = f"PMC{id_elem.text}"
            
            # Extract title and authors
            for item in doc_sum.findall('.//Item'):
                name = item.get('Name', '')
                if name == 'Title':
                    title = item.text or "Unknown Title"
                elif name == 'AuthorList':
                    authors = item.text or "Unknown Authors"
            
            if pmcid:
                papers.append({
                    'pmcid': pmcid,
                    'title': title,
                    'authors': authors
                })
        
        return papers
        
    except Exception as e:
        print(f"Failed to get paper details: {e}")
        return [{'pmcid': pmcid, 'title': 'Unknown', 'authors': 'Unknown'} for pmcid in pmc_ids]
    
def download_with_selenium(PMCID):
    """Method 1: Let Selenium handle the download directly"""
    print("=== Method 1: Selenium Direct Download ===")
    
    # Setup download directory
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "plugins.always_open_pdf_externally": True,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    # You can use headless if you want:
    options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        base_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{PMCID}/"
        driver.get(base_url)
        time.sleep(3)

        # Find anchor link with class and aria-label="Download PDF"
        pdf_elem = driver.find_element(By.XPATH, "//a[@aria-label='Download PDF']")
        relative_url = pdf_elem.get_attribute("href")
        pdf_url = urljoin(base_url, relative_url)  # Make it absolute
        print(f"PDF URL: {pdf_url}")

        driver.get(base_url)
        time.sleep(3)
        
        # Find and click the PDF download link
        pdf_elem = driver.find_element(By.XPATH, "//a[@aria-label='Download PDF']")
        pdf_elem.click()
        
        print("✅ PDF download initiated. Check your downloads folder.")
        time.sleep(5)  # Wait for download to complete
        
    except Exception as e:
        print(f"❌ Error with Selenium method: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    PMCID = "PMC10054724"
    download_with_selenium(PMCID)
