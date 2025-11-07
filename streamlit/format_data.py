import streamlit as st
import pandas as pd
import io

def format_date(date_str):
    """Convert ISO date string (2025-09-17T00:00:00) to YYYY/MM/DD format."""
    try:
        return pd.to_datetime(date_str).strftime("%Y/%m/%d")
    except Exception:
        return ""

def get_period_end_date(period_code, year):
    """
    Map Coretax TD.007XX period codes to the end-of-month date.
    Example: TD.00709 + 2025 → 30/09/2025
    """
    if not period_code:
        return ""
    try:
        base_date = month_end_map.get(period_code[:8], "")  # first 8 chars e.g. TD.00709
        if base_date and year:
            return f"{year}{base_date}"
        return base_date
    except Exception:
        return ""



payloads = [
    {
        "RecordId": "b16a6adc-76ac-4b4f-aaf8-30ea58dcd3c0",
        "AggregateIdentifier": "ff585d7b-3863-4fe3-968c-12ea261e9712",
        "AggregateVersion": 1,
        "FormData": "{\"TransactionDocumentData\":{\"DownPayment\":False,\"RestOfPayment\":False,\"TaxInvoiceNumber\":\"04002500298459047\",\"TransactionCode\":\"TD.00304\",\"TransactionType\":"",\"DocumentNumber\":"",\"DocumentDate\":"",\"InvoiceDate\":\"2025-09-17T00:00:00\",\"InvoiceType\":\"TD.00400\",\"AdditionalInformation\":\"\",\"Period\":\"TD.00709\",\"Year\":\"2025\",\"CustomDocument\":\"\",\"Reference\":\"SBY MH-SI25091268\",\"FacilityStamp\":\"\",\"PlaceOfBusinessActivity\":\"0850507476604000000000\",\"SP2DNumber\":"",\"SellerAddress\":\"JL RAYA TANDES LOR NO.22B, RT 005, RW 001, TANDES, TANDES, KOTA SURABAYA, JAWA TIMUR 60185\",\"PeriodCredit\":"",\"YearCredit\":"",\"ContractDuration\":""},\"BuyerInformationData\":{\"BuyerTIN\":\"0638937201609000\",\"IDDocument\":\"BY.00204\",\"IDDocumentCountry\":\"IDN\",\"IDDocumentNumber\":\"-\",\"BuyerTaxpayerName\":\"CAHAY****************************\",\"BuyerTaxpayerNameInClear\":\"CAHAYA SARIPANGAN MANDIRI OPTIMUS\",\"BuyerTaxpayerAddress\":\"JL INDRAGIRI NO 08 , RT 000, RW 000, DARMO, WONOKROMO, KOTA SURABAYA, JAWA TIMUR 60241\",\"BuyerTaxpayerEmail\":\"cahayasmoptimus@gmail.com\",\"BussinessCode\":\"0638937201609000000000\"},\"TransactionDetailsData\":{\"Rows\":[{\"Type\":\"GOODS\",\"Name\":\"SARI CHOCO PASTE 2X5kg\",\"Code\":\"180600\",\"Quantity\":1.0,\"Unit\":\"UM.0022\",\"UnitPrice\":353189.19,\"TotalPrice\":353189.19,\"Discount\":0.0,\"VATRate\":0.12,\"TaxBase\":353189.19,\"OtherTaxBaseCheck\":True,\"OtherTaxBase\":323756.76,\"VAT\":38850.81,\"STLGRate\":0.0,\"STLG\":0.00}],\"FooterRow\":{\"TotalPrice\":353189.0,\"TotalDiscount\":0.0,\"TaxBaseTotal\":353189.0,\"OtherTaxBaseTotal\":323757.0,\"VATTotal\":38851.0,\"STLGTotal\":0.0,\"DownPayment\":0.0,\"TotalDownpaymentSum\":0.0,\"TotalDownpaymentHistoriesOtherTaxBaseSum\":0.0,\"RestOfPayment\":0.0,\"TaxBase\":353189.19,\"OtherTaxBase\":323757.0,\"STLG\":0.0,\"VAT\":38851.0,\"DownpaymentHistories\":[]}},\"IsDraft\":True,\"IsMigrated\":False,\"LastUpdatedBy\":"",\"LastUpdatedDate\":\"0001-01-01T00:00:00\"}",
        "InvoiceStatus": "APPROVED",
        "BuyerStatus": "",
        "FormDataObj": {
            "TransactionDocumentData": {
                "DownPayment": False,
                "RestOfPayment": False,
                "TaxInvoiceNumber": "04002500298459047",
                "TransactionCode": "TD.00304",
                "TransactionType": "",
                "DocumentNumber": "",
                "DocumentDate": "",
                "InvoiceDate": "2025-09-17T00:00:00",
                "InvoiceType": "TD.00400",
                "AdditionalInformation": "",
                "Period": "TD.00709",
                "Year": "2025",
                "CustomDocument": "",
                "Reference": "SBY MH-SI25091268",
                "FacilityStamp": "",
                "PlaceOfBusinessActivity": "0850507476604000000000",
                "SP2DNumber": "",
                "SellerAddress": "JL RAYA TANDES LOR NO.22B, RT 005, RW 001, TANDES, TANDES, KOTA SURABAYA, JAWA TIMUR 60185",
                "PeriodCredit": "",
                "YearCredit": "",
                "ContractDuration": ""
            },
            "BuyerInformationData": {
                "BuyerTIN": "0638937201609000",
                "IDDocument": "BY.00204",
                "IDDocumentCountry": "IDN",
                "IDDocumentNumber": "-",
                "BuyerTaxpayerName": "CAHAY****************************",
                "BuyerTaxpayerNameInClear": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
                "BuyerTaxpayerAddress": "JL INDRAGIRI NO 08 , RT 000, RW 000, DARMO, WONOKROMO, KOTA SURABAYA, JAWA TIMUR 60241",
                "BuyerTaxpayerEmail": "cahayasmoptimus@gmail.com",
                "BussinessCode": "0638937201609000000000"
            },
            "TransactionDetailsData": {
                "Rows": [
                    {
                        "Type": "GOODS",
                        "Name": "SARI CHOCO PASTE 2X5kg",
                        "Code": "180600",
                        "Quantity": 1.0,
                        "OriginalQuantity": "",
                        "Unit": "UM.0022",
                        "UnitPrice": 353189.19,
                        "TotalPrice": 353189.19,
                        "Discount": 0.0,
                        "VATRate": 0.12,
                        "TaxBase": 353189.19,
                        "OtherTaxBaseCheck": True,
                        "OtherTaxBase": 323756.76,
                        "VAT": 38850.81,
                        "STLGRate": 0.0,
                        "STLG": 0.00
                    }
                ],
                "FooterRow": {
                    "TotalPrice": 353189.0,
                    "TotalDiscount": 0.0,
                    "TaxBaseTotal": 353189.0,
                    "OtherTaxBaseTotal": 323757.0,
                    "VATTotal": 38851.0,
                    "STLGTotal": 0.0,
                    "DownPayment": 0.0,
                    "TotalDownpaymentSum": 0.0,
                    "TotalDownpaymentHistoriesOtherTaxBaseSum": 0.0,
                    "RestOfPayment": 0.0,
                    "TaxBase": 353189.19,
                    "OtherTaxBase": 323757.0,
                    "STLG": 0.0,
                    "VAT": 38851.0,
                    "DownpaymentHistories": []
                }
            },
            "IsDraft": True,
            "IsMigrated": False,
            "LastUpdatedBy": "",
            "LastUpdatedDate": "0001-01-01T00:00:00"
        },
        "HasSubsequentDownRestPayment": False,
        "Valid": True,
        "IsDelete": "",
        "SellerTaxpayerAggregateIdentifier": "f8e6e37c-a183-b86f-c527-575af759e5c3",
        "SellerTIN": "0850507476604000",
        "SellerName": "SAERAH SURYA PERKASA",
        "BuyerTaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701",
        "BuyerTIN": "0638937201609000",
        "BuyerName": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
        "TaxInvoiceDate": "2025-09-17T00:00:00+07:00",
        "AdditionalInformation": "",
        "InvoiceType": "TD.00400",
        "DownpaymentParentIdentifier": "",
        "TransactionCode": "TD.00304",
        "TaxInvoiceNumber": "04002500298459047",
        "IsMigrated": False,
        "Sp2dNumber": "",
        "LastUpdatedBy": "",
        "LastUpdatedDate": "2025-10-31T08:41:45+07:00"
    },
    {
        "RecordId": "b16a6adc-76ac-4b4f-aaf8-30ea58dcd3c0",
        "AggregateIdentifier": "ff585d7b-3863-4fe3-968c-12ea261e9712",
        "AggregateVersion": 1,
        "FormData": "{\"TransactionDocumentData\":{\"DownPayment\":False,\"RestOfPayment\":False,\"TaxInvoiceNumber\":\"04002500298459047\",\"TransactionCode\":\"TD.00304\",\"TransactionType\":"",\"DocumentNumber\":"",\"DocumentDate\":"",\"InvoiceDate\":\"2025-09-17T00:00:00\",\"InvoiceType\":\"TD.00400\",\"AdditionalInformation\":\"\",\"Period\":\"TD.00709\",\"Year\":\"2025\",\"CustomDocument\":\"\",\"Reference\":\"SBY MH-SI25091268\",\"FacilityStamp\":\"\",\"PlaceOfBusinessActivity\":\"0850507476604000000000\",\"SP2DNumber\":"",\"SellerAddress\":\"JL RAYA TANDES LOR NO.22B, RT 005, RW 001, TANDES, TANDES, KOTA SURABAYA, JAWA TIMUR 60185\",\"PeriodCredit\":"",\"YearCredit\":"",\"ContractDuration\":""},\"BuyerInformationData\":{\"BuyerTIN\":\"0638937201609000\",\"IDDocument\":\"BY.00204\",\"IDDocumentCountry\":\"IDN\",\"IDDocumentNumber\":\"-\",\"BuyerTaxpayerName\":\"CAHAY****************************\",\"BuyerTaxpayerNameInClear\":\"CAHAYA SARIPANGAN MANDIRI OPTIMUS\",\"BuyerTaxpayerAddress\":\"JL INDRAGIRI NO 08 , RT 000, RW 000, DARMO, WONOKROMO, KOTA SURABAYA, JAWA TIMUR 60241\",\"BuyerTaxpayerEmail\":\"cahayasmoptimus@gmail.com\",\"BussinessCode\":\"0638937201609000000000\"},\"TransactionDetailsData\":{\"Rows\":[{\"Type\":\"GOODS\",\"Name\":\"SARI CHOCO PASTE 2X5kg\",\"Code\":\"180600\",\"Quantity\":1.0,\"Unit\":\"UM.0022\",\"UnitPrice\":353189.19,\"TotalPrice\":353189.19,\"Discount\":0.0,\"VATRate\":0.12,\"TaxBase\":353189.19,\"OtherTaxBaseCheck\":True,\"OtherTaxBase\":323756.76,\"VAT\":38850.81,\"STLGRate\":0.0,\"STLG\":0.00}],\"FooterRow\":{\"TotalPrice\":353189.0,\"TotalDiscount\":0.0,\"TaxBaseTotal\":353189.0,\"OtherTaxBaseTotal\":323757.0,\"VATTotal\":38851.0,\"STLGTotal\":0.0,\"DownPayment\":0.0,\"TotalDownpaymentSum\":0.0,\"TotalDownpaymentHistoriesOtherTaxBaseSum\":0.0,\"RestOfPayment\":0.0,\"TaxBase\":353189.19,\"OtherTaxBase\":323757.0,\"STLG\":0.0,\"VAT\":38851.0,\"DownpaymentHistories\":[]}},\"IsDraft\":True,\"IsMigrated\":False,\"LastUpdatedBy\":"",\"LastUpdatedDate\":\"0001-01-01T00:00:00\"}",
        "InvoiceStatus": "APPROVED",
        "BuyerStatus": "",
        "FormDataObj": {
            "TransactionDocumentData": {
                "DownPayment": False,
                "RestOfPayment": False,
                "TaxInvoiceNumber": "04002500298459047",
                "TransactionCode": "TD.00304",
                "TransactionType": "",
                "DocumentNumber": "",
                "DocumentDate": "",
                "InvoiceDate": "2025-09-17T00:00:00",
                "InvoiceType": "TD.00400",
                "AdditionalInformation": "",
                "Period": "TD.00709",
                "Year": "2025",
                "CustomDocument": "",
                "Reference": "SBY MH-SI25091268",
                "FacilityStamp": "",
                "PlaceOfBusinessActivity": "0850507476604000000000",
                "SP2DNumber": "",
                "SellerAddress": "JL RAYA TANDES LOR NO.22B, RT 005, RW 001, TANDES, TANDES, KOTA SURABAYA, JAWA TIMUR 60185",
                "PeriodCredit": "",
                "YearCredit": "",
                "ContractDuration": ""
            },
            "BuyerInformationData": {
                "BuyerTIN": "0638937201609000",
                "IDDocument": "BY.00204",
                "IDDocumentCountry": "IDN",
                "IDDocumentNumber": "-",
                "BuyerTaxpayerName": "CAHAY****************************",
                "BuyerTaxpayerNameInClear": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
                "BuyerTaxpayerAddress": "JL INDRAGIRI NO 08 , RT 000, RW 000, DARMO, WONOKROMO, KOTA SURABAYA, JAWA TIMUR 60241",
                "BuyerTaxpayerEmail": "cahayasmoptimus@gmail.com",
                "BussinessCode": "0638937201609000000000"
            },
            "TransactionDetailsData": {
                "Rows": [
                    {
                        "Type": "GOODS",
                        "Name": "SARI CHOCO PASTE 2X5kg",
                        "Code": "180600",
                        "Quantity": 1.0,
                        "OriginalQuantity": "",
                        "Unit": "UM.0022",
                        "UnitPrice": 353189.19,
                        "TotalPrice": 353189.19,
                        "Discount": 0.0,
                        "VATRate": 0.12,
                        "TaxBase": 353189.19,
                        "OtherTaxBaseCheck": True,
                        "OtherTaxBase": 323756.76,
                        "VAT": 38850.81,
                        "STLGRate": 0.0,
                        "STLG": 0.00
                    }
                ],
                "FooterRow": {
                    "TotalPrice": 353189.0,
                    "TotalDiscount": 0.0,
                    "TaxBaseTotal": 353189.0,
                    "OtherTaxBaseTotal": 323757.0,
                    "VATTotal": 38851.0,
                    "STLGTotal": 0.0,
                    "DownPayment": 0.0,
                    "TotalDownpaymentSum": 0.0,
                    "TotalDownpaymentHistoriesOtherTaxBaseSum": 0.0,
                    "RestOfPayment": 0.0,
                    "TaxBase": 353189.19,
                    "OtherTaxBase": 323757.0,
                    "STLG": 0.0,
                    "VAT": 38851.0,
                    "DownpaymentHistories": []
                }
            },
            "IsDraft": True,
            "IsMigrated": False,
            "LastUpdatedBy": "",
            "LastUpdatedDate": "0001-01-01T00:00:00"
        },
        "HasSubsequentDownRestPayment": False,
        "Valid": True,
        "IsDelete": "",
        "SellerTaxpayerAggregateIdentifier": "f8e6e37c-a183-b86f-c527-575af759e5c3",
        "SellerTIN": "0850507476604000",
        "SellerName": "SAERAH SURYA PERKASA",
        "BuyerTaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701",
        "BuyerTIN": "0638937201609000",
        "BuyerName": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
        "TaxInvoiceDate": "2025-09-17T00:00:00+07:00",
        "AdditionalInformation": "",
        "InvoiceType": "TD.00400",
        "DownpaymentParentIdentifier": "",
        "TransactionCode": "TD.00304",
        "TaxInvoiceNumber": "04002500298459047",
        "IsMigrated": False,
        "Sp2dNumber": "",
        "LastUpdatedBy": "",
        "LastUpdatedDate": "2025-10-31T08:41:45+07:00"
    }
]

