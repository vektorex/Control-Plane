# Release Trains

A Release Train is the primary unit of macro-coordination in the AI Work Layer. It groups multiple STEP 53 Releases into a sequenced, deterministic deployment schedule.

## States
- **draft**: Train is being built.
- **planning**: Dependencies are being evaluated.
- **validation_required**: Conflicts detected or revalidation triggered.
- **blocked**: Hard blocking conflicts (e.g. dependency cycle).
- **scheduled**: Sequence generated and windows locked.
- **active**: Currently handing off to STEP 53.
- **completed**: All waves successfully finished.

## Waves
Releases in a train are grouped into discrete `ReleaseWave` entities. A wave must completely finish (all its rollouts complete) before the next wave triggers.
