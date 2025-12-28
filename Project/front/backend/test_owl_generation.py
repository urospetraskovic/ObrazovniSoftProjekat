#!/usr/bin/env python3
"""
Test OWL generation to verify it creates structured ontologies with axioms
"""

import json
from app import generate_owl_from_relationships

# Test 1: Minimal case - no relationships
print("=" * 70)
print("TEST 1: OWL Generation with NO relationships (should use fallback)")
print("=" * 70)

lesson_minimal = {
    'id': 1,
    'title': 'Test Lesson Minimal'
}

# Simulate database calls that return concepts
class MockDB:
    @staticmethod
    def get_sections_for_lesson(lesson_id):
        return [
            {'id': 1, 'title': 'Introduction'},
            {'id': 2, 'title': 'Main Concepts'},
        ]
    
    @staticmethod
    def get_learning_objects_for_section(section_id):
        if section_id == 1:
            return [
                {
                    'id': 1,
                    'title': 'Concept Definition',
                    'object_type': 'definition',
                    'description': 'What is a concept?',
                    'keywords': ['definition', 'concept']
                },
                {
                    'id': 2,
                    'title': 'Example Application',
                    'object_type': 'example',
                    'description': 'How to apply concepts',
                    'keywords': ['example', 'application']
                }
            ]
        else:
            return [
                {
                    'id': 3,
                    'title': 'Advanced Technique',
                    'object_type': 'procedure',
                    'description': 'Complex method for using concepts',
                    'keywords': ['technique', 'procedure']
                },
                {
                    'id': 4,
                    'title': 'Theoretical Framework',
                    'object_type': 'theory',
                    'description': 'Underlying theory',
                    'keywords': ['theory', 'framework']
                }
            ]

# Monkey-patch the database for this test
import app
original_db = None
try:
    from database import db as real_db
    original_db = real_db
    app.db = MockDB()
except:
    pass

# Generate OWL with NO relationships
owl_content_no_rels = generate_owl_from_relationships(lesson_minimal, [])

print("\n--- Generated OWL (first 2000 chars) ---")
print(owl_content_no_rels[:2000])
print("\n--- Checking for axioms ---")

# Check for axioms
has_subclass = 'SubClassOf' in owl_content_no_rels
has_class_assertion = 'ClassAssertion' in owl_content_no_rels
has_object_property = 'ObjectPropertyAssertion' in owl_content_no_rels
has_data_property = 'DataPropertyAssertion' in owl_content_no_rels
has_individuals = 'NamedIndividual' in owl_content_no_rels

print(f"✓ SubClassOf axioms: {has_subclass}")
print(f"✓ ClassAssertion axioms: {has_class_assertion}")
print(f"✓ ObjectPropertyAssertion axioms: {has_object_property}")
print(f"✓ DataPropertyAssertion axioms: {has_data_property}")
print(f"✓ NamedIndividuals: {has_individuals}")

# Count axioms
subclass_count = owl_content_no_rels.count('SubClassOf')
class_assertion_count = owl_content_no_rels.count('ClassAssertion')
object_prop_count = owl_content_no_rels.count('ObjectPropertyAssertion')
data_prop_count = owl_content_no_rels.count('DataPropertyAssertion')
individual_count = owl_content_no_rels.count('NamedIndividual')

print(f"\n--- Axiom Counts ---")
print(f"SubClassOf: {subclass_count}")
print(f"ClassAssertion: {class_assertion_count}")
print(f"ObjectPropertyAssertion: {object_prop_count}")
print(f"DataPropertyAssertion: {data_prop_count}")
print(f"NamedIndividuals: {individual_count}")

test1_pass = (has_subclass and has_class_assertion and has_object_property and 
              has_data_property and has_individuals and subclass_count > 0)
print(f"\n✅ TEST 1 PASSED!" if test1_pass else "\n❌ TEST 1 FAILED!")

# Test 2: With some relationships
print("\n\n" + "=" * 70)
print("TEST 2: OWL Generation WITH relationships")
print("=" * 70)

relationships_test = [
    {
        'id': 1,
        'source_id': 1,
        'target_id': 3,
        'source_title': 'Concept Definition',
        'target_title': 'Advanced Technique',
        'relationship_type': 'prerequisite',
        'description': 'Definition must be understood first'
    },
    {
        'id': 2,
        'source_id': 2,
        'target_id': 4,
        'source_title': 'Example Application',
        'target_title': 'Theoretical Framework',
        'relationship_type': 'related_to',
        'description': 'Examples apply the theory'
    }
]

owl_content_with_rels = generate_owl_from_relationships(lesson_minimal, relationships_test)

print("\n--- Checking for axioms ---")
has_user_relationships = 'prerequisite' in owl_content_with_rels and 'related_to' in owl_content_with_rels

print(f"✓ Has prerequisite relationship: {'prerequisite' in owl_content_with_rels}")
print(f"✓ Has related_to relationship: {'related_to' in owl_content_with_rels}")
print(f"✓ Has ObjectPropertyAssertion: {'ObjectPropertyAssertion' in owl_content_with_rels}")

object_prop_count_with_rels = owl_content_with_rels.count('ObjectPropertyAssertion')
print(f"\nObjectPropertyAssertion count: {object_prop_count_with_rels}")

test2_pass = has_user_relationships and object_prop_count_with_rels > 0
print(f"\n✅ TEST 2 PASSED!" if test2_pass else "\n❌ TEST 2 FAILED!")

# Summary
print("\n\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"TEST 1 (No relationships -> Fallback): {'✅ PASS' if test1_pass else '❌ FAIL'}")
print(f"TEST 2 (With relationships): {'✅ PASS' if test2_pass else '❌ FAIL'}")
print(f"\nOVERALL: {'✅ ALL TESTS PASSED!' if (test1_pass and test2_pass) else '❌ SOME TESTS FAILED'}")

# Save a sample OWL file for inspection
with open('sample_generated_ontology.owl', 'w') as f:
    f.write(owl_content_with_rels)
print(f"\nSample OWL file saved to: sample_generated_ontology.owl")
print(f"Open this in Protégé to verify structure is visible!")

# Restore original database
if original_db:
    app.db = original_db
