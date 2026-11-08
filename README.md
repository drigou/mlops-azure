# MLOps project for Azure-ML

### AZ Service principle

Login to AZ forcing mfa
```bash
az config set core.enable_broker_on_windows=false
az login

# If mfa is in the list go for it
az account get-access-token --query accessToken -o tsv \
  | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | jq '.amr'
```

Create a service principle in AZ. 
```bash
az ad sp create-for-rbac --name my-app \
```
Assign it a role on the subscription. 
```bash
az role assignment create \
  --assignee <appId> \
  --role Contributor \
  --scope /subscriptions/<subscription-id>
```

#### Foundry access for the evaluation workflow

The `evaluate-agent.yml` GitHub Action runs as this service principal, so it needs the **Azure AI User** role on the Foundry project. Without it the eval calls fail with a 403.
```bash
FOUNDRY_PROJECT=$(az resource list \
  --resource-type Microsoft.CognitiveServices/accounts/projects \
  --query "[].id" -o tsv \
  | grep rg-dg-foundry | tr -d '\r')

OBJ_ID=$(az ad sp show --id "$ARM_CLIENT_ID" --query id -o tsv | tr -d '\r')

az role assignment create \
  --assignee-object-id "$OBJ_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Foundry User" \
  --scope "$FOUNDRY_PROJECT"
```
The `tr -d '\r'` strips the Windows line endings that `az.exe` adds. Without it the request fails with a `Bad Request`.

### Terraform

Put the environment variables in a .env file.
```bash
ARM_CLIENT_ID=********
ARM_CLIENT_SECRET=********
ARM_TENANT_ID=********
ARM_SUBSCRIPTION_ID=********
```
Read these as environment variables
```bash
set -a; source ../.env; set +a
```
Afterwards run terraform in ./terraform folder
```bash 
terraform init
terraform plan
terraform apply
```