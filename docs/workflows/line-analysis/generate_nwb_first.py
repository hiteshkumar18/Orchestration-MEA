"""Render the study workflow using Hitesh's existing diagram style.

Only writes workflow figures and layout reports here. Does not run analysis.
"""
from pathlib import Path
import importlib.util
import json

OUT = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve().parents[2] / 'architecture' / 'make_diagrams.py'
spec = importlib.util.spec_from_file_location('hitesh_diagram_style', SOURCE)
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)
style.C['review'] = ('#fffbeb', '#b45309')
style.C['study'] = ('#f0fdfa', '#0f766e')
Svg = style.Svg
Svg._markers = set()
s = Svg(2240, 1980)
s.text(40, 48, 'MEA line analysis workflow', size=31, weight=700)
s.text(40, 81, 'NWB before signal analysis • reusable Nextflow blocks • well and chip → trial (T) → overall line', size=18, color=style.C['ink2'])
s.text(2200, 48, 'Target 0.2 · 14 October 2026', size=16, anchor='end', color=style.C['ink2'])

def box(x,y,w,h,title,lines,role='orch',dashed=False):
    s.box(x,y,w,h,title,lines,role=role,title_size=18,line_size=16,dashed=dashed)

s.add('<g id="nwb-intake">')
s.text(40,133,'0  Register, convert and validate before analysis',size=19,weight=700,color=style.C['ink2'])
box(40,180,330,190,'Original source archive',[
    'MaxWell Network + ActivityScan',
    'Assay logs and plate / genotype map',
    'Keep source HDF5 unchanged',
    'Record source identity and checksum',
    'Existing NWB can enter validation'],role='store')
box(410,180,330,190,'P01  Recording registry',[
    'Line / T / chip / well / raw run',
    'Recording time, DIV and culture',
    'Known metadata or explicit unknown',
    'Keep conflicts and unfinished files',
    'Link source → NWB identifier'],role='study',dashed=True)
box(780,180,590,190,'P02  Convert early to NWB',[
    'One immutable file per well / recording / assay',
    'Network conversion already exists as an optional route',
    'ActivityScan conversion and reader still need development',
    'Preserve scan blocks, routing, timestamps and events',
    'Populate verified biology metadata; pin converter version'],role='nwb')
box(1400,180,330,190,'P03  Validate NWB',[
    'PyNWB schema + NWB Inspector',
    'Compare traces, scaling and timing',
    'Check channels and scan coverage',
    'Save findings, including warnings',
    'Hold failed conversion / validation'],role='study',dashed=True)
box(1770,180,430,190,'Validated NWB dataset',[
    'Acquisition signals and event data',
    'Culture, chip and recording metadata',
    'Source / converter / schema versions',
    'NWB identifier and file checksum',
    'Derived tables always link back here'],role='nwb')
for left,right in [(370,408),(740,778),(1370,1398),(1730,1768)]:
    s.arrow([(left,275),(right,275)],color=style.C['nwb'][1])
s.arrow([(1985,370),(1985,395),(24,395),(24,675),(38,675)],color=style.C['nwb'][1])
s.add('</g>')
s.add('<g id="execution-control">')
box(40,420,2160,82,'Dashboard and proposed Nextflow execution',[
    'Browser workspace submits saved plans, displays evidence and records analyst decisions. Nextflow runs computational blocks on the tower.',
    'P labels name the proposed blocks below. Nextflow integration, ActivityScan NWB support and study gates are not deployed; existing algorithms are reused.'],role='orch')
s.add('</g>')
s.dy = 400
s.add('<g id="analysis-and-study-gates">')

for x, w, title in [(40,330,'1  Data and remote access'),(410,330,'2  Register and decide'),(780,590,'3  Process on the tower'),(1400,330,'4  Validate and select'),(1770,430,'5  Freeze the evidence')]:
    s.text(x, 133, title, size=19, weight=700, color=style.C['ink2'])
    s.add(f'<line x1="{x}" y1="{145+s.dy}" x2="{x+w}" y2="{145+s.dy}" stroke="#e5e7eb" stroke-width="2"/>')

box(40,180,330,190,'Canonical NWB registry',[
    'Validated NWB from the intake above',
    'Authoritative genotype / plate map',
    'Line, trial, chip, well, culture',
    'Original recording date and DIV',
    'Every result records its NWB input'],role='nwb')
box(40,435,330,185,'Analyst browser access',[
    'Mac on lab network; VPN off site',
    'SSH tunnel → personal MEA Bench',
    'BeyondTrust → tower desktop',
    'Tower reads its NAS mount',
    'Logs / reports return to analyst'],role='orch')
box(40,715,330,150,'Gate 0  Connection check',[
    'Verify user, NAS and free space',
    'Record code + runtime versions',
    'Confirm NWB access and validation',
    'No queue until checks pass'],role='review')

