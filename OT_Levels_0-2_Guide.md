# The OT World: Levels 0–2 — Complete Study Guide
### A Structured Deep-Dive into Industrial Operational Technology

---

## How to Use This Guide

This guide is structured as a **learning journey** — work through it top to bottom, or jump to any section. Each module ends with key takeaways and names to know. Estimated reading time: ~90 minutes for full pass.

**Reading order recommendation:**
1. Start with the Purdue Model (Section 1) — it's the map everything else hangs on
2. Work through Levels 0 → 1 → 2 in order
3. Then read History, Vendors, Protocols, and Trends
4. Use the Cheat Sheet at the end as a quick reference

---

## Section 1: The Map — Purdue Model / ISA-95

### What It Is

The **Purdue Enterprise Reference Architecture (PERA)** was developed by Theodore Williams at Purdue University in the early 1990s and formalised into the **ISA-95 standard** (ANSI/ISA-95, also IEC 62264). It divides industrial systems into hierarchical layers, each with a defined function and communication boundary.

Think of it as a **security and functional boundary model** — each level talks primarily to adjacent levels, not across the stack. This is *why* getting OT data to IT/cloud is non-trivial.

```
Level 5 │  Enterprise / Corporate IT         (ERP: SAP, Oracle)
Level 4 │  Site Business Planning / Logistics (MES, Historian aggregation)
─────────┼──────────────────────────────────────────────────────── DMZ / Level 3.5
Level 3  │  Site Operations / Manufacturing Ops (MES, LIMS, historians)
Level 2  │  Area Supervisory Control            (SCADA, DCS, HMI)    ◄── THIS GUIDE
Level 1  │  Basic Control                        (PLCs, RTUs, drives) ◄── THIS GUIDE
Level 0  │  Physical Process                     (sensors, actuators) ◄── THIS GUIDE
```

### Why This Matters Now

The industry is experiencing **convergence pressure**: cloud analytics platforms (Databricks, Azure, AWS) sit at Level 5, while the data is born at Level 0. Every byte of OT data must traverse 5 layers, each with its own protocols, vendors, and security posture. The Zerobus connector and similar tools are essentially **Level 3.5 translators**.

---

## Section 2: Level 0 — The Physical Process

### What Lives Here

Level 0 is the **physical world** — atoms, electrons, heat, pressure, flow, position. Nothing here is digital by nature; it only becomes data when a transducer converts it.

**Core function:** Sense and actuate the physical process.

### Sensors (Input Devices)

These convert physical phenomena into electrical signals.

| Sensor Type | Measures | Common Examples | Dominant Vendors |
|-------------|----------|-----------------|-----------------|
| **Temperature** | Process heat | RTD (PT100/PT1000), Thermocouple (Type K, J, T), Infrared | Endress+Hauser, Yokogawa, Emerson/Rosemount |
| **Pressure** | Absolute, gauge, differential | Capacitive, piezoelectric, strain gauge cells | Honeywell, Emerson/Rosemount, ABB, Siemens |
| **Flow** | Volumetric, mass flow | Coriolis, magnetic, ultrasonic, vortex, DP orifice | Emerson (Micromotion), Endress+Hauser, Yokogawa |
| **Level** | Tank/vessel fill | Radar (guided wave, free air), ultrasonic, float, DP | VEGA, Emerson, Siemens |
| **Vibration / Condition** | Machine health | Accelerometers, proximity probes | SKF, Bently Nevada (Baker Hughes), Fluke |
| **Analytical / Quality** | pH, conductivity, O₂, gas | Electrochemical, spectrographic | Mettler Toledo, Hach, ABB |
| **Position / Proximity** | Limit switches, encoder position | Inductive, capacitive, optical encoders | Pepperl+Fuchs, SICK, Balluff |

### Actuators (Output Devices)

These convert electrical signals back into physical action.

| Actuator Type | Does | Examples |
|--------------|------|---------|
| **Control Valves** | Throttle fluid flow | Globe, butterfly, ball valves with positioners |
| **On/Off Valves** | Binary open/shut | Solenoid valves |
| **Pumps / Compressors** | Move fluids/gases | Centrifugal, positive displacement |
| **Motors** | Mechanical motion | AC induction, servo, stepper |
| **Variable Speed Drives (VSD/VFD)** | Control motor speed | ABB, Danfoss, Siemens SINAMICS, Rockwell PowerFlex |
| **Relays / Contactors** | Switch high-power circuits | Schneider, Eaton, Siemens |
| **Heaters / Burners** | Add energy to process | Gas burners, electric heating elements |

### Signal Standards at Level 0

This is where the analog-to-digital boundary begins.

**4–20 mA (the workhorse of industry):**
- Born in the 1950s. Still the dominant sensor signal standard worldwide.
- 4 mA = 0% of range, 20 mA = 100% of range
- Current loop is inherently immune to voltage drop over long cable runs
- The "live zero" at 4 mA distinguishes a failed sensor (0 mA) from a real zero reading
- **HART** (Highway Addressable Remote Transducer) rides *on top* of 4–20 mA as a digital overlay at 1200 baud — two values for the price of one wire pair

**NAMUR sensors (IEC 60947-5-6):**
- Specifically designed for intrinsic safety in hazardous areas (Zone 0, 1, 2)
- 8 mA normal, <1 mA fault — feeds into intrinsically safe barriers

