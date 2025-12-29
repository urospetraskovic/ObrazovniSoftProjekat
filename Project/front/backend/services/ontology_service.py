"""
Ontology Export Utilities
Functions for generating OWL and Turtle format ontologies from lesson relationships
"""

import html
import re


def generate_owl_from_relationships(lesson, relationships):
    """
    Generate OWL/RDF-XML ontology with VISUAL RELATIONSHIPS for Protégé OntoGraf.
    
    This creates an ontology that displays properly in Protégé with:
    - Named individuals for each concept
    - Object properties for relationship types (part_of, is_type_of, prerequisite, etc.)
    - ObjectPropertyAssertions that create the visual edges in OntoGraf
    - Proper labels and annotations for readability
    
    To view relationships in Protégé:
    1. Open the OWL file in Protégé Desktop
    2. Go to Window → Tabs → OntoGraf (or OWLViz)
    3. In OntoGraf, click the filter icon and enable "Object Property Assertions"
    4. You'll see the relationship lines between concepts
    """
    
    def escape_xml(text):
        if not text:
            return ""
        return html.escape(str(text), quote=True)
    
    def make_id(text):
        if not text:
            return "Unknown"
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', str(text))
        if cleaned and cleaned[0].isdigit():
            cleaned = 'C_' + cleaned
        return cleaned or "Unknown"
    
    def normalize_rel_type(rel_type):
        """Normalize relationship type to valid property name"""
        if not rel_type:
            return 'relatedTo'
        # Convert to camelCase for standard OWL naming
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', str(rel_type).lower().strip())
        # Map common variations to standard names
        mappings = {
            'builds_upon': 'buildsUpon',
            'buildsupon': 'buildsUpon',
            'part_of': 'isPartOf',
            'partof': 'isPartOf',
            'is_part_of': 'isPartOf',
            'related_to': 'relatedTo',
            'relatedto': 'relatedTo',
            'contrasts_with': 'contrastsWith',
            'contrastswith': 'contrastsWith',
            'is_example_of': 'isExampleOf',
            'isexampleof': 'isExampleOf',
            'example_of': 'isExampleOf',
            'is_type_of': 'isTypeOf',
            'istypeof': 'isTypeOf',
            'type_of': 'isTypeOf',
            'prerequisite': 'hasPrerequisite',
            'prerequisite_for': 'isPrerequisiteFor',
            'enables': 'enables',
            'implements': 'implements',
            'defines': 'defines',
            'depends_on': 'dependsOn',
            'has_component': 'hasComponent',
            'uses': 'uses',
        }
        return mappings.get(normalized, normalized)
    
    def get_property_label(prop_id):
        """Get human-readable label for property"""
        labels = {
            'buildsUpon': 'builds upon',
            'isPartOf': 'is part of',
            'relatedTo': 'related to',
            'contrastsWith': 'contrasts with',
            'isExampleOf': 'is example of',
            'isTypeOf': 'is type of',
            'hasPrerequisite': 'has prerequisite',
            'isPrerequisiteFor': 'is prerequisite for',
            'enables': 'enables',
            'implements': 'implements',
            'defines': 'defines',
            'dependsOn': 'depends on',
            'hasComponent': 'has component',
            'uses': 'uses',
        }
        return labels.get(prop_id, prop_id.replace('_', ' '))
    
    lesson_title = make_id(lesson.get('title', f"Lesson_{lesson.get('id')}"))
    lesson_id = lesson.get('id', 'unknown')
    ontology_iri = f"http://example.org/educational-ontology/{lesson_title}"
    
    # ============= COLLECT CONCEPTS AND RELATIONSHIPS =============
    relationship_concepts = set()
    used_rel_types = set()
    processed_relationships = []
    
    for rel in relationships:
        if not rel:
            continue
        source = rel.get('source_title') or rel.get('source', '')
        target = rel.get('target_title') or rel.get('target', '')
        rel_type = normalize_rel_type(rel.get('relationship_type', 'relatedTo'))
        
        if source and target:
            relationship_concepts.add(source)
            relationship_concepts.add(target)
            used_rel_types.add(rel_type)
            processed_relationships.append({
                'source': source,
                'source_id': make_id(source),
                'target': target,
                'target_id': make_id(target),
                'rel_type': rel_type
            })
    
    # ============= BUILD OWL/XML =============
    owl = '<?xml version="1.0"?>\n'
    owl += f'''<Ontology xmlns="http://www.w3.org/2002/07/owl#"
     xml:base="{ontology_iri}"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     ontologyIRI="{ontology_iri}">
    
    <!-- Prefixes -->
    <Prefix name="" IRI="http://www.w3.org/2002/07/owl#"/>
    <Prefix name="owl" IRI="http://www.w3.org/2002/07/owl#"/>
    <Prefix name="rdf" IRI="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>
    <Prefix name="xml" IRI="http://www.w3.org/XML/1998/namespace"/>
    <Prefix name="xsd" IRI="http://www.w3.org/2001/XMLSchema#"/>
    <Prefix name="rdfs" IRI="http://www.w3.org/2000/01/rdf-schema#"/>
    <Prefix name="edu" IRI="{ontology_iri}#"/>

'''
    
    # ============= DECLARATIONS =============
    
    # Base class for all learning concepts
    owl += '    <!-- Base Class -->\n'
    owl += '    <Declaration>\n        <Class IRI="#LearningConcept"/>\n    </Declaration>\n\n'
    
    # Object property declarations with labels
    owl += '    <!-- Object Property Declarations (Relationship Types) -->\n'
    
    # Always include core relationship types
    core_props = {'hasPrerequisite', 'isPrerequisiteFor', 'buildsUpon', 'isPartOf', 
                  'relatedTo', 'contrastsWith', 'isExampleOf', 'isTypeOf',
                  'enables', 'implements', 'defines', 'dependsOn', 'hasComponent', 'uses'}
    all_props = core_props.union(used_rel_types)
    
    for prop in sorted(all_props):
        owl += f'    <Declaration>\n        <ObjectProperty IRI="#{prop}"/>\n    </Declaration>\n'
    
    # Named individuals (one per concept)
    owl += '\n    <!-- Named Individual Declarations (Concepts) -->\n'
    for concept_title in sorted(relationship_concepts):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'    <Declaration>\n        <NamedIndividual IRI="#{concept_id}"/>\n    </Declaration>\n'
    
    # ============= CLASS ASSERTIONS =============
    # Each individual is an instance of LearningConcept
    owl += '\n    <!-- Class Assertions (Each concept is a LearningConcept) -->\n'
    for concept_title in sorted(relationship_concepts):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'''    <ClassAssertion>
        <Class IRI="#LearningConcept"/>
        <NamedIndividual IRI="#{concept_id}"/>
    </ClassAssertion>
'''
    
    # ============= OBJECT PROPERTY ASSERTIONS (THE VISUAL RELATIONSHIPS!) =============
    owl += '\n    <!-- =========================================================== -->\n'
    owl += '    <!-- OBJECT PROPERTY ASSERTIONS - These create the visual edges! -->\n'
    owl += '    <!-- In Protégé OntoGraf: Enable "Object Property Assertions" filter -->\n'
    owl += '    <!-- =========================================================== -->\n\n'
    
    for rel in processed_relationships:
        owl += f'''    <ObjectPropertyAssertion>
        <ObjectProperty IRI="#{rel['rel_type']}"/>
        <NamedIndividual IRI="#{rel['source_id']}"/>
        <NamedIndividual IRI="#{rel['target_id']}"/>
    </ObjectPropertyAssertion>
'''
    
    # ============= ANNOTATIONS FOR READABILITY =============
    owl += '\n    <!-- Annotations - Human-readable labels -->\n'
    
    # Label the base class
    owl += '''    <AnnotationAssertion>
        <AnnotationProperty abbreviatedIRI="rdfs:label"/>
        <IRI>#LearningConcept</IRI>
        <Literal>Learning Concept</Literal>
    </AnnotationAssertion>
'''
    
    # Labels for object properties
    owl += '\n    <!-- Property Labels -->\n'
    for prop in sorted(all_props):
        label = get_property_label(prop)
        owl += f'''    <AnnotationAssertion>
        <AnnotationProperty abbreviatedIRI="rdfs:label"/>
        <IRI>#{prop}</IRI>
        <Literal>{escape_xml(label)}</Literal>
    </AnnotationAssertion>
'''
    
    # Labels for individuals (concepts)
    owl += '\n    <!-- Concept Labels -->\n'
    for concept_title in sorted(relationship_concepts):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'''    <AnnotationAssertion>
        <AnnotationProperty abbreviatedIRI="rdfs:label"/>
        <IRI>#{concept_id}</IRI>
        <Literal>{escape_xml(concept_title)}</Literal>
    </AnnotationAssertion>
'''
    
    owl += '''
</Ontology>

<!-- 
Generated by Educational Ontology Generator
============================================

HOW TO VIEW RELATIONSHIPS IN PROTÉGÉ:
1. Open this file in Protégé Desktop
2. Go to Window → Tabs → OntoGraf
3. In OntoGraf, click the wrench/settings icon
4. Under "Relationships to Display", check:
   - Object Property Assertions
   - All your relationship types (isPartOf, hasPrerequisite, etc.)
5. Click on an individual to see its connections
6. Use "Navigate to Entity" to center on specific concepts

ALTERNATIVE: Use the "Individuals by class" tab and select 
an individual to see its Object Property Assertions in the 
Description pane.
-->
'''
    
    return owl


