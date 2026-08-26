from app.services.accounting_client import AccountingClient

def main():
    client = AccountingClient()

    print("Health Check:\n", client.health())
    print("\nPartners:")

    for partner in client.get_partners():
        print(
            partner["partner_code"],
            partner["name"],
            partner["registration_no"]
        )

    print("\nTax Codes:")
    for tax_code in client.get_tax_codes():
        print(tax_code)

if __name__ == "__main__":
    main()