**0–10 V / 0–5 V:**
- Common in HVAC and building automation, less common in process

**Digital / Discrete:**
- Simple on/off: limit switches, proximity sensors, pushbuttons
- Feeds directly to PLC digital input cards

**Foundation Fieldbus / PROFIBUS PA:**
- Digital field protocols operating on the same 2-wire pair as power
- Enable multi-drop (multiple devices per cable), diagnostics, device parameter access
- Being superseded by **PROFINET**, **EtherNet/IP**, and increasingly Ethernet-APL

**Ethernet-APL (Advanced Physical Layer) — the future:**
- 2-wire Ethernet to the field device, intrinsically safe, 10 Mbit/s
- Ratified 2021–2022, rapidly adopted in new greenfield projects
- Eliminates the fieldbus translation layer entirely

### Big Names at Level 0

- **Emerson Electric** (Rosemount instruments, Fisher control valves, Micromotion Coriolis)
- **Endress+Hauser** — Swiss, family-owned, broad instrument portfolio
- **ABB** — Strong in analytical and flow
- **Yokogawa** — Japanese, strong in oil & gas
- **Siemens** — Broad coverage, especially in discrete manufacturing
- **Honeywell** — Strong in DCS-integrated instrumentation
- **VEGA** — Level measurement specialist
- **Pepperl+Fuchs** — Intrinsic safety barriers, discrete sensors
- **SICK** — Machine vision, safety sensors, lidar
- **SKF / Bently Nevada** — Condition monitoring and vibration

---

## Section 3: Level 1 — Basic Control

### What Lives Here

Level 1 is where **decisions happen in real time**. Sensors from Level 0 feed in, logic executes (often in milliseconds), and commands go back to actuators. This is the domain of **PLCs**, **RTUs**, **PACs**, and **drives**.

**Core function:** Execute control logic, respond to process conditions, enforce safety limits.

### Programmable Logic Controllers (PLCs)

**History:**
- Invented in 1968 by Dick Morley at Bedford Associates, commissioned by General Motors to replace hardwired relay panels in automotive assembly
- The first commercial PLC was the **Modicon 084** (MODular DIgital CONtroller — the origin of the Modicon brand)
- 1970s: Rapid adoption in automotive and manufacturing
- 1980s: IEC standardised PLC programming languages in **IEC 61131-3** (1993)
- 1990s: PLCs got serial comms (Modbus, Profibus), memory expanded, CPUs got faster
- 2000s: Ethernet connectivity, web servers built in
- 2010s: Soft PLCs, edge computing, OPC-UA integration
- 2020s: PLCs with direct cloud connectors, MQTT built in, cybersecurity hardening

**IEC 61131-3 Programming Languages (the universal PLC standard):**

| Language | Type | Use Case | Looks Like |
|----------|------|----------|------------|
| **LD (Ladder Diagram)** | Graphical | Discrete logic, relay replacement | Railroad tracks with contacts and coils |
| **FBD (Function Block Diagram)** | Graphical | Analog control, PID loops | Boxes connected by signal lines |
| **ST (Structured Text)** | Textual | Complex algorithms, maths | Pascal / C-like high-level language |
| **IL (Instruction List)** | Textual | Low-level, legacy | Assembly language |
| **SFC (Sequential Function Chart)** | Graphical | Batch sequences, state machines | Flowchart with steps and transitions |

Modern IDEs (TIA Portal, Studio 5000) allow mixing all five in one project.

**The Big PLC Vendors:**

| Vendor | Platform | Stronghold |
|--------|---------|-----------|
| **Siemens** | S7-1200, S7-1500, S7-300/400 (legacy), TIA Portal IDE | Automotive, food & bev, water, Europe generally |
| **Rockwell Automation** | Allen-Bradley: ControlLogix, CompactLogix, Micro820 — Studio 5000 IDE | Americas, automotive, oil & gas |
| **Schneider Electric** | Modicon M340, M580, Momentum — EcoStruxure | Water/wastewater, energy, Europe |
| **Mitsubishi Electric** | MELSEC iQ-R, iQ-F — GX Works | Asia-Pacific, automotive |
| **Omron** | NX/NJ series — Sysmac Studio | Asia-Pacific, machine builders |
| **Beckhoff** | EtherCAT-based, TwinCAT (soft PLC on Windows) | High-speed motion, OEMs, machine builders |
| **ABB** | AC500, Symphony Plus | Process industries, power utilities |
| **B&R (ABB)** | X20 series | Packaging, motion, OEM |
| **Honeywell** | ControlEdge, Safety Manager | Process industries, safety |
| **WAGO** | 750 series | Building automation, small systems |

**Market share 2024 (approx):** Siemens ~25%, Rockwell ~20%, Schneider ~12%, Mitsubishi ~10%, Omron ~8%, others split remainder.

### Remote Terminal Units (RTUs)

RTUs are PLCs built for **remote, unattended, low-power, wide-area deployment** — the field cabinet at a remote pumping station 50km from the control room.

Key differences vs PLCs:
- Designed for low power draw (battery + solar operation)
- Wide-temperature operation (−40°C to +70°C)
- Wide-area communications built in: radio, cellular 4G/5G, satellite
- Longer scan times acceptable (seconds vs milliseconds)
- Historically SCADA-focused, speaking DNP3 or IEC 60870-5-101/104

