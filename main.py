
import argparse
import os
from openai import OpenAI
from graph.workflow import run_workflow
from utils.parser import load_invoice_file
from agents.normalization_agent import normalize_invoice
from schemas.invoice_schema import Invoice
from dotenv import load_dotenv



load_dotenv()  # reads .env file
key = os.getenv("OPENAI_API_KEY")
db_path = "inventory.db"
client = OpenAI(api_key=key)



def process_invoice(file_path):

    run_workflow(client, file_path, db_path)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice_path", required=True, help="Path to invoice file ")
    args = parser.parse_args()
 
    path = args.invoice_path

    if os.path.isdir(path):
        for file in os.listdir(path):
            full_path = os.path.join(path, file)
            process_invoice(full_path)
    else:
        process_invoice(path)


if __name__ == "__main__":
    main()
