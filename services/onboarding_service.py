"""Student creation and curriculum generation."""
import json
import logging

from models import student as student_model
from models import topic as topic_model
from models import curriculum_node as node_model
from ai import curriculum_generator

logger = logging.getLogger(__name__)


def onboard(student_name, topic_name):
    """Create student (if needed) + topic + curriculum via Ollama.

    Returns (student, topic, nodes).
    """
    # Get or create student
    student = student_model.get_by_name(student_name)
    if not student:
        sid = student_model.create(student_name)
        student = student_model.get_by_id(sid)

    # Get or create topic
    topic = topic_model.get_by_name(topic_name)
    if not topic:
        description, nodes_data, model, prompt = \
            curriculum_generator.generate_curriculum(topic_name)
        tid = topic_model.create(topic_name, description)
        topic = topic_model.get_by_id(tid)

        # Create curriculum nodes, resolving prerequisite names to IDs
        created_ids = []
        for node in nodes_data:
            prereq_ids = [
                created_ids[i]
                for i in node.get('prerequisite_indices', [])
                if i < len(created_ids)
            ]
            nid = node_model.create(
                topic_id=tid,
                name=node['name'],
                description=node.get('description', ''),
                order_index=node.get('order_index', 0),
                prerequisites=json.dumps(prereq_ids),
                mastery_threshold=node.get('mastery_threshold', 0.75),
            )
            created_ids.append(nid)

        logger.info('Created curriculum for "%s": %d nodes via %s',
                     topic_name, len(created_ids), model)

    nodes = node_model.get_for_topic(topic['id'])
    return student, topic, nodes