**Key RTU vendors:** ABB (TeleUCA), Schneider (Quindar, SCADAPack), GE Grid Solutions, Yokogawa, Emerson (FloBoss for oil & gas flow measurement)

**DNP3 (Distributed Network Protocol 3):**
- Born in the 1990s for electric utility SCADA
- Designed for unreliable serial links: message integrity, timestamps, unsolicited reporting
- Dominant in power distribution, water utilities in North America and Australia
- Competitor IEC 60870-5-101 (serial) / IEC 60870-5-104 (TCP/IP) dominates Europe and Asia

### Programmable Automation Controllers (PACs)

The term "PAC" was coined by ARC Advisory Group in 2001 to describe devices that blur the PLC/DCS line — higher computing power, multi-domain control (discrete + process + motion in one unit), PC-based architecture.

Examples: Rockwell ControlLogix, GE RX3i, National Instruments CompactRIO

### Safety Instrumented Systems (SIS) / Safety PLCs

Separate from basic control — **functionally isolated** by IEC 61511 / IEC 61508.

**Key concept: Safety Integrity Level (SIL)**
- SIL 1 = 10% → 1% probability of failure on demand per year
- SIL 2 = 1% → 0.1%
- SIL 3 = 0.1% → 0.01%
- SIL 4 = theoretical maximum, near impossible to achieve in practice

**Architecture:** Redundant sensors → voting logic (2oo3 = 2-out-of-3) → safety PLC → final element (e.g. trip valve)

**Safety PLC vendors:** Rockwell (GuardLogix), Siemens (F-CPU S7-1500F), Pilz (PNOZmulti), Hima, Triconex (Schneider)

**Why this matters for data:** Safety data is highly sensitive — regulators require it to remain functionally independent. Historians typically read SIS data in read-only mode. Never write to SIS from a data pipeline.

### Variable Speed Drives (VSD / VFD / Inverters)

Control the speed of electric motors by varying supply frequency. Enormous energy savings — the dominant single point of electromechanical control in modern industry.

**Key vendors:** ABB (ACS series — largest drive market share globally), Danfoss (VLT series), Siemens (SINAMICS), Rockwell (PowerFlex), Schneider (Altivar), Yaskawa, WEG

**Why they matter for data:** VSDs produce rich process data — speed, torque, energy consumption, fault codes, harmonic distortion. Modern drives speak PROFINET, EtherNet/IP, Modbus TCP natively — prime candidates for Zerobus connectivity.

### Level 1 Protocols (Field Bus Layer)

**PROFIBUS DP (Decentralised Periphery):**
- Launched 1989 by Siemens et al., became IEC 61158 standard
- RS-485 physical layer, up to 12 Mbit/s, deterministic (cycle times ~1ms)
- Master-slave: one PLC master polls up to 126 slaves
- Still the most widely installed fieldbus globally — hundreds of millions of devices
- Being replaced by PROFINET in new installations

**DeviceNet:**
- CAN-based, launched by Allen-Bradley 1994
- Dominant in North American discrete manufacturing
- Being replaced by EtherNet/IP

**CANopen:**
- CAN-based, European machine builder standard
- Common in mobile machinery, medical devices

**EtherCAT (Ethernet for Control Automation Technology):**
- Beckhoff, 2003. Arguably the most technically elegant fieldbus
- Standard Ethernet frames, but devices process data on-the-fly as frame passes through
- Sub-microsecond synchronisation — used for high-speed motion control
- Increasingly popular in robotics, semiconductor, packaging

**IO-Link:**
- Point-to-point digital protocol for smart sensors (IEC 61131-9, 2013)
- Replaces analog 4–20 mA with digital connection — bi-directional, parameter upload/download
- Growing rapidly: market expected $8B by 2027
- Gateway devices aggregate IO-Link data to PROFINET/EtherNet/IP

**Modbus RTU / ASCII:**
- Created by Modicon 1979 — the oldest industrial protocol still in common use
- Simple master-slave over RS-232/RS-485
- No inherent security, no authentication
- Ubiquitous because it's free, simple, and every device supports it
- Will be with us for 30+ more years in legacy systems

---

## Section 4: Level 2 — Supervisory Control

### What Lives Here

Level 2 is where humans **see and supervise** the process. The SCADA system, DCS, and HMIs sit here, providing operators with a real-time view and control capability across the facility.

**Core function:** Monitor, visualise, and supervisory-control the process. Log data. Raise alarms.

### SCADA (Supervisory Control and Data Acquisition)

SCADA is an **architecture**, not a product. It describes a system where a central software platform communicates with distributed RTUs/PLCs to acquire data and issue commands.

**Classic SCADA architecture:**
```
Operator Workstations
        │
SCADA Server (polling engine, historian, alarm server)
        │
Communications (radio, fibre, cellular, satellite, IP WAN)
        │
RTU / PLC at field location
        │
Sensors / Actuators (Level 0)
```

**SCADA vendors (the "Big 5"):**

