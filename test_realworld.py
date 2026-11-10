from main import correct_text, CorrectionRequest, CorrectionMode

samples = [
    # 1. News
    ("News", "According to the recent report published by the minister, the countrys economic growth have slowed down due to inflation, which is rising rapidly.", CorrectionMode.GRAMMAR),
    ("News", "The United Nations announced yesterday that severe drought in the region has effected millions of people and urgent aid is needed immediately.", CorrectionMode.GRAMMAR),
    
    # 2. Tech / Business Article
    ("Article", "In todays competitive market, companies must leverage artificial inteligence in order to optimize their supply chain and reduce operational costs.", CorrectionMode.GRAMMAR),
    ("Article", "The startup which was founded in 2022 has raised $50 million, and they is planning to expand into european markets.", CorrectionMode.GRAMMAR),
    
    # 3. Scientific Research Paper
    ("Research", "In this paper, we investigates the empirical performance of deep convolutional neural networks when applied to high-dimensional biomedical datasets.", CorrectionMode.GRAMMAR),
    ("Research", "The experimental results clearly shows that our proposed algorithm achieves superior convergence rates as compared to baseline models (p < 0.05).", CorrectionMode.GRAMMAR),
    ("Research", "Furthermore, the data was collected from over five hundred participants, which proves that cognitive awareness plays an crucial role in decision making.", CorrectionMode.GRAMMAR)
]

for category, text, mode in samples:
    req = CorrectionRequest(text=text, mode=mode, use_llm=False)
    resp = correct_text(req)
    print(f"[{category.upper()} IN ]: {text}")
    print(f"[{category.upper()} OUT]: {resp.corrected_text}")
    print(f"CHANGES ({len(resp.changes)}):")
    for c in resp.changes:
        rule = c.get("rule", c.get("type", "change"))
        print(f"  - {rule}: {repr(c.get('original'))} -> {repr(c.get('replacement'))}")
    print("=" * 80)
