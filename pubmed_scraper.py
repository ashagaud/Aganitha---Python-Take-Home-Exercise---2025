import requests
import pandas as pd
import xml.etree.ElementTree as ET
from Bio import Entrez
import re
import argparse

# Configure PubMed API
Entrez.email = "your-email@example.com"

# Heuristic to detect non-academic affiliations
COMPANY_KEYWORDS = ["pharma", "biotech", "inc", "ltd", "corporation", "genomics", "therapeutics"]


def fetch_pubmed_papers(query, max_results=10, debug=False):
    """Fetch research papers from PubMed using the provided query."""
    search_handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    search_results = Entrez.read(search_handle)
    search_handle.close()
    
    paper_ids = search_results["IdList"]
    if debug:
        print(f"Found {len(paper_ids)} papers for query: {query}")
    
    papers = []
    for paper_id in paper_ids:
        fetch_handle = Entrez.efetch(db="pubmed", id=paper_id, retmode="xml")
        xml_data = fetch_handle.read()
        fetch_handle.close()
        
        root = ET.fromstring(xml_data)
        for article in root.findall(".//PubmedArticle"):
            title = article.findtext(".//ArticleTitle", default="Unknown Title")
            pub_date = article.findtext(".//PubDate/Year", default="Unknown Date")
            authors = []
            companies = []
            email = "Not Available"
            
            for author in article.findall(".//Author"):
                last_name = author.findtext("LastName", default="")
                fore_name = author.findtext("ForeName", default="")
                affiliation = author.findtext(".//Affiliation", default="")
                
                full_name = f"{fore_name} {last_name}".strip()
                if full_name:
                    authors.append(full_name)

                if affiliation and any(keyword in affiliation.lower() for keyword in COMPANY_KEYWORDS):
                    companies.append(affiliation)
                
                # Extract email if available
                email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", affiliation)
                if email_match:
                    email = email_match.group(0)
            
            # If at least one non-academic author is found, store paper
            if companies:
                papers.append([paper_id, title, pub_date, ", ".join(authors), ", ".join(companies), email])
    
    return papers


def save_to_csv(data, filename):
    """Save extracted data to a CSV file."""
    df = pd.DataFrame(data, columns=["PubmedID", "Title", "Publication Date", "Non-academic Authors", "Company Affiliations", "Corresponding Author Email"])
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")


def main():
    """Command-line interface for fetching PubMed research papers."""
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument("-q", "--query", required=True, help="Search query for PubMed.")
    parser.add_argument("-f", "--file", default="papers.csv", help="Filename to save results (default: papers.csv).")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")

    args = parser.parse_args()

    papers = fetch_pubmed_papers(args.query, debug=args.debug)
    if papers:
        save_to_csv(papers, args.file)
    else:
        print("No relevant papers found.")


if __name__ == "__main__":
    main()
