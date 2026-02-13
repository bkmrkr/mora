"""Generate a structured curriculum for any topic via Ollama."""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert curriculum designer. Given a topic, create a
structured learning curriculum with 8-12 nodes ordered from foundational to advanced.

Return ONLY valid JSON in this exact format:
{
  "topic_description": "Brief description of the overall topic",
  "nodes": [
    {
      "name": "Node Name",
      "description": "What this node covers",
      "order_index": 1,
      "prerequisites": [],
      "mastery_threshold": 0.75
    }
  ]
}

Rules:
1. Order from most fundamental to most advanced.
2. Prerequisites reference node names (not indices).
3. Early nodes should have no prerequisites.
4. Each node should be a focused, testable concept.
5. Cover breadth: mix foundational, intermediate, and advanced concepts.
6. Descriptions should be detailed enough to generate questions from.
7. Return ONLY the JSON, no other text."""


def generate_curriculum(topic_name):
    """Generate curriculum nodes for a topic.

    Returns (topic_description, list_of_node_dicts, model_used, prompt_used).
    """
    user_prompt = f"Create a learning curriculum for: {topic_name}"
    response_text, model, prompt = ask(SYSTEM_PROMPT, user_prompt, max_tokens=2048)
    data = parse_ai_json(response_text)

    nodes = data.get('nodes', [])
    node_names = [n['name'] for n in nodes]

    # Resolve prerequisite names to indices
    for node in nodes:
        resolved = []
        for prereq_name in node.get('prerequisites', []):
            if prereq_name in node_names:
                resolved.append(node_names.index(prereq_name))
        node['prerequisite_indices'] = resolved

    logger.info('Generated curriculum for "%s": %d nodes', topic_name, len(nodes))
    return data.get('topic_description', ''), nodes, model, prompt
