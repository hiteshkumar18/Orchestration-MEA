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
s = Svg(2240, 1580)
s.text(40, 48, 'MEA line analysis workflow', size=31, weight=700)
s.text(40, 81, 'Current tools plus explicit analyst gates • raw data → well and chip → trial (T) → overall line', size=18, color=style.C['ink2'])
s.text(2200, 48, 'Draft 0.1 · 13 October 2026', size=16, anchor='end', color=style.C['ink2'])

for x, w, title in [(40,330,'1  Data and remote access'),(410,330,'2  Register and decide'),(780,590,'3  Process on the tower'),(1400,330,'4  Validate and select'),(1770,430,'5  Freeze the evidence')]:
    s.text(x, 133, title, size=19, weight=700, color=style.C['ink2'])
    s.add(f'<line x1="{x}" y1="145" x2="{x+w}" y2="145" stroke="#e5e7eb" stroke-width="2"/>')

def box(x,y,w,h,title,lines,role='orch',dashed=False):
    s.box(x,y,w,h,title,lines,role=role,title_size=18,line_size=16,dashed=dashed)

box(40,180,330,190,'Raw recordings and study log',[
    'Network + ActivityScan HDF5',
    'Authoritative genotype / plate map',
    'Line, trial, chip, well, culture',
    'Original recording date and DIV',
    'NAS input stays unchanged'],role='store')
box(40,435,330,185,'Off site analyst',[
    'Mac browser + connected VPN',
    'SSH tunnel → personal MEA Bench',
    'BeyondTrust → tower desktop',
    'Tower reads its NAS mount',
    'Logs / reports return to analyst'],role='orch')
box(40,715,330,150,'Gate 0  Connection check',[
    'Verify user, NAS and free space',
    'Record code + runtime versions',
    'Read one HDF5 header',
    'No queue until checks pass'],role='review')

