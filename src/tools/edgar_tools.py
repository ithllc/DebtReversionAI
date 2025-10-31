from mcp.types import TextContent
from edgar import Company, set_identity
from datetime import datetime, date, timedelta
import os
import re

# Set SEC identity if provided
if os.getenv("SEC_API_USER_AGENT"):
    try:
        set_identity(os.getenv("SEC_API_USER_AGENT"))
    except Exception:
        # Fail silently here; caller will see errors when calling EDGAR
        pass


async def search_debt_conversions(ticker: str, months_back: int = 3) -> str:
    try:
        company = Company(ticker)

        cutoff_date = datetime.now() - timedelta(days=months_back * 30)

        # Some EDGAR client implementations use pyarrow-backed filters which may
        # behave differently across environments. To avoid pyarrow-specific
        # attribute errors, fetch a reasonable recent slice of filings and
        # perform date filtering in Python.
        raw_filings = company.get_filings(form="8-K")

        conversions = []
        keywords = [
            "conversion",
            "convertible",
            "debt conversion",
            "note conversion",
            "debenture",
        ]

        # Try to iterate a modest number of recent filings and filter by date
        # in-Python to avoid pyarrow/chunked array issues in some installs.
        try:
            candidate_filings = list(raw_filings[:200])
        except Exception:
            # If slicing fails for any reason, fallback to using the raw iterator
            try:
                candidate_filings = list(raw_filings)
            except Exception:
                candidate_filings = []

        # Debug: print how many candidate filings we will scan and their accessions/dates
        try:
            debug_list = []
            for f in candidate_filings:
                debug_list.append({
                    'accession': getattr(f, 'accession_no', None),
                    'filing_date': getattr(f, 'filing_date', getattr(f, 'date', None))
                })
            print(f"[DEBUG] candidate_filings_count={len(candidate_filings)} sample={debug_list[:10]}")
        except Exception:
            print("[DEBUG] candidate_filings: unable to enumerate details")

        # Limit how many filings we will scan to avoid very long runs
        for filing in candidate_filings:
            try:
                fdate = getattr(filing, 'filing_date', None)
                if fdate is None:
                    # Some filing objects provide date as a string under different attrs
                    fdate = getattr(filing, 'date', None)
                # Normalize to datetime for comparison
                if isinstance(fdate, str):
                    try:
                        fdate_dt = datetime.fromisoformat(fdate)
                    except Exception:
                        # Try parsing only the date component
                        try:
                            fdate_dt = datetime.strptime(fdate.split('T')[0], '%Y-%m-%d')
                        except Exception:
                            fdate_dt = None
                elif isinstance(fdate, datetime):
                    fdate_dt = fdate
                elif isinstance(fdate, date):
                    # Convert date to datetime at midnight for comparison
                    fdate_dt = datetime(fdate.year, fdate.month, fdate.day)
                else:
                    fdate_dt = None

                # Debug: print raw and parsed date for this filing
                try:
                    accession_dbg = getattr(filing, 'accession_no', None)
                except Exception:
                    accession_dbg = None
                print(f"[DEBUG] checking filing accession={accession_dbg} raw_date={fdate} parsed_date={fdate_dt}")

                # If we could not determine a datetime for this filing, skip it
                if not fdate_dt:
                    print(f"[DEBUG] skipping accession={accession_dbg}: no parseable date")
                    continue
                # Skip filings older than cutoff
                if fdate_dt < cutoff_date:
                    print(f"[DEBUG] skipping accession={accession_dbg}: date {fdate_dt} older than cutoff {cutoff_date}")
                    continue

                # Try to get a cleaned text representation suitable for keyword search
                try:
                    # edgartools exposes filing.text(detail=...) for different levels
                    # of extraction; prefer a standard/clean text if available.
                    text = filing.text(detail='standard')
                except Exception:
                    try:
                        text = filing.text()
                    except Exception:
                        try:
                            text = str(filing)
                        except Exception:
                            text = ''

                if not isinstance(text, str):
                    try:
                        text = str(text)
                    except Exception:
                        text = ''

                text_l = text.lower()

                if any(keyword in text_l for keyword in keywords):
                    # Find the first keyword match and produce a context snippet
                    first_idx = min((text_l.find(k) for k in keywords if k in text_l), default=-1)
                    snippet = ''
                    if first_idx != -1:
                        start = max(0, first_idx - 500)
                        end = min(len(text), first_idx + 500)
                        snippet = text[start:end]

                    # We do not attempt to guess a single conversion price here —
                    # the LLM can inspect the snippet if it needs to identify the
                    # correct price. Store the snippet and metadata only.
                    conversions.append(
                        {
                            "date": getattr(filing, 'filing_date', getattr(filing, 'date', None)),
                            "accession": getattr(filing, 'accession_no', None),
                            "url": getattr(filing, 'url', None),
                            "snippet": snippet,
                        }
                    )
            except Exception:
                # Ignore issues parsing a single filing and continue
                continue

        result = f"Debt Conversion Search for {ticker} (Last {months_back} months):\n"
        result += f"Found {len(conversions)} potential conversion events\n\n"

        for conv in conversions:
            result += f"- Date: {conv['date']}\n"
            result += f"  Accession: {conv['accession']}\n"
            result += f"  URL: {conv['url']}\n"
            if conv.get('snippet'):
                result += "  Snippet:\n\n"
                # include snippet in a fenced code block so LLMs can read it verbatim
                result += "```\n" + conv['snippet'] + "\n```\n\n"

        return result

    except Exception as e:
        return f"Error searching conversions for {ticker}: {str(e)}"


