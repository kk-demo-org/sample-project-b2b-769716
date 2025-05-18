# sample-project-b2b-769716

## Billing Utility

The `assume_role_get_billing.py` script prints service and usage type costs for the previous month for a given AWS account.

```bash
python assume_role_get_billing.py <account-id>
```

It assumes the `OrganizationAccountAccessRole` in the target account and queries AWS Cost Explorer for service and usage details.

## LangGraph Code Generation Agent

The `langgraph_agent.py` module offers an experimental agent that iteratively generates and executes Python code using LangChain and LangGraph. The agent uses the GPT-4.1 model and is aware of `assume_role_get_billing.list_service_usage` for incorporation when generating code.

Run it from the command line:

```bash
python langgraph_agent.py "Write code to <task description>"
```

The agent will attempt to produce code, execute it in a sandboxed environment and print the result or any final error message.