def generate_turtle_from_relationships(lesson, relationships):
    """Generate Turtle format from relationships"""
    lesson_title = lesson.get('title', f"Lesson_{lesson.get('id')}").replace(' ', '_')
    
    turtle = f"""# Turtle format ontology for {lesson.get('title', 'Lesson')}
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/educational-ontology/{lesson_title}#> .
@base <http://example.org/educational-ontology/{lesson_title}/> .

# Ontology metadata
<> a owl:Ontology ;
    rdfs:label "Educational Ontology for {lesson.get('title', 'Lesson')}" ;
    rdfs:comment "Domain ontology extracted from lesson content" .

"""
    
    # Track unique concepts
    concepts = set()
    for rel in relationships:
        concepts.add(rel.get('source', ''))
        concepts.add(rel.get('target', ''))
    
    # Add class definitions
    for concept in sorted(concepts):
        if concept:
            turtle += f"""# Learning object/concept
ex:Concept_{concept.replace(' ', '_')} a owl:Class ;
    rdfs:label "{concept}" .

"""
    
    # Add relationships
    for rel in relationships:
        source = rel.get('source', '').replace(' ', '_')
        target = rel.get('target', '').replace(' ', '_')
        rel_type = rel.get('type', 'related')
        description = rel.get('description', '')
        
        turtle += f"""# Relationship
ex:Concept_{source} ex:{rel_type} ex:Concept_{target} ;
    rdfs:comment "{description}" .

"""
    
    return turtle
