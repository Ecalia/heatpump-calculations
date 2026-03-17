
# PART 1: TIMELESS COMPANY CONTEXT

## Company Overview: Ecalia GmbH

### Core Business & Technology
Ecalia GmbH is a German deep-tech startup developing innovative compressor-expander systems for refrigerant technology. The company's core innovation addresses a fundamental limitation in the refrigeration industry: expander technology has not been commercially viable at scales below a few kilowatts due to technical challenges with two-phase regime expansion. Traditional turbo expanders struggle with liquid presence and two-phase changes, limiting applications primarily to supercritical CO2 systems, which have their own disadvantages.

Ecalia's approach uses scroll compressor-expander technology coupled on a single shaft, combined with proprietary material science innovations and advanced control mechanisms. This technology can handle the challenges of two-phase regime expansion with conventional refrigerants, opening applications in smaller-scale systems. The company's systems aim to approximate a Carnot process more closely than traditional refrigeration systems, offering significant efficiency improvements. The specific material science innovations remain confidential at this stage.

The technology represents a breakthrough in making expander-based refrigeration economically and technically feasible for applications under a few kilowatts, potentially revolutionizing residential and small commercial refrigeration and heat pump systems.

### Industry & Market Position
Ecalia operates in the refrigeration and heat pump technology sector, specifically in the advanced R&D space bridging academic research and industrial application. The company has been recognized as one of the top 10 most innovative tech startups in Germany by the Economy Award (jointly awarded by Technical University Munich, Handelsblatt, and Wissensfabrik), indicating strong validation of their technological approach within the German innovation ecosystem.

The target market includes residential heat pump applications, commercial refrigeration systems, and potentially specialized industrial cooling applications (such as laser cooling for companies like Trumpf). The company is navigating challenges typical of deep-tech startups: long development cycles, high technical risk, and the need to educate a conservative industrial market about novel technology.

### Company Structure & Location
Ecalia is hosted at the Institute for Plastics Technology (IKT) at the University of Stuttgart, where they maintain office space and workshop facilities. This institutional relationship provides access to research infrastructure, expertise, and legitimacy while the company develops its technology.

The company operates with a flat organizational structure typical of early-stage startups:
- **Leadership Team:** CEO/CTO and COO (co-founders) who share strategic decision-making
- **Technical Team:** Mechanical engineer focused on prototyping and manufacturing
- **Extended Team:** Part-time CNC machinist (mini-jobber), occasional specialist contractors
- **Advisory Network:** Extensive informal network of advisors across startup and industrial sectors, formal agile coach for operational development

### Company Culture & Values
Ecalia's culture reflects its founding team's technical depth and pragmatic approach:

**Innovation-Driven:** The company balances cutting-edge technical development with practical engineering and business realities. There's strong emphasis on finding novel solutions while maintaining focus on commercial viability.

**Efficiency & Resourcefulness:** With limited runway, the team is mindful of spending while avoiding false economy. The philosophy is to spend money when it saves time and advances critical goals, not to over-save at the cost of progress.

**Automation & AI-First:** Unusual for a hardware startup, Ecalia has deeply integrated AI tools into operations, building custom prompts, workflows, and automation to multiply the small team's effectiveness. This represents both a cultural value and a potential secondary business opportunity.

**Quality & Continuous Improvement:** High standards for technical work, documentation, and systematic processes, balanced with understanding that quality is built through training, systems, and leadership rather than demands.

**Collaborative Decision-Making:** Important decisions are made jointly by co-founders, with clear delegation of operational authority. The culture values autonomy within defined boundaries (€1,000 for necessary expenditures, €100 for optional ones without approval).

**Learning Organization:** Active investment in developing team capabilities through coaching (agile coach), systems (prompts and workflows), and leadership development. Recognition that building a mature organization requires intentional skill development.

### Technical Infrastructure & Capabilities

**Workshop & Manufacturing:**
- CNC machine with regular operator support
- Professional 3D printer for rapid prototyping
- Comprehensive workshop tools for mechanical assembly
- Refrigerant system tools and testing equipment
- Copper pipe soldering and brazing capabilities
- Microgram scale for precise material measurement

**Electronics & Control Systems:**
- Electronics workshop access at IKT
- PCB design and prototyping capabilities
- Electrical cabinet design and assembly
- Custom C++ framework for research machine control
- Microcontroller programming infrastructure

**Research Equipment:**
- Material test rig (for testing self-lubricating material combinations under realistic conditions)
- Carnot test rig (for measuring compressor-expander system performance with propane refrigerant)
- Instrumentation for measuring: isentropic efficiency, mass flow, density, pressures at multiple points, temperatures

