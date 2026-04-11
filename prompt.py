def create_prompt(article):

    prompt = f"""
You are a financial market analyst.

Your task is to classify the following financial news article as:

Market-Moving
or
Non-Market-Moving

Definitions:

Market-Moving:
- New or unexpected financial information
- Likely to affect stock prices or markets
- Triggers trading activity

Non-Market-Moving:
- Routine or expected information
- Informational but not urgent
- No major financial impact

Return ONLY in this format:

Label: <Market-Moving or Non-Market-Moving>
Reason: <short explanation>

Article:
{article}
"""

    return prompt