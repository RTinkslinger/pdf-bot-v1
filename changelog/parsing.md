# Changelog: parsing

## Summary
Add AI summarization feature to topdf - enabling optional LLM-powered company overview generation after PDF conversion.

---

## Iteration 1: Created Summarization Spec

**Objective:** Define the complete specification for the AI summarization feature

**Files Modified:**
- `spec/summarisation_spec.md` (new file)

### Changes Made:
1. Created comprehensive specification for PDF summarization feature
2. Defined architecture and data flow for OCR + LLM pipeline
3. Specified config.py module for API key management
4. Specified summarizer.py module for OCR text extraction and LLM calls
5. Defined user interface flow with interactive prompts
6. Documented API key lookup order (config file → ENV → prompt)
7. Specified error handling and graceful degradation

### Test Results:
- Specification reviewed and approved

---

## Iteration 2: Updated Main Spec Files

**Objective:** Integrate summarization feature into the four main spec files

**Files Modified:**
- `spec/requirements.md`
- `spec/architecture.md`
- `spec/SPEC.md`
- `spec/test-plan.md`

### Changes Made:

#### requirements.md:
1. Added FR-5: AI Summarization (6 requirements)
2. Added FR-6: API Key Management (7 requirements)
3. Updated NFR-1: Privacy & Security to include LLM opt-in
4. Added optional dependencies section (anthropic, openai)
5. Updated glossary with LLM, API Key, Summarization terms

#### architecture.md:
1. Updated high-level architecture diagram with Summarizer and Config components
2. Added component responsibilities for Summarizer and Config
3. Added Section 3.8: Config Module specification
4. Added Section 3.9: Summarizer Module specification
5. Added Section 4.1: Summarization Data Flow diagram
6. Updated exception hierarchy with SummaryError and OCRError
7. Added API Key Security section

#### SPEC.md:
1. Added FR-5 and FR-6 requirements to Section 1
2. Updated NFR-1 for privacy with LLM opt-in
3. Updated architecture diagram with Summarizer and Config
4. Updated directory structure with new files
5. Added optional dependencies section
6. Added Phase 8: AI Summarization with 10 tasks and exit criteria
7. Added config.py and summarizer.py tests to Section 7.2
8. Added summarization integration tests to Section 7.3
9. Added E2E-11 through E2E-18 for summarization testing
10. Updated summary to reflect 8 phases

#### test-plan.md:
1. Updated version to 1.1
2. Updated test pyramid (65-75 unit tests, 18 E2E tests)
3. Added CLI-010, CLI-011 for --check-key and --reset-key
4. Added Section 2.6: config.py Tests (CFG-001 to CFG-010)
5. Added Section 2.7: summarizer.py Tests (SUM-001 to SUM-014)
6. Added Section 3.3: Summarization Integration (SUM-INT-001 to SUM-INT-008)
7. Added E2E-11 through E2E-18 for summarization scenarios
8. Added new fixtures: mock_api_key, mock_llm_response, temp_config_dir
9. Added mock objects: MockAnthropicClient, MockOpenAIClient
10. Updated test schedule to include Phase 8

### Test Results:
- All spec files successfully updated
- Ready for Phase 8 implementation

---

## Iteration 3: Final Verification & Gap Fixes

**Objective:** Verify all summarisation_spec.md content is integrated and fix minor gaps

**Files Modified:**
- `spec/architecture.md`
- `spec/SPEC.md`

### Changes Made:

#### architecture.md:
1. Added Section 3.10: LLM Configuration
   - Supported Providers table (claude-3-haiku, gpt-4o-mini)
   - Prompt template structure
   - Summary content guidelines
2. Added Section 3.11: Summarization Error Handling
   - Error scenarios table with exceptions and user messages
   - Graceful degradation code example

#### SPEC.md:
1. Added Section 5.2.5: Converter Module Modifications
   - ConversionResult dataclass with screenshots field
2. Added Acceptance Criteria (Summarization Feature)
   - 12-item checklist for feature sign-off

### Verification Results:
- requirements.md: ✅ Complete
- test-plan.md: ✅ Complete
- architecture.md: ✅ Complete (after fixes)
- SPEC.md: ✅ Complete (after fixes)

### Test Results:
- All summarisation_spec.md content now integrated into main specs
- summarisation_spec.md can be removed if desired

---

## Iteration 4: Structured Summarization with Perplexity

**Objective:** Update specs for structured output format with Perplexity peer search

**Files Modified:**
- `spec/requirements.md`
- `spec/architecture.md`
- `spec/SPEC.md`
- `spec/test-plan.md`
- `CLAUDE.md`

### Changes Made:

#### requirements.md:
1. Updated FR-5 (AI Summarization) with structured output requirements:
   - FR-5.3: Generate structured company analysis (≤200 char description)
   - FR-5.4: Assign sector tags (primary + secondary)
   - FR-5.5: Identify early customer traction
   - FR-5.6: Find recently funded peers via Perplexity (up to 10)
