# External Dataset Audit — V6 Completion

## SciFact (CONFIRMATORY)

- **Why included**: Evidence-grounded scientific claim verification with external gold labels, real document corpus, and sentence-level rationales. Independent of project hypothesis — designed for fact-checking, not cognitive sequencing.
- **Task type**: Claim verification (SUPPORTS / REFUTES / NOT_ENOUGH_INFO)
- **Gold answer**: Human expert labels (veracity + rationale)
- **Gold evidence**: Annotated document IDs + sentence IDs
- **Corpus**: 5,183 scientific abstracts
- **License**: CC BY-NC 2.0
- **Retrieval setting**: BM25 keyword retrieval over full corpus
- **Native metric**: Label accuracy, gold document recall
- **Known shortcut risks**: Some claims contain lexical overlap with gold abstracts
- **Expected experimental pressure**: Hypothesis-guided retrieval should improve gold evidence recall on claims requiring non-obvious evidence
- **Confirmatory/exploratory**: CONFIRMATORY

## HotpotQA (CONFIRMATORY)

- **Why included**: Multi-hop question answering with sentence-level supporting facts. Requires combining information from multiple paragraphs. Independent of this project.
- **Task type**: Multi-hop question answering
- **Gold answer**: Short factual answers
- **Gold evidence**: Paragraph titles containing supporting facts
- **Corpus**: Per-question paragraph set (distractor setting with ~10 paragraphs)
- **License**: CC BY-SA 4.0
- **Retrieval setting**: BM25 over distractor paragraphs per question
- **Native metric**: Answer F1, Exact Match, supporting fact recall
- **Known shortcut risks**: Some questions solvable from single paragraph; distractor setting provides limited paragraphs
- **Expected experimental pressure**: Multi-hop questions may benefit from hypothesis-guided evidence selection
- **Confirmatory/exploratory**: CONFIRMATORY

## Selection Principle

Both datasets were selected BEFORE any external results were observed.
Neither dataset was designed to exhibit cognitive complementarity.
Both provide externally-defined gold labels and evidence.
Selection criterion: evidence-grounded tasks with real documents and gold evidence annotations.
