# 3. FLOW DIAGRAMS WITH PERSONAS

This document maps the end-to-end workflows for each user persona in the XFORIA DAD system.

---

## Personas

### **Persona 1: Frank (Fraud Analyst)**

**Role**: Fraud Investigation Team Member at Regional Bank

**Demographics**:
- Age: 35-45
- Experience: 8-12 years in fraud detection
- Tech Savvy: Medium (comfortable with basic software)
- Works: Monday-Friday, 9am-5pm, occasional weekends during fraud spikes

**Motivations**:
- Catch fraudsters and prevent losses
- Reduce manual review time (currently spends 60% of day reviewing documents)
- Understand decision reasoning (wants to learn patterns)
- Handle high volumes (50-200 daily documents)

**Pain Points**:
- Manual document review is tedious and error-prone
- Easy to miss subtle frauds after reviewing 100+ documents
- No clear audit trail for compliance
- Repeat fraudsters exploit lack of customer history

**Technology Comfort**:
- Uses email, Excel, bank's legacy system daily
- Comfortable with web applications
- Needs mobile-friendly interface (views on phone sometimes)
- Wants clear, visual decision explanations

**Goals with XFORIA DAD**:
- Reduce manual review time from 60% to 20% of day
- Catch more frauds (99.6% recall)
- Have clear reasoning for each decision
- Track repeat offenders

---

### **Persona 2: Rita (Risk Officer)**

**Role**: Chief Risk Officer (CRO) at Large National Bank

**Demographics**:
- Age: 50-60
- Experience: 20+ years in banking/compliance
- Tech Savvy: Low (delegates IT details to team)
- Works: Monday-Friday, office hours

**Motivations**:
- Reduce fraud losses (currently $2-5M annually)
- Maintain regulatory compliance
- Demonstrate controls to auditors
- Enable business growth without increasing risk

**Pain Points**:
- Fraud detection is scattered across multiple legacy systems
- No unified audit trail for regulators
- Can't scale manual review with transaction growth
- Pressure from board to reduce fraud losses

**Technology Comfort**:
- Prefers reports and dashboards over raw data
- Wants executive summaries, not technical details
- Needs mobile access to key metrics
- Relies on IT team for technical implementation

**Goals with XFORIA DAD**:
- ROI: 3-5x return on investment
- 60%+ reduction in fraud losses
- Audit trail demonstrating reasonable controls
- Compliance reporting for regulators
- Scalability to handle 10x transaction growth

---

### **Persona 3: Dev (System Developer)**

**Role**: Backend Integration Engineer at Bank's IT Department

**Demographics**:
- Age: 25-35
- Experience: 5-8 years software development
- Tech Savvy: High (expert programmer)
- Works: Monday-Friday, occasional on-call

**Motivations**:
- Fast, clean API integration
- Minimal changes to existing systems
- Clear documentation and support
- Predictable cost/scaling

**Pain Points**:
- Integration with legacy banking systems is complex
- Poor API documentation slows development
- Need to test thoroughly before production
- Limited support availability

**Technology Comfort**:
- Expert in Python, Java, C#, REST APIs
- Familiar with Docker, CI/CD, databases
- Comfort with error handling, logging, monitoring
- Prefers code examples over written documentation

**Goals with XFORIA DAD**:
- 2-4 week integration timeline
- Well-documented API with examples
- Fast response times (< 3 seconds ideal)
- Clear error messages and debugging info
- Automated testing capability

---

### **Persona 4: Clara (Compliance Manager)**

**Role**: Compliance Officer at Check Cashing Service

**Demographics**:
- Age: 40-50
- Experience: 10-15 years compliance/regulation
- Tech Savvy: Medium-Low
- Works: Monday-Friday, office hours + regulatory deadlines

**Motivations**:
- Ensure regulatory compliance (Know Your Customer, Anti-Money Laundering)
- Generate audit trails for regulators
- Reduce fraud exposure
- Minimize compliance violations/fines

**Pain Points**:
- Manual document review doesn't create audit trail
- Hard to demonstrate "reasonable controls" to auditors
- Compliance reports require manual data compilation
- Fear of regulatory penalties

**Technology Comfort**:
- Uses spreadsheets, document management systems
- Understands databases conceptually
- Needs to export/report data easily
- Prefers structured templates

**Goals with XFORIA DAD**:
- Audit trail for every document analyzed
- Export reports for regulatory submission
- Document decision reasoning for audits
- Track policy compliance over time
- Support SOX, BSA, AML requirements

---

### **Persona 5: Andy (Admin/IT Support)**

**Role**: System Administrator / Help Desk at Bank

**Demographics**:
- Age: 28-40
- Experience: 4-10 years IT operations
- Tech Savvy: Medium-High
- Works: Monday-Friday, some on-call rotation

**Motivations**:
- Keep systems running smoothly
- Minimize support tickets
- Enable user productivity
- Maintain system security

**Pain Points**:
- Users confused about how to use new system
- Integration issues cause system downtime
- No clear troubleshooting documentation
- Pressure to resolve issues quickly

**Technology Comfort**:
- Linux/Windows server management
- Database administration basics
- API troubleshooting
- Monitoring tools, logging systems

**Goals with XFORIA DAD**:
- Easy deployment (Docker, clear setup)
- Detailed troubleshooting documentation
- Clear error messages and logs
- Scalability without manual intervention
- Admin dashboard for system monitoring

---

## End-to-End User Workflows

### **Workflow 1: Frank's Daily Fraud Detection (Main Path)**