2. Added FR-6.8: Manage both Anthropic and Perplexity API keys
3. Updated optional dependencies: anthropic (deck analysis), openai (Perplexity SDK)
4. Added glossary terms: Perplexity, Sector Tag, Funded Peers

#### architecture.md:
1. Updated Section 3.9 (Summarizer Module) with new data classes:
   - CompanyAnalysis, FundedPeer, StructuredSummary
2. Updated Section 3.10 (LLM Configuration):
   - Claude for deck analysis, Perplexity for peer search
   - Claude analysis prompt (JSON extraction)
   - Perplexity peer search query
   - Perplexity API setup code (OpenAI SDK with custom base_url)
   - Allowed sector tags list
3. Updated Section 3.11 (Error Handling):
   - Added Perplexity-specific error scenarios
   - Updated graceful degradation code
4. Updated Section 4.1 (Summarization Data Flow):
   - 6-step pipeline: User Prompt → API Keys → OCR → Claude → Perplexity → Markdown
   - Added output markdown format template
5. Updated config file format: anthropic_api_key + perplexity_api_key

#### SPEC.md:
1. Updated FR-5 with structured output requirements
2. Added FR-6.6: Manage both Anthropic and Perplexity API keys
3. Updated optional dependencies section with Perplexity note
4. Updated Phase 8 tasks for Perplexity integration
5. Updated acceptance criteria (15 items) including peer search

#### test-plan.md:
1. Updated test pyramid: 20 E2E tests (was 18)
2. Updated summarizer.py tests (SUM-001 to SUM-017):
   - Added Claude JSON parsing tests
   - Added Perplexity search tests
   - Added sector validation tests
3. Updated integration tests (SUM-INT-001 to SUM-INT-010):
   - Added Perplexity-specific integration tests
4. Updated E2E tests (E2E-11 to E2E-20):
   - Added Perplexity failure graceful degradation
   - Added structured output verification
5. Updated fixtures: mock_anthropic_key, mock_perplexity_key, mock_claude_response, mock_perplexity_response
6. Updated mock objects: MockAnthropicClient, MockPerplexityClient

#### CLAUDE.md:
1. Updated project overview with structured analysis + Perplexity
2. Updated conversion flow step 7 with OCR → Claude → Perplexity pipeline
3. Updated tech stack: anthropic (deck analysis), openai (Perplexity SDK)
4. Updated API keys note: Anthropic + Perplexity

### Architecture Decision:
- **Perplexity API** replaces Brave Search + Claude parsing
- Single API call does web search + AI synthesis
- Uses OpenAI SDK with custom base_url
- Graceful degradation: if Perplexity fails, summary generated without peers

### Test Results:
- All spec files updated with Perplexity-based architecture
- Ready for Phase 8 implementation

---

## Iteration 5: Single Provider Architecture (Perplexity Only)

**Objective:** Simplify to single Perplexity provider for both deck analysis and peer search

**Files Modified:**
- `spec/requirements.md`
- `spec/architecture.md`
- `spec/SPEC.md`
- `spec/test-plan.md`
- `CLAUDE.md`

### Changes Made:

#### requirements.md:
1. Updated FR-5.3: Generate structured analysis via Perplexity (single call)
2. Removed FR-5.9 (Claude-specific requirement)
3. Updated FR-6: Single Perplexity API key management (removed FR-6.8)
4. Updated optional dependencies: only `openai>=1.0.0`

#### architecture.md:
1. Updated Summarizer module interface: single `perplexity_key` parameter
2. Updated internal methods: `_call_perplexity`, `_parse_response`
3. Updated Section 3.10: Perplexity Configuration (single provider)
4. Added combined analysis + peer search prompt
5. Updated error handling: simplified for single provider
6. Updated data flow: 5 steps instead of 6

#### SPEC.md:
1. Updated FR-5 and FR-6 requirements
2. Updated Phase 8 tasks for single provider
3. Updated acceptance criteria (13 items instead of 15)
4. Updated optional dependencies section

#### test-plan.md:
1. Updated test pyramid: 18 E2E tests
2. Updated summarizer tests: removed Claude-specific tests
3. Updated integration tests: 7 tests instead of 10
4. Updated E2E tests: E2E-11 to E2E-18
5. Updated fixtures: single `mock_perplexity_response` with full structure
6. Updated mock objects: only `MockPerplexityClient`

#### CLAUDE.md:
1. Updated project overview: single Perplexity provider
2. Updated conversion flow: single API call
3. Updated tech stack: only `openai` for Perplexity
4. Updated API keys note: Perplexity only

### Architecture Decision:
- **Single Perplexity provider** replaces Claude + Perplexity dual setup
- One API key, one API call handles both analysis and peer search
- Simpler UX and architecture

### Test Results:
- All spec files updated with single provider architecture
- Ready for Phase 8 implementation

---
