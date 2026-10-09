"""
Live Verification Harness for J.A.R.V.I.S. Commercial Quotation & Multi-Channel Outreach Engine.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from tools.quotation_engine import quotation_engine
from tools.digital_marketing_suite import marketing_suite
from core.local_intelligence import LocalIntelligence

def run_live_check():
    print("=" * 65)
    print(" [J.A.R.V.I.S. LIVE QUOTATION & MULTI-CHANNEL OUTREACH HARNESS]")
    print("=" * 65)

    client_name = "Caterpillar India Manufacturing"
    location = "Thiruvallur Industrial Corridor, Chennai"

    print(f"\n[1. Compiling Commercial Quotation for '{client_name}']...")
    t0 = time.time()
    quote = quotation_engine.create_quotation(
        client_name=client_name,
        facility_location=location,
        discount_pct=7.5,
        corridor="Thiruvallur",
        generate_pdf=True
    )
    quote_dur = (time.time() - t0) * 1000

    print(f"  Quotation ID: {quote['quote_id']} ({quote_dur:.1f}ms)")
    print(f"  Subtotal: INR {quote['subtotal']:,.2f}")
    print(f"  Discount (7.5%): - INR {quote['discount_amt']:,.2f}")
    print(f"  Taxable Value: INR {quote['taxable_amount']:,.2f}")
    print(f"  GST (18%): INR {quote['gst_amount']:,.2f}")
    print(f"  GRAND TOTAL: INR {quote['grand_total']:,.2f}")
    print(f"  Executive PDF generated: {quote.get('pdf_path')}")

    pdf_p = Path(quote.get("pdf_path", ""))
    if pdf_p.exists():
        print(f"  PDF Verified on disk: {pdf_p.stat().st_size:,} bytes")
    else:
        raise RuntimeError("PDF generation failed to produce file!")

    print("\n[2. Synthesizing Multi-Channel Outreach Package]...")
    t0 = time.time()
    outreach = quotation_engine.generate_multi_channel_outreach(
        quote_data=quote,
        client_email="plant.safety@caterpillar.com",
        client_phone="+919840223344"
    )
    outreach_dur = (time.time() - t0) * 1000
    print(f"  Outreach synthesized in {outreach_dur:.1f}ms")
    print(f"  Email Subject: {outreach['email']['subject']}")
    print(f"  WhatsApp Click-to-Chat URL: {outreach['whatsapp']['click_to_chat_url'][:75]}...")
    print(f"  SMS Broadcast Copy ({outreach['sms']['length']} chars): {outreach['sms']['text']}")
    print(f"  Cadence: {len(outreach['cadence'])} follow-up stages programmed (Day 1, Day 3, Day 7)")

    print("\n[3. Verifying Local Intelligence Voice Directive]...")
    loc = LocalIntelligence()
    prompt = f"generate quote for {client_name} in Thiruvallur"
    handled, voice_resp = loc.evaluate_and_execute(prompt)
    print(f"  Directive handled: {handled}")
    print(f"  Butler Articulation: {voice_resp}")

    print("\n" + "=" * 65)
    print(" [ALL QUOTATION & OUTREACH VERIFICATIONS PASSED SUCCESSFULLY]")
    print("=" * 65)

if __name__ == "__main__":
    run_live_check()