```
MORNING START (8:45am)
├─ Frank logs into XFORIA DAD via browser
├─ Enters username/password
├─ 2FA verification (optional security)
└─ Lands on Dashboard

DASHBOARD VIEW
├─ Frank sees:
│  ├─ Queue of pending documents (42 waiting)
│  ├─ Recent decisions and accuracy stats
│  ├─ High-risk documents flagged for review
│  ├─ System status (healthy)
│  └─ Fraud alerts for known repeat offenders
└─ Time: 1-2 minutes

DOCUMENT ANALYSIS (Repeat 20-50x per day)
├─ Click "View Next Document" or manually select
│
├─ UPLOAD PHASE (if needed)
│  ├─ Drag-and-drop check image into upload area
│  ├─ System validates file (size, format)
│  ├─ Progress bar shows upload status
│  └─ Time: 30 seconds
│
├─ ANALYSIS PHASE
│  ├─ System processes document:
│  │  ├─ OCR extraction (Google Vision)
│  │  ├─ Data normalization
│  │  ├─ ML fraud prediction
│  │  ├─ AI reasoning (GPT-4)
│  │  └─ Customer history lookup
│  ├─ Frank sees loading spinner
│  └─ Time: 1-3 seconds
│
├─ RESULTS DISPLAY
│  ├─ Decision box (APPROVE/ESCALATE/REJECT) prominently shown
│  ├─ Risk score (e.g., "73% Fraud Risk")
│  ├─ Confidence level (e.g., "High confidence")
│  │
│  ├─ Extracted Data Section
│  │  ├─ Bank: Chase Bank
│  │  ├─ Payee: John Smith
│  │  ├─ Payer: Alice Corporation
│  │  ├─ Amount: $5,000.00
│  │  ├─ Check #: 1234567
│  │  ├─ Date: 12/15/2024
│  │  └─ Confidence indicators (green/yellow/red) per field
│  │
│  ├─ AI Reasoning Section
│  │  └─ "Risk identified: Payer has 2 previous fraud incidents.
│  │     Routing number validation passed but amount shows suspicious
│  │     pattern (similar to declined transaction from 2 weeks ago).
│  │     AI recommends ESCALATE for human review."
│  │
│  ├─ Customer History (if available)
│  │  ├─ Payer: Alice Corp
│  │  ├─ Total fraud attempts: 2
│  │  ├─ Escalations: 1
│  │  ├─ Last activity: 2 weeks ago
│  │  └─ Pattern: Similar amounts, frequent attempts
│  │
│  ├─ Similar Past Cases (related)
│  │  ├─ Check #0988765 ($4,950, rejected)
│  │  ├─ Check #0988876 ($5,100, escalated)
│  │  └─ Common pattern: Amounts near $5K, same payer
│  │
│  ├─ Action Buttons
│  │  ├─ "Approve This Check"
│  │  ├─ "Escalate for Review"
│  │  ├─ "Reject Immediately"
│  │  ├─ "Save for Later"
│  │  ├─ "Add Note" (free text)
│  │  └─ "Export Details" (JSON/PDF)
│  │
│  └─ Time: 30 seconds to review
│
├─ FRANK'S DECISION
│  ├─ Scenario A: AI says APPROVE, Frank trusts → Clicks "Approve"
│  │  ├─ System logs decision with timestamp
│  │  ├─ Document moved to APPROVED queue
│  │  └─ Auto-advances to next document
│  │
│  ├─ Scenario B: AI says ESCALATE → Frank reviews AI reasoning
│  │  ├─ Reads customer history (2 previous frauds!)
│  │  ├─ Compares with similar past cases
│  │  ├─ Checks current amount ($5K) vs previous ($4.95K, $5.1K)
│  │  ├─ Makes judgment: "Yes, pattern looks suspicious"
│  │  ├─ Clicks "Reject Immediately"
│  │  ├─ System logs: Rejected, reason = "Customer history + pattern matching"
│  │  └─ Updates customer fraud count for next time
│  │
│  ├─ Scenario C: AI says REJECT, Frank disagrees
│  │  ├─ Frank reviews OCR extraction carefully
│  │  ├─ OCR shows 99% confidence all fields
│  │  ├─ Frank sees customer has NO fraud history (first time)
│  │  ├─ Frank overrides: "This looks legitimate"
│  │  ├─ Clicks "Approve This Check"
│  │  ├─ System logs: Approved (override), reason = "First-time customer, clean fields"
│  │  └─ AI learns from feedback (optional retraining)
│  │
│  └─ Time per decision: 15-60 seconds depending on confidence
│
├─ REPEAT for next 40-50 documents throughout day
└─ Total daily volume: 50 documents = ~45 minutes vs. 3+ hours manual

MID-DAY REPORT (12:00pm)
├─ Frank checks dashboard stats:
│  ├─ Documents processed: 28
│  ├─ Approved: 20
│  ├─ Escalated: 5
│  ├─ Rejected: 3
│  ├─ Avg time per document: 52 seconds
│  ├─ Accuracy compared to past: +15% improvement
│  └─ Fraud prevented (est): $48,000
└─ Time: 2 minutes

BATCH EXPORT (3:00pm)
├─ Frank needs to report daily results to supervisor
├─ Clicks "Export Daily Report"
├─ Selects fields:
│  ├─ Document ID, Decision, Risk Score, AI Reasoning
│  ├─ Customer Name, Fraud Count
│  ├─ Timestamp, User
│  └─ File format: CSV or PDF
├─ System generates report in 5 seconds
├─ Downloads 52 KB PDF report
└─ Forwards to supervisor, Rita

END OF DAY (5:00pm)
├─ Frank logs out
├─ System shows summary:
│  ├─ Total documents: 48
│  ├─ Time saved vs manual: 180 minutes
│  ├─ Estimated fraud prevented: $156,000
│  └─ Productivity increase: +70%
└─ Frank goes home feeling accomplished
```

