# Ontology Management - Visual Guide

## New Workflow Steps

### Step 1: Parse Content (Existing)
```
Upload PDF Lesson
        ↓
Click "Parse" Button in Lesson Manager
        ↓
AI Extracts:
- Sections
- Learning Objects
        ↓
View in Content Viewer
```

### Step 2: Generate/Manage Ontology (NEW - Now Separate)
```
In Content Viewer, scroll to "Domain Ontology" section
        ↓
┌─────────────────────────────────────────────────────┐
│  Domain Ontology                   [5 Relationships]  │
├─────────────────────────────────────────────────────┤
│  [🔄 Regenerate] [🗑️ Clear] [⬇️ Download OWL] [Show] │
└─────────────────────────────────────────────────────┘
```

## Button Descriptions

### 🔄 Regenerate Button (Blue/Info Color)
**Location**: Right side of "Domain Ontology" header

**What it does**:
- Analyzes current sections and learning objects
- Uses AI to extract semantic relationships
- Creates a new, updated ontology
- Replaces the current ontology completely

**When to use**:
- After creating/editing sections
- After adding/removing learning objects
- To update relationships with current content
- To test different relationship extractions

**Confirmation**: Yes, shows dialog asking for confirmation

---

### 🗑️ Clear Button (Orange/Warning Color)
**Location**: Right side of "Domain Ontology" header, next to Regenerate

**What it does**:
- Removes ALL ontology relationships
- Leaves sections and learning objects intact
- Returns ontology to empty state

**When to use**:
- To start fresh with a new ontology
- To remove low-quality relationships
- Before regenerating with updated AI models

**Confirmation**: Yes, shows dialog with warning

**Enabled**: Only when ontology has relationships

---

### ⬇️ Download OWL Button (Primary Blue)
**Location**: Right side, after Regenerate and Clear buttons

**What it does**:
- Exports ontology in proper OWL/RDF-XML format
- Uses industry-standard structure
- Compatible with Protégé and other OWL editors

**File Format**:
```xml
<?xml version="1.0"?>
<!DOCTYPE Ontology [...]>
<Ontology xmlns="http://www.w3.org/2002/07/owl#">
    <!-- Declarations -->
    <Declaration>
        <Class IRI="#ConceptName"/>
    </Declaration>
    
    <!-- Relationships -->
    <ObjectPropertyAssertion>
        <ObjectProperty IRI="#relationshipType"/>
        <NamedIndividual IRI="#concept1_instance"/>
        <NamedIndividual IRI="#concept2_instance"/>
    </ObjectPropertyAssertion>
    ...
</Ontology>
```

**Enabled**: Only when ontology has relationships

---

## Complete User Journey Example

### Scenario: Create a Quiz from a New Lesson

1. **Upload PDF**
   - Click "📄 Upload PDF Lesson"
   - Select a PDF file (e.g., "Virtual_Memory.pdf")
   - System uploads and stores the file

2. **Parse Lesson (STEP 1)**
   - Click "🔍 Parse" button in lesson card
   - Wait for AI to analyze content
   - System extracts sections and learning objects
   - Notification: "Parsed 3 sections with 12 learning objects!"

3. **Review Content**
   - Click on lesson to open Content Viewer
   - Expand sections to view learning objects
   - Edit/refine sections and learning objects if needed
   - Verify structure matches your expectations

4. **Generate Ontology (STEP 2)**
   - Scroll to "Domain Ontology" section
   - Click "🔄 Regenerate" button
   - Confirm in dialog
   - Wait for AI to extract relationships
   - See notification: "Regenerated 8 ontology relationships"

5. **Review Ontology**
   - Click "Show" to expand ontology table
   - Review extracted relationships
   - Delete any incorrect relationships using "Delete" buttons
   - If unsatisfied, click "🗑️ Clear" and "🔄 Regenerate" again

6. **Export Ontology**
   - Click "⬇️ Download OWL" button
   - File "ontology_Virtual_Memory.owl" is downloaded
   - Open in Protégé to visualize or further edit

7. **Generate Questions**
   - Proceed to Question Generator
   - Select sections and learning objects
   - Generate SOLO-level questions from parsed content

---

## Keyboard Shortcuts & Tips

- **Double-click ontology row**: View relationship details
- **Delete button in table**: Remove individual relationships
- **Clear button**: Fastest way to start fresh
- **Regenerate button**: Fastest way to update

---

## FAQ

**Q: Why are sections and ontology now separate?**
A: This allows you to edit and refine sections before generating the ontology, giving you more control over the quality of extracted relationships.

**Q: Can I regenerate multiple times?**
A: Yes! Each regenerate clears the old ontology and creates a new one. This is useful for testing.

**Q: What if regenerate doesn't find good relationships?**
A: Try:
1. Ensure sections and learning objects have clear titles
2. Add more descriptive content to learning objects
3. Regenerate again - AI may find different relationships
4. Manually add relationships using the Content Viewer

**Q: How do I know if my OWL file is correct?**
A: Open it in Protégé. It should:
- Load without errors
- Show all your learning objects as classes
- Display relationships between them
- Have proper annotations and labels

**Q: Can I edit ontology relationships in the UI?**
A: Currently you can only delete individual relationships. To edit, you would:
1. Clear the ontology
2. Regenerate with different content
3. Or manually edit the downloaded OWL file and reimport

---

## Color Coding

| Color | Meaning | Examples |
|-------|---------|----------|
| 🔵 Blue (Primary) | Main action | Download, Confirm |
| 🟦 Info/Blue | Constructive change | Regenerate, Create |
| 🟧 Warning/Orange | Destructive action | Clear, Delete |
| ✅ Green | Success | Parsed, Saved |
| ⚠️ Red | Error/Critical | Failed, Error |

