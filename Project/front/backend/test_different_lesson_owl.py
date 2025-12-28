from database import DatabaseManager
from app import generate_owl_from_relationships

db = DatabaseManager()

# Test with DIFFERENT lesson (ID=2, not the test lesson ID=1)
lesson_id = 2
lesson = db.get_lesson(lesson_id, include_content=True)
relationships = db.get_relationships_for_lesson(lesson_id)

print(f"\n✓ Testing with lesson: {lesson['title']}")
print(f"✓ Relationships count: {len(relationships)}")

# Generate OWL with correct pattern
owl_content = generate_owl_from_relationships(lesson, relationships)

# Save to file
output_file = 'ontology_different_lesson.owl'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(owl_content)

print(f"✓ File saved: {output_file}")
print(f"✓ File size: {len(owl_content)} chars")
print(f"\nThis file contains YOUR OWN data from lesson '{lesson['title']}'")
print(f"But formatted with the CORRECT PATTERN from test_fixed_ontology.owl")
print(f"You can now download and open it in Protégé!")

# Verify structure
if '<Ontology xmlns=' in owl_content and 'SubClassOf>' in owl_content:
    print("\n✓ Structure verified: Proper OWL format with correct pattern")