---

### **Workflow 2: Rita's Compliance & Risk Review (Weekly)**

```
MONDAY MORNING (9:00am)
├─ Rita's assistant prepares weekly fraud report
├─ Logs into XFORIA DAD as admin
└─ Navigates to "Executive Dashboard"

EXECUTIVE DASHBOARD
├─ Rita sees key metrics:
│  ├─ Total documents processed: 2,847
│  ├─ Fraud detected: 178 (6.3%)
│  ├─ Estimated fraud prevented: $892,000
│  ├─ System uptime: 99.97%
│  ├─ Average processing time: 1.8 seconds
│  ├─ User satisfaction: 8.7/10
│  ├─ Cost savings vs manual review: $284,000
│  └─ Compared to last week: +12% volume, -3% fraud rate
│
├─ TREND ANALYSIS
│  ├─ 30-day fraud trend chart (decreasing)
│  ├─ Most common fraud type: Altered checks (42%)
│  ├─ Most common payer: Alice Corp (28 incidents)
│  ├─ Geographic hotspot: California (35% of fraud)
│  └─ Time patterns: 60% of fraud Mon-Wed
│
└─ Time: 5 minutes

AUDIT TRAIL REVIEW (For Compliance)
├─ Rita clicks "Compliance Reports"
├─ Selects:
│  ├─ Date range: Last 30 days
│  ├─ Report type: Decisions with full audit trail
│  └─ Export format: PDF for regulators
│
├─ System generates report showing:
│  ├─ Every document processed (2,847 entries)
│  ├─ For each:
│  │  ├─ Document ID, timestamp
│  │  ├─ Extracted data (OCR fields)
│  │  ├─ ML predictions (both models)
│  │  ├─ AI reasoning (full GPT-4 response)
│  │  ├─ Customer history at time of decision
│  │  ├─ Final decision and human override (if any)
│  │  ├─ User who reviewed and timestamp
│  │  └─ Confidence scores
│  │
│  ├─ This demonstrates to auditors:
│  │  ├─ "Reasonable controls" in place
│  │  ├─ Consistent decision logic
│  │  ├─ Human review when needed
│  │  ├─ Transparency and explainability
│  │  └─ Full audit trail (SOX, BSA, AML compliant)
│  │
│  └─ Generates 47-page PDF in 30 seconds
│
├─ Rita reviews summary page:
│  ├─ Processing statistics
│  ├─ Detection methodology explanation
│  ├─ False positive/negative analysis
│  ├─ Repeat offender tracking
│  └─ Recommendations for policy adjustments
│
└─ Time: 10 minutes

ROI ANALYSIS
├─ Rita requests financial impact report
├─ System calculates:
│  ├─ Fraud losses prevented (last 30 days): $892,000
│  ├─ Cost of system (monthly): $45,000
│  ├─ Cost of manual review (previous method): $180,000/month
│  │  ├─ 50 analysts × $100/hour × 40 hours = $200k/month
│  │  ├─ Coverage lost due to context switching
│  │  └─ Estimated 90% reduction with XFORIA
│  │
│  ├─ Savings:
│  │  ├─ Manual review labor: $162,000/month
│  │  ├─ Fraud losses reduced: $500,000-$2M/month
│  │  ├─ Operational efficiency: +45% throughput
│  │  └─ TOTAL MONTHLY BENEFIT: $662,000 - $2.162M
│  │
│  ├─ NET ROI:
│  │  └─ (Benefit - Cost) / Cost = ($662K - $45K) / $45K = 13.7x (Year 1)
│  │
│  └─ Payback period: 10 days
│
└─ Time: 5 minutes (Rita prints for board meeting)

BOARD PRESENTATION PREP
├─ Rita downloads executive summary
├─ Key slides for board:
│  ├─ Slide 1: "XFORIA DAD reduces fraud by 60%+"
│  ├─ Slide 2: "ROI: 13.7x in first month"
│  ├─ Slide 3: "System processes 99.6% of fraud correctly"
│  ├─ Slide 4: "Compliance audit trail demonstrates controls"
│  └─ Slide 5: "Recommendation: Expand to other document types"
│
└─ Time: 20 minutes total

MONTH-END STRATEGIC REVIEW (Monthly)
├─ Rita meets with Frank (fraud analyst) and Dev (tech lead)
├─ Discussion topics:
│  ├─ "Fraud patterns changing? Need to adjust risk thresholds?"
│  ├─ "System performing within SLAs? Any outages?"
│  ├─ "Cost tracking: Are we hitting $45K/month budget?"
│  ├─ "Accuracy: Are we still at 99.6% recall?"
│  ├─ "Expansion plan: Ready for paystubs/money orders?"
│  └─ "Anything we should investigate further?"
│
├─ Action items from meeting:
│  ├─ Increase risk threshold to 75% (from 70%) to reduce false positives
│  ├─ Schedule quarterly model retraining (due next week)
│  ├─ Plan expansion to paystub analysis (Q1 2025)
│  └─ Upgrade Supabase plan for 3x volume growth
│
└─ Time: 30 minutes
```

---

### **Workflow 3: Dev's Integration & Deployment (Initial Setup)**