| Vendor | Platform | Stronghold |
|--------|---------|-----------|
| **Ignition (Inductive Automation)** | Ignition SCADA | Water, food & bev, manufacturing — fastest growing |
| **AVEVA (Schneider)** | System Platform, InTouch, Historian | Oil & gas, power, large enterprise |
| **Siemens** | WinCC, WinCC OA (PVSS) | European process industry, power |
| **GE Vernova / iFIX** | iFIX, Proficy SCADA | Power utilities, water |
| **Rockwell / FactoryTalk** | FactoryTalk View, FactoryTalk Historian | Americas manufacturing |
| **Honeywell** | Experion (also DCS role) | Refining, petrochemicals |
| **Yokogawa** | FAST/TOOLS, Exaquantum historian | Oil & gas, Asia-Pacific |
| **Emerson** | Ovation (power), DeltaV (process) | Power generation, pharma |

**Ignition deserves special attention:**
Released 2010 by Inductive Automation, Ignition disrupted the traditional per-tag, per-seat licensing model with unlimited tags and clients for one server price. Built on Java, runs anywhere, web-based clients (no fat client install). OPC-UA native. The primary platform for Databricks Zerobus connector customers today.

### DCS (Distributed Control System)

Where SCADA supervises dispersed remote assets, **DCS is built for tight, integrated control of a continuous process plant** — a refinery, chemical plant, power station. Everything is tightly coupled.

**Key differences SCADA vs DCS:**

| | SCADA | DCS |
|--|-------|-----|
| Geography | Wide area (km to 1000s km) | Single plant/site |
| Control emphasis | Supervisory, not real-time | Real-time tight control |
| Redundancy | RTU-level | System-wide, triple redundant |
| Integration | Open, multi-vendor PLCs | Proprietary, vendor-complete ecosystem |
| Typical industry | Water, power transmission, pipelines | Refining, chemicals, pharma, power gen |
| Typical I/O count | Hundreds to thousands | Thousands to 100,000+ |

**DCS Vendors:**

| Vendor | Platform | Stronghold |
|--------|---------|-----------|
| **Honeywell** | Experion PKS, TPS (legacy) | Refining, petrochemicals — #1 globally |
| **Emerson** | DeltaV (process), Ovation (power) | Pharma, food & bev, power generation |
| **ABB** | System 800xA, Symphony Plus | Pulp & paper, power, marine |
| **Siemens** | PCS 7, PCS neo (successor) | Chemical, pharma, Europe |
| **Yokogawa** | CENTUM VP | Oil & gas, Asia-Pacific |
| **Schneider / AVEVA** | EcoStruxure Foxboro, Triconex | Oil & gas, LNG, nuclear |
| **Rockwell** | PlantPAx | Americas process industries |

**Why DCS data is hard to get out:**
DCS systems are proprietary end-to-end. The historian, the engineering workstation, the controller — all from one vendor, all using proprietary databases and protocols. Getting data out typically requires OPC-DA or OPC-UA server add-ons, or purpose-built historian connectors (OSI PI, AspenTech IP.21).

### Historians

The **process historian** is the time-series database of Level 2. It stores all process values at high frequency (1-second or sub-second) with compression.

**Why process historians exist:**
Standard relational databases (SQL Server, Oracle) cannot handle high-frequency time-series at industrial scale — writing 50,000 tags at 1-second intervals is 50,000 rows/second. Process historians use **swinging-door compression** (only store a point when the trend deviates from a straight line) to achieve 10–50:1 compression ratios.

**The dominant historians:**

| Product | Vendor | Notes |
|---------|--------|-------|
| **OSI PI** | AVEVA (acquired from OSIsoft 2021) | Dominant globally, millions of installations, the de facto standard in oil & gas, energy, utilities |
| **Aspen IP.21 (InfoPlus.21)** | AspenTech | Strong in chemicals and refining |
| **Proficy Historian** | GE Vernova | Manufacturing |
| **FactoryTalk Historian** | Rockwell | Rockwell-ecosystem plants |
| **Exaquantum** | Yokogawa | Asia-Pacific process |
| **InduSoft / AVEVA Historian** | AVEVA | Bundled with AVEVA SCADA |

**OSI PI deserves its own paragraph:**
PI was created by Art Parsons at OSIsoft in 1980. For 40 years it was the only serious industrial historian. The PI Interface ecosystem has 450+ vendor-specific interfaces. By 2021, OSIsoft claimed 1.5 billion sensors connected. AVEVA paid $5B to acquire it. Running PI analytics at scale is the primary driver for Databricks OSI PI connector adoption — moving from expensive PI AF (Asset Framework) queries to native Spark.

### HMI (Human-Machine Interface)

The operator-facing screen. Can be:
- **Thin HMI:** Small touchscreen panel mounted on a machine. Vendor-specific (Siemens KTP, Rockwell PanelView, Weintek, Advantech)
- **Thick HMI / SCADA client:** PC-based workstation running SCADA client software
- **Web-based:** Ignition Perspective — any browser, any device

**ISA-101 HMI Philosophy:**
Published 2015, defines best practice for high-performance HMI design. Key principles: grayscale backgrounds (not green-on-black), colour used only for alarming, process values clearly labelled, alarm states unmistakable. The old "Christmas tree" HMIs with colour-coded everything are actively dangerous.

### Alarms and Alarm Management

**The alarm flood problem:**
Poorly designed SCADA/DCS systems generate thousands of alarms per shift. Buncefield (2005), Texas City (2005), Deepwater Horizon (2010) all had alarm system overload as a contributing factor. Operators were managing hundreds of standing/active alarms simultaneously.

