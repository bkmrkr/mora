"""Seed a Neuroscience Brain Anatomy curriculum with 35 nodes covering
major structures, functional systems, and clinical applications.

Domains covered:
  - Cellular Foundations (4 nodes)
  - Brainstem and Cerebellum (5 nodes)
  - Diencephalon (3 nodes)
  - Cerebral Cortex — Lobes and Landmarks (6 nodes)
  - Limbic System and Memory (4 nodes)
  - Basal Ganglia and Motor Systems (3 nodes)
  - White Matter and Connectivity (3 nodes)
  - Ventricular System and Vasculature (3 nodes)
  - Functional Systems (4 nodes)

Run from project root: python3 scripts/seed_brain_anatomy.py
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH

TOPIC_NAME = 'Brain Anatomy'
TOPIC_DESC = (
    'Comprehensive neuroscience curriculum covering human brain anatomy from '
    'cellular foundations through major structures, functional systems, and '
    'clinical correlations. Progresses from neurons and glia through the '
    'brainstem, diencephalon, cerebral cortex, limbic system, basal ganglia, '
    'white matter tracts, vasculature, and integrated functional networks. '
    'Emphasizes structure-function relationships and clinical relevance.'
)

# Each node: (name, description, order, prerequisite_indices[])
# prerequisite_indices reference 0-based position in this list
NODES = [
    # === CELLULAR FOUNDATIONS (CF) ===
    (
        'Neurons: Structure and Types',
        'The neuron is the fundamental signaling cell of the nervous system. '
        'Key structures: cell body (soma) containing the nucleus, dendrites that receive '
        'input, axon that transmits output, axon hillock where action potentials initiate, '
        'axon terminals (synaptic boutons) that release neurotransmitters. '
        'Types by structure: unipolar (one process, sensory ganglia), bipolar (two processes, '
        'retina, olfactory), multipolar (many dendrites, most common in CNS — motor neurons, '
        'interneurons). Types by function: sensory (afferent), motor (efferent), interneurons. '
        'Purkinje cells of the cerebellum and pyramidal cells of the cortex are distinctive '
        'multipolar neurons. A typical neuron receives ~10,000 synaptic inputs.',
        1, [],
    ),
    (
        'Glial Cells',
        'Glial cells support, protect, and maintain neurons. They outnumber neurons and are '
        'essential for brain function. Four major types in the CNS: '
        'Astrocytes — star-shaped, form the blood-brain barrier (BBB) with their end-feet, '
        'regulate extracellular potassium and glutamate, provide metabolic support. '
        'Oligodendrocytes — produce myelin in the CNS; each one myelinates segments of '
        'multiple axons. Microglia — resident immune cells, phagocytose debris and pathogens, '
        'derived from mesoderm (not neural crest). Ependymal cells — line the ventricles, '
        'produce cerebrospinal fluid (CSF), have cilia. In the PNS: Schwann cells myelinate '
        'one axon segment each; satellite cells surround cell bodies in ganglia.',
        2, [0],
    ),
    (
        'Synapses and Neurotransmitters',
        'Synapses are junctions where neurons communicate. Chemical synapses: presynaptic '
        'terminal releases neurotransmitter into the synaptic cleft; binds receptors on '
        'postsynaptic membrane. Electrical synapses: gap junctions allow direct ion flow. '
        'Major neurotransmitters and their roles: Glutamate — main excitatory NT in the CNS. '
        'GABA (gamma-aminobutyric acid) — main inhibitory NT in the brain. Glycine — '
        'inhibitory in the spinal cord. Acetylcholine (ACh) — neuromuscular junction, '
        'autonomic ganglia, basal forebrain memory circuits. Dopamine — reward, motivation, '
        'motor control (substantia nigra, VTA). Serotonin (5-HT) — mood, sleep, appetite '
        '(raphe nuclei). Norepinephrine — alertness, attention (locus coeruleus). '
        'EPSPs depolarize, IPSPs hyperpolarize. Summation determines firing.',
        3, [0],
    ),
    (
        'Myelination and Saltatory Conduction',
        'Myelin is a lipid-rich insulating sheath wrapped around axons that dramatically '
        'increases conduction velocity. In the CNS: produced by oligodendrocytes. In the '
        'PNS: produced by Schwann cells. Nodes of Ranvier are gaps between myelin segments '
        'where voltage-gated sodium channels cluster. Action potentials jump from node to '
        'node — saltatory conduction — increasing speed from ~1 m/s (unmyelinated) to '
        '~120 m/s (myelinated). White matter = myelinated axon tracts; gray matter = '
        'cell bodies and unmyelinated regions. Demyelination diseases: Multiple sclerosis '
        '(CNS, oligodendrocytes attacked), Guillain-Barré syndrome (PNS, Schwann cells).',
        4, [1],
    ),

    # === BRAINSTEM AND CEREBELLUM (BS) ===
    (
        'Brainstem Overview and Medulla Oblongata',
        'The brainstem connects the cerebrum to the spinal cord and contains nuclei for '
        'cranial nerves, autonomic functions, and ascending/descending tracts. Three parts '
        'from caudal to rostral: medulla oblongata, pons, midbrain. '
        'Medulla oblongata: most caudal part, continuous with the spinal cord. Contains '
        'vital autonomic centers — cardiovascular center (heart rate, blood pressure), '
        'respiratory center (breathing rhythm), and the chemoreceptor trigger zone (vomiting). '
        'Key structures: pyramids (corticospinal tracts, which decussate here — ~90% cross), '
        'inferior olivary nucleus (sends climbing fibers to cerebellum), gracile and cuneate '
        'nuclei (relay fine touch/proprioception from the dorsal columns). '
        'Cranial nerves IX (glossopharyngeal), X (vagus), XI (accessory), XII (hypoglossal) '
        'emerge from the medulla.',
        5, [2],
    ),
    (
        'Pons',
        'The pons lies between the medulla and midbrain, forming a prominent bulge on the '
        'ventral brainstem. "Pons" means bridge — it relays signals between the cerebral '
        'cortex and the cerebellum via the middle cerebellar peduncle. '
        'Key structures: Pontine nuclei relay cortical motor plans to the cerebellum. '
        'The pneumotaxic and apneustic centers modulate breathing rhythm (set by the medulla). '
        'The locus coeruleus — a small nucleus with widespread norepinephrine projections — '
        'controls arousal, attention, and the sleep-wake cycle. The raphe nuclei (also '
        'spanning the medulla) produce serotonin and project throughout the brain. '
        'Cranial nerves V (trigeminal), VI (abducens), VII (facial), and VIII '
        '(vestibulocochlear) are associated with the pons.',
        6, [4],
    ),
    (
        'Midbrain (Mesencephalon)',
        'The midbrain is the most rostral part of the brainstem, connecting the pons to '
        'the diencephalon. Divided into the tectum (roof) and tegmentum (floor). '
        'Tectum: Superior colliculi — visual reflexes (saccades, head turning toward stimuli). '
        'Inferior colliculi — auditory processing relay to the medial geniculate nucleus. '
        'Tegmentum: Substantia nigra — pars compacta produces dopamine, projects to the '
        'striatum (nigrostriatal pathway); degeneration causes Parkinson disease. '
        'Ventral tegmental area (VTA) — dopamine neurons projecting to nucleus accumbens '
        '(mesolimbic/reward pathway) and prefrontal cortex (mesocortical pathway). '
        'Red nucleus — motor coordination. Periaqueductal gray (PAG) — pain modulation, '
        'surrounds the cerebral aqueduct. Cerebral peduncles carry descending corticospinal '
        'and corticobulbar fibers. CN III (oculomotor), CN IV (trochlear) emerge here.',
        7, [5],
    ),
    (
        'Reticular Formation',
        'The reticular formation is a diffuse network of neurons spanning the brainstem '
        'core from the medulla through the pons to the midbrain. It has no sharp boundaries '
        'and integrates sensory, motor, and autonomic functions. '
        'Key systems: Ascending reticular activating system (ARAS) — drives arousal and '
        'consciousness; damage causes coma. Projects to the thalamus and cortex. '
        'Descending reticulospinal tracts — modulate spinal motor neuron excitability, '
        'muscle tone, and posture. Autonomic regulation — coordinates cardiovascular, '
        'respiratory, and GI reflexes. Contains pattern generators for rhythmic activities '
        'like breathing and locomotion. The reticular formation integrates with the '
        'locus coeruleus, raphe nuclei, and periaqueductal gray.',
        8, [6],
    ),
    (
        'Cerebellum',
        'The cerebellum ("little brain") sits posterior to the brainstem, connected by '
        'three pairs of cerebellar peduncles (superior, middle, inferior). Contains more '
        'neurons than the rest of the brain combined (~80% of all neurons). '
        'Gross anatomy: Two hemispheres connected by the vermis. Surface has folia (folds). '
        'Three lobes: anterior, posterior, flocculonodular. '
        'Deep cerebellar nuclei (medial to lateral): fastigial, interposed (globose + '
        'emboliform), dentate — these are the OUTPUT nuclei of the cerebellum. '
        'Cortical layers: molecular (outer), Purkinje (middle — large inhibitory neurons, '
        'sole output of cerebellar cortex), granular (inner — granule cells, most numerous '
        'neurons in the brain). '
        'Functions by region: Vestibulocerebellum (flocculonodular lobe) — balance, eye '
        'movements. Spinocerebellum (vermis + paravermal) — posture, gait, limb coordination. '
        'Cerebrocerebellum (lateral hemispheres) — motor planning, cognitive functions. '
        'Lesions: ipsilateral deficits (does not cross), ataxia, dysmetria, intention tremor, '
        'dysdiadochokinesia. Cerebellar stroke affects the same side.',
        9, [7],
    ),

    # === DIENCEPHALON (DI) ===
    (
        'Thalamus',
        'The thalamus is a paired egg-shaped structure forming the bulk of the diencephalon. '
        'It is the "relay station" of the brain — nearly all sensory information (except '
        'olfaction) passes through it before reaching the cortex. Also relays motor and '
        'limbic information. '
        'Key nuclei and connections: '
        'VPL (ventral posterolateral) — relays somatosensory from body → S1 cortex. '
        'VPM (ventral posteromedial) — relays somatosensory from face → S1 cortex. '
        'LGN (lateral geniculate nucleus) — relays visual information → V1 (primary visual). '
        'MGN (medial geniculate nucleus) — relays auditory information → A1 (primary auditory). '
        'VL (ventral lateral) — receives from cerebellum and basal ganglia → motor cortex. '
        'VA (ventral anterior) — basal ganglia output → premotor cortex. '
        'Anterior nucleus — mammillary bodies → cingulate cortex (Papez circuit, memory). '
        'Pulvinar — visual attention. MD (mediodorsal) — prefrontal cortex, executive function. '
        'The reticular nucleus is a shell of GABAergic neurons that modulates thalamic gating.',
        10, [7],
    ),
    (
        'Hypothalamus',
        'The hypothalamus lies below the thalamus and above the pituitary gland. Despite '
        'being small (~4g), it is the master regulator of homeostasis and the autonomic '
        'nervous system. "The four Fs": feeding, fighting, fleeing, and mating. '
        'Key nuclei and functions: '
        'Suprachiasmatic nucleus (SCN) — master circadian clock, receives retinal input. '
        'Paraventricular nucleus (PVN) — produces oxytocin and vasopressin (ADH); projects '
        'to posterior pituitary (neurohypophysis). Also sends CRH to anterior pituitary. '
        'Supraoptic nucleus — also produces ADH and oxytocin. '
        'Arcuate nucleus — releases hormones to anterior pituitary via hypophyseal portal '
        'system (GnRH, GHRH, dopamine inhibiting prolactin). Also regulates appetite '
        '(NPY/AgRP = hunger, POMC/CART = satiety). '
        'Lateral hypothalamus — hunger center (lesion → anorexia). '
        'Ventromedial hypothalamus — satiety center (lesion → obesity). '
        'Anterior hypothalamus — cooling (parasympathetic). '
        'Posterior hypothalamus — heating (sympathetic). '
        'Mammillary bodies — memory circuit (Papez), damaged in Wernicke-Korsakoff syndrome.',
        11, [9],
    ),
    (
        'Epithalamus and Subthalamus',
        'The epithalamus sits posterior to the thalamus. Key structure: pineal gland — '
        'produces melatonin from serotonin, regulated by the SCN via the superior cervical '
        'ganglion. Melatonin promotes sleep and is suppressed by light. The habenula is part '
        'of the epithalamus and connects the limbic system to the midbrain; it modulates '
        'reward, aversion, and monoamine systems (dopamine, serotonin). The habenula is '
        'involved in decision-making and is implicated in depression. '
        'The subthalamus lies ventral to the thalamus. Key structure: subthalamic nucleus '
        '(STN) — part of the indirect pathway of the basal ganglia. It is excitatory '
        '(glutamatergic) and projects to the globus pallidus internus (GPi). '
        'Lesions of the STN cause hemiballismus — violent flinging movements of the '
        'contralateral limbs. Deep brain stimulation (DBS) of the STN is a treatment '
        'for advanced Parkinson disease.',
        12, [9, 10],
    ),

    # === CEREBRAL CORTEX — LOBES AND LANDMARKS (CX) ===
    (
        'Cerebral Cortex Overview and Sulci/Gyri',
        'The cerebral cortex is the outer layer of gray matter (~2-4 mm thick) covering '
        'the cerebral hemispheres. It is highly folded into gyri (ridges) and sulci (grooves) '
        'to increase surface area (~2,500 cm²). Deeper grooves are called fissures. '
        'Key landmarks: Longitudinal fissure — separates left and right hemispheres. '
        'Central sulcus (of Rolando) — separates frontal from parietal lobe; precentral '
        'gyrus (motor) anterior, postcentral gyrus (sensory) posterior. '
        'Lateral sulcus (of Sylvius) — separates temporal lobe from frontal and parietal; '
        'contains the insula deep within. Parieto-occipital sulcus — separates parietal '
        'from occipital lobe (visible on medial surface). Calcarine sulcus — primary visual '
        'cortex (V1) lies along its banks. '
        'Cortical layers (neocortex has 6): I molecular, II external granular, '
        'III external pyramidal, IV internal granular (sensory input from thalamus), '
        'V internal pyramidal (output to brainstem/spinal cord — contains Betz cells in M1), '
        'VI multiform (output to thalamus). Brodmann areas map cytoarchitectural regions.',
        13, [9],
    ),
    (
        'Frontal Lobe',
        'The frontal lobe is the largest lobe, occupying the anterior third of each hemisphere. '
        'Bounded posteriorly by the central sulcus, inferiorly by the lateral sulcus. '
        'Key regions and functions: '
        'Primary motor cortex (M1, precentral gyrus, Brodmann area 4) — direct voluntary '
        'movement; organized as a motor homunculus (face lateral/inferior, leg medial/superior). '
        'Premotor cortex (area 6) — motor planning and sequencing. '
        'Supplementary motor area (SMA, medial area 6) — planning complex movements, '
        'bimanual coordination. '
        'Broca area (areas 44, 45, inferior frontal gyrus, LEFT hemisphere) — speech '
        'production; damage causes Broca aphasia (nonfluent, telegraphic, comprehension intact). '
        'Prefrontal cortex (PFC) — executive function, working memory, decision-making, '
        'personality, social behavior, impulse control. Dorsolateral PFC = working memory. '
        'Orbitofrontal cortex = reward, emotion regulation, social judgment. '
        'Frontal eye fields (area 8) — voluntary saccadic eye movements. '
        'Lesion example: Phineas Gage — orbitofrontal damage → personality change.',
        14, [12],
    ),
    (
        'Parietal Lobe',
        'The parietal lobe lies between the central sulcus (anterior) and parieto-occipital '
        'sulcus (posterior), above the lateral sulcus. '
        'Key regions: '
        'Primary somatosensory cortex (S1, postcentral gyrus, areas 3,1,2) — receives '
        'touch, pressure, temperature, pain, proprioception from the contralateral body '
        'via the thalamus (VPL/VPM). Organized as a sensory homunculus (lips and hands '
        'have disproportionately large representation). '
        'Superior parietal lobule (areas 5,7) — sensorimotor integration, spatial awareness '
        'of the body, reaching and grasping. '
        'Inferior parietal lobule — supramarginal gyrus (area 40) and angular gyrus (area 39). '
        'Left angular gyrus: reading, writing, calculation (Gerstmann syndrome if damaged — '
        'agraphia, acalculia, finger agnosia, left-right confusion). '
        'Damage to right parietal lobe → hemispatial neglect (ignores left side of space). '
        'The intraparietal sulcus contains areas for number sense and attention.',
        15, [13],
    ),
    (
        'Temporal Lobe',
        'The temporal lobe lies below the lateral sulcus, anterior to the occipital lobe. '
        'Key regions and functions: '
        'Primary auditory cortex (A1, Heschl gyrus, areas 41,42) — tonotopic sound processing. '
        'Wernicke area (posterior superior temporal gyrus, area 22, LEFT hemisphere) — '
        'language comprehension; damage causes Wernicke aphasia (fluent but nonsensical, '
        'poor comprehension, word salad). '
        'Superior temporal sulcus — social perception, voice recognition, theory of mind. '
        'Inferior temporal cortex — visual object recognition ("what pathway" terminus), '
        'fusiform face area (prosopagnosia if damaged — cannot recognize faces). '
        'Medial temporal lobe: hippocampus (declarative memory formation), entorhinal cortex '
        '(grid cells, gateway to hippocampus), amygdala (emotion, fear). '
        'Uncus — contains amygdala, can herniate in raised intracranial pressure '
        '(uncal herniation → CN III palsy, ipsilateral pupil dilation).',
        16, [13],
    ),
    (
        'Occipital Lobe',
        'The occipital lobe is the most posterior lobe, primarily dedicated to vision. '
        'Bounded anteriorly by the parieto-occipital sulcus (medial) and an imaginary line '
        'to the preoccipital notch (lateral). '
        'Key regions: '
        'Primary visual cortex (V1, area 17, striate cortex) — lines the banks of the '
        'calcarine sulcus. Receives input from the LGN of the thalamus. Organized '
        'retinotopically: upper visual field → below calcarine sulcus (lingual gyrus), '
        'lower visual field → above calcarine sulcus (cuneus). '
        'Contralateral visual field: left V1 processes right visual field and vice versa. '
        'V2 (area 18), V3, V4 (color processing), V5/MT (motion processing). '
        'Two visual streams originate here: dorsal stream ("where/how" → parietal lobe, '
        'spatial processing) and ventral stream ("what" → temporal lobe, object recognition). '
        'Damage to V1: cortical blindness (contralateral homonymous hemianopia). '
        'Bilateral V1 damage: Anton syndrome (cortical blindness with denial of deficit).',
        17, [13],
    ),
    (
        'Insular Cortex',
        'The insula (Island of Reil) is a cortical lobe hidden deep within the lateral '
        'sulcus, covered by the opercula of the frontal, parietal, and temporal lobes. '
        'Divided into anterior insula and posterior insula. '
        'Functions: Interoception — awareness of internal body states (heartbeat, breathing, '
        'hunger, thirst, temperature, pain). The anterior insula integrates these signals '
        'with emotions to create subjective feelings ("how do I feel?"). '
        'Gustatory cortex — primary taste perception (with frontal operculum). '
        'Autonomic regulation — sympathetic and parasympathetic coordination. '
        'Pain processing — pain perception and empathy for others\' pain. '
        'Disgust — both literal (taste) and moral disgust. '
        'Emotional awareness — implicated in anxiety, addiction, and body dysmorphia. '
        'The anterior insula is part of the salience network (with dorsal ACC) — detects '
        'behaviorally relevant stimuli and switches between default mode and central '
        'executive networks.',
        18, [13],
    ),

    # === LIMBIC SYSTEM AND MEMORY (LS) ===
    (
        'Hippocampus and Memory Formation',
        'The hippocampus is a seahorse-shaped structure in the medial temporal lobe. '
        'It is essential for forming new declarative (explicit) memories — both episodic '
        '(events) and semantic (facts). It does NOT store long-term memories; it consolidates '
        'them to the cortex over weeks to months. '
        'Anatomy: Cornu Ammonis (CA1-CA4) subfields and the dentate gyrus. The trisynaptic '
        'pathway: entorhinal cortex → dentate gyrus (perforant path) → CA3 (mossy fibers) '
        '→ CA1 (Schaffer collaterals) → subiculum → entorhinal cortex. '
        'Long-term potentiation (LTP) at CA1 synapses is the cellular basis of memory — '
        'NMDA receptors require coincident pre- and postsynaptic activity. '
        'Place cells in the hippocampus fire at specific locations (spatial memory). '
        'Grid cells in the entorhinal cortex provide spatial coordinates. '
        'Bilateral hippocampal damage: anterograde amnesia (cannot form new memories) — '
        'famously documented in patient H.M. (Henry Molaison). '
        'Hippocampal atrophy is an early marker of Alzheimer disease.',
        19, [16],
    ),
    (
        'Amygdala and Emotion',
        'The amygdala is an almond-shaped group of nuclei in the anterior medial temporal '
        'lobe, adjacent to the hippocampus. It is the brain\'s threat detector and emotional '
        'processing center. '
        'Key nuclei: Basolateral complex (lateral + basal nuclei) — receives sensory input '
        'from thalamus and cortex; where fear conditioning occurs. Central nucleus — '
        'output to hypothalamus and brainstem for autonomic fear responses (increased heart '
        'rate, sweating, freezing, fight-or-flight via the sympathetic nervous system). '
        'Two pathways for fear: "Low road" — thalamus → amygdala (fast, crude, automatic) '
        'and "High road" — thalamus → cortex → amygdala (slower, detailed, conscious). '
        'The amygdala enhances emotional memory consolidation via hippocampal interactions '
        '(emotionally charged events are remembered better). '
        'Bilateral amygdala damage: Klüver-Bucy syndrome — loss of fear, hyperorality, '
        'visual agnosia, altered sexual behavior. Urbach-Wiethe disease selectively '
        'calcifies the amygdala, showing preserved recognition of all emotions except fear.',
        20, [16],
    ),
    (
        'Cingulate Cortex',
        'The cingulate cortex is a C-shaped cortical region wrapping around the corpus '
        'callosum on the medial surface of each hemisphere. It is a key component of the '
        'limbic system. Divided into anterior cingulate cortex (ACC) and posterior cingulate '
        'cortex (PCC). '
        'Anterior cingulate cortex (ACC, area 24,32): '
        'Dorsal ACC — cognitive control, error detection, conflict monitoring, attention. '
        'Activates when you make a mistake or face conflicting choices. '
        'Ventral/subgenual ACC (area 25) — emotion regulation, autonomic functions; '
        'hyperactivity implicated in depression (target for DBS treatment). '
        'Posterior cingulate cortex (PCC, area 23,31): '
        'Part of the default mode network (DMN) — active during self-referential thought, '
        'autobiographical memory, mind-wandering. Highly connected hub. '
        'Early amyloid deposition in Alzheimer disease. '
        'The cingulum bundle is the white matter tract beneath the cingulate cortex, '
        'connecting frontal, parietal, and temporal regions.',
        21, [13, 19],
    ),
    (
        'Papez Circuit and Fornix',
        'The Papez circuit is a classical limbic circuit for emotion and memory. '
        'Pathway: Hippocampus → fornix → mammillary bodies (hypothalamus) → mammillothalamic '
        'tract → anterior thalamic nucleus → cingulate cortex → cingulum bundle → '
        'parahippocampal gyrus → entorhinal cortex → hippocampus (completing the loop). '
        'The fornix is the major output pathway of the hippocampus — a C-shaped white matter '
        'bundle arching beneath the corpus callosum. It carries ~1.2 million fibers. '
        'Damage to the circuit at any point impairs memory: '
        'Mammillary body damage (thiamine deficiency, chronic alcoholism) → '
        'Wernicke-Korsakoff syndrome (confabulation, anterograde and retrograde amnesia). '
        'Fornix transection → memory impairment similar to hippocampal damage. '
        'The circuit demonstrates that memory is not localized to one structure but depends '
        'on an intact network.',
        22, [10, 19],
    ),

    # === BASAL GANGLIA AND MOTOR SYSTEMS (BG) ===
    (
        'Basal Ganglia: Structures',
        'The basal ganglia are a group of subcortical nuclei involved in motor control, '
        'habit formation, reward learning, and executive function. NOT part of the motor '
        'cortex — they modulate movement by adjusting cortical output via the thalamus. '
        'Key structures: '
        'Striatum — the input nucleus, composed of caudate nucleus and putamen (separated '
        'by the internal capsule but functionally connected). Receives glutamatergic input '
        'from the cortex. Contains medium spiny neurons (MSNs) that are GABAergic. '
        'Nucleus accumbens — ventral striatum, reward and motivation center. '
        'Globus pallidus — external segment (GPe) and internal segment (GPi). GPi is a '
        'major output nucleus. Both are GABAergic. '
        'Subthalamic nucleus (STN) — the only excitatory (glutamatergic) nucleus in the '
        'basal ganglia circuit. '
        'Substantia nigra — pars compacta (SNc, dopaminergic, projects to striatum) and '
        'pars reticulata (SNr, GABAergic output, functionally similar to GPi).',
        23, [6, 9],
    ),
    (
        'Basal Ganglia: Direct and Indirect Pathways',
        'The basal ganglia facilitate wanted movements (direct pathway) and suppress '
        'unwanted movements (indirect pathway). Understanding these pathways explains '
        'Parkinson and Huntington diseases. '
        'Direct pathway (GO): Cortex → striatum (D1 receptors, excitatory effect of dopamine) '
        '→ inhibits GPi/SNr → disinhibits thalamus → thalamus excites cortex → MOVEMENT. '
        'Net effect: cortex activates a movement. '
        'Indirect pathway (STOP): Cortex → striatum (D2 receptors, inhibitory effect of '
        'dopamine) → inhibits GPe → disinhibits STN → STN excites GPi/SNr → GPi/SNr '
        'inhibits thalamus → LESS MOVEMENT. Net effect: cortex suppresses a movement. '
        'Dopamine from SNc modulates both: excites direct (D1, facilitates movement), '
        'inhibits indirect (D2, reduces suppression) — both effects promote movement. '
        'Parkinson disease: loss of SNc dopamine → underactive direct, overactive indirect '
        '→ bradykinesia, rigidity, resting tremor ("pill-rolling"). '
        'Huntington disease: degeneration of indirect pathway MSNs first → chorea '
        '(involuntary jerky movements), then progresses to akinesia as direct pathway dies.',
        24, [22],
    ),
    (
        'Motor Pathways: Corticospinal and Extrapyramidal',
        'Motor commands reach the body via descending pathways. '
        'Corticospinal tract (pyramidal): Primary motor cortex (and premotor, SMA) → '
        'internal capsule (posterior limb) → cerebral peduncle → basis pontis → '
        'medullary pyramids → 90% decussate (lateral corticospinal → contralateral '
        'voluntary movement of limbs) + 10% ipsilateral (anterior corticospinal → '
        'axial/trunk muscles). Upper motor neuron (UMN) lesion signs: spastic paralysis, '
        'hyperreflexia, Babinski sign (upgoing toe), no significant atrophy. '
        'Lower motor neuron (LMN) lesion signs: flaccid paralysis, hyporeflexia, '
        'fasciculations, muscle atrophy. '
        'Extrapyramidal tracts: Rubrospinal (red nucleus — flexor tone), vestibulospinal '
        '(vestibular nuclei — posture/balance), reticulospinal (reticular formation — '
        'posture/locomotion), tectospinal (superior colliculus — head orientation to stimuli). '
        'Decorticate posture (flexion, lesion above red nucleus) vs decerebrate posture '
        '(extension, lesion below red nucleus).',
        25, [8, 14],
    ),

    # === WHITE MATTER AND CONNECTIVITY (WM) ===
    (
        'Corpus Callosum and Commissures',
        'The corpus callosum is the largest white matter structure in the brain, containing '
        '~200 million axons connecting the left and right cerebral hemispheres. It enables '
        'interhemispheric communication. '
        'Parts (anterior to posterior): Rostrum, genu (connects prefrontal regions), body '
        '(connects motor and somatosensory), splenium (connects occipital and temporal — '
        'visual and language areas). '
        'Split-brain patients (callosotomy for epilepsy): left hand doesn\'t know what the '
        'right hand is doing. Objects presented to the left visual field (right hemisphere) '
        'cannot be named (language is in left hemisphere) but can be identified by touch '
        'with the left hand. '
        'Agenesis of the corpus callosum — congenital absence, surprisingly mild symptoms '
        'due to compensatory pathways. '
        'Other commissures: Anterior commissure (connects temporal lobes, olfactory), '
        'posterior commissure (midbrain, pupillary light reflex), hippocampal commissure '
        '(connects hippocampi).',
        26, [12, 13],
    ),
    (
        'Major Association and Projection Tracts',
        'White matter tracts connect brain regions. Three categories: '
        'Association fibers — connect regions within the same hemisphere. '
        'Arcuate fasciculus: connects Broca area (frontal) to Wernicke area (temporal); '
        'damage causes conduction aphasia (intact comprehension and fluency, impaired '
        'repetition). Superior longitudinal fasciculus (SLF): fronto-parietal connections '
        'for attention and spatial awareness. Inferior longitudinal fasciculus (ILF): '
        'occipital-temporal, visual processing. Uncinate fasciculus: frontal-temporal, '
        'emotion regulation. Cingulum: limbic tract beneath cingulate cortex. '
        'Projection fibers — connect cortex to subcortical structures. '
        'Internal capsule — contains corticospinal, corticobulbar, thalamocortical fibers. '
        'Anterior limb: frontopontine, thalamocortical to prefrontal. '
        'Genu: corticobulbar (head/face motor). '
        'Posterior limb: corticospinal (body motor), somatosensory thalamocortical. '
        'Lacunar stroke in internal capsule → pure motor or pure sensory deficit.',
        27, [25, 14],
    ),
    (
        'Lateralization and Hemispheric Specialization',
        'The left and right hemispheres have distinct functional specializations despite '
        'their anatomical similarity. '
        'Left hemisphere (dominant in ~95% of right-handers, ~70% of left-handers): '
        'Language production and comprehension (Broca and Wernicke areas), reading, writing, '
        'calculation, logical/analytical reasoning, sequential processing. '
        'Right hemisphere: Visuospatial processing, face recognition, emotional prosody '
        '(tone of voice), music perception, attention to both visual fields (left hemisphere '
        'only attends to right — explains why right parietal lesions cause left neglect '
        'but left parietal lesions rarely cause right neglect). '
        'Handedness correlates with but does not determine language lateralization. '
        'The Wada test (injecting sodium amobarbital into one carotid) was used pre-surgery '
        'to determine language dominance; now largely replaced by fMRI. '
        'Planum temporale is larger on the left (language areas). '
        'The right hemisphere is better at holistic/gestalt processing; the left is better '
        'at detail-oriented processing.',
        28, [25, 14, 15, 16],
    ),

    # === VENTRICULAR SYSTEM AND VASCULATURE (VV) ===
    (
        'Ventricular System and CSF',
        'The ventricular system is a series of interconnected fluid-filled cavities within '
        'the brain. Cerebrospinal fluid (CSF) is produced by the choroid plexus (modified '
        'ependymal cells) in each ventricle. Total CSF volume: ~150 mL, produced at '
        '~500 mL/day (turned over 3-4 times daily). '
        'Anatomy: Two lateral ventricles (one in each hemisphere, C-shaped with frontal '
        'horn, body, atrium, temporal horn, occipital horn) → interventricular foramen '
        '(of Monro) → third ventricle (between the two halves of the thalamus) → cerebral '
        'aqueduct (of Sylvius, through the midbrain) → fourth ventricle (between pons/'
        'medulla and cerebellum). CSF exits via the foramina of Luschka (lateral, paired) '
        'and foramen of Magendie (midline) into the subarachnoid space. '
        'CSF is reabsorbed by arachnoid granulations into the dural venous sinuses '
        '(particularly the superior sagittal sinus). '
        'Hydrocephalus: excess CSF. Communicating (impaired absorption) vs obstructive/'
        'non-communicating (blockage, e.g., aqueductal stenosis). '
        'CSF functions: cushions brain (buoyancy reduces effective weight from 1,400g to ~50g), '
        'removes metabolic waste, transports hormones.',
        29, [6],
    ),
    (
        'Meninges and Brain Protection',
        'Three membranes (meninges) surround the brain and spinal cord. '
        'From outside in: Dura mater (tough mother) — thick fibrous layer, adheres to '
        'skull. Two layers: periosteal (attached to bone) and meningeal (continues into '
        'spinal cord). Dural folds: falx cerebri (between hemispheres), tentorium cerebelli '
        '(between cerebrum and cerebellum), falx cerebelli. Dural venous sinuses run between '
        'dural layers (superior/inferior sagittal, transverse, sigmoid, cavernous). '
        'Arachnoid mater — web-like, avascular, contains arachnoid granulations. '
        'Subarachnoid space — between arachnoid and pia, filled with CSF, contains major '
        'arteries (circle of Willis). Subarachnoid hemorrhage (ruptured berry aneurysm) → '
        '"worst headache of life," bloody CSF. '
        'Pia mater (gentle mother) — delicate, adheres directly to brain surface, follows '
        'every gyrus and sulcus. '
        'Hemorrhage locations: Epidural (between skull and dura — middle meningeal artery, '
        'lens-shaped on CT, lucid interval). Subdural (between dura and arachnoid — bridging '
        'veins, crescent-shaped on CT, elderly/shaken baby). Subarachnoid — berry aneurysms.',
        30, [28],
    ),
    (
        'Cerebral Blood Supply',
        'The brain receives ~15% of cardiac output and uses ~20% of total oxygen despite '
        'being only ~2% of body weight. Two arterial systems: '
        'Internal carotid arteries (anterior circulation, ~80%): '
        'Anterior cerebral artery (ACA) — medial surface of frontal and parietal lobes, '
        'supplies leg motor/sensory strip. Stroke → contralateral leg weakness. '
        'Middle cerebral artery (MCA) — lateral surface (largest territory), supplies face '
        'and arm motor/sensory, Broca and Wernicke areas. Stroke → contralateral face/arm '
        'weakness, aphasia (if dominant hemisphere). Most common stroke location. '
        'Vertebrobasilar system (posterior circulation, ~20%): '
        'Vertebral arteries merge into basilar artery. '
        'Posterior cerebral artery (PCA) — occipital lobe, visual cortex. '
        'Stroke → contralateral homonymous hemianopia with macular sparing. '
        'PICA (posterior inferior cerebellar artery) — lateral medulla. '
        'Occlusion → Wallenberg syndrome (lateral medullary syndrome). '
        'Circle of Willis: connects anterior and posterior circulations via anterior '
        'communicating artery (AComm — most common aneurysm site) and posterior '
        'communicating arteries (PComm). Provides collateral flow. '
        'Berry aneurysms most common at bifurcations; rupture causes SAH.',
        31, [4, 29],
    ),

    # === FUNCTIONAL SYSTEMS (FS) ===
    (
        'Somatosensory Pathways',
        'Sensory information from the body reaches the cortex via two main pathways. '
        'Dorsal column-medial lemniscus (DCML) pathway — fine touch, vibration, '
        'proprioception, two-point discrimination. Route: peripheral receptor → dorsal '
        'root ganglion → ipsilateral dorsal columns (gracile fasciculus from lower body, '
        'cuneate fasciculus from upper body) → synapse at gracile/cuneate nuclei in medulla '
        '→ internal arcuate fibers decussate → medial lemniscus → VPL of thalamus → S1. '
        'Spinothalamic tract (STT) — pain, temperature, crude touch. Route: peripheral '
        'receptor → dorsal root ganglion → synapse in dorsal horn → decussates in anterior '
        'white commissure (crosses 1-2 levels above entry) → ascends in anterolateral '
        'system → VPL of thalamus → S1. '
        'Key clinical principle: DCML crosses in the medulla; STT crosses in the spinal cord. '
        'Brown-Séquard syndrome (hemisection of spinal cord): ipsilateral loss of DCML '
        '(fine touch, proprioception) + contralateral loss of STT (pain, temperature) below '
        'the lesion.',
        32, [4, 9, 15],
    ),
    (
        'Visual System: Retina to Cortex',
        'Visual processing pathway: Retina → optic nerve (CN II) → optic chiasm → optic '
        'tract → LGN of thalamus → optic radiations → V1 (primary visual cortex). '
        'At the optic chiasm: nasal fibers (from the medial retina, representing the '
        'temporal visual field) cross; temporal fibers (lateral retina, nasal field) do not. '
        'Result: each optic tract carries the contralateral visual field. '
        'Optic radiations: upper fibers (Meyer loop) pass through the temporal lobe → '
        'cuneus (lower visual field). Lower fibers → lingual gyrus (upper visual field). '
        'Visual field defects by lesion location: '
        'Optic nerve → ipsilateral monocular blindness. '
        'Optic chiasm (e.g., pituitary tumor compressing crossing fibers) → bitemporal '
        'hemianopia. Optic tract → contralateral homonymous hemianopia. '
        'Meyer loop (temporal radiation) → contralateral superior quadrantanopia ("pie in '
        'the sky"). Optic radiation (parietal) → contralateral inferior quadrantanopia '
        '("pie on the floor"). V1 → contralateral homonymous hemianopia with macular sparing. '
        'V4 damage → achromatopsia (color blindness). V5/MT damage → akinetopsia (motion blind).',
        33, [9, 17],
    ),
    (
        'Auditory and Vestibular Systems',
        'Auditory pathway: Sound → cochlea (organ of Corti, hair cells) → cochlear nerve '
        '(CN VIII) → cochlear nuclei (pons) → BILATERAL projections (unlike other senses). '
        'Route: cochlear nuclei → superior olivary complex (first bilateral integration, '
        'sound localization) → lateral lemniscus → inferior colliculus (midbrain) → MGN of '
        'thalamus → A1 (Heschl gyrus, primary auditory cortex). '
        'Because of bilateral projections, unilateral lesions above the cochlear nuclei '
        'do NOT cause deafness in one ear. Unilateral deafness = lesion at ear, CN VIII, '
        'or cochlear nuclei. '
        'Tonotopic organization: frequency maps maintained from cochlea to cortex. '
        'Vestibular system: semicircular canals (angular acceleration), utricle and saccule '
        '(linear acceleration and gravity). Vestibular nerve (CN VIII) → vestibular nuclei '
        '(pons/medulla) → connections to cerebellum (flocculonodular lobe), ocular motor '
        'nuclei (vestibulo-ocular reflex — stabilizes gaze during head movement), and '
        'spinal cord (vestibulospinal tract — balance/posture). '
        'Damage: vertigo, nystagmus, nausea, imbalance.',
        34, [5, 9],
    ),
    (
        'Brain Networks: Default Mode, Salience, and Executive',
        'Modern neuroscience views brain function as emerging from large-scale networks '
        'of interconnected regions rather than isolated areas. Three major networks: '
        'Default Mode Network (DMN) — active at rest, during introspection, '
        'autobiographical memory, future planning, and mind-wandering. Key nodes: medial '
        'prefrontal cortex (mPFC), posterior cingulate cortex (PCC)/precuneus, angular '
        'gyrus, hippocampus, lateral temporal cortex. Deactivates during focused tasks. '
        'Abnormal DMN activity in Alzheimer disease, depression, and autism. '
        'Salience Network (SN) — detects behaviorally relevant stimuli and switches between '
        'DMN and CEN. Key nodes: anterior insula, dorsal anterior cingulate cortex (dACC). '
        'Acts as a switch operator. Dysfunctional in anxiety, psychosis, and chronic pain. '
        'Central Executive Network (CEN) — goal-directed attention, working memory, '
        'decision-making. Key nodes: dorsolateral prefrontal cortex (dlPFC), posterior '
        'parietal cortex. Active during demanding cognitive tasks. '
        'The salience network detects something important → suppresses DMN → activates CEN '
        '→ focused attention. This dynamic switching is disrupted in many psychiatric and '
        'neurological disorders.',
        35, [14, 15, 17, 18, 20],
    ),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()

    # Create the topic
    cur.execute(
        'INSERT INTO topics (name, description) VALUES (?, ?)',
        (TOPIC_NAME, TOPIC_DESC),
    )
    topic_id = cur.lastrowid
    print(f'Created topic "{TOPIC_NAME}" with id={topic_id}')

    # Insert curriculum nodes
    node_ids = []
    for name, desc, order, _prereqs in NODES:
        cur.execute(
            '''INSERT INTO curriculum_nodes
               (topic_id, name, description, order_index, prerequisites, mastery_threshold)
               VALUES (?, ?, ?, ?, '[]', 0.75)''',
            (topic_id, name, desc, order),
        )
        node_ids.append(cur.lastrowid)

    # Resolve prerequisites (indices → actual DB IDs)
    for i, (name, desc, order, prereq_indices) in enumerate(NODES):
        if prereq_indices:
            prereq_ids = [node_ids[pi] for pi in prereq_indices]
            cur.execute(
                'UPDATE curriculum_nodes SET prerequisites=? WHERE id=?',
                (json.dumps(prereq_ids), node_ids[i]),
            )

    conn.commit()
    conn.close()

    # Pretty print the curriculum
    domains = {
        (1, 4): 'CF',   # Cellular Foundations
        (5, 9): 'BS',   # Brainstem & Cerebellum
        (10, 12): 'DI',  # Diencephalon
        (13, 18): 'CX',  # Cerebral Cortex
        (19, 22): 'LS',  # Limbic System
        (23, 25): 'BG',  # Basal Ganglia & Motor
        (26, 28): 'WM',  # White Matter
        (29, 31): 'VV',  # Ventricular & Vascular
        (32, 35): 'FS',  # Functional Systems
    }

    print(f'\nInserted {len(NODES)} curriculum nodes for "{TOPIC_NAME}":')
    for i, (name, desc, order, prereqs) in enumerate(NODES):
        prereq_names = [NODES[p][0] for p in prereqs] if prereqs else []
        domain = '??'
        for (lo, hi), d in domains.items():
            if lo <= order <= hi:
                domain = d
                break
        prereq_str = f' (prereqs: {", ".join(prereq_names)})' if prereq_names else ''
        print(f'  [{domain}] {order:2d}. {name}{prereq_str}')


if __name__ == '__main__':
    main()