```
WEEK 1: DISCOVERY & SETUP

Day 1-2: API Documentation Review
├─ Dev receives API documentation from vendor
├─ Reviews:
│  ├─ Authentication (JWT token flow)
│  ├─ Check analysis endpoint (/api/check/analyze)
│  ├─ Request/response formats
│  ├─ Error codes and handling
│  ├─ Rate limits (1000 requests/min, 100 concurrent)
│  ├─ Timeout behavior (5-second timeout)
│  ├─ Example cURL requests
│  └─ Sample payloads (JSON examples)
│
├─ Dev asks questions:
│  ├─ "Does system support batch processing?"
│  │  └─ Response: "Not yet, but in Q1 2025 roadmap"
│  │
│  ├─ "What if our legacy system has 60-second timeout? Will it work?"
│  │  └─ Response: "Consider async option: POST document, poll status with ID"
│  │
│  ├─ "How do we handle credentials securely?"
│  │  └─ Response: "API key in Authorization header, store in environment variables"
│  │
│  └─ "What data format does system expect for address fields?"
│     └─ Response: "Free text, we normalize it (example: '123 Main St' → '123 Main Street')"
│
└─ Time: 4 hours

Day 2-3: Environment Setup
├─ Dev clones SDK from GitHub
├─ Sets up local development:
│  ├─ Creates test API key (provided by vendor)
│  ├─ Stores in .env file (not committed to git):
│  │  ├─ XFORIA_API_URL=https://api.xforia.com
│  │  ├─ XFORIA_API_KEY=sk_test_xxx
│  │  └─ XFORIA_ORG_ID=org_xxx
│  │
│  ├─ Sets up test environment with fake data
│  ├─ Runs vendor's SDK client examples
│  └─ Tests basic API connectivity
│
└─ Time: 2 hours

Day 3-4: Build Adapter Layer
├─ Dev creates Python adapter to XFORIA API
├─ File: `/integrations/xforia_client.py`
├─ Code structure:
│  ```python
│  class XFORIAClient:
│      def __init__(self, api_key, org_id):
│          self.api_key = api_key
│          self.org_id = org_id
│
│      def analyze_check(self, file_path):
│          # Read file, call XFORIA API, return result
│
│      def analyze_paystub(self, file_path):
│          # Similar pattern
│  ```
│
├─ Error handling:
│  ├─ Network timeouts (retry up to 3x)
│  ├─ API errors (parse error message, map to internal error codes)
│  ├─ Rate limiting (queue requests if hitting limit)
│  └─ Invalid response (log for debugging)
│
├─ Logging:
│  ├─ Info: "Sent check to XFORIA, received fraud_score=73"
│  ├─ Error: "XFORIA timeout after 5 seconds, retrying..."
│  └─ Debug: "Request body: {..}, Response body: {..}"
│
└─ Time: 6 hours

WEEK 2: INTEGRATION & TESTING

Day 5-6: Database Integration
├─ Dev adds fields to check_storage table:
│  ├─ xforia_request_id (track specific call)
│  ├─ xforia_fraud_score (save result)
│  ├─ xforia_ai_recommendation (save decision)
│  ├─ xforia_extracted_fields (JSON blob)
│  └─ xforia_processing_time (performance tracking)
│
├─ Dev updates database schema:
│  ```sql
│  ALTER TABLE checks ADD COLUMN (
│    xforia_request_id VARCHAR(255),
│    xforia_fraud_score FLOAT,
│    xforia_ai_recommendation VARCHAR(20),
│    xforia_extracted_fields JSONB,
│    xforia_processing_time_ms INT
│  );
│  ```
│
└─ Time: 2 hours

Day 6-7: Test Cases
├─ Dev writes test suite (pytest):
│  ├─ Unit tests:
│  │  ├─ Test adapter with mock API responses
│  │  ├─ Test error handling (timeouts, malformed responses)
│  │  ├─ Test database storage
│  │  └─ Test rate limiting logic
│  │
│  ├─ Integration tests:
│  │  ├─ Test with real (sandbox) API
│  │  ├─ Test full flow: upload → analyze → store → display
│  │  ├─ Test with 10 sample checks (various edge cases)
│  │  └─ Measure performance (should be < 3 seconds)
│  │
│  └─ Regression tests:
│     ├─ Ensure existing system still works
│     ├─ Test with non-check documents
│     └─ Test with other users/concurrent requests
│
├─ Test data:
│  ├─ Real sample check images provided by vendor
│  ├─ Edge cases: blurry, rotated, low-contrast
│  ├─ Invalid cases: blank page, non-check documents
│  └─ Large files: 10MB scans (stress test)
│
├─ Results:
│  ├─ 47 tests: 46 passing, 1 failing
│  │  └─ Issue: Timeout on 10MB file takes 8 seconds (expected 3-5s)
│  │     - Solution: Implement async processing for large files
│  │
│  ├─ Performance benchmarks:
│  │  ├─ Small check (500KB): 1.2 seconds average
│  │  ├─ Medium check (1.5MB): 2.1 seconds average
│  │  ├─ Large check (3MB): 3.8 seconds average
│  │  └─ Network latency: 180-250ms (acceptable)
│  │
│  └─ Uptime test:
│     ├─ Simulated 100 concurrent requests
│     ├─ 2 failed (temporary network blip, retried successfully)
│     ├─ Success rate: 99.8% ✓
│     └─ No crashes or data loss
│
└─ Time: 8 hours

WEEK 3: STAGING & QA

Day 8-10: Staging Deployment
├─ Dev deploys to staging environment
├─ Parallel testing:
│  ├─ Run old system (manual review) alongside XFORIA
│  ├─ Process same 100 test checks both ways
│  ├─ Compare results:
│  │  ├─ XFORIA: 73 approved, 15 escalated, 12 rejected
│  │  ├─ Manual: 74 approved, 14 escalated, 12 rejected
│  │  ├─ Accuracy: 98% agreement (acceptable variation)
│  │  └─ Speed: XFORIA 2.1 sec/check vs manual 10 min/check
│  │
│  └─ Frank (fraud analyst) validates decisions
│     ├─ "XFORIA escalated this check, I would have too" ✓
│     ├─ "This one it approved, but I'm suspicious of that payer"
│     │  └─ Dev notes: "Customer has no fraud history, OCR 99% confident"
│     │     Frank: "Okay, makes sense, I trust it"
│     └─ "Excellent, this catches the repeat offender ring!" ✓
│
├─ Monitor system health:
│  ├─ CPU usage: 15-30% (good)
│  ├─ Memory: stable at 800MB (good)
│  ├─ API response times: consistently 1.2-3 seconds (good)
│  ├─ Error rate: 0.2% (acceptable)
│  └─ No uncontrolled memory growth (no leaks detected)
│
├─ Performance characteristics:
│  ├─ Throughput: 1,440 documents/day = 1 per minute average
│  ├─ Peak: 10 concurrent requests handled smoothly
│  ├─ Bottleneck: OCR latency (not our system)
│  └─ Recommendation: Pre-queue large files during off-hours
│
└─ Time: 8 hours

WEEK 4: PRODUCTION DEPLOYMENT & SUPPORT

Day 11-14: Production Rollout
├─ Dev coordinates with Ops/Security team
├─ Pre-flight checklist:
│  ├─ ✓ All tests passing in staging
│  ├─ ✓ Frank validated decisions are accurate
│  ├─ ✓ Performance metrics within SLA
│  ├─ ✓ Scaling tested (handles 10x load)
│  ├─ ✓ Disaster recovery plan documented
│  ├─ ✓ Rollback plan in place (< 5 min)
│  └─ ✓ Security review passed (no vulns)
│
├─ Deploy to production (Tuesday 2:00pm)
│  ├─ Step 1: Deploy API adapter code
│  ├─ Step 2: Run database migration (2-minute downtime accepted)
│  ├─ Step 3: Switch traffic from old system to XFORIA (canary rollout: 10% → 50% → 100%)
│  ├─ Step 4: Monitor for issues for 30 minutes
│  ├─ Step 5: Full traffic switchover
│  └─ Deployment window: 2:00pm - 3:15pm (during low volume)
│
├─ Post-deployment monitoring:
│  ├─ First 1 hour: Dev and Ops watch dashboards
│  │  ├─ Error rate: 0.1% ✓ (within tolerance)
│  │  ├─ Response time: 2.3 sec avg ✓
│  │  ├─ No database issues ✓
│  │  └─ All alerts quiet ✓
│  │
│  ├─ First 24 hours:
│  │  ├─ Frank reports: "System is working great, saving me hours"
│  │  ├─ Rita reports: "Great, we're catching more fraud"
│  │  └─ No support tickets escalated
│  │
│  └─ First week: Monitor for edge cases, performance drifts
│
├─ Go-live communication:
│  ├─ Email to stakeholders:
│  │  ├─ "XFORIA DAD is now live in production"
│  │  ├─ "Processing 50-200 documents/day"
│  │  ├─ "Questions? Contact: dev-support@bank.com"
│  │  └─ "API docs: https://internal-wiki.bank.com/xforia"
│  │
│  └─ Kick-off meeting with Frank, Rita, Andy (admin)
│     ├─ Live demo of dashboard
│     ├─ Q&A: Common questions
│     ├─ Escalation process if issues arise
│     └─ Support phone number for emergencies
│
└─ Time: 6 hours

ONGOING: Monitoring & Maintenance

Day 15+: First Month Operations
├─ Daily monitoring:
│  ├─ Dev checks error logs (email alert summary)
│  ├─ Monitors API performance
│  └─ Responds to support issues (< 2 hour response)
│
├─ Weekly:
│  ├─ Review system metrics with Ops team
│  ├─ Discuss any anomalies
│  ├─ Plan infrastructure changes if needed
│  └─ Feedback from Frank & Rita incorporated
│
├─ Monthly:
│  ├─ 1-hour retrospective: "What went well, what could be better"
│  ├─ Plan next improvements (paystubs, batch processing, etc.)
│  ├─ Update documentation based on real usage
│  └─ Capacity planning for growth
│
└─ Ongoing support:
   ├─ Vendor support phone: 24/7 (for critical issues)
   ├─ Slack channel: #xforia-support (internal)
   ├─ Email: vendor-support@xforia.com
   └─ Monthly check-in calls with vendor
```