**EEMUA 191 and ISA-18.2:**
The two key alarm management standards. Targets: <1 alarm per 10 minutes during normal operation, <10 alarms per 10 minutes during upset. Alarm rationalisation projects (systematically auditing every alarm for priority, consequence, response) are a major industry.

**Why alarm data matters for AI:**
Alarm histograms, alarm floods, and standing alarms are rich training data for **predictive analytics** and **root cause analysis** — a major Databricks use case in energy and process industries.

---

## Section 5: History of OT — Timeline

```
1769  ┤ Watt's steam engine — first feedback control (centrifugal governor)
1930s ┤ Pneumatic control (3-15 PSI) — first standardised process control signal
1950s ┤ 4-20 mA electronic signal replaces pneumatic in new installations
1958  ┤ First transistorised industrial controllers
1968  ┤ Dick Morley invents the PLC (Modicon 084) for GM Hydramatic
1970s ┤ PLCs proliferate in automotive; first SCADA systems (mainframe-based)
1975  ┤ First commercial DCS — Honeywell TDC 2000 (Total Distributed Control)
      ┤ Simultaneously: Yokogawa CENTUM, Bailey (ABB) Network 90
1979  ┤ Modbus protocol created by Modicon — first open industrial protocol
1980  ┤ OSI PI historian created by Art Parsons / OSIsoft
1984  ┤ HART protocol developed (released commercially 1989)
1987  ┤ S5 PLC (Siemens) dominates European manufacturing
1989  ┤ PROFIBUS launched by Siemens consortium
1990s ┤ PLCs get RS-485 serial comms; SCADA moves to PC-based platforms
1991  ┤ Allen-Bradley (Rockwell) PLC-5 / SLC-500 era
1993  ┤ IEC 61131-3 published — standardises PLC programming languages
1994  ┤ DeviceNet (Rockwell), OPC DA spec begins development
1996  ┤ OPC DA (Data Access) v1.0 published — first interoperability layer
      ┤ Rockwell ControlLogix launched
1998  ┤ EtherNet/IP (ODVA/Rockwell) — Ethernet to the PLC
2000  ┤ Stuxnet era begins (discovered 2010 but development ~2005-2009)
2003  ┤ EtherCAT launched by Beckhoff
2006  ┤ OPC-UA (Unified Architecture) specification published — platform-independent, secure
2008  ┤ Ignition SCADA beta (released commercially 2010)
2010  ┤ Stuxnet discovered — watershed moment for OT cybersecurity
2011  ┤ NERC CIP (Critical Infrastructure Protection) standards enforced
2013  ┤ Industrie 4.0 coined by German government / Fraunhofer Institute
2014  ┤ IIoT (Industrial Internet of Things) term popularised by GE / Predix launch
2016  ┤ Ukraine power grid attacks (BlackEnergy) — first confirmed OT cyberattack on power grid
      ┤ TRITON/TRISIS malware targets Triconex SIS at Saudi Aramco facility
2017  ┤ IO-Link becomes IEC 61131-9
2018  ┤ MQTT and Sparkplug B adopted into ISA-100
2019  ┤ Ethernet-APL project launched (ratified 2022)
2021  ┤ AVEVA acquires OSIsoft for $5B
      ┤ Colonial Pipeline ransomware attack — OT security in mainstream news
2022  ┤ Ethernet-APL physical layer ratified — 2-wire Ethernet to field devices
      ┤ NIS2 Directive adopted by EU (effective October 2024)
2023  ┤ OPC-UA FX (Field eXchange) — OPC-UA all the way to field devices
2024  ┤ IEC 62443 adoption accelerates; AI/ML in OT mainstream conversation
      ┤ Databricks, Microsoft Fabric, AWS IoT compete for OT analytics
2025+ ┤ Agentic AI for OT operations; Digital twin convergence; Unified namespace
```

---

## Section 6: Key Protocols Reference

### The Protocol Stack

```
Application Layer  │  OPC-UA, MQTT, Sparkplug B, DNP3, IEC 61850, Modbus TCP
Transport Layer    │  TCP/IP, UDP
Network Layer      │  Ethernet (OT), 4G/5G (RTU), Serial (legacy)
Physical Layer     │  Cat5/6 Ethernet, Fibre, RS-485, Ethernet-APL, HART
```

### OPC-UA — The Convergence Protocol

Published 2006 by the OPC Foundation, OPC-UA (Unified Architecture) is the most important OT protocol development in 20 years. It replaces the Windows-only, DCOM-based OPC Classic (DA/HDA/A&E) with a platform-independent, secure, semantic standard.

**Key features:**
- **Information model:** Not just data values — full object model with types, methods, events
- **Security:** X.509 certificates, session signing, encrypted transport (TLS)
- **Transport:** TCP binary (performance), HTTPS/WebSockets (firewall-friendly)
- **Pub/Sub extension (2018):** MQTT and AMQP transport — the bridge to cloud
- **Companion specifications:** OPC-UA for PackML (packaging), PLC open (motion), ISA-95, etc.

**Why it matters:** OPC-UA is the only protocol that can carry both real-time data *and* the semantic context (what the data means, what asset it came from, its engineering units) in one message. This is critical for Gold-layer Databricks analytics.

### MQTT and Sparkplug B

**MQTT** (Message Queuing Telemetry Transport) was created by Andy Stanford-Clark (IBM) and Arlen Nipper in 1999 for satellite monitoring of oil pipelines. OASIS standard 2013. Designed for constrained devices on unreliable networks.

