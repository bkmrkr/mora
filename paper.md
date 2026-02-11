# Mora: Integrating Established Learning Science with LLM-Driven Adaptive Instruction

**Greg Gurevich**
February 2026

---

## Abstract

Mora is an adaptive learning system that uses a locally-hosted large language model (LLM) to generate curricula, produce assessment items, grade responses, and dynamically adjust difficulty — all without pre-authored content. This paper situates Mora's design within the educational research literature, identifying which components rest on well-established cognitive science and which represent genuinely novel contributions. We argue that Mora's primary innovation is not any single technique but the integration architecture: a unified LLM-driven pipeline that operationalizes decades of learning science research without requiring human-authored item banks, fixed curricula, or centralized infrastructure.

## 1. Established Foundations

Mora's pedagogical design draws on four pillars of learning science, each supported by decades of empirical evidence.

**Retrieval practice.** The testing effect — the finding that actively retrieving information from memory produces stronger long-term retention than passive re-study — is among the most replicated results in cognitive psychology. Roediger and Karpicke (2006) demonstrated that students who took practice tests retained significantly more material than those who spent equivalent time re-reading, even without feedback. A meta-analysis by Rowland (2014) confirmed a medium effect size (*g* = 0.50) across hundreds of studies. Karpicke and Blunt (2011), published in *Science*, showed that retrieval practice outperformed concept mapping for both recall and inference. Mora's core interaction loop — presenting questions and requiring active responses before revealing answers — is a direct implementation of retrieval practice.

**Spaced repetition.** Ebbinghaus (1885) first documented the forgetting curve and the spacing effect: distributing practice across time improves retention compared to massed study. Cepeda et al. (2006) confirmed this in a quantitative synthesis across verbal recall tasks. The SM-2 algorithm (Wozniak, 1987), which underpins Anki and Mnemosyne, formalized adaptive review scheduling. More recently, FSRS (Ye, 2022–2024) applies machine learning to personalize scheduling, reducing required reviews by 20–30%. Mora does not implement calendar-based review intervals like traditional SRS. Instead, it uses a recent-history window (last 30 attempts) and ELO-based skill tracking to achieve a functionally similar effect: weak topics resurface naturally through the next-question selection algorithm, while mastered topics recede.

**Mastery learning.** Bloom (1968, 1984) proposed that students should demonstrate proficiency in prerequisite material before advancing, reporting that one-on-one tutoring with mastery requirements produced a two-standard-deviation improvement over conventional instruction. While subsequent reviews have tempered this estimate — VanLehn (2011) found roughly *d* = 0.79 for human tutoring, and a systematic review by Ricarte (2019) suggested the original claim was overstated — the core principle remains widely endorsed. Khan Academy, Carnegie Learning's Cognitive Tutors, and Math Academy all implement mastery gates. Mora enforces mastery through prerequisite-aware sequencing: the next-question engine automatically falls back to prerequisite nodes when a student's accuracy on the current node drops below 60%, and advances only when mastery (a blend of ELO rating and recent accuracy) exceeds 0.75.

**Zone of proximal development.** Vygotsky (1978) described the ZPD as the space between what a learner can do independently and what they can achieve with guidance. Wood, Bruner, and Ross (1976) operationalized this as "scaffolding" — temporary support that fades as competence grows. Mora operationalizes the ZPD quantitatively: question difficulty is calibrated so the learner has an estimated 80% probability of success, keeping every question in a narrow band that is challenging but achievable. Furthermore, question format scaffolds from multiple-choice (below 0.3 mastery) to short-answer (0.3–0.6) to open-ended problems (above 0.6), progressively removing structural support as competence increases.

## 2. Moderately Established Components

**Adaptive learning and knowledge tracing.** Corbett and Anderson (1995) introduced Bayesian Knowledge Tracing (BKT), modeling learning as a hidden Markov process with binary mastery states per skill. Carnegie Learning's Cognitive Tutors, built on BKT and the ACT-R architecture, produced roughly one standard deviation of improvement in deployed studies. Piech et al. (2015) introduced deep knowledge tracing using recurrent neural networks. Mora takes a different approach: rather than BKT's binary hidden states, it uses a continuous ELO rating with Bayesian uncertainty decay. The K-factor (learning rate) starts large when uncertainty is high and shrinks as the system gains confidence, producing behavior similar to BKT's transition from "unlearned" to "learned" but on a continuous scale. This is a known technique in rating systems but a less common choice in educational software.

**Microlearning.** Research supports delivering content in focused 5–15 minute sessions targeting single objectives (Shail, 2024; Leong et al., 2021), with evidence that bite-sized modules improve retention by approximately 20% over extended sessions. Mora's session structure — open-ended but focused on a single topic with one question at a time — aligns with microlearning principles, though sessions have no fixed time limit.

## 3. Novel Contributions