**Software & AI Infrastructure:**
Extensive custom-built AI workflow system including:
- Prompt library stored in Confluence for various engineering tasks
- Meta-prompt for prompt engineering
- Specialized prompts for: risk management documentation, explosion safety concepts, engineering module documentation, PCB planning, electrical cabinet design, grant applications
- Automation platform using make.com and n8n
- Vision for unified AI agent system that routes tasks to specialized assistants with full context integration to Confluence and Jira

### Core Technical Domains

**Physics & Thermodynamics:**
- Carnot cycle and thermodynamic processes
- Isentropic efficiency and compression/expansion processes
- Two-phase vs. supercritical refrigerant behavior
- Heat pump performance modeling and simulation

**Refrigeration Technology:**
- Scroll compressor and scroll expander mechanics
- Refrigerant systems (particularly propane, but also CO2 and synthetic refrigerants)
- Refrigerant safety and explosion safety protocols
- System performance testing and validation

**Materials Science:**
- Self-lubricating materials (particularly polyoxymethylene/POM)
- Material testing under pressure, temperature, and friction conditions
- Injection molding processes
- Material compatibility with refrigerants

**Mechanical Engineering:**
- Precision machining and manufacturing
- CAD design and engineering simulation
- Prototype development and iterative design
- Workshop processes and quality control

**Electronics & Control:**
- Embedded systems and microcontroller programming
- Sensor integration and data acquisition
- Control algorithms for compressor-expander systems
- PCB design and power electronics

**Software & Automation:**
- C++ for embedded control systems
- Python for simulation and data analysis
- AI prompt engineering and workflow automation
- Version control and collaborative development

---

# PART 2: TEMPORAL CONTEXT (Updated as of Q1 2026)

## Current Company Stage

**Incorporation & Funding Status:**
Ecalia incorporated approximately three months ago (Q4 2024), following ~2 years of pre-incorporation development. The company is currently in the research and validation phase, transitioning from scholarship-funded academic research toward commercial development.

**Current Funding:**
- €160,000 convertible loan from Landesbank Baden-Württemberg
- €40,000 investment from TTI (Technologie Transfer Initiative Stuttgart)
- Total runway: 12-18 months
- Potential: Funding amount doubles upon achievement of technical milestones
- Reporting: Quarterly progress reports to investors

**Development Timeline:**
- 2023: Project initiated, applied for EXIST scholarship
- 2023-2024: EXIST scholarship period (first co-founder left first week, operated primarily solo with high team churn due to low scholarship compensation)
- Mid-2024: Valentin joined as co-founder and COO (~18 months into project)
- 2024: EXIST follow-up funding, built Carnot test rig
- Late 2024: Incorporated, received convertible loan and TTI investment
- Current: Completing material test rig, preparing for system validation testing

## Current Team Composition

**Michael Ilewicz - CEO, CTO, Co-founder**
Handles: Technology strategy, AI/software development, machine design, control systems, refrigerant systems, technical decision-making, team development and training, strategic business decisions, grant application development (20-30% contribution)

**Valentin - COO, Co-founder**
Handles: Operations, bookkeeping, administrative tasks (insurance, contracts, salaries), plastics technology expertise, supplier relationships for plastics, investor communications, fundraising applications (primary owner ~70-80%), team administrative management
Background: Master's in Plastics Technology, joined ~18 months into project

**Simon - Mechanical Engineer**
Handles: Prototyping, mechanical design execution, workshop tasks, manufacturing
Challenge areas: File management discipline, workshop organization, systematic workflows
Working style: Creative, impulse-driven

**CNC Machinist - Part-time Contractor (Mini-jobber)**
Weekly support for machining operations

**Agile Coach - Consultant**
Kickoff scheduled in approximately 2 weeks to establish agile working structure and Jira workflows

**Team Expansion:** Actively planning next hire(s), prioritizing candidates who can increase operational capacity

## Active Projects & Immediate Priorities

### Priority 1: Test Rig Completion & Validation (Highest Priority)
**Material Test Rig:**
- Status: Final assembly scheduled in 1 week
- Next steps: Complete C++ control framework, sensor integration debugging, system-level testing
- Purpose: Test material combinations under realistic pressure, temperature, and friction conditions

**Carnot Test Rig:**
- Status: Hardware complete, needs benchmarking
- Next steps: Benchmark with classical compressor, then test compressor-expander prototypes
- Safety requirement: Complete explosion safety testing for propane system
- Purpose: Validate system performance, measure isentropic efficiency and other key metrics

**Timeline Goal:** Both rigs fully operational with initial test results within 6 months
**Milestone Significance:** Test results validating material suitability trigger doubling of funding

