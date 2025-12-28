def generate_owl_from_relationships(lesson, relationships):
    """
    Generate OWL/RDF-XML following the EXACT template pattern from the working example.
    CRITICAL: Order is - XML → Ontology → Prefixes → Declarations → Axioms → Close
    """
    import html
    import re
    
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
    
    lesson_title = make_id(lesson.get('title', f"Lesson_{lesson.get('id')}"))
    lesson_id = lesson.get('id', 'unknown')
    ontology_iri = f"http://example.org/educational-ontology/{lesson_title}"
    
    # Collect concepts
    concepts = {}
    try:
        from database import db
        sections = db.get_sections_for_lesson(lesson_id) or []
        for section in sections:
            section_los = db.get_learning_objects_for_section(section['id']) or []
            for lo in section_los:
                title = lo['title']
                concepts[title] = {
                    'type': lo.get('object_type', 'concept'),
                    'description': lo.get('description', ''),
                    'section': section.get('title', '')
                }
    except:
        pass
    
    # Also from relationships
    for rel in relationships:
        if not rel:
            continue
        source = rel.get('source_title') or rel.get('source', '')
        target = rel.get('target_title') or rel.get('target', '')
        if source and source not in concepts:
            concepts[source] = {'type': 'concept', 'description': '', 'section': ''}
        if target and target not in concepts:
            concepts[target] = {'type': 'concept', 'description': '', 'section': ''}
    
    # Group by section
    section_categories = {}
    for title, info in concepts.items():
        if not info:
            continue
        section = info.get('section', '')
        if section:
            if section not in section_categories:
                section_categories[section] = []
            section_categories[section].append(title)
    
    # ============= BUILD OWL IN CORRECT ORDER =============
    # Step 1: XML Declaration
    owl = '<?xml version="1.0"?>\n'
    
    # Step 2: Ontology tag with ALL namespaces (EXACTLY like template)
    owl += f'''<Ontology xmlns="http://www.w3.org/2002/07/owl#"
     xml:base="{ontology_iri}"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     ontologyIRI="{ontology_iri}">
    '''
    
    # Step 3: Prefix declarations
    owl += '''    <Prefix name="" IRI="http://www.w3.org/2002/07/owl#"/>
    <Prefix name="owl" IRI="http://www.w3.org/2002/07/owl#"/>
    <Prefix name="rdf" IRI="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>
    <Prefix name="xml" IRI="http://www.w3.org/XML/1998/namespace"/>
    <Prefix name="xsd" IRI="http://www.w3.org/2001/XMLSchema#"/>
    <Prefix name="rdfs" IRI="http://www.w3.org/2000/01/rdf-schema#"/>
    '''
    owl += f'    <Prefix name="edu" IRI="{ontology_iri}#"/>\n'
    
    # Step 4: ALL CLASS DECLARATIONS (before any axioms)
    owl += '\n    <!-- CLASS DECLARATIONS -->\n'
    
    # Declare base classes
    base_classes = ['LearningObject', 'Concept', 'Definition', 'Procedure', 'Example', 
                    'Principle', 'Fact', 'Theory', 'Process', 'Section']
    for cls in base_classes:
        owl += f'    <Declaration>\n        <Class IRI="#{cls}"/>\n    </Declaration>\n'
    
    # Declare section classes
    for section_name in sorted(section_categories.keys()):
        section_id = make_id(section_name)
        owl += f'    <Declaration>\n        <Class IRI="#{section_id}_Section"/>\n    </Declaration>\n'
    
    # Declare concept classes
    for concept_title in sorted(concepts.keys()):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'    <Declaration>\n        <Class IRI="#{concept_id}"/>\n    </Declaration>\n'
    
    # Step 5: OBJECT PROPERTY DECLARATIONS
    owl += '\n    <!-- OBJECT PROPERTY DECLARATIONS -->\n'
    object_props = ['prerequisite', 'builds_upon', 'part_of', 'related_to', 'contrasts_with',
                   'implements', 'enables', 'is_example_of', 'defines', 'uses', 'hasPart',
                   'belongsToSection', 'is_type_of']
    for prop in object_props:
        owl += f'    <Declaration>\n        <ObjectProperty IRI="#{prop}"/>\n    </Declaration>\n'
    
    # Step 6: DATA PROPERTY DECLARATIONS
    owl += '\n    <!-- DATA PROPERTY DECLARATIONS -->\n'
    data_props = ['hasDescription', 'hasKeywords', 'hasObjectType', 'hasOrderIndex', 'hasContent']
    for prop in data_props:
        owl += f'    <Declaration>\n        <DataProperty IRI="#{prop}"/>\n    </Declaration>\n'
    
    # Step 7: NAMED INDIVIDUAL DECLARATIONS
    owl += '\n    <!-- NAMED INDIVIDUAL DECLARATIONS -->\n'
    
    # Declare section instances
    for section_name in sorted(section_categories.keys()):
        section_id = make_id(section_name)
        owl += f'    <Declaration>\n        <NamedIndividual IRI="#{section_id}_Section_inst"/>\n    </Declaration>\n'
    
    # Declare concept instances
    for concept_title in sorted(concepts.keys()):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'    <Declaration>\n        <NamedIndividual IRI="#{concept_id}_inst"/>\n    </Declaration>\n'
    
    # ========== NOW ADD AXIOMS (after ALL declarations) ==========
    
    # Step 8: SUBCLASS OF AXIOMS
    owl += '\n    <!-- SUBCLASS AXIOMS -->\n'
    
    # Base type hierarchy
    for cls in ['Concept', 'Definition', 'Procedure', 'Example', 'Principle', 'Fact', 'Theory', 'Process']:
        owl += f'    <SubClassOf>\n        <Class IRI="#{cls}"/>\n        <Class IRI="#LearningObject"/>\n    </SubClassOf>\n'
    
    # Section hierarchy
    for section_name in sorted(section_categories.keys()):
        section_id = make_id(section_name)
        owl += f'    <SubClassOf>\n        <Class IRI="#{section_id}_Section"/>\n        <Class IRI="#Section"/>\n    </SubClassOf>\n'
    
    # Concept type hierarchy
    for concept_title in sorted(concepts.keys()):
        if concept_title:
            concept_id = make_id(concept_title)
            obj_type = concepts[concept_title].get('type', 'concept').lower()
            if obj_type not in ['concept', 'definition', 'procedure', 'example', 'principle', 'fact', 'theory', 'process']:
                obj_type = 'concept'
            obj_type = obj_type.capitalize()
            owl += f'    <SubClassOf>\n        <Class IRI="#{concept_id}"/>\n        <Class IRI="#{obj_type}"/>\n    </SubClassOf>\n'
    
    # Relationship-based SubClassOf
    relationships_added = set()
    for rel in relationships:
        if not rel:
            continue
        source = rel.get('source_title') or rel.get('source', '')
        target = rel.get('target_title') or rel.get('target', '')
        rel_type = rel.get('relationship_type', 'part_of').lower()
        
        if rel_type in ['part_of', 'is_a', 'subclass_of'] and source and target:
            source_id = make_id(source)
            target_id = make_id(target)
            pair = (source_id, target_id)
            if pair not in relationships_added:
                owl += f'    <SubClassOf>\n        <Class IRI="#{source_id}"/>\n        <Class IRI="#{target_id}"/>\n    </SubClassOf>\n'
                relationships_added.add(pair)
    
    # Step 9: CLASS ASSERTIONS (individuals belong to classes)
    owl += '\n    <!-- CLASS ASSERTIONS -->\n'
    
    for concept_title in sorted(concepts.keys()):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'    <ClassAssertion>\n        <Class IRI="#{concept_id}"/>\n        <NamedIndividual IRI="#{concept_id}_inst"/>\n    </ClassAssertion>\n'
    
    for section_name in sorted(section_categories.keys()):
        section_id = make_id(section_name)
        owl += f'    <ClassAssertion>\n        <Class IRI="#{section_id}_Section"/>\n        <NamedIndividual IRI="#{section_id}_Section_inst"/>\n    </ClassAssertion>\n'
    
    # Step 10: OBJECT PROPERTY ASSERTIONS (relationships)
    owl += '\n    <!-- OBJECT PROPERTY ASSERTIONS -->\n'
    
    # belongsToSection relationships
    for section_name, concepts_in_section in section_categories.items():
        section_id = make_id(section_name)
        for concept_title in concepts_in_section:
            concept_id = make_id(concept_title)
            owl += f'    <ObjectPropertyAssertion>\n        <ObjectProperty IRI="#belongsToSection"/>\n        <NamedIndividual IRI="#{concept_id}_inst"/>\n        <NamedIndividual IRI="#{section_id}_Section_inst"/>\n    </ObjectPropertyAssertion>\n'
    
    # User-provided relationships
    for rel in relationships:
        if not rel:
            continue
        source = rel.get('source_title') or rel.get('source', '')
        target = rel.get('target_title') or rel.get('target', '')
        rel_type = rel.get('relationship_type', 'related_to')
        
        if source and target and source in concepts and target in concepts:
            source_id = make_id(source)
            target_id = make_id(target)
            owl += f'    <ObjectPropertyAssertion>\n        <ObjectProperty IRI="#{rel_type}"/>\n        <NamedIndividual IRI="#{source_id}_inst"/>\n        <NamedIndividual IRI="#{target_id}_inst"/>\n    </ObjectPropertyAssertion>\n'
    
    # Step 11: DATA PROPERTY ASSERTIONS
    owl += '\n    <!-- DATA PROPERTY ASSERTIONS -->\n'
    
    for concept_title in sorted(concepts.keys()):
        if concept_title:
            concept_id = make_id(concept_title)
            info = concepts[concept_title]
            obj_type = info.get('type', 'concept')
            description = escape_xml(info.get('description', ''))
            
            owl += f'    <DataPropertyAssertion>\n        <DataProperty IRI="#hasObjectType"/>\n        <NamedIndividual IRI="#{concept_id}_inst"/>\n        <Literal>{obj_type}</Literal>\n    </DataPropertyAssertion>\n'
            
            if description:
                owl += f'    <DataPropertyAssertion>\n        <DataProperty IRI="#hasDescription"/>\n        <NamedIndividual IRI="#{concept_id}_inst"/>\n        <Literal>{description}</Literal>\n    </DataPropertyAssertion>\n'
    
    # Step 12: ANNOTATION ASSERTIONS
    owl += '\n    <!-- ANNOTATION ASSERTIONS -->\n'
    
    for concept_title in sorted(concepts.keys()):
        if concept_title:
            concept_id = make_id(concept_title)
            owl += f'    <AnnotationAssertion>\n        <AnnotationProperty abbreviatedIRI="rdfs:label"/>\n        <IRI>#{concept_id}</IRI>\n        <Literal>{escape_xml(concept_title)}</Literal>\n    </AnnotationAssertion>\n'
    
    # Step 13: Close ontology
    owl += '\n</Ontology>\n\n<!-- Generated by Educational Ontology Generator -->\n'
    
    return owl