column_map = {
    "FormDataObj_TransactionDocumentData_InvoiceDate": "tanggal",
    "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": "nota",
    "SellerTIN": "relasi",
    "kode": "kode",
    "qtybox": "qtybox",
    "qtylsn": "qtylsn",
    "FormDataObj_TransactionDetailsData_Quantity": "qtypcs",
    "hrgbox": "hrgbox",
    "hrglsn": "hrglsn",
    "FormDataObj_TransactionDetailsData_UnitPrice": "hrgpcs",
    "FormDataObj_TransactionDetailsData_Discount": "discount",
    "FormDataObj_TransactionDetailsData_VATRate": "ppn",
    "FormDataObj_TransactionDocumentData_Period": "sptmasa",
    "FormDataObj_TransactionDetailsData_TotalPrice": "jmldpp",
    "FormDataObj_TransactionDetailsData_VAT": "jmlppn",
    "SellerName": "nmsup",
    "FormDataObj_TransactionDetailsData_Name": "nmbrg",
    "divisi": "divisi",
    "TaxInvoiceNumber": "nofp"
}

month_end_map = {
    "TD.00701": "/01/31",
    "TD.00702": "/02/28",
    "TD.00703": "/03/31",
    "TD.00704": "/04/30",
    "TD.00705": "/05/31",
    "TD.00706": "/06/30",
    "TD.00707": "/07/31",
    "TD.00708": "/08/31",
    "TD.00709": "/09/30",
    "TD.00710": "/10/31",
    "TD.00711": "/11/30",
    "TD.00712": "/12/31",
}


