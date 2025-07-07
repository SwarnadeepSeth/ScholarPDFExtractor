from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time, os
import requests
from xml.etree import ElementTree as ElementTree
import json
from datetime import datetime

class PubMedDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = os.path.join(os.getcwd(), download_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        
    def search_pubmed_and_convert(self, search_term, max_results=10):
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
                print("❌ No articles found")
                return [], {}
            
            print(f"Found {len(pmids)} PubMed articles. Converting to PMC IDs...")
            
            # Convert PMIDs to PMCIDs and track mapping
            pmc_ids = []
            pmid_to_pmcid_map = {}
            for pmid in pmids:
                pmcid = self.convert_pmid_to_pmcid(pmid)
                if pmcid:
                    pmc_ids.append(pmcid)
                    pmid_to_pmcid_map[pmid] = pmcid
                    print(f"✅ PMID {pmid} → {pmcid}")
                else:
                    print(f"❌ PMID {pmid} → No PMC version")
            
            return pmc_ids, pmid_to_pmcid_map
            
        except Exception as e:
            print(f"PubMed search failed: {e}")
            return [], {}

    def convert_pmid_to_pmcid(self, pmid):
        """Convert a PMID to PMCID using NCBI's ID converter"""
        try:
            converter_url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
            params = {
                'tool': 'pubmed_downloader',
                'email': 'user@example.com',
                'ids': pmid,
                'format': 'json'
            }
            
            response = requests.get(converter_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'records' in data and len(data['records']) > 0:
                record = data['records'][0]
                if 'pmcid' in record:
                    return record['pmcid']
            
            return None
            
        except Exception as e:
            print(f"Conversion failed for PMID {pmid}: {e}")
            return None

    def get_paper_details(self, pmc_ids, original_pmids):
        """Get detailed information about papers including titles, DOI, and PMID"""
        if not pmc_ids:
            return []
        
        # Get paper details from PMC
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
                doi = "Unknown DOI"
                
                # Extract PMC ID
                id_elem = doc_sum.find('Id')
                if id_elem is not None:
                    pmcid = f"PMC{id_elem.text}"
                
                # Extract title and DOI
                for item in doc_sum.findall('.//Item'):
                    name = item.get('Name', '')
                    if name == 'Title':
                        title = item.text or "Unknown Title"
                    elif name == 'DOI':
                        doi = item.text or "Unknown DOI"
                
                if pmcid:
                    # Find corresponding PMID
                    pmid = "Unknown PMID"
                    for orig_pmid, converted_pmcid in original_pmids.items():
                        if converted_pmcid == pmcid:
                            pmid = orig_pmid
                            break
                    
                    papers.append({
                        'pmcid': pmcid,
                        'pmid': pmid,
                        'title': title,
                        'doi': doi
                    })
            
            return papers
            
        except Exception as e:
            print(f"Failed to get paper details: {e}")
            return [{'pmcid': pmcid, 'pmid': 'Unknown', 'title': 'Unknown', 'doi': 'Unknown'} for pmcid in pmc_ids]

    def download_with_selenium(self, pmcid, paper_info=None):
        """Download PDF using Selenium and rename according to PMCID"""
        print(f"\n📄 Downloading {pmcid}...")
        if paper_info:
            print(f"PMID: {paper_info['pmid']}")
            print(f"Title: {paper_info['title'][:80]}...")
            print(f"DOI: {paper_info['doi']}")
        
        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        # Run headless for batch downloads
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            base_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            driver.get(base_url)
            time.sleep(2)
            
            # Find PDF download link
            pdf_elem = driver.find_element(By.XPATH, "//a[@aria-label='Download PDF']")
            pdf_elem.click()
            
            print(f"✅ {pmcid} download initiated")
            time.sleep(5)  # Increased wait time to ensure download completes
            
            # Rename the downloaded file
            downloaded_file = self._find_latest_downloaded_file()
            if downloaded_file:
                new_filename = f"{pmcid}.pdf"
                new_filepath = os.path.join(self.download_dir, new_filename)
                
                # Check if the target filename already exists
                if os.path.exists(new_filepath):
                    print(f"⚠️ File {new_filename} already exists, skipping rename.")
                else:
                    os.rename(downloaded_file, new_filepath)
                    print(f"✅ Renamed downloaded file to {new_filename}")
            else:
                print(f"❌ Could not find downloaded file for {pmcid}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading {pmcid}: {e}")
            return False
        finally:
            driver.quit()
    def _find_latest_downloaded_file(self):
        """Find the most recently downloaded PDF file in the download directory"""
        try:
            files = [os.path.join(self.download_dir, f) for f in os.listdir(self.download_dir) if f.endswith('.pdf')]
            if not files:
                return None
            # Return the most recently modified PDF file
            return max(files, key=os.path.getmtime)
        except Exception as e:
            print(f"Error finding latest downloaded file: {e}")
            return None
    def save_search_results(self, papers, search_term):
        """Save search results to JSON file"""
        results = {
            'search_term': search_term,
            'search_date': datetime.now().isoformat(),
            'total_papers': len(papers),
            'papers': papers
        }
        
        filename = f"search_results_{search_term.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.download_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Search results saved to: {filename}")

    def search_and_download(self, search_term, max_results=10, download_method='selenium'):
        """Complete workflow: search, get details, and download PDFs"""
        print(f"\n🚀 Starting PubMed search and download for: '{search_term}'")
        print(f"Max results: {max_results}")
        print(f"Download method: {download_method}")
        print(f"Download directory: {self.download_dir}")
        print("-" * 60)
        
        # Step 1: Search PubMed and convert to PMC IDs
        pmc_ids, pmid_mapping = self.search_pubmed_and_convert(search_term, max_results)
        
        if not pmc_ids:
            print("❌ No PMC articles found. Exiting.")
            return
        
        # Step 2: Get paper details
        papers = self.get_paper_details(pmc_ids, pmid_mapping)
        
        # Step 3: Save search results
        self.save_search_results(papers, search_term)
        
        # Step 4: Download PDFs
        print(f"\n📥 Starting downloads for {len(papers)} papers...")
        successful_downloads = 0
        
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}] Processing {paper['pmcid']}...")
            
            if download_method == 'selenium':
                success = self.download_with_selenium(paper['pmcid'], paper)
            else:
                success = self.download_with_requests(paper['pmcid'], paper)
            
            if success:
                successful_downloads += 1
            
            # Small delay between downloads to be respectful
            time.sleep(2)
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎯 DOWNLOAD SUMMARY")
        print(f"Search term: {search_term}")
        print(f"Total papers found: {len(papers)}")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Download directory: {self.download_dir}")
        print("=" * 60)

def main():
    """Main function with user input"""
    downloader = PubMedDownloader()
    
    print("🔬 PubMed PDF Downloader")
    print("=" * 40)
    
    # Get search term from user
    search_term = input("Enter your search term: ").strip()
    
    if not search_term:
        print("❌ No search term provided. Exiting.")
        return
    
    # Get max results
    try:
        max_results = int(input("Number of papers to download (default 5): ") or "5")
    except ValueError:
        max_results = 5
    
    # Get download method
    method = 'selenium'
    
    # Run the search and download
    downloader.search_and_download(search_term, max_results, method)

if __name__ == "__main__":
    main()