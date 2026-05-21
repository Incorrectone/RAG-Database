import os
import pandas as pd

dtype_Person = {
    "personId": "string",
    "firstName": "string",
    "lastName": "string",
    "dob": "datetime64[ns]",
    "taxId": "string",
    "nationality": "string",
    "pepStatus": "boolean",
    "kycStatus": "string",
    "riskScore": "Float64"
}

dtype_Company = {
    "companyId": "string",
    "name": "string",
    "regNumber": "string",
    "incorporationDate": "datetime64[ns]",
    "industryCode": "string",
    "kycStatus": "string",
    "riskScore": "Float64"
}

dtype_Account = {
    "accountId": "string",
    "accountType": "string",
    "balance": "Float64",
    "currency": "string",
    "status": "string",
    "openedDate": "datetime64[ns]",
    "branchCode": "string"
}

dtype_Transaction = {
    "txId": "string",
    "amount": "Float64",
    "baseCurrencyAmount": "Float64",
    "timestamp": "datetime64[ns]",
    "txType": "string",
    "channel": "string",
    "status": "string"
}

dtype_Address = {
    "addressId": "string",
    "street": "string",
    "city": "string",
    "state": "string",
    "zipCode": "string",
    "country": "string"
}

dtype_Device = {
    "deviceId": "string",
    "deviceType": "string",
    "os": "string",
    "ipAddress": "string",
    "macAddress": "string",
    "isp": "string"
}

dtype_Document = {
    "docId": "string",
    "docType": "string",
    "issuedCountry": "string",
    "expiryDate": "datetime64[ns]",
    "isForged": "boolean"
}

dtype_WatchlistEntity = {
    "entityId": "string",
    "listName": "string",
    "listType": "string",
    "addedDate": "datetime64[ns]"
}

# --- RELATIONSHIPS ---

dtype_OWNS_ACCOUNT = {
    "_from": "string", "_to": "string",
    "role": "string",
    "since": "datetime64[ns]"
}

dtype_HAS_ADDRESS = {
    "_from": "string", "_to": "string",
    "addressType": "string",
    "isCurrent": "boolean"
}

dtype_USES_DEVICE = {
    "_from": "string", "_to": "string",
    "firstSeen": "datetime64[ns]",
    "lastSeen": "datetime64[ns]",
    "trustScore": "Float64"
}

dtype_SENT_TX = {
    "_from": "string", "_to": "string",
    "postTxBalance": "Float64"
}

dtype_RECIEVED_TX = {
    "_from": "string", "_to": "string",
    "postTxBalance": "Float64"
}

dtype_INITIATED_VIA = {
    "_from": "string", "_to": "string",
    "locationData": "string"
}

dtype_WORKS_FOR = {
    "_from": "string", "_to": "string",
    "jobTitle": "string",
    "employmentType": "string",
    "startDate": "datetime64[ns]",
    "salaryRange": "string"
}

dtype_OWNS_EQUITY = {
    "_from": "string", "_to": "string",
    "percentage": "Float64",
    "votingRights": "Float64"
}

dtype_DIRECTS = {
    "_from": "string", "_to": "string",
    "role": "string",
    "appointedDate": "datetime64[ns]"
}

dtype_PROVIDED_DOC = {
    "_from": "string", "_to": "string",
    "submissionDate": "datetime64[ns]",
    "verificationMethod": "string"
}

dtype_MATCHES_WATCHLIST = {
    "_from": "string", "_to": "string",
    "similarityScore": "Float64",
    "matchDate": "datetime64[ns]",
    "status": "string"
}

df_Person = pd.DataFrame(columns=dtype_Person.keys()).astype(dtype_Person)
df_Company = pd.DataFrame(columns=dtype_Company.keys()).astype(dtype_Company)
df_Account = pd.DataFrame(columns=dtype_Account.keys()).astype(dtype_Account)
df_Transaction = pd.DataFrame(columns=dtype_Transaction.keys()).astype(dtype_Transaction)
df_Address = pd.DataFrame(columns=dtype_Address.keys()).astype(dtype_Address)
df_Device = pd.DataFrame(columns=dtype_Device.keys()).astype(dtype_Device)
df_Document = pd.DataFrame(columns=dtype_Document.keys()).astype(dtype_Document)
df_WatchlistEntity = pd.DataFrame(columns=dtype_WatchlistEntity.keys()).astype(dtype_WatchlistEntity)

