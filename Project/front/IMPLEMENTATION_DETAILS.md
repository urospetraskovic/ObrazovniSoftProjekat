# Implementation Details - Ontology Restructuring

## Technical Architecture

### Backend Flow

#### Clear Ontology Flow
```
POST /api/lessons/{lessonId}/ontology/clear
  ↓
1. Fetch lesson from database
2. Get all relationships for this lesson
3. Loop through each relationship and delete it
4. Return cleared_count
```

#### Regenerate Ontology Flow
```
POST /api/lessons/{lessonId}/ontology/regenerate
  ↓
1. Fetch lesson with raw_content
2. Get all sections for the lesson
3. Get all learning objects from all sections
4. Create mapping: LO_title → LO_id
5. Call content_parser.extract_ontology_relationships()
6. Get existing relationships and delete them
7. For each extracted relationship:
   - Lookup source_id from title mapping
   - Lookup target_id from title mapping
   - If both found, create relationship in DB
8. Return regenerated_count
```

### Frontend Flow

#### Clear Button Handler
```javascript
handleClearOntology()
  ↓
1. Show confirmation dialog
2. If confirmed:
   - Set loading = true
   - Call lessonApi.clearOntology()
   - Clear local ontology state
   - Show success message
   - Set loading = false
```

#### Regenerate Button Handler
```javascript
handleRegenerateOntology()
  ↓
1. Show confirmation dialog
2. If confirmed:
   - Set loading = true
   - Call lessonApi.regenerateOntology()
   - Show success with count
   - Fetch fresh ontology data
   - Update UI with new relationships
   - Set loading = false
```

---

## Code Structure

### Backend Changes (`app.py`)

#### 1. OWL Generator Function
**Location**: Lines ~25-165  
**Function**: `generate_owl_from_relationships(lesson, relationships)`  
**Key Components**:
- XML declaration and DOCTYPE
- Namespace declarations
- Ontology metadata
- Class declarations
- ObjectProperty declarations
- SubClass axioms
- ObjectProperty assertions
- Class assertions
- Data property assertions
- Annotation assertions

**Sample Output Structure**:
```xml
<?xml version="1.0"?>
<!DOCTYPE Ontology [...]>
<Ontology xmlns="http://www.w3.org/2002/07/owl#" ...>
    <Prefix name="" IRI="http://www.w3.org/2002/07/owl#"/>
    
    <!-- Declarations -->
    <Declaration>
        <Class IRI="#Concept_Name"/>
    </Declaration>
    
    <!-- Assertions -->
    <ObjectPropertyAssertion>
        <ObjectProperty IRI="#relationship_type"/>
        <NamedIndividual IRI="#concept1_instance"/>
        <NamedIndividual IRI="#concept2_instance"/>
    </ObjectPropertyAssertion>
</Ontology>
```

#### 2. Clear Ontology Endpoint
**Location**: Lines ~548-576  
**Route**: `POST /api/lessons/<lesson_id>/ontology/clear`  
**Parameters**: lesson_id (URL param)  
**Returns**:
```python
{
    'message': 'Ontology cleared successfully',
    'cleared_count': int
}
```

#### 3. Regenerate Ontology Endpoint
**Location**: Lines ~578-643  
**Route**: `POST /api/lessons/<lesson_id>/ontology/regenerate`  
**Parameters**: lesson_id (URL param)  
**Process**:
1. Validates lesson exists and has content
2. Collects all learning objects with ID mapping
3. Calls AI provider to extract relationships
4. Clears old relationships
5. Saves new relationships to database
**Returns**:
```python
{
    'message': 'Ontology regenerated successfully',
    'regenerated_count': int
}
```

---

### Frontend Changes

#### API Client (`api.js`)
**File**: `frontend/src/api.js`  
**Lines**: ~40-41  
**Added Methods**:
```javascript
clearOntology: (lessonId) => apiClient.post(`/lessons/${lessonId}/ontology/clear`),
regenerateOntology: (lessonId) => apiClient.post(`/lessons/${lessonId}/ontology/regenerate`),
```

#### Content Viewer Component (`ContentViewer.js`)
**File**: `frontend/src/components/ContentViewer.js`

**New Event Handlers** (Lines ~176-219):
- `handleClearOntology()` - Calls API and clears local state
- `handleRegenerateOntology()` - Calls API and refreshes ontology

**UI Changes** (Lines ~245-320):
- Added "Regenerate" button (🔄) with blue styling
- Added "Clear" button (🗑️) with orange/warning styling
- Buttons positioned in ontology section header
- Buttons have proper disabled states and loading feedback
- Hover effects on buttons
- Proper spacing and layout

**Button Styles**:
```javascript
// Regenerate Button
{
  background: 'var(--info-600)',
  color: 'white',
  cursor: loading ? 'not-allowed' : 'pointer',
  opacity: loading ? 0.6 : 1,
  onHover: background → 'var(--info-700)'
}

// Clear Button  
{
  background: 'var(--warning-600)',
  color: 'white',
  disabled: loading || ontology.length === 0,
  opacity: (loading || empty) ? 0.6 : 1,
  onHover: background → 'var(--warning-700)'
}
```

