# Infrastructure as Code

## What is it?
- A layer of automation that helps System Administrators, Developers, and Software Engineers (and eventually the business as a whole - especially if it's IT) set up infrastructure in an easy and programmatic manner. It enables version control, testing, and re-spinning of infrastructure configurations on demand

## Why would I want it?
- IaC allows you to deploy and manage infrastructure quickly and reliably. It provides resilience, efficiency, trackability, security, and collaboration. IaC ensures consistency across environments and allows for parameterization and automation. It also facilitates easy rollback and disaster recovery

## Are there any alternatives?
- Not really, unless you prefer manual configuration

# Observability

## What do we want to observe?
- Availability: Ensuring business can deliver
- Efficiency: Monitoring resource utilization and performance
- Costs: Make sure we track costs and stay in budget + we can forcast
- Trackability: Keeping track of changes and their impacts
- Anomalies: Detecting and responding to unusual behaviors or patterns

## What kind of challenges do you see in a distributed environment?
- Code maintainability: Ensuring observability code remains manageable
- Scale: Efficient handling of data (regardless of the volume)
- Costs: Track and maintain low costs without losing efficiency
- Interoperability: Ensuring different tools and systems work well together
- Security/Compliance: Protecting data and ensuring observability practices comply with regulations (protect PII data for customers that book rooms/apartments)

## How can we solve them?
- Maintain a DevOps approach with an efficient lifecycle
- Implement self-healing alerting systems
- Design security from the ground up (Security by Design)
- Follow the principle of least privilege (Need to Know Principle)
- Use automated tools to manage scaling and cost
- Regularly review and update observability practices to align with industry standards and regulations

# Security

## First 3 things to check when joining an AWS Infra to limit the risk of a breach:
Considering a hotel/rental business:

### Availability (must condition)
- **Importance:** Downtime can significantly impact the business’s reputation and revenue

### 1. Assess Attack Surface
- Identify public endpoints and applications
- Check their initial security level and perform a thorough assessment
- Ensure they are patched regularly and look for any known vulnerabilities (CVEs)
- Ensure there are no Web related issues (for web applications)

### 2. Restrict Public Endpoints
- Ensure only necessary endpoints are public - the rest should be private
- Use Security Groups, Load Balancers, WAF to protect web/scale endpoints
- Ensure data transfer is encrypted both in transit and at rest

### 3. Check IAM (Identity and Access Management)
- Review and assess who has access to what resources in order to be able to asses the impact in case of credentials leak
- Ensure sensitive data in pipelines and automation is stored as secrets and not logged, or if logged, it should be masked

### Extra:
#### 4. Pipelines
- Ensure pipelines include security checks such as code scanning, image scanning, and endpoint scanning

#### 5. Continuous Monitoring and Logging
- Implement continuous monitoring and logging for development, security, and audit purposes

## Explain Why

- Already done inline

## Extra

- **Resilience:** Ensure there is a robust plan to resume business operations quickly in case of a disaster. This includes regular backups, disaster recovery strategies, and periodic testing of the plan
