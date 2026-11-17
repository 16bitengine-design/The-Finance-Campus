"""Zero-cost, evergreen money-mindset topic discovery with authoritative source checks.

Topics are selected from human money behaviours and beliefs. Official educational
sources are checked for relevance; candidates remain unapproved pending claim review.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request

from collections.abc import Callable
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from finance_campus.mindset_topics import MINDSET_TOPIC_BLUEPRINTS
from finance_campus.topics import add_topic, load_topics, save_topics


USER_AGENT = "TheFinanceCampusResearchBot/1.0 (educational research; contact via GitHub repository)"
SOURCE_CATALOG: dict[str, dict[str, str]] = {
    "cfpb_emergency": {
        "url": "https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/",
        "publisher": "Consumer Financial Protection Bureau",
        "domain": "consumerfinance.gov",
    },
    "cfpb_toolkit": {
        "url": "https://www.consumerfinance.gov/consumer-tools/educator-tools/your-money-your-goals/toolkit/",
        "publisher": "Consumer Financial Protection Bureau",
        "domain": "consumerfinance.gov",
    },
    "bou_literacy": {
        "url": "https://bou.or.ug/financial_literacy",
        "publisher": "Bank of Uganda",
        "domain": "bou.or.ug",
    },
    "bou_strategy": {
        "url": "https://www.bou.or.ug/uploads/Strategy_for_Financial_in_Uganda_2026_2031_Detailed_Version_signed_Oct_2_2026_bffc2d40d2.pdf",
        "publisher": "Bank of Uganda",
        "domain": "bou.or.ug",
    },
    "sec_investor": {
        "url": "https://www.investor.gov/introduction-investing",
        "publisher": "U.S. Securities and Exchange Commission",
        "domain": "investor.gov",
    },
}

# Topic definitions are deliberately explicit: each one has a real learning outcome,
# a geographic label, a source, and the key phrases expected on that source page.
TOPIC_BLUEPRINTS: list[dict[str, Any]] = [
    {"slug":"emergency-fund-first-step","title":"How to start an emergency fund when money is tight","category":"Saving and Emergency Funds","source":"cfpb_emergency","keywords":["emergency","savings"],"geo":["global","Uganda","East Africa"],"problem":"One unexpected repair, medical bill or income interruption can disrupt a household that has no money set aside.","stakes":"When there is no cash buffer, a person may have to borrow or use money meant for essential bills; repayments and fees can make the next month harder.","explanation":"An emergency fund is money kept separately for necessary, unplanned costs. The right starting target depends on a person's expenses, income stability and circumstances.","action":"List the unexpected costs you have faced before, choose a small amount that is genuinely affordable, and set a regular saving day."},
    {"slug":"emergency-fund-irregular-income","title":"Building emergency savings with irregular income","category":"Saving and Emergency Funds","source":"cfpb_emergency","keywords":["emergency","savings"],"geo":["global","Uganda","East Africa"],"problem":"When income changes from week to week, saving a fixed amount can feel impossible.","stakes":"A quiet week or delayed payment can leave essential costs uncovered and make borrowing feel like the only option.","explanation":"A savings habit can be adapted to variable cash flow: track when money arrives, protect essentials first, and save a manageable amount when cash is available.","action":"Record income dates for one month and choose a flexible contribution rule, such as saving a small share only after essential costs are covered."},
    {"slug":"cash-flow-budget-timing","title":"Why cash-flow timing matters more than a monthly budget alone","category":"Budgeting and Money Management","source":"cfpb_toolkit","keywords":["cash","income","bills"],"geo":["global","Uganda","East Africa"],"problem":"A household can earn enough over a month and still run short before the next payment arrives.","stakes":"When bills fall due before income arrives, late fees, missed payments or emergency borrowing can follow.","explanation":"Cash-flow planning tracks not only how much money comes in and goes out, but also when it arrives and when each bill is due.","action":"Write down expected income dates and bill due dates for the next four weeks, then identify any timing gap early."},
    {"slug":"needs-vs-wants-under-pressure","title":"Needs versus wants when every shilling already has a job","category":"Budgeting and Money Management","source":"bou_literacy","keywords":["personal","financial","management"],"geo":["Uganda","East Africa"],"problem":"When money is limited, small unplanned purchases can compete with food, transport, rent or school costs.","stakes":"Repeatedly spending money assigned to essentials can create shortages and force difficult choices later.","explanation":"A practical spending plan prioritises basic needs and obligations before optional purchases, while recognising that personal circumstances differ.","action":"Before your next non-essential purchase, check which essential expense that money may need to cover first."},
    {"slug":"budget-for-irregular-expenses","title":"The hidden expenses that quietly break a budget","category":"Budgeting and Money Management","source":"cfpb_toolkit","keywords":["budget","spending","bills"],"geo":["global","Uganda","East Africa"],"problem":"A budget may look balanced until school supplies, annual fees, repairs or seasonal costs appear.","stakes":"If irregular expenses are ignored, they can repeatedly push a household into debt or force it to abandon other goals.","explanation":"A useful budget accounts for predictable non-monthly expenses by estimating them ahead of time and setting aside money gradually where possible.","action":"Review the last year and list three expenses that did not happen monthly; estimate when they may return."},
    {"slug":"debt-repayment-plan","title":"How to make a debt repayment plan you can actually follow","category":"Debt and Loans","source":"cfpb_toolkit","keywords":["debt","repaying"],"geo":["global","Uganda","East Africa"],"problem":"When several debts compete for attention, it can be difficult to know what is owed and what must be paid next.","stakes":"Missed due dates, penalties and additional borrowing can make an already difficult debt situation more expensive.","explanation":"A repayment plan starts with a complete debt list, payment dates, interest and fees, then compares realistic repayment options against essential living costs.","action":"List every debt, its balance, due date, required payment, interest and fees before choosing a repayment approach."},
    {"slug":"loan-total-cost-not-installment","title":"The loan question people forget: what is the total cost?","category":"Debt and Loans","source":"bou_strategy","keywords":["loan","interest","credit"],"geo":["Uganda","East Africa"],"problem":"A loan can look affordable when attention is focused only on the size of each instalment.","stakes":"Fees, interest, penalties and the repayment period can make the total amount repaid much higher than the amount borrowed.","explanation":"Responsible borrowing means comparing the total cost of credit and checking whether repayments remain affordable after essential expenses.","action":"Before accepting a loan, request the full repayment schedule and calculate the total amount you will repay, including disclosed fees."},
    {"slug":"multiple-loans-stacking-risk","title":"How taking one loan to repay another can become a debt trap","category":"Debt and Loans","source":"bou_strategy","keywords":["debt","borrowing","loan"],"geo":["Uganda","East Africa"],"problem":"A person under repayment pressure may consider a new loan simply to meet an older loan instalment.","stakes":"If the new borrowing adds costs without fixing the original cash-flow problem, total debt and repayment pressure can grow.","explanation":"Loan stacking is a warning sign that the current repayment plan may be unsustainable; the full debt position and available support need to be assessed.","action":"Pause before taking another loan, write down the total balances and costs, and contact the lender or a qualified debt-support service to discuss options."},
    {"slug":"compare-savings-accounts","title":"How to compare a savings account beyond the advertised rate","category":"Banking and Financial Services","source":"cfpb_emergency","keywords":["savings","account"],"geo":["global","Uganda","East Africa"],"problem":"A savings product may look attractive from one headline feature while important conditions remain unnoticed.","stakes":"Access restrictions, fees, minimum balances and withdrawal rules can affect whether the account fits the purpose of the money.","explanation":"A suitable place for emergency savings should balance safety, access, costs and the saver’s own circumstances; product protections differ by country.","action":"Compare the account's fees, minimum balance, access rules and applicable deposit-protection arrangements before opening it."},
    {"slug":"mobile-money-security-basics","title":"Protecting your money when using digital financial services","category":"Financial Scams and Fraud Prevention","source":"bou_strategy","keywords":["digital","financial","safety"],"geo":["Uganda","East Africa"],"problem":"Mobile money and digital financial services make transactions convenient, but they also create opportunities for impersonation and fraud.","stakes":"Sharing a PIN, approving an unfamiliar prompt or trusting an urgent caller can expose money or account access.","explanation":"Digital financial literacy includes recognising suspicious requests, protecting credentials and using official provider channels to verify transactions.","action":"Never share your PIN or one-time code, stop when a request feels urgent, and verify it through the provider's official contact channel."},
    {"slug":"spot-investment-scam-red-flags","title":"Investment scam warning signs everyone should recognise","category":"Financial Scams and Fraud Prevention","source":"sec_investor","keywords":["investing","fraud"],"geo":["global","Uganda","East Africa"],"problem":"A persuasive investment pitch can make a risky or fraudulent offer appear like a rare opportunity.","stakes":"Money sent to a fraudulent scheme may be difficult or impossible to recover, especially when the offer relies on urgency or secrecy.","explanation":"Investors should understand what they are buying, who is offering it, how returns are supposedly generated and what risks are disclosed.","action":"Pause, independently verify the firm and product with the relevant regulator in your country, and never invest solely because of pressure or a promised return."},
    {"slug":"investing-risk-and-diversification","title":"Why diversification matters when you start investing","category":"Investing Fundamentals","source":"sec_investor","keywords":["investing","risk"],"geo":["global"],"problem":"Putting all investment money into one company or asset can make a person's outcome depend heavily on one result.","stakes":"If that single investment performs badly, the impact on the whole portfolio may be substantial.","explanation":"Diversification spreads exposure across different investments; it can manage concentration risk but cannot eliminate investment risk or guarantee a profit.","action":"Learn how different assets behave and consider whether your holdings are overly concentrated before making investment decisions."},
    {"slug":"compound-interest-time","title":"How time changes the effect of compound growth","category":"Compound Interest","source":"sec_investor","keywords":["investing","compound"],"geo":["global"],"problem":"People often underestimate how much time can matter when money earns returns that are reinvested.","stakes":"Starting later can mean fewer periods for potential growth to build, although returns are uncertain and losses are possible.","explanation":"Compounding occurs when returns remain invested and future returns are earned on both the original amount and prior returns; actual outcomes vary.","action":"Use a calculator to compare different time periods with clearly labelled hypothetical rates, and remember that fees, inflation and losses affect results."},
    {"slug":"inflation-purchasing-power","title":"Why the same amount of money buys less when prices rise","category":"Inflation and Purchasing Power","source":"bou_literacy","keywords":["financial","management"],"geo":["global","Uganda","East Africa"],"problem":"A household may receive the same income while the prices of everyday goods and services increase.","stakes":"If income does not keep pace with prices, the same amount of money may cover fewer needs over time.","explanation":"Inflation is a general rise in prices that reduces the purchasing power of money; the effect on each household depends on its spending pattern.","action":"Track the prices of your most important regular purchases and review your budget when those costs change."},
    {"slug":"insurance-risk-transfer","title":"What insurance does and does not protect you from","category":"Insurance and Risk Management","source":"bou_literacy","keywords":["insurance","risk"],"geo":["Uganda","East Africa"],"problem":"A major accident, illness, theft or property loss can create costs that a household may struggle to pay alone.","stakes":"Without a plan for significant risks, one event can disrupt savings, income and other financial goals.","explanation":"Insurance transfers specified financial risks to an insurer under agreed policy terms; exclusions, limits, premiums and claim conditions matter.","action":"Read the policy schedule and exclusions, check the insurer's regulatory status, and ask questions about what is and is not covered."},
    {"slug":"retirement-start-small","title":"Why retirement planning should begin before retirement feels close","category":"Retirement Planning","source":"bou_literacy","keywords":["retirement","old","age"],"geo":["Uganda","East Africa"],"problem":"When daily expenses consume all available income, retirement can feel too distant to plan for.","stakes":"Delaying every conversation about later-life income can leave fewer years to prepare and fewer options to adjust.","explanation":"Retirement planning considers future living costs, expected income sources, saving capacity and the risks that may affect long-term plans.","action":"Write down the income sources you may have later in life and identify one realistic step to learn about or strengthen them."},
    {"slug":"financial-goals-prioritisation","title":"Turn a vague money wish into a practical financial goal","category":"Wealth Creation","source":"cfpb_toolkit","keywords":["goals","saving"],"geo":["global","Uganda","East Africa"],"problem":"A goal such as 'I want to be financially stable' can feel too large to act on.","stakes":"Without a clear target and next step, everyday spending decisions can repeatedly push the goal further away.","explanation":"A useful financial goal is specific, time-aware and connected to an amount or action that can be reviewed and adjusted.","action":"Write one goal, the amount or action involved, a realistic time frame and the next small step."},
    {"slug":"track-income-expenses","title":"The simple money record that reveals where your income goes","category":"Financial Literacy","source":"cfpb_toolkit","keywords":["income","bills","spending"],"geo":["global","Uganda","East Africa"],"problem":"It is easy to lose track of small payments when money moves through cash, bank accounts and mobile money.","stakes":"Without a clear record, people may underestimate spending or overlook recurring charges and obligations.","explanation":"Recording income, bills and spending creates a clearer picture of cash flow and supports more informed choices.","action":"For seven days, record every payment and income entry, including cash and digital transactions, then group them into categories."},
    {"slug":"understand-financial-product-fees","title":"The small fees that can change the real cost of a financial product","category":"Banking and Financial Services","source":"cfpb_toolkit","keywords":["financial","products","services"],"geo":["global","Uganda","East Africa"],"problem":"A financial service may appear inexpensive until transaction charges, account fees or penalties are considered.","stakes":"Repeated fees can reduce savings or make borrowing and payments more expensive than expected.","explanation":"Comparing financial products requires looking beyond the headline rate to the complete fee schedule, conditions and consumer protections.","action":"Ask for the full fee schedule and compare the total likely cost for the way you actually plan to use the service."},
    {"slug":"avoid-impulse-financial-decisions","title":"A pause that can protect you from costly money decisions","category":"Financial Psychology","source":"cfpb_toolkit","keywords":["financial","decisions","spending"],"geo":["global","Uganda","East Africa"],"problem":"Pressure, excitement or fear can make an immediate financial decision feel more urgent than it really is.","stakes":"Rushed decisions can lead to unaffordable purchases, unsuitable borrowing or investment in products that are not understood.","explanation":"A deliberate decision process gives you time to compare costs, check facts and consider how a choice affects existing goals.","action":"For any non-emergency financial commitment, pause, write down the total cost and compare at least one alternative before agreeing."}
]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.in_script = False

    def handle_data(self, data: str) -> None:
        if not self.in_script and data.strip():
            self.parts.append(data.strip())


def fetch_source(url: str, timeout: int = 15) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(2_000_000)
        content_type = response.headers.get("Content-Type", "")
        if response.status != 200:
            raise ValueError(f"Source returned HTTP {response.status}: {url}")
        if "pdf" in content_type.casefold() or url.casefold().endswith(".pdf"):
            # PDFs are accepted as reachable official sources, but text extraction is
            # deliberately not claimed here; PDF evidence needs a separate parser/review.
            return {"url": url, "final_url": response.geturl(), "status": response.status, "content_type": content_type, "text": ""}
        parser = _TextExtractor()
        parser.feed(body.decode("utf-8", errors="replace"))
        text = re.sub(r"\s+", " ", " ".join(parser.parts))
        if len(text) < 200:
            raise ValueError(f"Source page returned too little readable text: {url}")
        return {"url": url, "final_url": response.geturl(), "status": response.status, "content_type": content_type, "text": text[:50000]}


def _default_fetcher(url: str) -> dict[str, Any]:
    return fetch_source(url)


def refresh_topics(
    library_path: str | Path,
    *,
    target: int = 20,
    fetcher: Callable[[str], dict[str, Any]] = _default_fetcher,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Add up to target unused topics whose official source pages are reachable."""
    if target < 1:
        raise ValueError("target must be at least 1")
    topics = load_topics(library_path)
    known = {str(item.get("id")) for item in topics}
    timestamp = (now or datetime.now(UTC)).isoformat()
    cache: dict[str, dict[str, Any]] = {}
    added: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    # Topic discovery is deliberately evergreen and mindset-first. News feeds are
    # not used to set the editorial agenda; official sources only validate principles.
    for blueprint in MINDSET_TOPIC_BLUEPRINTS:
        if len(added) >= target:
            break
        topic_id = "TFC-" + hashlib.sha1(blueprint["slug"].encode()).hexdigest()[:10].upper()
        if topic_id in known:
            continue
        source_key = blueprint["source"]
        source_meta = SOURCE_CATALOG[source_key]
        try:
            if source_key not in cache:
                cache[source_key] = fetcher(source_meta["url"])
            source_result = cache[source_key]
            if source_result.get("status") != 200:
                raise ValueError("Source did not return HTTP 200")
            page_text = str(source_result.get("text", "")).casefold()
            if page_text:
                matched = [word for word in blueprint["keywords"] if word.casefold() in page_text]
                if len(matched) < min(1, len(blueprint["keywords"])):
                    raise ValueError("Source page did not contain the topic's expected evidence keywords")
            elif not source_meta["url"].endswith(".pdf"):
                raise ValueError("Source page has no extracted text for relevance checking")
            source_record = {
                "url": source_meta["url"],
                "publisher": source_meta["publisher"],
                "domain": source_meta["domain"],
                "http_status": 200,
                "checked_at": timestamp,
                "page_title": source_result.get("title", ""),
                "verification": ("reachable_pdf_needs_text_review" if not page_text and source_meta["url"].casefold().endswith(".pdf") else "reachable_and_keyword_checked"),
                "evidence_note": "Official source page was reachable and contained at least one mapped topic keyword; claim-level support still requires editorial review.",
            }
        except (OSError, ValueError, TimeoutError, urllib.error.URLError) as exc:  # Fail closed.
            rejected.append({"title": blueprint["title"], "reason": str(exc)})
            continue

        topic = {
            "id": topic_id,
            "title": blueprint["title"],
            "category": blueprint["category"],
            "target_audience": ["global adults", "young adults", "households", "entrepreneurs"],
            "geographic_relevance": blueprint["geo"],
            "research_sources": [source_record],
            "sources": [source_meta["url"]],
            "research_status": ("source_reachable_needs_manual_review" if not page_text and source_meta["url"].casefold().endswith(".pdf") else "source_checked_needs_claim_review"),
            "research_checked_at": timestamp,
            "production_status": "not_started",
            "publication_status": "not_published",
            "editorial_brief": {
                "problem": blueprint["problem"],
                "stakes": blueprint["stakes"],
                "explanation": blueprint["explanation"],
                "action": blueprint["action"],
            },
            "topic_slug": blueprint["slug"],
            "discovery_metadata": {"method": "evergreen_money_mindset_blueprint", "candidate_only": True},
        }
        if add_topic(topics, topic):
            added.append(topic)
            known.add(topic_id)

    save_topics(library_path, topics)
    return {
        "target": target,
        "added_count": len(added),
        "library_count": len(topics),
        "added": added,
        "rejected": rejected,
        "discovery_method": "evergreen_money_mindset_blueprints",
        "news_feed_topics_added": 0,
        "mindset_topics_added": len(added),
        "target_met": len(added) >= target,
        "saved_to": str(library_path),
        "research_limitations": "Topics are selected from an evergreen money-mindset library. Official source pages are checked for reachability and mapped relevance keywords; this does not prove claim-level support. Every candidate requires editorial review.",
    }


def main_refresh(library_path: str, target: int = 20) -> int:
    report = refresh_topics(library_path, target=target)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["target_met"] else 2