#### Lesson Manager Component (`LessonManager.js`)
**File**: `frontend/src/components/LessonManager.js`  
**Lines**: ~165-175  
**Change**: Updated workflow help section to clarify 2-step process

**Old Text**:
```
1. Upload
2. Parse
3. Review
4. Generate
```

**New Text**:
```
1. Upload
2. Parse (Step 1)
3. Review
4. Generate Ontology (Step 2)
5. Generate Questions
```

---

## Error Handling

### Backend Error Cases

#### Clear Ontology
- **404**: Lesson not found
- **500**: Database error during deletion

#### Regenerate Ontology
- **404**: Lesson not found
- **400**: No content to extract from (lesson not parsed)
- **400**: No learning objects found
- **500**: AI provider error or database error

### Frontend Error Handling
```javascript
try {
  // Call API
} catch (err) {
  // Extract error message
  const errorMsg = err.response?.data?.error || 'Failed to [action]';
  // Call onError handler which shows notification
  onError(errorMsg);
} finally {
  // Always cleanup loading state
  setLoading(false);
}
```

---

## Database Interactions

### Relationships Table Structure
```python
class ConceptRelationship(Base):
    id                  : Integer (Primary Key)
    source_id           : Integer (FK to learning_objects)
    target_id           : Integer (FK to learning_objects)
    relationship_type   : String (prerequisite, part_of, etc.)
    description         : Text
    created_at          : DateTime
```

### Clear Operation
```sql
DELETE FROM concept_relationships 
WHERE id IN (
  SELECT r.id FROM concept_relationships r
  JOIN learning_objects lo ON r.source_id = lo.id
  JOIN sections s ON lo.section_id = s.id
  WHERE s.lesson_id = {lesson_id}
)
```

### Regenerate Operation
1. Get all learning objects for lesson
2. Call AI extraction (content_parser)
3. Delete all existing relationships
4. Insert new relationships in bulk

---

## Performance Considerations

### Clear Operation
- **Time**: O(n) where n = number of relationships
- **Database**: DELETE operations (indexed by lesson_id via FK)
- **Bottleneck**: If many relationships exist, deletion could take time

### Regenerate Operation
- **Time**: 
  - DB queries: O(1) for lesson, O(m) for sections
  - AI call: 5-15 minutes (main bottleneck)
  - DB inserts: O(k) where k = extracted relationships
- **Bottleneck**: AI provider response time (content_parser.extract_ontology_relationships)

### Optimization Ideas
1. Batch delete using IN clause (already done)
2. Cache learning object mappings
3. Async processing for long-running AI calls
4. Rate limiting on regenerate calls

---

## Testing Checklist

### Manual Testing

- [ ] Upload lesson PDF
- [ ] Parse lesson (Step 1)
- [ ] Open Content Viewer
- [ ] Verify ontology relationships show up
- [ ] Click "Regenerate" button
  - [ ] Confirmation dialog appears
  - [ ] Loading spinner shows
  - [ ] Success message displays with count
  - [ ] Relationships update in table
- [ ] Click "Clear" button
  - [ ] Confirmation dialog appears (warning message)
  - [ ] Relationships disappear
  - [ ] Success message shows count cleared
  - [ ] Button becomes disabled (no relationships)
- [ ] Click "Download OWL"
  - [ ] File downloads
  - [ ] File contains proper XML structure
  - [ ] File opens in text editor
  - [ ] File imports into Protégé without errors
- [ ] Delete individual relationships
- [ ] Regenerate again
  - [ ] New relationships are generated
  - [ ] Old deleted ones may or may not return

### Edge Cases

- [ ] Lesson with no content (raw_content = null)
- [ ] Lesson with no sections yet (not parsed)
- [ ] Lesson with sections but no learning objects
- [ ] Lesson with relationships but AI fails to regenerate
- [ ] Rapid clicks on Regenerate button (debounce?)
- [ ] Network error during regenerate

### Browser DevTools

- [ ] Console has no errors
- [ ] Network tab shows correct API calls
- [ ] Loading state managed properly
- [ ] Buttons disabled/enabled appropriately
- [ ] Responsive on mobile/tablet

---

## Future Enhancements

1. **Batch Operations**: Clear/regenerate multiple lessons
2. **Relationship Editing**: Edit relationships in UI instead of just delete
3. **AI Model Selection**: Choose which AI model to use for extraction
4. **Relationship Filtering**: Filter ontology by type, strength, etc.
5. **Visualization**: Display ontology as graph/network diagram
6. **Undo/Redo**: Support undo for clear/regenerate operations
7. **Version Control**: Track ontology versions over time
8. **Export Formats**: Support additional ontology formats (RDF, Turtle, etc.)
9. **Import**: Import ontologies from external OWL files
10. **Validation**: Validate ontology against SHACL constraints
