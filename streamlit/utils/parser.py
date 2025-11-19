import pandas as pd

def clean_taxcertificate(df):
    if "TaxCertificate" in df.columns:
        df["TaxCertificate"] = df["TaxCertificate"].astype(str).str.strip()
        df.loc[df["TaxCertificate"] == "9", "TaxCertificate"] = "Tanpa Fasilitas"
    return df

def parse_lampiran(spt_choice,details):
    """Parse list of invoice JSON payloads into multiple DataFrames."""
    dfs = {}

    if not details:
        return dfs
    
    # Extract each section conditionally
    match spt_choice:
        case 'PPN':
            # --- A-1 ---
            try:
                raw_data = details[0]
                if len(raw_data) == 0 : 
                    df_a1 = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_a1 = pd.DataFrame(records)[["Name", "DocumentNumber", "DocumentDate", "TaxBase", "Information"]]
            except Exception as e:
                print("Error parsing df_a1:", e)
                df_a1 = pd.DataFrame(columns=["Name", "DocumentNumber", "DocumentDate", "TaxBase", "Information"])

            # --- A-2 ---
            try:
                raw_data = details[1]  
                if len(raw_data) == 0 : 
                    df_a2 = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_a2 = pd.DataFrame(records)[["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase", "OtherTaxBase", "VAT","STLG", "TaxInvoiceCode","DocumentNumberByBuyerInfor"]]
            except Exception as e:
                print("Error parsing df_a2:", e)
                df_a2 = pd.DataFrame(columns=["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase", "OtherTaxBase", "VAT","STLG", "TaxInvoiceCode","DocumentNumberByBuyerInfor"])
                
            # --- B-1 ---
            try:
                raw_data = details[2]  
                if len(raw_data) == 0 : 
                    df_b1 = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_b1 = pd.DataFrame(records)[["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase", "VAT","STLG", "Information"]]
            except Exception as e:
                print("Error parsing df_b1:", e)
                df_b1 = pd.DataFrame(columns=["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase", "VAT","STLG", "Information"])
                
            # --- B-2 ---
            try:
                raw_data = details[3] 
                if len(raw_data) == 0 : 
                    df_b2 = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_b2 = pd.DataFrame(records)[["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase","OtherTaxBase", "VAT","STLG","TaxInvoiceCode"]]
            except Exception as e:
                print("Error parsing df_b2:", e)
                df_b2 = pd.DataFrame(columns=["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase","OtherTaxBase", "VAT","STLG","TaxInvoiceCode"])    
            
           # --- B-3 ---
            try:
                raw_data = details[4] 
                if len(raw_data) == 0 : 
                    df_b3 = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_b3 = pd.DataFrame(records)[["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase", "OtherTaxBase", "VAT","STLG","TaxInvoiceCode"]]
            except Exception as e:
                print("Error parsing df_b3:", e)
                df_b3 = pd.DataFrame(columns=["Name", "TIN", "DocumentNumber", "DocumentDate", "TaxBase", "OtherTaxBase", "VAT","STLG","TaxInvoiceCode"])
            
            dfs = {
                "A-1":df_a1,
                "A-2":df_a2,
                "B-1":df_b1,
                "B-2":df_b2,
                "B-3":df_b3,
            }
        case 'PPh21':
            # --- L-IA ---
            try:
                raw_data = details[0]
                if len(raw_data) == 0 : 
                    df_l1a = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_l1a = pd.DataFrame(records)[["TIN", "Name", "WithholdingSlipsNumber", "WithholdingSlipsDate", "TaxObjectCode","GrossIncome", "TaxRate", "IncomeTax","TaxCertificate", "CountryCode","PlaceOfBusinessID", "RevenueCode", "Status"]]
                    df_l1a = clean_taxcertificate(df_l1a)
            except Exception as e:
                print("Error parsing df_l1a:", e)
                df_l1a = pd.DataFrame(columns=["TIN", "Name", "WithholdingSlipsNumber", "WithholdingSlipsDate", "TaxObjectCode","GrossIncome", "TaxRate", "IncomeTax","TaxCertificate", "CountryCode","PlaceOfBusinessID", "RevenueCode", "Status"])

            # --- L-III ---
            try:
                raw_data = details[1]  
                if len(raw_data) == 0 : 
                    df_l3 = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_l3 = pd.DataFrame(records)[["TIN", "Name", "TaxArticle", "WithholdingNumber", "WithholdingDate", "TaxObjectCode", "TaxObject", "GrossIncome", "IncomeTax","TaxCertificate","PlaceOfBusinessID", "RevenueCode", "Status"]]
                    df_l3 = clean_taxcertificate(df_l3)
            except Exception as e:
                print("Error parsing df_l3:", e)
                df_l3 = pd.DataFrame(columns=["TIN", "Name", "TaxArticle", "WithholdingNumber", "WithholdingDate", "TaxObjectCode", "TaxObject", "GrossIncome", "IncomeTax","TaxCertificate","PlaceOfBusinessID", "RevenueCode", "Status"])
            
            dfs = {
                "L-IA":df_l1a,
                "L-III":df_l3,
            }
        case 'Unifikasi':
            # --- DAFTAR-I ---
            try:
                raw_data = details[0]  
                if len(raw_data) == 0 : 
                    df_bppu = pd.DataFrame()
                else:
                    records = raw_data.get("Data", []) if isinstance(raw_data, dict) else []
                    df_bppu = pd.DataFrame(records)[["TaxIdentificationNumber", "TaxpayerName", "WithholdingSlipsNumber", "WithholdingSlipsDate","TaxArticle", "TaxObjectCode", "TaxObject", "TaxBase", "TaxRate", "IncomeTax","TaxCertificate", "PaymentMethod","BranchId", "Status", "RevenueCode"]]
                    df_bppu = clean_taxcertificate(df_bppu)
            except Exception as e:
                print("Error parsing df_bppu:", e)
                df_bppu = pd.DataFrame(columns=["TaxIdentificationNumber", "TaxpayerName", "WithholdingSlipsNumber", "WithholdingSlipsDate","TaxArticle", "TaxObjectCode", "TaxObject", "TaxBase", "TaxRate", "IncomeTax","TaxCertificate", "PaymentMethod","BranchId", "Status", "RevenueCode"])
            
            dfs = {
                "DAFTAR-I":df_bppu,
            }
            
    return dfs
