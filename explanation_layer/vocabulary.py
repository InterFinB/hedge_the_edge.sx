VOCABULARY_MAP = {
    "Risk": "How much the portfolio may move up or down.",
    "Diversification": "Spreading across different assets so the portfolio relies less on one source of return.",
    "Concentration": "How much the portfolio depends on a small number of positions.",
    "Risk contribution": "How much each asset adds to total portfolio risk.",
    "Modeled range of outcomes": "A rough spread of weaker and stronger scenarios from the simulation.",
    "Downside limit": "A user-defined limit for how much risk is acceptable.",
}


def generate_vocabulary(used_terms=None):
    if not used_terms:
        return []

    items = []
    for term in used_terms:
        if term in VOCABULARY_MAP:
            items.append(f"{term} — {VOCABULARY_MAP[term]}")
    return items