**Broker model:** Publishers send to a broker (Mosquitto, EMQX, HiveMQ, AWS IoT Core) → subscribers receive. Massively scalable.

**Sparkplug B** (Eclipse Foundation, originally Cirrus Link 2016):
MQTT alone has no schema — any payload can be sent. Sparkplug B standardises MQTT for industrial use:
- Payload format: Google Protobuf
- Birth/death certificates (device connect/disconnect events)
- Unified namespace concept (topic hierarchy mirrors physical hierarchy)
- Metric aliasing for bandwidth efficiency
- Ignition is the dominant Sparkplug B publisher

**Unified Namespace (UNS):**
Concept championed by Walker Reynolds (The 4.0 Solutions) — a single MQTT broker that is the *single source of truth* for all OT data in a plant. Every device, every system publishes to one broker. Becoming the dominant architectural pattern for greenfield IIoT.

### Modbus TCP/RTU

See Level 1 section. Still dominant by installed base despite being unauthenticated and unencrypted. Modbus TCP wraps RTU in a TCP envelope — same register model, just over Ethernet.

### DNP3

See Level 1 (RTU section). Critical for power/water utilities. IEEE Std 1815-2012.

### IEC 61850

The protocol family for **power substation automation**. Complex, comprehensive, and powerful:
- GOOSE (Generic Object-Oriented Substation Events): sub-millisecond protection relay messaging
- Sampled Values: raw waveform data from instrument transformers
- MMS (Manufacturing Message Specification): supervisory communications
- XMPP/CIM integration for utility-wide data exchange

If your customer is a power utility at the substation level, IEC 61850 is essential knowledge.

### PROFINET

Siemens-led, IEC 61158/61784. Ethernet-based successor to PROFIBUS. Three performance classes:
- **PROFINET NRT** (Non-Real-Time): standard TCP/IP, ~100ms cycle
- **PROFINET RT** (Real-Time): prioritised Ethernet frames, ~1ms cycle
- **PROFINET IRT** (Isochronous Real-Time): hardware-synchronised, <1ms, for motion control

### EtherNet/IP

ODVA (led by Rockwell). Uses standard TCP/IP for configuration, UDP multicast for real-time I/O. The CIP (Common Industrial Protocol) layer is shared with DeviceNet and ControlNet. Dominant in Rockwell-ecosystem plants.

---

## Section 7: OT Cybersecurity

### Why OT Security Is Different From IT Security

| Dimension | IT | OT |
|-----------|----|----|
| **Priority** | Confidentiality → Integrity → Availability | Availability → Integrity → Safety |
| **Patch cycles** | Monthly (Windows Update) | Annually, or never (vendor approval required) |
| **Downtime tolerance** | Hours to days acceptable | Zero — a paper mill doesn't stop |
| **Protocols** | TLS everywhere, authentication | Legacy protocols (Modbus) have zero security |
| **Device lifetime** | 3–5 years | 15–30 years |
| **Testing** | Pen testing acceptable | Pen testing can crash a PLC |
| **Ownership** | IT department | Operations / engineering |

### The Threat Landscape

**Notable incidents:**
- **Stuxnet (2010):** Targeted Iranian uranium centrifuges via Siemens S7 PLCs. First known cyberweapon to cause physical damage. Changed everything.
- **Ukraine Power Grid (2015, 2016):** BlackEnergy, Industroyer malware. First confirmed grid-level OT attack.
- **TRITON/TRISIS (2017):** Targeted Schneider Triconex SIS at Saudi Aramco. Attempted to disable safety systems — if successful, could cause explosion.
- **Colonial Pipeline (2021):** Ransomware on IT systems forced OT shutdown by operators. $4.4M ransom paid.
- **Oldsmar Water Treatment (2021):** Attacker attempted to increase sodium hydroxide to 111× safe level via TeamViewer remote access.

**Threat vectors:**
1. IT-OT convergence (attackers crossing from IT network)
2. Vendor remote access / third-party VPN
3. USB drives (especially for PLCs with no network connection)
4. Compromised engineering workstations
5. Supply chain attacks on software updates

### Key Standards

**IEC 62443** (formerly ISA-99):
The primary OT cybersecurity standard series. Covers:
- 62443-2-1: Security Management System
- 62443-3-3: System Security Requirements (Security Levels SL 1–4)
- 62443-4-2: Component Security Requirements

**NERC CIP (Critical Infrastructure Protection):**
Mandatory for bulk power system operators in North America. CIP-013 (Supply Chain Risk Management) is the most recent major addition.

**NIS2 Directive (EU, effective October 2024):**
Expanded cybersecurity requirements for critical infrastructure. Relevant to Zerobus presentations — it mandates incident reporting within 24/72 hours, risk management, supply chain security.

**Zero Trust OT Architecture:**
- No implicit trust based on network location
- Every device, user, and data flow must authenticate
- Microsegmentation: each Level 2 cell is its own network segment
- DMZ / Data Diode between Level 3.5 and Level 2

---

## Section 8: Current Trends (2023–2026)

### 1. IT/OT Convergence and the Push for Data

The single biggest trend. OT data that sat isolated in historians is now demanded by:
- Executive dashboards (real-time OEE, energy consumption)
- AI/ML models (predictive maintenance, quality prediction)
- Digital twins (virtual replicas of physical assets)
- ESG reporting (Scope 1 emissions require real-time process data)

