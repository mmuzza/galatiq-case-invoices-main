
def approval_agent(validation_result: dict, invoice, client) -> dict:
    
    import json

    vp_review_required = False
    reasons = []

    # Any validation_agent generated errors will require VP review as payment cannot be processed
    if validation_result.get("errors"):
        vp_review_required = True
        reasons.extend(validation_result["errors"])

    # Large invoices require extra scrutiny --> based on read me file
    total_amount = invoice.total_amount
    if total_amount and total_amount > 10_000:
        vp_review_required = True
        reasons.append(f"Invoice total is high (${total_amount})")


    prompt = f"""
You are an accounts VP. Given the following invoice data and validation results:

Invoice:
{invoice.dict()}

Validation errors:
{validation_result.get('errors', [])}

Determine if this invoice requires VP review. Explain your reasoning in clear human-readable language.

Return a JSON object with these keys:
- vp_review_required (true/false)
- summary (1 to 2 sentences)
- reasoning (as a list of concise bullet points, do not just state the error but explain what such error could lead to for which the payment cannot be processed for if not resolved)


For Example:
{{
    "vp_review_required": true,
    "summary": "Invoice needs VP review",
    "reasoning": ["Quantity exceeds stock", "Invoice total is high"]
}}

Return only valid JSON. Do not include any extra text.
"""

    llm_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    reasoning_text = llm_response.choices[0].message.content.strip()


    try:
        llm_result = json.loads(reasoning_text)
    except json.JSONDecodeError:
        llm_result = {
            "vp_review_required": vp_review_required,
            "summary": "Could not parse LLM output.",
            "reasoning": reasons or [reasoning_text]
        }


    vp_review_required = vp_review_required or llm_result.get("vp_review_required", False)


    reasoning = llm_result.get("reasoning")
    if isinstance(reasoning, str):
        reasoning = [reasoning]

    return {
        "vp_review_required": vp_review_required,
        "summary": llm_result.get("summary", ""),
        "reasoning": reasoning
    }