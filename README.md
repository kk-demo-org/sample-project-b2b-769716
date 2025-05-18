# sample-project-b2b-769716

## Billing Utility

The `assume_role_get_billing.py` script prints service and usage type costs for the previous month for a given AWS account.

```bash
python assume_role_get_billing.py <account-id>
```

It assumes the `OrganizationAccountAccessRole` in the target account and queries AWS Cost Explorer for service and usage details.
