import argparse
import boto3
from datetime import date, timedelta


def assume_role(account_id, role_name="OrganizationAccountAccessRole"):
    sts = boto3.client("sts")
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    response = sts.assume_role(RoleArn=role_arn, RoleSessionName="BillingAccess")
    creds = response["Credentials"]
    session = boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
    return session


def last_month_period():
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    return first_day_last_month.strftime("%Y-%m-%d"), first_day_this_month.strftime("%Y-%m-%d")


def list_service_usage(account_id):
    session = assume_role(account_id)
    ce = session.client("ce")
    start, end = last_month_period()
    results = []

    token = None
    while True:
        params = {
            "TimePeriod": {"Start": start, "End": end},
            "Granularity": "MONTHLY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [
                {"Type": "DIMENSION", "Key": "SERVICE"},
                {"Type": "DIMENSION", "Key": "USAGE_TYPE"},
            ],
        }
        if token:
            params["NextPageToken"] = token
        response = ce.get_cost_and_usage(**params)
        results.extend(response.get("ResultsByTime", []))
        token = response.get("NextPageToken")
        if not token:
            break

    services = []
    for item in results:
        for group in item.get("Groups", []):
            service = group["Keys"][0]
            usage_type = group["Keys"][1]
            amount = group["Metrics"]["UnblendedCost"]["Amount"]
            services.append({"service": service, "usage_type": usage_type, "amount": amount})

    return services


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List services contributing to billing")
    parser.add_argument("account_id", help="Account ID to query")
    args = parser.parse_args()

    for item in list_service_usage(args.account_id):
        print(f"{item['service']}\t{item['usage_type']}\t${item['amount']}")