async def get_recent_filings(ticker: str, form_type: str = "8-K", count: int = 10) -> str:
    try:
        company = Company(ticker)
        # Return at most `count` filings within the last 6 months
        cutoff = datetime.now() - timedelta(days=6 * 30)
        recent = []
        try:
            all_filings = company.get_filings(form=form_type)
        except Exception:
            all_filings = []

        for filing in all_filings:
            if len(recent) >= count:
                break
            fdate = getattr(filing, 'filing_date', None) or getattr(filing, 'date', None)
            fdate_dt = None
            if isinstance(fdate, str):
                try:
                    fdate_dt = datetime.fromisoformat(fdate)
                except Exception:
                    try:
                        fdate_dt = datetime.strptime(fdate.split('T')[0], '%Y-%m-%d')
                    except Exception:
                        fdate_dt = None
            elif isinstance(fdate, datetime):
                fdate_dt = fdate
            elif isinstance(fdate, date):
                fdate_dt = datetime(fdate.year, fdate.month, fdate.day)

            if not fdate_dt:
                # Skip filings without a parseable date
                continue
            if fdate_dt < cutoff:
                continue
            recent.append(filing)

        result = f"Recent {form_type} Filings for {ticker} (last 6 months, max {count}):\n\n"
        for filing in recent:
            result += f"- {getattr(filing, 'filing_date', getattr(filing, 'date', 'unknown'))}: {getattr(filing, 'form', form_type)}\n"
            result += f"  Accession: {getattr(filing, 'accession_no', 'unknown')}\n"
            result += f"  URL: {getattr(filing, 'url', 'unknown')}\n\n"

        return result

    except Exception as e:
        return f"Error getting {form_type} filings for {ticker}: {str(e)}"


def _extract_price(text: str):
    # Backwards-compatible single-price extractor: return first candidate
    prices = _extract_prices_from_text(text)
    return prices[0] if prices else None


def _extract_prices_from_text(text: str):
    """Return a list of numeric price candidates extracted from text.

    Supports numbers with optional commas and decimals, e.g. $1,234.56
    Filters out implausible values via simple heuristics.
    """
    if not text:
        return []

    # Match $1,234.56 or $1234.56 or $1234
    price_pattern = r"\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
    raw_matches = re.findall(price_pattern, text)
    candidates = []
    for rm in raw_matches:
        try:
            norm = rm.replace(',', '')
            val = float(norm)
            # Filter out unrealistic values for conversion prices
            if 0.0001 < val < 1000000:
                candidates.append(val)
        except Exception:
            continue
    return candidates


async def extract_conversion_terms(filing_url: str) -> str:
    return "Conversion term extraction not yet implemented"