**The architecture shift:** From polling historians → to streaming directly from PLCs/SCADA via MQTT/OPC-UA → to cloud data platforms.

### 2. Unified Namespace (UNS)

The most discussed architectural concept in IIoT 2022–2025. One MQTT broker as the single source of truth. Walker Reynolds, Kudzai Manditereza, and the broader community are driving adoption. Most greenfield industrial IoT projects now specify UNS as the target architecture.

### 3. Edge Computing

Moving compute closer to the process, not to the cloud. Microsoft Azure IoT Edge, AWS Greengrass, and purpose-built industrial edge (Siemens Industrial Edge, Rockwell Plex, Canonical Ubuntu Core) enable:
- Local ML inference (anomaly detection at the edge)
- Data pre-processing and aggregation before cloud transmission
- Offline operation when WAN connectivity drops

### 4. Digital Twins

A **digital twin** is a real-time virtual replica of a physical asset, process, or system. Three levels:
- **Descriptive twin:** 3D model + real-time sensor overlay
- **Diagnostic twin:** Root cause analysis, historical replay
- **Predictive twin:** What-if simulation, failure prediction

**Key vendors:** Siemens (Simatic WinCC Digital Twin), AVEVA Digital Twin, Ansys, Bentley iTwin, Azure Digital Twins, NVIDIA Omniverse.

**Databricks play:** Gold-layer aggregated data feeds the ML models that underpin predictive twin behaviour.

### 5. AI/ML in OT

From early promise to early production:
- **Predictive maintenance (PdM):** Vibration + process data → bearing failure prediction 4–6 weeks ahead. ROI-proven.
- **Process optimisation:** Real-time AI recommendations to operators (Augmented Intelligence)
- **Anomaly detection:** Isolation Forest, LSTM autoencoders on historian data
- **Computer vision:** Cameras on production lines for quality inspection (replacing manual QC)
- **LLM for OT:** Early days — LLMs for alarm rationalisation, procedure lookup, shift handover automation

### 6. Cybersecurity as Product Feature

Post-Colonial Pipeline, OT cybersecurity shifted from "optional hardening" to procurement requirement. NIS2 in Europe, NERC CIP in North America. Zerobus's NIS2 compliance messaging is directly addressing this trend.

**Key growth areas:** OT-specific SOC capabilities (Claroty, Dragos, Nozomi Networks), OT network visibility, secure remote access platforms (Tosibox, IXON, Secomea).

### 7. Ethernet-APL and the Flat Network Future

With Ethernet-APL, the traditional 4-tier fieldbus stack collapses. A field transmitter can now be an IP endpoint with:
- Web browser-based configuration
- Native OPC-UA or MQTT publishing
- Cybersecurity features (TLS, certificates)

This will take 10–15 years to fully roll out but represents the end of PROFIBUS, HART, and Foundation Fieldbus for new installations.

### 8. Semiconductor and Battery Manufacturing

New growth verticals for OT data:
- **Semiconductor fab:** Extremely data-intensive — 1000s of sensors per tool, sub-second data, SECS/GEM protocol (unique to semi industry)
- **Battery gigafactories:** High-throughput, high-data, greenfield — tend to adopt modern architectures from day one
- **Green hydrogen / electrolysers:** Modbus-heavy, rapidly expanding

---

## Section 9: The OT Vendor Ecosystem Map

### By Category

**Level 0 Instrumentation:**
Emerson (Rosemount), Endress+Hauser, ABB, Honeywell, Yokogawa, Siemens, VEGA, Bürkert, Krohne

**Level 1 Controllers (PLC/PAC/RTU):**
Siemens, Rockwell, Schneider, Mitsubishi, Omron, Beckhoff, ABB, Honeywell, GE Vernova, WAGO

**Level 2 SCADA:**
Ignition (Inductive Automation), AVEVA (Schneider), Siemens WinCC, GE iFIX/Cimplicity, Rockwell FactoryTalk, Honeywell Experion, Copadata Zenon

**DCS:**
Honeywell Experion, Emerson DeltaV / Ovation, ABB 800xA, Siemens PCS 7 / PCS neo, Yokogawa CENTUM, Schneider/Foxboro

**Historians:**
OSI PI (AVEVA), Aspen IP.21 (AspenTech), GE Proficy, Rockwell FactoryTalk, Inductive Automation (built into Ignition)

**Safety (SIS):**
Triconex (Schneider), Pilz, Hima, Rockwell GuardLogix, Siemens F-CPU, ABB

**Drives / Motion:**
ABB, Danfoss, Siemens, Rockwell, Yaskawa, Bosch Rexroth, Parker Hannifin

**OT Networking:**
Cisco (Catalyst IE switches), Hirschmann (Belden), Phoenix Contact, Moxa, Red Lion

**OT Cybersecurity:**
Claroty, Dragos, Nozomi Networks, Armis, Microsoft Defender for IoT, Fortinet, Palo Alto

**IIoT Middleware / Connectivity:**
Inductive Automation (Ignition + Zerobus), PTC ThingWorx, PTC Kepware, Litmus Automation, Cogent DataHub, ICONICS, Canary Labs

---

## Section 10: Structured Learning Plan

### Week 1 — Foundations

