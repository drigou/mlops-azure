# MLOps project for Azure-ML

### AZ Service principle

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