---

### **Workflow 4: Clara's Audit & Compliance Review (Quarterly)**

```
QUARTERLY AUDIT (December)

WEEK 1: DATA GATHERING

Monday (Dec 2):
├─ Clara notifies IT that quarterly audit is starting
├─ Requests export of all documents processed (last 90 days)
└─ Asks for system configuration documentation

Tuesday-Wednesday (Dec 3-4):
├─ Dev exports audit data:
│  ├─ All 8,567 checks processed (Oct-Dec)
│  ├─ Includes: timestamp, extracted data, ML scores, decision, user
│  ├─ Format: CSV (for spreadsheet analysis) + XML (for auditor software)
│  └─ File size: 45 MB, uploaded to secure cloud folder
│
├─ IT provides system documentation:
│  ├─ Architecture diagram
│  ├─ Data flow documentation
│  ├─ User access logs (who accessed what, when)
│  ├─ Database backup logs (when backed up, verified)
│  ├─ Vendor SLA reports (Google Vision uptime, OpenAI reliability)
│  └─ Security audit results (no vulnerabilities found)
│
└─ Clara reviews initial data
   ├─ Spot check: 20 random decisions
   │  ├─ Verify AI reasoning was sound
   │  ├─ Check customer history was accurate
   │  ├─ Confirm decision matches policy
   │  └─ All 20 look good ✓
   │
   └─ Questions for deeper dive:
      ├─ "Why did document #5234 get approved? Customer had previous fraud."
      ├─ "Are false positive rates acceptable? (< 5% required)"
      └─ "Is system audit trail sufficient for SOX compliance?"

Thursday (Dec 5):
├─ Clara meets with Frank & Dev to discuss findings
├─ Discussion:
│  ├─ Clara: "Document #5234 - why approved?"
│  ├─ Frank: "That was an override. New payer, different pattern, I reviewed myself."
│  ├─ System log shows: Manual override, timestamp, Frank's signature
│  ├─ Clara: "Good, audit trail captured it" ✓
│  │
│  ├─ Clara: "False positive rate?"
│  ├─ Dev shows chart: 4.2% false positives (within 5% threshold)
│  ├─ Analysis: "Mostly old checks, low confidence. Analysts review anyway, so safe."
│  ├─ Clara: "Acceptable" ✓
│  │
│  └─ Clara: "SOX compliance?"
│     ├─ Dev shows: Every decision logged with reasoning
│     ├─ User authentication logged
│     ├─ Changes create audit trail
│     ├─ Nightly backups to offsite cloud
│     ├─ Access controls restrict to fraud team only
│     └─ Clara: "Meets SOX requirements" ✓

WEEK 2: DETAILED ANALYSIS

Monday-Tuesday (Dec 9-10):
├─ Clara analyzes fraud detection accuracy:
│  ├─ Load test data (predefined fraud/non-fraud checks)
│  ├─ Re-run through system in test mode
│  ├─ Compare results to expected outcomes:
│  │  ├─ Detection rate: 99.2% ✓ (exceeds 99% target)
│  │  ├─ False positive: 3.8% ✓ (below 5% threshold)
│  │  └─ Processing time: 1.9 sec avg ✓ (within 3 sec SLA)
│  │
│  └─ Conclusion: "System performing as promised"
│
├─ Clara analyzes policy compliance:
│  ├─ Policy: "All escalations must be reviewed within 24 hours"
│  │  ├─ Sample 50 escalations
│  │  ├─ 48 reviewed within 24 hours
│  │  ├─ 2 reviewed within 48 hours (holiday weekend, acceptable)
│  │  └─ Compliance: 100% ✓
│  │
│  ├─ Policy: "Repeat offenders (2+ frauds) must be rejected"
│  │  ├─ Find all customers with fraud_count ≥ 2
│  │  ├─ Check if subsequent checks were rejected
│  │  ├─ Result: 147/147 rejected automatically ✓
│  │  └─ Compliance: 100% ✓
│  │
│  └─ Policy: "KYC verification before processing new customers"
│     ├─ Check if new payers added to system
│     ├─ Verify their identity was confirmed
│     ├─ System design: Doesn't track KYC (separate process)
│     ├─ Manual verification done by compliance team
│     └─ Compliance: ✓ (working as designed)
│
└─ Wednesday (Dec 11):
   ├─ Clara creates audit report
   ├─ Sections:
   │  ├─ Executive Summary
   │  │  └─ "XFORIA DAD fraud detection system reviewed for Q4 2024.
   │     │   Findings: System operating in compliance with all policies.
   │     │   No material weaknesses identified."
   │  │
   │  ├─ System Description
   │  │  └─ Technical architecture, data flows, ML models used
   │  │
   │  ├─ Controls Testing
   │  │  ├─ Access controls: ✓ Only fraud team can access
   │  │  ├─ Change management: ✓ All updates logged
   │  │  ├─ Data integrity: ✓ Database backups verified
   │  │  └─ Disaster recovery: ✓ RTO 1 hour, RPO 4 hours
   │  │
   │  ├─ Effectiveness Testing
   │  │  ├─ Detection accuracy: 99.2% ✓
   │  │  ├─ Policy compliance: 100% ✓
   │  │  ├─ Performance: 1.9 sec avg ✓
   │  │  └─ Uptime: 99.8% ✓
   │  │
   │  ├─ Sample Transactions
   │  │  ├─ 20 approved transactions reviewed
   │  │  ├─ 20 escalated transactions reviewed
   │  │  ├─ 20 rejected transactions reviewed
   │  │  └─ All decisions appeared sound with good reasoning
   │  │
   │  ├─ Risk Assessment
   │  │  ├─ Residual risk: LOW
   │  │  ├─ Mitigation: System controls adequate
   │  │  └─ Recommend: Continue quarterly reviews
   │  │
   │  └─ Conclusion
   │     └─ "No audit findings. System approved for continued use."
   │
   └─ File: /reports/Q4_2024_XFORIA_Audit_Report.pdf (32 pages)

WEEK 3-4: REPORTING

Thursday (Dec 12):
├─ Clara presents findings to Rita (CRO)
├─ Discussion:
│  ├─ Rita: "Any issues we need to address?"
│  ├─ Clara: "No, all systems in order"
│  ├─ Rita: "Great, can we expand to paystubs?"
│  ├─ Clara: "Yes, with same audit scope"
│  └─ Rita: "Set it up for Q1 2025"
│
└─ Clara submits report to external auditors
   ├─ Email: "Q4 2024 Fraud Detection Audit Report"
   ├─ Attachment: Full 32-page report with schedules
   ├─ Summary: "System controls operating effectively"
   └─ Auditor response: "Report accepted, no follow-up questions"
```

