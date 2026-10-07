# AI Work Service Catalog & Capability Discovery Layer

## Overview
The **Service Catalog** (STEP 48) is the governed, operational directory that describes *what* capabilities are available across the platform and *how* they can be consumed. It abstracts the complexity of disparate execution engines (Agents, Workflows, Connectors) into a unified discovery interface.

### Catalog vs Marketplace
- **Marketplace** (STEP 38): Responsible for package distribution, versioning, and installation (the *supply chain*).
- **Service Catalog** (STEP 48): Responsible for operational discovery of *instantiated and active* capabilities within a workspace (the *live inventory*).

### Catalog vs Agent/Workflow Registries
The Catalog does not duplicate the Agent Runtime or Workflow Engine. It stores a normalized representation (a `ServiceCatalogItem`) that contains a strict reference (`resource_type` and `resource_id`) back to the originating execution system. 

## Capability Discovery
The catalog implements deterministic discovery. It maps capabilities to required inputs, outputs, and permissions. 

### Compatibility & Eligibility
- **Compatibility**: Determines if a capability technically satisfies a requested schema/modality.
- **Eligibility**: Determines if the current user and context have the necessary Governance and RBAC approvals to actually *use* the capability.

## Availability & Freshness
The catalog tracks `availability_status` (Available, Limited, Unavailable) dynamically by referencing the underlying resource's health metrics.
`freshness_status` (Fresh, Aging, Stale) indicates how recently the catalog metadata was synchronized with the source of truth via the Event Bus.

## Integration Points
- **Planning (STEP 44)**: Queries the catalog to find resources capable of fulfilling planned objectives.
- **Contracts (STEP 47)**: References catalog capabilities as assigned resources for SLAs.
- **Control Tower (STEP 45)**: Surfaces stale or broken catalog capabilities for administrator attention.
- **Events & Jobs (STEP 24/26)**: Drives the synchronization of metadata between source systems and the catalog.