box(410,180,330,205,'Gate 1  Verify identity',[
    'Trial + chip + well + raw run',
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
box(410,715,330,150,'Resolved processing plan',[
    'Choose detection or sorted units',
    'Snapshot effective settings',
    'Preview expected files / wells',
    'Separate output per version'],role='study',dashed=True)

s.container(780,180,590,470,'Network analysis  existing code',role='mea')
box(802,215,546,95,'Preprocessing  CPU',[
    'Load well → 300 Hz high pass → common reference',
    'Write binary cache; inspect warnings and duration'],role='mea')
box(802,355,258,145,'A  Detection only',[
    'Threshold events / channel',
    'CPU; no unit sorting',
    'Channel activity metrics',
    'Current Bench default'],role='nosort')
box(1090,355,258,145,'B  Sorted units',[
    'Kilosort4  GPU',
    'Optional unit merging',
    'Waveforms + unit QC',
    'Retained / rejected units'],role='sort')
box(802,545,546,80,'Network burst analysis',[
    'Current Hitesh branch calls the parameter-free detector',
    'Spikes, rasters and burst metrics; log actual mode'],role='mea')
box(780,715,590,150,'ActivityScan  existing code  CPU',[
    'Whole-array electrode rates and amplitude maps',
    'Per-well pass / warn / fail reasons',
    'Burst / synchrony preview within scan blocks',
    'Save summary.json, per_electrode.csv and figures'],role='scan')

box(1400,180,330,205,'Gate 3  Per-well validation',[
    'Expected vs completed wells',
    'Read logs and checkpoints',
    'Review raster / burst overlays',
    'Check units and denominators',
    'Keep failures and no-event flags',
    'Choose accepted / hold / rerun'],role='review')
box(1400,435,330,230,'Gate 4  Deduplicate results',[
    'Same source + same measurement',
    'Select one accepted code version',
    'Log duplicate → retained result',
    'Keep genuine repeat recordings',
    'Resolve changed-value conflicts',
    'Never use shifted run ID alone',
    'Retain original table and labels'],role='review')
box(1400,715,330,150,'Gate 5  Freeze included data',[
    'Apply reviewed scope decisions',
    'Save all / included / excluded',
    'Original DIV + grouped DIV',
    'Link every row to its evidence'],role='study',dashed=True)

box(1770,180,430,205,'Existing outputs and history',[
    'Network JSON, spikes and raster figures',
    'Processing mode, logs and checkpoints',
    'Sorted mode: unit QC and rejection log',
    'ActivityScan summary and electrode table',
    'Bench run history and AI handoff manifest',
    'Completed processing ≠ scientific acceptance'],role='orch')
box(1770,435,430,230,'Validated measurement table',[
    'One row per well / recording / metric',
    'Trial, chip, culture and group identifiers',
    'Assay, detection mode and code version',
    'Measured duration, unit and denominator',
    'Zero events vs undefined metric vs missing',
    'Criterion version + inclusion decision',
    'Counts reconciled before aggregation'],role='study',dashed=True)
box(1770,715,430,150,'Accepted analysis package',[
    'Source list + selected result versions',
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
    'Input identity and fingerprint • effective settings and software version • measured QC values • criterion and scope • decision and reason • analyst and time • linked outputs',
    'Technical logs already exist. Structured study decisions, canonical tables and cross-trial statistics are the study layer to add; amber gates are analyst reviews.'],role='study',dashed=True)
s.arrow([(1985,865),(1985,915),(370,915),(370,948)],color=style.C['study'][1])
s.arrow([(370,1055),(370,1168)],color=style.C['study'][1])

for x, label, title, lines, review_title, review_lines in [
    (40,'6  CHIP  preserve each well','Chip report across recording dates',[
        'Every well: raw and retained metrics, coverage, duration and QC',
        'Show activity maps, rasters, exclusions and per-well trajectories',
        'Keep wells and repeated recordings identifiable',
        'Chip-wide exclusion requires a recorded scope decision'], 'Gate 6  Chip review',[
        'Expected / discovered / completed / included counts reconcile',
        'Reviewer accepts the chip package or returns a named step',
        'Units / electrodes are observations, not biological replicates']),
    (760,'7  TRIAL T  preserve each chip','Trial report within one preparation',[
        'Combine accepted chip packages under one policy version',
        'Genotype / treatment trajectories with wells shown individually',
        'Report animal, culture, chip, well and recording sample sizes',
        'Document DIV grouping, missingness and any time-specific exclusion'], 'Gate 7  Trial review',[
        'Review batch consistency, genotype map and contamination notes',
        'Choose independent unit, endpoints and within-trial comparison',
        'Freeze accepted trial table, model plan and exception ledger']),
    (1480,'8  OVERALL LINE  preserve each trial','Line report and statistical analysis',[
        'Compare trial effects and group coverage before combining',
        'Model the chosen unit, repeated observations and trial structure',
        'Record test, contrasts, corrections, diagnostics and sensitivity',
        'Show effect sizes, uncertainty and all retained trial contributions'], 'Gate 8  Final validation',[
        'Code-generated figures and exact tables agree with the report',
        'Reviewer accepts methods, counts, tests and limitations',
        'Archive the frozen dataset, code, settings, logs and outputs'])]:
    s.container(x,1130,720 if x==1480 else 660,350,label,role='study')
    width=676 if x==1480 else 616
    box(x+22,1170,width,140,title,lines,role='study',dashed=True)
    box(x+22,1340,width,116,review_title,review_lines,role='review')
    s.arrow([(x+330,1310),(x+330,1338)])
s.arrow([(370,1456),(370,1498),(735,1498),(735,1235),(780,1235)],color=style.C['study'][1])
s.arrow([(1090,1456),(1090,1498),(1458,1498),(1458,1235),(1500,1235)],color=style.C['study'][1])

style.legend(s,40,1530,[('orch','Existing orchestration'),('mea','Existing network code'),('scan','ActivityScan'),('review','Analyst gate'),('study','Study layer to formalize')])
s.text(40,1560,'Same diagram language as Hitesh’s MEA architecture overview. This is a workflow draft; no inclusion threshold or statistical model has been approved or applied.',size=15,color=style.C['ink2'])
(OUT/'mea-line-workflow-baseline.svg').write_text(s.render())
(OUT/'mea-line-workflow-baseline.layout.json').write_text(json.dumps({'warnings':s.warnings,'canvas':[s.w,s.h],'style_source':'docs/architecture/make_diagrams.py'},indent=2)+'\n')
print(json.dumps({'diagram':str(OUT/'mea-line-workflow-baseline.svg'),'warnings':s.warnings},indent=2))