box(410,180,330,205,'Gate 1  Verify identity',[
    'Trial + chip + well + NWB / raw run',
    'Map well000 to physical well 1',
    'Reconcile labels and DIV0',
    'Detect missing / unfinished files',
    'Resolve identity conflicts first',
    'Save discovery and join report'],role='review')
box(410,435,330,230,'Gate 2  Inclusion policy',[
    'Choose assays and eligible DIVs',
    'Technical, culture and feature QC',
    'Rule, threshold, scope, rationale',
    'Include / exclude / hold',
    'Record exceptions and reviewer',
    'Low activity prompts review',
    'Freeze a version before testing'],role='review')
box(410,715,330,150,'P04  Frozen processing plan',[
    'Choose detection or sorted units',
    'Snapshot effective settings',
    'Preview expected files / wells',
    'Separate output per version'],role='study',dashed=True)

s.container(780,180,590,470,'Network blocks  wrap existing code',role='mea')
box(802,215,546,95,'P05  Preprocessing  CPU',[
    'Read NWB → 300 Hz high pass → common reference',
    'Write binary cache; inspect warnings and duration'],role='mea')
box(802,355,258,145,'P06A  Detection only',[
    'Threshold events / channel',
    'CPU; no unit sorting',
    'Channel activity metrics',
    'Current Bench default'],role='nosort')
box(1090,355,258,145,'P06B / P07  Units',[
    'Kilosort4  GPU',
    'Optional unit merging',
    'Waveforms + unit QC',
    'Retained / rejected units'],role='sort')
box(802,545,546,80,'P08  Network burst analysis',[
    'Current Hitesh branch calls the parameter-free detector',
    'Spikes, rasters and burst metrics; log actual mode'],role='mea')
box(780,715,590,150,'P09  ActivityScan from NWB  CPU',[
    'Existing metrics; NWB reader still to implement',
    'Keep per-channel exposure and block routing',
    'Whole-array activity maps; within-block comparisons',
    'Save NWB-linked summaries, tables and QC figures'],role='scan',dashed=True)

box(1400,180,330,205,'Gate 3  Per-well validation',[
    'P10  Expected vs completed wells',
    'Read logs and checkpoints',
    'Review raster / burst overlays',
    'Check units and denominators',
    'Keep failures and no-event flags',
    'Choose accepted / hold / rerun'],role='review')
box(1400,435,330,230,'Gate 4  Deduplicate results',[
    'P11  Same NWB + measurement key',
    'Select one accepted code version',
    'Log duplicate → retained result',
    'Keep genuine repeat recordings',
    'Resolve changed-value conflicts',
    'Never use shifted run ID alone',
    'Retain original table and labels'],role='review')
box(1400,715,330,150,'P12  Freeze included data',[
    'Apply reviewed scope decisions',
    'Save all / included / excluded',
    'Original DIV + grouped DIV',
    'Link every row to its evidence'],role='study',dashed=True)

box(1770,180,430,205,'Outputs with NWB provenance',[
    'NWB-linked JSON, spikes and raster figures',
    'Processing mode, logs and checkpoints',
    'Sorted mode: unit QC and rejection log',
    'ActivityScan summary and electrode table',
    'Export derived NWB; add Units for sorted data',
    'Completed processing ≠ scientific acceptance'],role='orch')
box(1770,435,430,230,'Validated measurement table',[
    'One row per well / recording / metric',
    'Trial, chip, culture and group identifiers',
    'NWB ID / checksum, assay and code version',
    'Measured duration, unit and denominator',
    'Zero events vs undefined metric vs missing',
    'Criterion version + inclusion decision',
    'Counts reconciled before aggregation'],role='study',dashed=True)
box(1770,715,430,150,'Accepted analysis package',[
    'NWB list + selected result versions',
    'Settings, exclusions and duplicate ledger',
    'Validation figures and stage decisions',
    'Only this frozen package goes forward'],role='study',dashed=True)

