# Retrieval Evaluation

LegalConnect uses retrieval evaluation to measure whether the system can identify the correct legal section for a user's query.

## Benchmark

The current benchmark contains 22 test queries covering:

- BNS
- BNSS
- BSA

## Results

| Metric | Result |
|---|---:|
| Total Queries | 22 |
| Hit Rate@1 | 90.9% |
| Hit Rate@3 | 100.0% |
| Hit Rate@5 | 100.0% |
| MRR | 0.9470 |

## Metric Definitions

### Hit Rate@1

Measures how often the correct legal section appears as the first retrieved result.

### Hit Rate@3

Measures how often the correct legal section appears within the top three results.

### Hit Rate@5

Measures how often the correct legal section appears within the top five results.

### Mean Reciprocal Rank (MRR)

Measures how highly the correct result is ranked across all queries.

## Retrieval Improvements

The retrieval system includes metadata-aware retrieval for explicit section references.

For example:

```text
"What does BNSS Section 35 say?"