---

### **Workflow 5: Andy's System Administration (Ongoing)**

```
SETUP PHASE (Week 1)

Day 1: Initial Deployment
├─ Andy receives deployment plan from vendor
├─ Requirements checklist:
│  ├─ Server: 4 CPU, 8GB RAM minimum
│  ├─ Database: PostgreSQL 13+, 50GB storage
│  ├─ Internet: 100 Mbps connection
│  ├─ Firewall: Port 5001 (backend), 3002 (frontend)
│  ├─ DNS: frontend.bank.com, api.bank.com
│  └─ SSL: TLS 1.2+ required
│
├─ Andy provisions AWS infrastructure:
│  ├─ EC2 instance (t3.medium): $50/month
│  ├─ RDS PostgreSQL: $100/month (managed DB)
│  ├─ S3 storage: $10/month
│  ├─ CloudFront CDN: $20/month
│  └─ Total: ~$180/month infrastructure cost
│
├─ Andy installs software:
│  ├─ Linux: Ubuntu 22.04 LTS
│  ├─ Python: 3.13
│  ├─ Node.js: 18.x
│  ├─ Docker: Latest (for containerization)
│  ├─ Nginx: Reverse proxy
│  └─ Certbot: Automatic SSL renewal
│
└─ Day 2: Configuration
   ├─ Andy sets environment variables:
   │  ├─ SUPABASE_URL
   │  ├─ OPENAI_API_KEY
   │  ├─ GOOGLE_APPLICATION_CREDENTIALS
   │  ├─ DATABASE_URL
   │  └─ FLASK_SECRET_KEY
   │
   ├─ Secrets stored in:
   │  ├─ AWS Secrets Manager (recommended)
   │  ├─ NOT in .env file in git
   │  ├─ NOT in code comments
   │  └─ Only accessible to authorized team members
   │
   ├─ Configures database:
   │  ├─ Create tables from migrations
   │  ├─ Set up backups (daily, 30-day retention)
   │  ├─ Enable replication (for disaster recovery)
   │  └─ Test restore from backup
   │
   └─ Tests connectivity:
      ├─ Flask backend responds to API calls
      ├─ React frontend loads in browser
      ├─ Database connections successful
      ├─ External APIs (Google Vision, OpenAI) work
      └─ All green ✓

DAY-TO-DAY OPERATIONS

Daily (5 minutes):
├─ Andy checks monitoring dashboard
├─ Key metrics reviewed:
│  ├─ System uptime (target: 99.9%)
│  ├─ Error rate (alert if > 1%)
│  ├─ Response time (alert if > 5 seconds avg)
│  ├─ Database disk usage (alert if > 80%)
│  ├─ API rate limit consumption (should be < 70%)
│  └─ Alert summary (any new issues?)
│
├─ If issues detected:
│  ├─ Check logs for error patterns
│  ├─ Restart service if hung
│  ├─ Notify Dev team if persistent
│  └─ Document incident
│
└─ Log summary in ops notebook

Weekly (30 minutes):
├─ Review system performance:
│  ├─ Uptime: 99.92% ✓
│  ├─ Error rate: 0.3% ✓
│  ├─ Avg response time: 1.8 sec ✓
│  ├─ Database size growth: +2GB (healthy)
│  └─ Cost tracking: $180/month (within budget)
│
├─ Check backups:
│  ├─ Verify last backup completed (should be < 24h old)
│  ├─ Test restore from backup (once/week)
│  ├─ Check backup storage (AWS S3 redundant ✓)
│  └─ Document any issues
│
└─ Security updates:
   ├─ Check for OS patches (apply within 7 days)
   ├─ Check for dependency updates (Python, Node packages)
   ├─ Apply critical security patches immediately
   └─ Test in staging before production

Monthly (1-2 hours):
├─ Capacity planning:
│  ├─ CPU usage: currently 20% peak (plenty of headroom)
│  ├─ Memory: currently 45% peak
│  ├─ Disk: currently 35% used
│  ├─ Projection: At current growth (20%/month), may need upgrade in 6 months
│  └─ Recommendation: Monitor monthly, upgrade before hitting 70%
│
├─ Cost optimization:
│  ├─ Compare Reserved Instance pricing (save 30-40%)
│  ├─ Rightsize instances based on actual usage
│  ├─ Review CloudFront usage (can be expensive)
│  └─ Negotiate volume pricing with AWS
│
├─ Disaster recovery drill:
│  ├─ Simulate database loss
│  ├─ Restore from backup
│  ├─ Measure RTO (recovery time): Target 1 hour
│  ├─ Measure RPO (data loss): Target < 4 hours of data
│  ├─ Document: "Backup from 3-Dec, restored to 3-Dec 10am, success ✓"
│  └─ Improve procedures if needed
│
└─ Team meeting:
   ├─ Discuss system health with Dev and Ops teams
   ├─ Planned maintenance windows
   ├─ Infrastructure upgrades
   └─ Budget review

ISSUE RESOLUTION (Ad-hoc)

Scenario 1: System Performance Degradation
├─ Alert: "API response time > 5 seconds"
├─ Andy investigates:
│  ├─ Check recent deployments (anything new?)
│  ├─ Check database slow query log
│  ├─ Check resource utilization (CPU, memory, disk I/O)
│  ├─ Check network bandwidth
│  └─ Check if external APIs are slow (Google Vision, OpenAI)
│
├─ In this case:
│  ├─ Found: Database queries scanning entire checks table
│  ├─ Cause: Missing index on check creation timestamp
│  ├─ Fix: CREATE INDEX idx_checks_created_at
│  ├─ Result: Response time drops to 1.8 sec
│  └─ Notify Dev team: "Update migration script with this index"
│
└─ Document in incident log

Scenario 2: Database Disk Filling Up
├─ Alert: "Database 85% full"
├─ Andy investigates:
│  ├─ Query disk usage by table
│  ├─ Found: check_documents table is 45GB (old images)
│  ├─ Policy: Keep documents only 6 months
│  ├─ Solution: Delete docs older than 6 months (archive to S3)
│  └─ Freed: 20GB
│
├─ Prevent recurring:
│  ├─ Set up automated archive job
│  ├─ Runs monthly, moves old docs to S3
│  ├─ Keeps database lean
│  └─ Saves ~$50/month on database storage
│
└─ Update wiki: Document retention policy

Scenario 3: External API Outage (Google Vision Down)
├─ Alert: "Google Vision API returning 503 errors"
├─ Andy checks:
│  ├─ Google Cloud status page: Yes, US region outage, ETA 1 hour
│  │  └─ Not our issue, but impacts our users
│  │
│  ├─ System behavior: Automatically falls back to Tesseract OCR
│  │  └─ Slower (5-10 sec vs 2 sec) but works
│  │
│  ├─ User experience: Users see warning "Using fallback OCR, slower processing"
│  │
│  └─ Action:
│     ├─ Notify Frank: "Use system during outage, will be slower"
│     ├─ Monitor recovery
│     ├─ Once Google Vision back: System auto-switches back
│     └─ No manual intervention needed
│
├─ Post-incident:
│  ├─ Discuss with team: "How can we reduce dependency on Google Vision?"
│  ├─ Decision: Invest in Tesseract optimization (less reliance on cloud)
│  └─ Document incident: "Google Vision US outage, 1 hour, fallback worked"
│
└─ Update wiki: Incident response procedures

USER SUPPORT

When Frank has an issue:
├─ Frank: "I keep getting '500 error' when uploading checks"
├─ Andy investigates:
│  ├─ Check application logs: "File too large: 45MB"
│  ├─ Check system policy: Max upload 10MB
│  │
│  ├─ Solution options:
│  │  ├─ Option A: Increase limit (if server can handle)
│  │  ├─ Option B: Compress images before upload
│  │  ├─ Option C: Upload via backend API directly (advanced)
│  │  └─ Chosen: Option B (user responsibility)
│  │
│  ├─ Andy helps Frank:
│  │  ├─ "Compress PDFs to < 5MB using Acrobat or online tool"
│  │  ├─ Provides link: https://www.ilovepdf.com/compress_pdf
│  │  └─ "Try again, should work now"
│  │
│  └─ Follow-up:
│     ├─ Frank confirms: "Works now!"
│     ├─ Andy documents: Add to FAQ section of wiki
│     └─ Consider UI improvement: Show file size warning before upload

SECURITY & COMPLIANCE

Monthly Security Review:
├─ Andy reviews access logs:
│  ├─ Who accessed which systems?
│  ├─ Any suspicious access patterns?
│  ├─ All access for legitimate business purposes?
│  └─ Disable any unused accounts
│
├─ Andy checks firewall rules:
│  ├─ Backend API (port 5001): Only from office IPs + VPN ✓
│  ├─ Database (port 5432): Only from backend server ✓
│  ├─ Frontend (port 3002): Public (internal users) ✓
│  └─ SSH (port 22): Only from bastion host + key auth ✓
│
├─ Andy verifies SSL certificates:
│  ├─ Certificates expiration: Check in 30 days ✓
│  ├─ Renewal: Automatic via Certbot ✓
│  └─ Supported TLS versions: 1.2+ ✓ (no deprecated TLS 1.0)
│
└─ Quarterly vulnerability scan:
   ├─ Run automated security scanner (Nessus, Qualys)
   ├─ Fix any identified vulnerabilities
   ├─ Document remediation
   └─ Provide report to security team

DOCUMENTATION

Andy maintains:
├─ Runbook: Step-by-step procedures for common tasks
│  ├─ How to deploy new version
│  ├─ How to restore from backup
│  ├─ How to scale for high volume
│  ├─ How to debug common issues
│  └─ How to escalate to vendor
│
├─ On-call guide: For overnight/weekend support
│  ├─ Escalation procedures
│  ├─ Emergency contact numbers
│  ├─ Critical system status checks
│  └─ Common quick fixes
│
└─ Architecture diagram: Showing all infrastructure
   ├─ Updated after any infrastructure change
   ├─ Shared with team
   └─ Used for onboarding new team members
```