| Day | Topic | Resource |
|-----|-------|---------|
| 1 | Purdue Model + ISA-95 | ISA-95 Part 1 white paper (free); ISA website |
| 2 | Level 0: sensors and 4-20 mA | Endress+Hauser Field Instrumentation Guide (free PDF) |
| 3 | Level 1: PLC basics, IEC 61131-3 | CODESYS online simulator (free); PLCopen website |
| 4 | Level 1: Modbus protocol | Simply Modbus explainer; Modbus.org specification |
| 5 | Level 2: SCADA fundamentals | Inductive Automation free Ignition trial + tutorials |

### Week 2 — Protocols and Standards

| Day | Topic | Resource |
|-----|-------|---------|
| 1 | OPC-UA deep dive | OPC Foundation website; Matthias Damm OPC-UA series |
| 2 | MQTT + Sparkplug B | HiveMQ tutorials; Eclipse Sparkplug spec |
| 3 | PROFIBUS/PROFINET | PI International (profibusandprofinet.com) |
| 4 | DCS vs SCADA | Control magazine articles; ISA books |
| 5 | OSI PI architecture | AVEVA community OSIsoft tutorials |

### Week 3 — Vendors and Products

| Day | Topic | Resource |
|-----|-------|---------|
| 1 | Siemens TIA Portal / S7-1500 | Siemens Industry Online Support; YouTube TIA Portal tutorials |
| 2 | Rockwell Studio 5000 / ControlLogix | Rockwell literature library; RA Knowledgebase |
| 3 | Ignition deep dive | Inductive University (free, certification available) |
| 4 | Honeywell DCS / Experion | Honeywell Process Solutions user conference materials |
| 5 | AVEVA PI System | AVEVA Learning (formerly OSIsoft PI World content) |

### Week 4 — Security, Trends, Applications

| Day | Topic | Resource |
|-----|-------|---------|
| 1 | IEC 62443 overview | ISA security resources; CISA OT security guides |
| 2 | OT cybersecurity incidents (case studies) | Dragos Year in Review; Claroty threat research |
| 3 | Unified Namespace concept | Walker Reynolds YouTube; The 4.0 Solutions content |
| 4 | Digital twins and AI in OT | Gartner OT reports; ARC Advisory Group |
| 5 | Integration architecture (your context) | Databricks + Zerobus; this document |

### Certifications Worth Knowing

| Cert | Body | Level |
|------|------|-------|
| **GIAC GICSP** (Global Industrial Cyber Security Professional) | GIAC/SANS | Mid-level OT security |
| **ISA/IEC 62443 Cybersecurity Certificate Program** | ISA | Standards-focused |
| **ISA-99 / ISA Certified Automation Professional (CAP)** | ISA | Broad automation |
| **Inductive University (Ignition Core/Advanced)** | Inductive Automation | Free, credible |
| **Siemens TIA Portal** certifications | Siemens | Product-specific |

---

## Section 11: Quick Reference Cheat Sheet

### The Essential Acronyms

| Acronym | Stands For | One-line description |
|---------|-----------|---------------------|
| PLC | Programmable Logic Controller | Real-time controller, born 1968 GM |
| RTU | Remote Terminal Unit | PLC for remote, unattended locations |
| DCS | Distributed Control System | Tightly integrated plant control |
| SCADA | Supervisory Control and Data Acquisition | Wide-area supervisory monitoring |
| HMI | Human-Machine Interface | Operator screen |
| SIS | Safety Instrumented System | Independent safety layer (SIL-rated) |
| VSD/VFD | Variable Speed/Frequency Drive | Motor speed control |
| OPC-UA | OPC Unified Architecture | The modern OT interoperability standard |
| HART | Highway Addressable Remote Transducer | Digital overlay on 4-20mA |
| SIL | Safety Integrity Level | Safety system reliability rating (1-4) |
| UNS | Unified Namespace | Single MQTT broker as source of truth |
| DMZ | Demilitarised Zone | Network buffer between OT and IT |
| APL | Advanced Physical Layer | 2-wire Ethernet to field devices |
| IIoT | Industrial Internet of Things | OT devices connected to internet/cloud |

### The 10 People/Companies That Shaped OT

1. **Dick Morley** (1968) — Invented the PLC, changed manufacturing forever
2. **Theodore Williams** (1992) — Purdue Model / ISA-95, gave us the architecture language
3. **Art Parsons / OSIsoft** (1980) — Created PI historian, the backbone of industrial data for 40 years
4. **Andy Stanford-Clark / IBM** (1999) — Created MQTT, now the dominant IIoT messaging protocol
5. **Hans-Georg Kempf / Siemens PROFIBUS** (1989) — Led the fieldbus that connects 50 million devices
6. **Walker Reynolds** (2018+) — Popularised Unified Namespace concept, shaped modern IIoT architecture
7. **Stuxnet team** (2010) — Changed the entire OT security conversation permanently
8. **Honeywell TDC 2000 team** (1975) — First commercial DCS, defined what plant control means
9. **OPC Foundation** (1996, OPC-UA 2006) — Created the interoperability layer OT desperately needed
10. **Inductive Automation / Steve Hechtman** (2010) — Democratised SCADA with Ignition

---

*Document compiled February 2026. OT standards and vendor landscapes evolve — verify current product names and versions against vendor documentation.*