**LLM-generated curricula.** When a student enters any topic, Mora calls a local LLM to generate a structured 8–12 node curriculum with prerequisite relationships, ordered from foundational to advanced concepts. While automatic question generation (AQG) has a growing literature — Elkins et al. (2024), Moore et al. (2024), and a 2025 AIED study found LLM-generated MCQs approaching human parity in psychometric quality — automatic *curriculum* generation (topic sequencing, prerequisite specification, scope decisions) has minimal peer-reviewed validation. This is among Mora's most speculative design choices and its most distinctive feature.

**LLM-generated assessment items calibrated to ELO difficulty.** Mora does not draw from a pre-authored item bank. Each question is generated on-the-fly by the LLM, targeted to a specific ELO difficulty (normalized to a 0–1 scale for the prompt). A self-calibrating feedback loop adjusts the target: if recent accuracy exceeds 80%, difficulty rises; if it falls below, difficulty drops. Post-generation, a 12-rule validator catches common LLM failure modes (hallucinated answers, answer giveaways, biased distractor lengths, placeholder text). While LLM-based question generation is an active research area, the closed-loop integration with ELO-calibrated difficulty targeting and automated quality gating is, to our knowledge, not described in prior published systems.

**Three-layer deduplication.** Mora prevents question repetition at three levels: within-session (never repeat a question), lifetime (never re-ask a correctly answered question), and prompt-level (exclusion lists passed to the LLM). This addresses a practical problem unique to generative systems — the LLM's tendency to produce similar questions — that does not arise in fixed item banks.

**Fully offline, single-LLM architecture.** Unlike cloud-dependent adaptive platforms, Mora runs entirely on a local Ollama instance with SQLite storage. A single LLM serves four distinct functions: curriculum generation, question generation, open-ended answer grading, and feedback/explanation generation. This collapses what would traditionally require separate authored databases, psychometric calibration studies, and expert-written feedback into a single generative model. The privacy and accessibility implications are significant, though the quality ceiling is bounded by the local model's capabilities.

## 4. What Remains Unvalidated

Mora's design synthesizes well-established principles, but several assumptions lack direct empirical support. The 80% target success rate, while grounded in ZPD theory, has no precise consensus value in the literature — some researchers suggest 85% (Bjork, 1994), others lower. The ELO rating system is well-validated for competitive ranking but less studied as a mastery estimator in education. The quality and pedagogical alignment of LLM-generated curricula have not been systematically evaluated. And the 12-rule validator, while practically motivated, represents engineering heuristics rather than empirically derived quality criteria.

## 5. Conclusion

Mora's individual components — retrieval practice, mastery gating, difficulty scaffolding, adaptive sequencing — are backed by robust cognitive science with effect sizes ranging from *d* = 0.5 to *d* = 1.0. What is genuinely new is the integration: a single locally-hosted LLM simultaneously generates the curriculum, produces the assessments, estimates mastery, and delivers feedback, eliminating the traditional dependency on pre-authored content. This architecture makes it possible to deliver evidence-based adaptive instruction on *any topic* without human content authoring — a capability that, if validated, addresses Bloom's two-sigma problem not through tutoring labor but through generative AI. The established science provides the pedagogical foundation; the LLM provides the engine that makes it practical.

## References

Bloom, B.S. (1984). The 2 sigma problem. *Educational Researcher*, 13(6), 4–16.
Cepeda, N.J. et al. (2006). Distributed practice in verbal recall tasks. *Psychological Bulletin*, 132(3), 354–380.
Corbett, A.T. & Anderson, J.R. (1995). Knowledge tracing. *User Modeling and User-Adapted Interaction*, 5(4), 253–278.
Elkins, S. et al. (2024). Analysis of LLMs for educational question classification and generation. *Computers and Education: AI*, 7, 100290.
Karpicke, J.D. & Blunt, J.R. (2011). Retrieval practice produces more learning than elaborative studying. *Science*, 331(6018), 772–775.
Karpicke, J.D. & Roediger, H.L. (2007). Repeated retrieval during learning. *Journal of Memory and Language*, 57(2), 151–162.
Moore, S. et al. (2024). Can LLMs generate school-level questions? *Computers and Education: AI*, 8, 100315.
Piech, C. et al. (2015). Deep knowledge tracing. *Advances in Neural Information Processing Systems*, 28.
Roediger, H.L. & Karpicke, J.D. (2006). The power of testing memory. *Perspectives on Psychological Science*, 1(3), 181–210.
Rowland, C.A. (2014). The effect of testing versus restudy on retention. *Psychological Bulletin*, 140(6), 1432–1463.
Shail, M.S. (2024). Microlearning beyond boundaries. *Heliyon*, 10(20), e39243.
VanLehn, K. (2011). The relative effectiveness of human tutoring and ITS. *Educational Psychologist*, 46(4), 197–221.
Vygotsky, L.S. (1978). *Mind in Society*. Harvard University Press.
Wood, D., Bruner, J.S. & Ross, G. (1976). The role of tutoring in problem solving. *Journal of Child Psychology and Psychiatry*, 17(2), 89–100.