### Priority 2: Runway Extension & Business Development
**Current Focus:**
- Exploring AI workflow SaaS offering (risk assessments, engineering documentation) as secondary revenue stream
- Pursuing grant applications, particularly one high-potential independent grant
- Seeking pilot project partner for winter testing in real residential application
- Partnership exploration (e.g., Trumpf for laser cooling applications)

**Challenge:** Industrial market has high barriers, companies struggling economically, may require strategy adjustment

### Priority 3: Team & Operational Excellence
**Immediate Goals:**
- Implement agile workflow structure (kickoff in 2 weeks)
- Improve project planning and task management in Jira
- Develop quality systems and training for team members
- Hire additional team member(s)
- Improve team efficiency and systematic workflows

### Other Active Projects
- Workshop modernization and reorganization (moving to different area within IKT soon)
- Bookkeeping finalization post-incorporation
- Safety certifications (first aid designation, risk management certifications)
- CRM implementation (HubSpot or Odoo equivalent) - lower priority but needed
- Toggl API integration for Forschungszulage (R&D grant) time tracking compliance
- Material probe specification and procurement planning
- Patent application preparation (target: summer 2025)

## Key External Relationships

**Primary Institutional Partners:**
- **Institute for Plastics Technology (IKT), University of Stuttgart:** Host institution, provides facilities and research collaboration
- **TTS (Technologie Transfer Stuttgart):** Investor and strategic partner, supporting university startup commercialization
- **Landesbank Baden-Württemberg:** Primary lender (convertible loan)

**Active Partnerships & Collaborations:**
- **TechSolute:** Technology partner, designed material test rig, provides occasional engineering support
- **University of Bochum:** Collaborating on cavitation experiments
- **Institute for Climate, Refrigeration & Environment, Karlsruhe:** Refrigerant compressor specialist professor, potential joint grant applications and projects (relationship building, waiting for material test rig completion before deeper engagement)
- **Trumpf:** Scheduled meeting to discuss laser cooling applications

**Accelerator & Support Programs:**
- **Weeconomy Grant:** Significant ongoing support and networking
- **Smart Green Accelerator:** Some connection and support
- **Economy Award Network:** Access to professionals from high-performance companies across Germany through recognition program

**Network:** Dozens of additional contacts across startup and industrial sectors for ad-hoc advice and potential partnerships. Political network is underdeveloped relative to startup/industry connections.

**CRM Need:** Relationship tracking is currently informal; implementing AI-supported CRM with email integration is an open priority project.

## Current Tools & Technology Stack

**AI & Automation:**
- Primary: Gemini (most used)
- Also: ChatGPT, Claude
- Gemini AI Builder for custom applications (inventory manager, CNC parameter optimizer - both WIP)
- Automation: make.com (ordering, invoicing), n8n (workflow automation)

**Engineering & Design:**
- CAD: Autodesk (including Nastran for simulations)
- PCB Design: Flux.ai
- Drawing/Sketching: Draw.io
- Microcontroller Development: Platform.io
- Custom C++ framework for machine control

**Simulation & Analysis:**
- Python with CoolProp for heat pump performance simulation
- Previous CFD work (employee who did this no longer with company)

**Project Management & Documentation:**
- Project Management: Jira (being restructured with agile coach)
- Documentation: Confluence (also stores prompt library)
- Version Control: GitHub (code and CAD files)
- Time Tracking: Toggl (important for Forschungszulage compliance)

**Communication & Collaboration:**
- Team Communication: Microsoft Teams
- File Sharing: OneDrive/SharePoint
- Email: Outlook

**Business Operations:**
- Bookkeeping/ERP: Odoo
- Website: WordPress (self-hosted on virtual machine)
- Cloud Infrastructure: Azure (PDF analysis endpoints, VM hosting)

## Success Metrics for Next 6 Months

**Technical Validation:**
- Both test rigs fully operational
- Initial test results demonstrating material suitability
- Benchmark data from Carnot test rig with classical compressor
- Prototype testing begun on compressor-expander system

**Financial Sustainability:**
- Runway extended beyond 18 months through grants or secondary revenue
- Milestone achievement triggering funding doubling
- Ideally: High-potential independent grant secured

**Organizational Maturity:**
- Team expanded (at least one additional hire)
- Agile workflows implemented and functioning
- Quality systems and training improving team efficiency
- Time tracking compliant with Forschungszulage requirements

**Market Development:**
- Pilot project partner identified for winter testing
- Progress on strategic partnerships (e.g., Trumpf, Karlsruhe institute)
- Decision made on AI workflow SaaS viability

**Stretch Goal:**
- Patent application submitted (summer target)
- Pilot project launched by winter in real residential application

---