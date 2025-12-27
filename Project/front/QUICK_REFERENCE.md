# Quick Reference - Ontology Management

## What Changed?

### ✅ New Buttons in Content Viewer
1. **🔄 Regenerate** - Create new ontologies from sections/learning objects
2. **🗑️ Clear** - Remove all ontology relationships
3. **⬇️ Download OWL** - Export (existing, now improved format)

### ✅ Workflow Now 2 Steps
- **Step 1**: Parse (extract sections & learning objects)
- **Step 2**: Generate Ontology (create relationships)

### ✅ Better OWL Format
- Proper XML structure
- Industry-standard format
- Compatible with Protégé
- Includes declarations, assertions, annotations

---

## Where to Find Things

### In Content Viewer
Scroll to **"Domain Ontology"** section (shows number of relationships)

```
┌─────────────────────────────────────────────────────┐
│ Domain Ontology                     [5 Relationships] │
└─────────────────────────────────────────────────────┘
│ [🔄 Regenerate] [🗑️ Clear] [⬇️ Download OWL] [Show] │
└─────────────────────────────────────────────────────┘
```

### Backend API Endpoints
- `POST /api/lessons/{id}/ontology/clear`
- `POST /api/lessons/{id}/ontology/regenerate`
- `GET /api/lessons/{id}/ontology/export/owl` (existing, improved)

---

## Button Usage Chart

| Button | Action | When to Use | Confirmation | Color |
|--------|--------|------------|--------------|-------|
| 🔄 Regenerate | Create new ontologies | After editing sections/LOs | Yes | Blue 🔵 |
| 🗑️ Clear | Delete all relationships | Start fresh, before regenerate | Yes | Orange 🟧 |
| ⬇️ Download OWL | Export as OWL file | When happy with ontology | No | Blue 🔵 |
| 📋 Table Delete | Remove one relationship | Fix bad relationships | No | - |
| 🔍 Show/Hide | Expand/collapse table | View relationships | No | - |

---

## Common Workflows

### Workflow A: Create Ontology
```
1. Upload PDF
2. Parse (Step 1)
3. Review sections/LOs
4. Click "🔄 Regenerate" → Click "Generate Ontology" (Step 2)
5. Review relationships
6. Click "⬇️ Download OWL"
```

### Workflow B: Fix Bad Ontology
```
1. Review relationships
2. Delete bad ones (click "Delete" in table)
3. OR click "🗑️ Clear" to start over
4. Click "🔄 Regenerate"
5. Download new OWL
```

### Workflow C: Update After Editing Content
```
1. Edit sections/learning objects
2. Click "🔄 Regenerate"
3. Relationships update automatically
4. Download new OWL
```

---

## Response Messages

### Success Messages
```
"Regenerated 8 ontology relationships"
"Cleared 8 relationships successfully"
"Ontology exported successfully"
```

### Error Messages
```
"Lesson has no content to extract relationships from"
"No learning objects to create ontology from. Parse the lesson first."
"Failed to regenerate ontology"
```

---

## Color Meanings

- 🔵 **Blue**: Main/safe action
- 🔵 **Info Blue**: Constructive action (regenerate)
- 🟧 **Orange/Warning**: Destructive action (clear)
- ✅ **Green**: Success notification
- ❌ **Red**: Error notification

---

## Files Changed

| File | Changes |
|------|---------|
| `app.py` | OWL generator, 2 new endpoints |
| `api.js` | 2 new API methods |
| `ContentViewer.js` | 2 new buttons, 2 handlers |
| `LessonManager.js` | Updated workflow description |

---

## How to Use Each Button

### 🔄 Regenerate Button
```
1. Click button
2. Dialog: "Regenerate ontology relationships?"
3. Click "OK" to confirm
4. System thinks... (AI processing)
5. Success: "Regenerated X relationships"
6. Relationships update in table below
```

**Result**: New ontology based on current sections & learning objects

### 🗑️ Clear Button
```
1. Click button
2. Dialog: "Clear ALL ontology relationships?"
3. Click "OK" to confirm
4. Relationships disappear immediately
5. Success: "Cleared X relationships"
```

**Result**: Ontology table is empty

### ⬇️ Download OWL Button
```
1. Click button
2. File "ontology_[LessonName].owl" downloads
3. Open file with:
   - Text editor (view XML)
   - Protégé (visualize/edit)
   - Any OWL-compatible tool
```

**Result**: OWL file saved to Downloads folder

---

## Troubleshooting

**Q: Regenerate button doesn't appear**
A: You need to parse the lesson first (Step 1). Parse will extract sections & learning objects.

**Q: Regenerate not creating relationships**
A: 
- Make sure sections have clear titles
- Ensure learning objects have descriptive names
- Check lesson content has enough information
- Try regenerating again (AI varies)

**Q: Clear button is disabled**
A: There are no relationships to clear. Generate/regenerate first.

**Q: Download button not working**
A: There are no relationships to export. Generate/regenerate first.

**Q: OWL file looks wrong**
A: Open in Protégé to validate. If errors:
- Check section/learning object names
- Regenerate and try again
- Report the issue

---

## Next Steps After Creating Ontology

1. ✅ Download OWL file
2. ✅ Open in Protégé to visualize
3. ✅ Use sections + ontology for question generation
4. ✅ Build quizzes from questions
5. ✅ Export quiz as PDF or JSON

---

## Version Info

- **Version**: 2.0
- **Date**: December 2025
- **Status**: Released
- **Features**: Proper OWL, Regenerate, Clear, 2-step workflow

