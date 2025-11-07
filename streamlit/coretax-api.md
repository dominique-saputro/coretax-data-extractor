# Coretax API Documentation

Here lies all the notes needed for Coretax's API

## Token

First thing, that you'll need to access the API is a token as all the API will need the token as it's authentication.  
To obtain the token, use the [extension](https://insert-link-here)

> [!Important]
> This token changes everytime the representititve switches to a different company.

## User Info

Returns information based on the token's user.  
User's `taxpayer_id` will be used in many future queries as `TaxpayerAggregateIdentifier`

> Link: _/identityproviderportal/connect/userinfo_

Method:

- `GET`

Header:

- Authorization : `Bearer {{token}}`
- Content-Type : `apllication/json`

Body:

- `empty`

Example JSON output:

```
{
   "identifier": "aebced72-3c1a-ba2a-9e21-0bfeff4dcf74",
   "user_name": "0638937201609000",
   "inactivityTimeout": "900",
   "language": "id-ID",
   "lastlogintime": "2025-05-07T11:55:00.000",
   "taxoffice": "609",
   "full_name": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
   "email": "cahayasmoptimus@gmail.com",
   "permissions": "[4,17,18,20,21,25,29,37,41,45,49,53,57,61,62,63,64,
   ...
   921]",
   "roles": "[30,34,38,42,46,1209,31,35,39,43,47,32,36,40,44,1002,33,37,41,45,1104]",
   "user_roles": "[31,1104,1209,44,11,34,40,36,38,32]",
   "taxpayer_id": "8716fc8f-1481-0966-f5cb-5ba92132c701",
   "dataaccesspolicies": "[\"VAT_VATTNTEVATC\",\"AlwaysAllowTaxpayerEdit\",\"VAT_DVAT\",\"AllowEditIfTaxpayerTaxRegionMatchesUserTaxRegion\",\"VAT_VAT\",\"AllowEditIfTaxpayerTaxOfficeMatchesUserTaxOffice\"]",
   "representativeTaxTypes": "[]",
   "representativeSubservices": "[]",
   "representativeFullAddress": "DESA BAMBE ,  RT 008,  RW 001, BAMBE, DRIYOREJO, KAB. GRESIK, JAWA TIMUR, Indonesia 61177",
   "representativePhone": "0811310402",
   "representativeEmailAddress": "siska@orientcomp.com",
   "representativeType": "internal",
   "Impersonating": "true",
   "RepresentativeId": "4fb5cb3e-9542-6c48-a63c-b1a0ed93f9bc",
   "RepresentativeUserId": "0bd8a1f8-f580-63f4-79fa-ddd8672d61f7",
   "RepresentativeUsername": "SISKA",
   "RepresentativeTin": "3525155905860001",
   "sub": "0638937201609000"
}
```

## Pajak Masukan - Header

Returns PM headers **only** based on the defined filters.

> Link: _/einvoiceportal/api/inputinvoice/list_

Method:

- `POST`

Header:

- Authorization : `Bearer {{token}}`
- Content-Type : `apllication/json`

Body:

- `BuyerTaxpayerAggregateIdentifier` -> `taxpayer_id` from [User Info](#user-info)
- `TaxpayerAggregateIdentifier` -> `taxpayer_id` from [User Info](#user-info)

```
{
    "BuyerTaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701",
    "First": 0,
    "Rows": 50,
    "SortField": "",
    "SortOrder": 1,
    "Filters": [
        {
            "PropertyName": "TaxInvoicePeriod",
            "Value": [
                "TD.00709",
                "TD.00710"
            ],
            "MatchMode": "contains",
            "CaseSensitive": true,
            "AsString": false
        },
        {
            "PropertyName": "TaxInvoiceYear",
            "Value": 2025,
            "MatchMode": "equals",
            "CaseSensitive": true,
            "AsString": false
        },
        {
            "PropertyName": "TaxInvoiceStatus",
            "Value": "APPROVED",
            "MatchMode": "equals",
            "CaseSensitive": true,
            "AsString": false
        }
    ],
    "LanguageId": "id-ID",
    "TaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701"
}
```

Example JSON output:

```
{
   "IsSuccessful": true,
    "Message": null,
    "ErrorType": 0,
    "Payload": {
        "TotalRecords": 100,
        "Data": [
            {
                "SP2DNumber": null,
                "RecordId": "b16a6adc-76ac-4b4f-aaf8-30ea58dcd3c0",
                "AggregateIdentifier": "ff585d7b-3863-4fe3-968c-12ea261e9712",
                "SellerTaxpayerAggregateIdentifier": "f8e6e37c-a183-b86f-c527-575af759e5c3",
                "BuyerTaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701",
                "CreatedBySeller": false,
                "SellerTIN": "0850507476604000",
                "BuyerTIN": "0638937201609000",
                "DocumentNumber": null,
                "SellerTaxpayerName": "SAERAH SURYA PERKASA",
                "BuyerTaxpayerNameClear": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
                "BuyerTaxpayerName": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
                "BuyerName": null,
                "TaxInvoiceCode": "TD.00304",
                "TaxInvoiceNumber": "04002500298459047",
                "TaxInvoiceDate": "2025-09-17T00:00:00+07:00",
                "TaxInvoicePeriod": "TD.00709",
                "TaxInvoiceYear": "2025",
                "TaxInvoiceStatus": "APPROVED",
                "BuyerStatus": null,
                "SellingPrice": 353189,
                "OtherTaxBase": 323757,
                "VAT": 38851,
                "STLG": 0,
                "Signer": "MARGARETH TAN",
                "DownpaymentParentIdentifier": "00000000-0000-0000-0000-000000000000",
                "DownpaymentSum": 0,
                "AmendedRecordId": null,
                "Valid": true,
                "ReportedByBuyer": false,
                "ReportedBySeller": true,
                "ReportedByVATCollector": null,
                "LastUpdatedDate": "2025-10-31T08:41:45+07:00",
                "CreationDate": "2025-09-19T14:25:23+07:00",
                "PeriodCredit": null,
                "YearCredit": null,
                "InputInvoiceStatus": "APPROVED",
                "DocumentFormNumber": "DN2025638939256974742660000",
                "DocumentFormAggregateIdentifier": "f2d7ad0d-10ed-4002-8042-0035c4769b9a",
                "ESignStatus": "Done",
                "AmendedDocumentFormNumber": null,
                "AmendedDocumentFormAggregateIdentifier": null,
                "CanceledDocumentFormNumber": null,
                "CanceledDocumentFormAggregateIdentifier": null,
                "IsShowCancelInGrid": true,
                "Reference": null,
                "ChannelCode": null,
                "DisplayName": null,
                "IsMigrated": false,
                "IdDocument": null,
                "IdDocumentCountry": null,
                "IdDocumentNumber": null,
                "SellerLastUpdatedDate": "0001-01-01T00:00:00",
                "SellingPriceRemainingAmount": null,
                "OtherTaxBaseRemainingAmount": null,
                "VATRemainingAmount": null,
                "STLGRemainingAmount": null,
                "LastUpdatedBy": null,
                "CreatedBy": null
            },
    ...
}
```

## Pajak Masukan - Details

Returns PM details **only** based on the PM Headers.

> Link: _/einvoiceportal/api/inputinvoice/view_

Method:

- `POST`

Header:

- Authorization : `Bearer {{token}}`
- Content-Type : `apllication/json`

Body:

- `RecordIdentifier` -> `RecordId` from [Header](#pajak-masukan---header)
- `TaxpayerAggregateIdentifier` -> `taxpayer_id` from [User Info](#user-info)

```
{
    "RecordIdentifier": "b16a6adc-76ac-4b4f-aaf8-30ea58dcd3c0",
    "EinvoiceVATStatus": "",
    "TaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701"
}
```

Example JSON output:

```
{
   "IsSuccessful": true,
    "Message": null,
    "ErrorType": 0,
    "Payload": {
        "TotalRecords": 100,
        "Data": [
            {
                "SP2DNumber": null,
                "RecordId": "b16a6adc-76ac-4b4f-aaf8-30ea58dcd3c0",
                "AggregateIdentifier": "ff585d7b-3863-4fe3-968c-12ea261e9712",
                "SellerTaxpayerAggregateIdentifier": "f8e6e37c-a183-b86f-c527-575af759e5c3",
                "BuyerTaxpayerAggregateIdentifier": "8716fc8f-1481-0966-f5cb-5ba92132c701",
                "CreatedBySeller": false,
                "SellerTIN": "0850507476604000",
                "BuyerTIN": "0638937201609000",
                "DocumentNumber": null,
                "SellerTaxpayerName": "SAERAH SURYA PERKASA",
                "BuyerTaxpayerNameClear": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
                "BuyerTaxpayerName": "CAHAYA SARIPANGAN MANDIRI OPTIMUS",
                "BuyerName": null,
                "TaxInvoiceCode": "TD.00304",
                "TaxInvoiceNumber": "04002500298459047",
                "TaxInvoiceDate": "2025-09-17T00:00:00+07:00",
                "TaxInvoicePeriod": "TD.00709",
                "TaxInvoiceYear": "2025",
                "TaxInvoiceStatus": "APPROVED",
                "BuyerStatus": null,
                "SellingPrice": 353189,
                "OtherTaxBase": 323757,
                "VAT": 38851,
                "STLG": 0,
                "Signer": "MARGARETH TAN",
                "DownpaymentParentIdentifier": "00000000-0000-0000-0000-000000000000",
                "DownpaymentSum": 0,
                "AmendedRecordId": null,
                "Valid": true,
                "ReportedByBuyer": false,
                "ReportedBySeller": true,
                "ReportedByVATCollector": null,
                "LastUpdatedDate": "2025-10-31T08:41:45+07:00",
                "CreationDate": "2025-09-19T14:25:23+07:00",
                "PeriodCredit": null,
                "YearCredit": null,
                "InputInvoiceStatus": "APPROVED",
                "DocumentFormNumber": "DN2025638939256974742660000",
                "DocumentFormAggregateIdentifier": "f2d7ad0d-10ed-4002-8042-0035c4769b9a",
                "ESignStatus": "Done",
                "AmendedDocumentFormNumber": null,
                "AmendedDocumentFormAggregateIdentifier": null,
                "CanceledDocumentFormNumber": null,
                "CanceledDocumentFormAggregateIdentifier": null,
                "IsShowCancelInGrid": true,
                "Reference": null,
                "ChannelCode": null,
                "DisplayName": null,
                "IsMigrated": false,
                "IdDocument": null,
                "IdDocumentCountry": null,
                "IdDocumentNumber": null,
                "SellerLastUpdatedDate": "0001-01-01T00:00:00",
                "SellingPriceRemainingAmount": null,
                "OtherTaxBaseRemainingAmount": null,
                "VATRemainingAmount": null,
                "STLGRemainingAmount": null,
                "LastUpdatedBy": null,
                "CreatedBy": null
            },
    ...
}
```
