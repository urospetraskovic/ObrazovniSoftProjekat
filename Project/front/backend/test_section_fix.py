import sys
sys.path.insert(0, '.')
from database import db, Lesson
from app import generate_owl_from_relationships

# Get session
session = db.get_session()

# Query for lesson ORM object first to get ID
lesson_orm = session.query(Lesson).filter_by(title='03 - Procesi').first()
session.close()

if lesson_orm:
    print(f"✓ Found lesson: {lesson_orm.title}")
    
    # Now use db methods which return dicts
    lesson = db.get_lesson(lesson_orm.id)
    relationships = db.get_relationships_for_lesson(lesson_orm.id)
    
    print(f"✓ Relationships count: {len(relationships)}")
    
    owl_content = generate_owl_from_relationships(lesson, relationships)
    
    # Count sections and concepts
    sections = owl_content.count('_Section_inst')
    concepts = owl_content.count('Concept_inst')
    
    print(f"✓ Section instance declarations: {sections}")
    print(f"✓ Concept instance declarations: {concepts}")
    print(f"✓ Total file size: {len(owl_content)} chars")
    
    # Verify structure
    has_subclass = '<SubClassOf>' in owl_content
    has_class_assert = '<ClassAssertion>' in owl_content
    has_prop_assert = '<ObjectPropertyAssertion>' in owl_content
    
    print(f"✓ Has SubClassOf axioms: {has_subclass}")
    print(f"✓ Has ClassAssertion axioms: {has_class_assert}")
    print(f"✓ Has ObjectPropertyAssertion axioms: {has_prop_assert}")
    
    with open('test_fixed_ontology.owl', 'w', encoding='utf-8') as f:
        f.write(owl_content)
    print(f"\n✓ Fixed OWL file saved successfully!")
    print(f"✓ Open in Protégé to verify structure displays correctly")
else:
    print("✗ Lesson not found")
