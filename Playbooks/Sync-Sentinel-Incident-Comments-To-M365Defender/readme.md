# Sync-Sentinel-Incident-Comments-To-M365Defender
author: Prateek Taneja, Benjamin Kovacevic

This Playbook synchronizes the comments made to Microsoft 365 Defender Incidents in Azure Sentinel to comments in the corresponding Incident in the Microsoft 365 Defender portal. The LogicApp looks for comments added to Incidents in the past 24 hours and writes these comments to the corresponding M365 incident in the M365 Security and Compliance exprience available at https://security.microsoft.com

<a href=https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FAzure%2FAzure-Sentinel%2Fmaster%2FPlaybooks%2FSync-Sentinel-Incident-Comments-To-M365Defender%2Fazuredeploy.json target="_blank">
    <img src=https://aka.ms/deploytoazurebutton/>
</a>
<a href=https://portal.azure.us/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FAzure%2FAzure-Sentinel%2Fmaster%2FPlaybooks%2FSync-Sentinel-Incident-Comments-To-M365Defender%2Fazuredeploy.json target="_blank">
<img src=https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/1-CONTRIBUTION-GUIDE/images/deploytoazuregov.png>
</a>

Deploying this playbook requires the following steps:

1. Register an Azure Active Directory Application

![screenshot](./images/AzureADAppRegistration.PNG)

Provide a name and leave everything as defaults and click Register.

2. The permission required to make a PATCH request in M365 Defender is - Incident.readWrite.All

Here's how these permissions can be provided.

On the application that was created in the above step, click on API Permissions on the left blade, then click Add a  Permission.

From the options that open on the right, select APIs mu organization uses and search for and then click Microsft Threat Protection. 

Next, click Application permissions. Select Incident.ReadWrite.All and then click on Add permissions.

Once the permissions have been assigned, you'll need to click on Grant Admin consent.

3. Generate a Secret for Authenticating to M365 Defender

Back on the application that was registered in Step 1, click on Certificates & Secrets.

Click on '+ New client secret'. Provide a description and expiration and click Add.

![screenshot](./images/Secret.PNG)

NOTE: The secret is displayed only once, so make sure you copy and save it NOW so this can be used when deploying the LogicApp.

4. Obtain the Tenant ID and the Client ID for use when deploying the LogicApp from template.

Back on the application that was registered in Step 1, copy the Directory (tenant) ID and the Application (client) ID

![screenshot](./images/IDs.JPG)
-------------------------------------------------------------------------------------------