---

## User Journey Summary

### **Timeframe Summary**

| User | Daily Time | Weekly Time | Monthly Time | Key Emotion |
|------|-----------|------------|-------------|------------|
| **Frank** (Analyst) | 1-2 hrs processing | Report writing (30m) | Review patterns | Satisfied - much faster workflow |
| **Rita** (CRO) | Dashboard check (10m) | Report review (1h) | Strategic planning (2h) | Confident - has metrics for board |
| **Dev** (Engineer) | Monitoring (10m) | Performance review (30m) | Roadmap planning (2h) | Proud - stable system in production |
| **Clara** (Compliance) | Ad-hoc as needed | Spot checks (30m) | Detailed audit (8h/quarter) | Assured - audit trail is solid |
| **Andy** (Admin) | Health checks (5m) | Capacity review (30m) | Planning (2h) | Calm - system runs smoothly |

---

## Key Insights from User Workflows

1. **Frank's Productivity**: 60% time savings (manual 3+ hours → XFORIA 45 minutes for 50 documents)

2. **Rita's ROI Visibility**: Clear metrics demonstrating 13.7x return within first month

3. **Dev's Integration**: 4-week end-to-end timeline from API review to production deployment

4. **Clara's Compliance**: Comprehensive audit trail for regulatory requirements

5. **Andy's Operations**: Minimal daily overhead with clear escalation procedures

---

## Next Steps

1. **User Training**: Develop role-specific training materials
2. **Onboarding Process**: Create standardized customer onboarding
3. **Support Tiers**: Define support response times for each user level
4. **Feedback Loops**: Regular check-ins with each persona to improve workflows