try:
    all_rows = []

    for payload in payloads:  # assume this is your list of invoices
        try:
            details = payload["FormDataObj"]["TransactionDetailsData"]["Rows"]
        except (KeyError, TypeError):
            continue  # skip malformed payloads

        for d in details:
            period_code = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Period", "")
            year = payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("Year", "")

            sptmasa_value = get_period_end_date(period_code, year)

            row = {
                # pull in detail-level fields
                # "FormDataObj_TransactionDetailsData_Type": d.get("Type", ""),
                "FormDataObj_TransactionDetailsData_Name": d.get("Name", ""),
                # "FormDataObj_TransactionDetailsData_Code": d.get("Code", ""),
                "FormDataObj_TransactionDetailsData_Quantity": d.get("Quantity", 0),
                # "FormDataObj_TransactionDetailsData_Unit": d.get("Unit", ""),
                "FormDataObj_TransactionDetailsData_UnitPrice": d.get("UnitPrice", 0),
                "FormDataObj_TransactionDetailsData_Discount": d.get("Discount", 0),
                "FormDataObj_TransactionDetailsData_VATRate": d.get("VATRate", 0),
                "FormDataObj_TransactionDetailsData_TotalPrice": d.get("TotalPrice", 0),
                "FormDataObj_TransactionDetailsData_VAT": d.get("VAT", 0),

                # include parent-level info from FormDataObj_TransactionDocumentData
                "FormDataObj_TransactionDocumentData_InvoiceDate": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("InvoiceDate", ""),
                "FormDataObj_TransactionDocumentData_TaxInvoiceNumber": payload.get("FormDataObj", {}).get("TransactionDocumentData", {}).get("TaxInvoiceNumber", ""),
                "FormDataObj_TransactionDocumentData_Period": sptmasa_value,

                # add seller info
                "SellerTIN": payload.get("SellerTIN", ""),
                "SellerName": payload.get("SellerName", ""),
                "TaxInvoiceNumber": payload.get("TaxInvoiceNumber", ""),
            }
            all_rows.append(row)

    df_all = pd.DataFrame(all_rows)
    df_all.rename(columns=column_map, inplace=True)

    # Ensure all target columns exist
    for col in column_map.values():
        if col not in df_all.columns:
            df_all[col] = ""

    # Reorder safely
    df_all = df_all[list(column_map.values())]
    df_all["tanggal"] = df_all["tanggal"].apply(format_date)

    st.write(df_all.columns.tolist())
    st.dataframe(df_all.head())

except Exception as e:
    st.error(e)