# Top-level paths. Review arrows represent gates, not automatic UI features.
s.arrow([(370,275),(408,275)])
s.arrow([(575,385),(575,433)])
s.arrow([(575,665),(575,713)])
s.arrow([(370,790),(408,790)])
s.arrow([(740,785),(762,785),(762,263),(800,263)],color=style.C['orch'][1])
s.arrow([(740,812),(778,812)],color=style.C['scan'][1])
s.arrow([(1075,310),(1075,332),(931,332),(931,353)],color=style.C['nosort'][1])
s.arrow([(1075,332),(1219,332),(1219,353)],color=style.C['sort'][1])
s.arrow([(931,500),(931,530),(1000,530),(1000,543)],color=style.C['nosort'][1])
s.arrow([(1219,500),(1219,530),(1150,530),(1150,543)],color=style.C['sort'][1])
s.arrow([(1348,585),(1385,585),(1385,282),(1398,282)])
s.arrow([(1370,790),(1388,790),(1388,315),(1398,315)],color=style.C['scan'][1])
s.arrow([(1565,385),(1565,433)])
s.arrow([(1565,665),(1565,713)])
s.arrow([(1730,790),(1768,790)],color=style.C['study'][1])
s.arrow([(1985,385),(1985,433)])
s.arrow([(1985,665),(1985,713)])
s.arrow([(1730,282),(1768,282)],color=style.C['orch'][1])
s.arrow([(1730,550),(1768,550)],color=style.C['review'][1])

box(40,950,2160,105,'Every step writes evidence and a decision',[
    'NWB input and checksum • code / environment / parameters • measured QC • criterion and scope • decision and reason • analyst and time • linked outputs',
    'Human approvals become versioned inputs between workflow phases. Nextflow validates them; the reviewer makes the decision. Study controls still need implementation.'],role='study',dashed=True)
s.arrow([(1985,865),(1985,915),(370,915),(370,948)],color=style.C['study'][1])
s.arrow([(370,1055),(370,1168)],color=style.C['study'][1])

for x, label, title, lines, review_title, review_lines in [
    (40,'6  CHIP  preserve each well','P13  Chip report across dates',[
        'Every well: raw and retained metrics, coverage, duration and QC',
        'Show activity maps, rasters, exclusions and per-well trajectories',
        'Keep wells and repeated recordings identifiable',
        'Chip-wide exclusion requires a recorded scope decision'], 'Gate 6  Chip review',[
        'Expected / discovered / completed / included counts reconcile',
        'Reviewer accepts the chip package or returns a named step',
        'Units / electrodes are observations, not biological replicates']),
    (760,'7  TRIAL T  preserve each chip','P14  Trial report within a preparation',[
        'Combine accepted chip packages under one policy version',
        'Genotype / treatment trajectories with wells shown individually',
        'Report animal, culture, chip, well and recording sample sizes',
        'Document DIV grouping, missingness and any time-specific exclusion'], 'Gate 7  Trial review',[
        'Review batch consistency, genotype map and contamination notes',
        'Choose independent unit, endpoints and within-trial comparison',
        'Freeze accepted trial table, model plan and exception ledger']),
    (1480,'8  OVERALL LINE  preserve each trial','P15 / P16  Line statistics and report',[
        'Compare trial effects and group coverage before combining',
        'Model the chosen unit, repeated observations and trial structure',
        'Record test, contrasts, corrections, diagnostics and sensitivity',
        'Show effect sizes, uncertainty and all retained trial contributions'], 'Gate 8  Final validation',[
        'Code-generated figures and exact tables agree with the report',
        'Reviewer accepts methods, counts, tests and limitations',
        'P17  Archive NWB, frozen tables, code, decisions and outputs'])]:
    s.container(x,1130,720 if x==1480 else 660,350,label,role='study')
    width=676 if x==1480 else 616
    box(x+22,1170,width,140,title,lines,role='study',dashed=True)
    box(x+22,1340,width,116,review_title,review_lines,role='review')
    s.arrow([(x+330,1310),(x+330,1338)])
s.arrow([(370,1456),(370,1498),(735,1498),(735,1235),(780,1235)],color=style.C['study'][1])
s.arrow([(1090,1456),(1090,1498),(1458,1498),(1458,1235),(1500,1235)],color=style.C['study'][1])

s.add('</g>')
s.dy = 0
style.legend(s,40,1930,[('orch','Dashboard / execution'),('nwb','Canonical NWB'),('mea','Network algorithms'),('scan','ActivityScan'),('review','Human review'),('study','Study layer to build')])
s.text(40,1960,'Target workflow, not a deployment claim. Scientific criteria remain unapproved. Varda’s existing Nextflow blocks inform the design; NWB comes before analysis.',size=15,color=style.C['ink2'])
svg = s.render().replace('width="2240" height="1980"', 'width="790.2222mm" height="698.5mm"', 1)
svg = svg.replace('<defs>', '<title>MEA line analysis with early NWB and Nextflow blocks</title><defs>', 1)
(OUT/'mea-line-workflow-nwb-first.svg').write_text(svg)
(OUT/'mea-line-workflow-nwb-first.layout.json').write_text(json.dumps({'warnings':s.warnings,'canvas':[s.w,s.h],'style_source':'docs/architecture/make_diagrams.py'},indent=2)+'\n')
print(json.dumps({'diagram':str(OUT/'mea-line-workflow-nwb-first.svg'),'warnings':s.warnings},indent=2))