# Relationships
df_PERSON_OWNS_ACCOUNT = pd.DataFrame(columns=dtype_OWNS_ACCOUNT.keys()).astype(dtype_OWNS_ACCOUNT)
df_COMPANY_OWNS_ACCOUNT = pd.DataFrame(columns=dtype_OWNS_ACCOUNT.keys()).astype(dtype_OWNS_ACCOUNT)
df_COMPANY_HAS_ADDRESS = pd.DataFrame(columns=dtype_HAS_ADDRESS.keys()).astype(dtype_HAS_ADDRESS)
df_PERSON_HAS_ADDRESS = pd.DataFrame(columns=dtype_HAS_ADDRESS.keys()).astype(dtype_HAS_ADDRESS)
df_COMPANY_USES_DEVICE = pd.DataFrame(columns=dtype_USES_DEVICE.keys()).astype(dtype_USES_DEVICE)
df_PERSON_USES_DEVICE = pd.DataFrame(columns=dtype_USES_DEVICE.keys()).astype(dtype_USES_DEVICE)
df_SENT_TX = pd.DataFrame(columns=dtype_SENT_TX.keys()).astype(dtype_SENT_TX)
df_RECEIVED_TX = pd.DataFrame(columns=dtype_RECIEVED_TX.keys()).astype(dtype_RECIEVED_TX)
df_INITIATED_VIA = pd.DataFrame(columns=dtype_INITIATED_VIA.keys()).astype(dtype_INITIATED_VIA)
df_WORKS_FOR = pd.DataFrame(columns=dtype_WORKS_FOR.keys()).astype(dtype_WORKS_FOR)
df_PERSON_OWNS_EQUITY = pd.DataFrame(columns=dtype_OWNS_EQUITY.keys()).astype(dtype_OWNS_EQUITY)
df_DIRECTS = pd.DataFrame(columns=dtype_DIRECTS.keys()).astype(dtype_DIRECTS)
df_COMPANY_PROVIDED_DOC = pd.DataFrame(columns=dtype_PROVIDED_DOC.keys()).astype(dtype_PROVIDED_DOC)
df_PERSON_PROVIDED_DOC = pd.DataFrame(columns=dtype_PROVIDED_DOC.keys()).astype(dtype_PROVIDED_DOC)
df_COMPANY_MATCHES_WATCHLIST = pd.DataFrame(columns=dtype_MATCHES_WATCHLIST.keys()).astype(dtype_MATCHES_WATCHLIST)
df_PERSON_MATCHES_WATCHLIST = pd.DataFrame(columns=dtype_MATCHES_WATCHLIST.keys()).astype(dtype_MATCHES_WATCHLIST)


def save_all_dfs_to_csv(output_directory: str):
    """
    Saves all initialized graph dataframes to individual CSV files.

    Parameters:
    output_directory (str): The folder path where CSV files will be saved.
    """
    # 1. Create directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created directory: {output_directory}")

    # 2. Map file names to your global DataFrame variables
    dataframes_to_save = {
        # Nodes
        "nodes_person.csv": df_Person,
        "nodes_company.csv": df_Company,
        "nodes_account.csv": df_Account,
        "nodes_transaction.csv": df_Transaction,
        "nodes_address.csv": df_Address,
        "nodes_device.csv": df_Device,
        "nodes_document.csv": df_Document,
        "nodes_watchlist_entity.csv": df_WatchlistEntity,

        # Relationships (Fixed unique file names and mapped to correct variables)
        "rel_person_owns_account.csv": df_PERSON_OWNS_ACCOUNT,
        "rel_company_owns_account.csv": df_COMPANY_OWNS_ACCOUNT,

        "rel_person_has_address.csv": df_PERSON_HAS_ADDRESS,
        "rel_company_has_address.csv": df_COMPANY_HAS_ADDRESS,

        "rel_person_uses_device.csv": df_PERSON_USES_DEVICE,
        "rel_company_uses_device.csv": df_COMPANY_USES_DEVICE,

        "rel_sent_tx.csv": df_SENT_TX,
        "rel_recieved_tx.csv": df_RECEIVED_TX,

        "rel_initiated_via.csv": df_INITIATED_VIA,
        "rel_works_for.csv": df_WORKS_FOR,

        "rel_person_owns_equity.csv": df_PERSON_OWNS_EQUITY,
        # Note: If you create a df_COMPANY_OWNS_EQUITY later, add it here:
        # "rel_company_owns_equity.csv": df_COMPANY_OWNS_EQUITY,

        "rel_directs.csv": df_DIRECTS,

        "rel_person_provided_doc.csv": df_PERSON_PROVIDED_DOC,
        "rel_company_provided_doc.csv": df_COMPANY_PROVIDED_DOC,

        "rel_person_matches_watchlist.csv": df_PERSON_MATCHES_WATCHLIST,
        "rel_company_matches_watchlist.csv": df_COMPANY_MATCHES_WATCHLIST
    }

    # 3. Loop and export each dataframe
    print("Starting CSV export...")
    for filename, df in dataframes_to_save.items():
        full_path = os.path.join(output_directory, filename)
        df.to_csv(full_path, index=False)
        print(f" -> Saved {filename} ({len(df)} rows)")

    print("\nAll files successfully saved!")