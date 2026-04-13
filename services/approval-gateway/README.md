# Approval Gateway Service Contract

Role:
- bridge pending actions to Linear approval workflow
- map Linear decisions back to system status transitions

Required behavior:
- create/update approval records in Linear
- map `Approved`/`Rejected` statuses to pending action states
- emit approval events for executor consumption
